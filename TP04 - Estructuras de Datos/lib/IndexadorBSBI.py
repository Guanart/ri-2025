from collections import Counter
import os
import pickle
import heapq
import time
from bs4 import BeautifulSoup
from typing import Dict

from lib.CollectionAnalyzerBase import CollectionAnalyzerBase
from lib.Tokenizador import Tokenizador
from lib.PartialPosting import PartialPosting
from lib.PostingChunk import PostingChunk
from lib.Posting import Posting


class IndexadorBSBI(CollectionAnalyzerBase):
    # Constantes de archivos y tamaños
    VOCABULARY_FILENAME = "vocabulary.pkl"
    POSTINGS_FILENAME = "final_index.bin"
    METADATA_FILENAME = "metadata.pkl"
    SKIPS_FILENAME = "skips.pkl"
    DOC_VECTORS_FILENAME = "doc_vectors.pkl"
    DOCID_SIZE = 4  # bytes
    FREQ_SIZE = 4  # bytes
    POSTING_STRUCT_FORMAT = "II"  # 2 unsigned ints
    POSTING_SIZE = DOCID_SIZE + FREQ_SIZE  # 8 bytes

    def __init__(
        self,
        tokenizer: Tokenizador,
        memory_limit: int = 1000,
        path_index: str = "index",
    ):
        super().__init__(tokenizer)
        self.memory_limit: int = memory_limit
        self.memory_usage: int = 0
        self.path_index: str = path_index
        self.vocabulary: Dict[str, Dict[str, int]] = (
            {}
        )  # término -> {"df": ..., "puntero": ...}
        self.chunks: list[str] = []  # paths a los archivos de chunks
        self.term2id: Dict[str, int] = {}
        self.id2term: Dict[int, str] = {}
        self.doc_id_map: Dict[int, str] = {}  # doc_id -> nombre del archivo
        self._doc_vectors = None  # Siempre None al inicio, se carga si existe

    def index_collection(self, docs_path: str) -> None:
        """
        Indexa la colección usando BSBI. Procesa bloques de n documentos, vuelca a disco y mergea los chunks.
        Mide y reporta los tiempos de indexado y merge por separado.
        """
        os.makedirs(self.path_index, exist_ok=True)
        doc_id: int = 0
        current_chunk_postings: list[PartialPosting] = []

        print("Iniciando indexado (BSBI)...")
        t_index_start = time.time()

        # Recorre recursivamente el directorio
        for root, _, files in os.walk(docs_path):
            for fname in files:
                # Validar memoria. Si se supera el límite, procesar el chunk actual y reiniciar
                if self.memory_usage > self.memory_limit:
                    self._process_chunk(
                        current_chunk_postings
                    )  # BSBI-Invert(block) de la diapositiva
                    current_chunk_postings = []
                    self.memory_usage = 0

                # ParseNextBlock() de la diapositiva
                if fname.endswith((".html", ".txt")):
                    self.memory_usage += 1
                    doc_id += 1
                    print(
                        f"\rProcesando documento {doc_id}: {fname}", end="", flush=True
                    )
                    tokens, doc_name = self._process_doc(fname, root, docs_path)
                    terms_freq = Counter(tokens)
                    for token, freq in terms_freq.items():
                        if token not in self.term2id:
                            self.term2id[token] = len(self.term2id) + 1
                            self.id2term[self.term2id[token]] = token
                        term_id = self.term2id[token]
                        current_chunk_postings.append(
                            PartialPosting(term_id, doc_id, freq)
                        )
                    self.doc_id_map[doc_id] = doc_name
                    # --- GUARDAR VECTOR DEL DOCUMENTO ---
                    if self._doc_vectors is None:
                        self._doc_vectors = {}
                    self._doc_vectors[doc_id] = terms_freq.copy()

        # Procesar el último chunk
        if len(current_chunk_postings) > 0:
            self._process_chunk(current_chunk_postings)
            current_chunk_postings = []

        t_index_end = time.time()
        print(
            f"\nTiempo de indexado (volcado parcial): {t_index_end - t_index_start:.2f} segundos"
        )

        print("Iniciando merge de chunks...")
        t_merge_start = time.time()
        self._merge_chunks()
        t_merge_end = time.time()
        print(f"Tiempo de merge: {t_merge_end - t_merge_start:.2f} segundos")

        self._write_vocabulary()
        self._write_metadata()
        if self._doc_vectors is not None:
            self._write_doc_vectors()

    def _process_doc(self, fname: str, root: str, path: str) -> tuple[list[str], str]:
        with open(os.path.join(root, fname), encoding="utf8", errors="ignore") as f:
            text = f.read()
            if fname.endswith(".html"):
                text: str = BeautifulSoup(text, "html.parser").get_text(separator=" ")
                """
                ACÁ SE PODRÍA HACER UN PARSEO MÁS COMPLEJO DEL HTML (usando BeautifulSoup)
                """
        tokens = self.tokenizer.tokenizar(text)
        doc_name = os.path.relpath(os.path.join(root, fname), path)
        return tokens, doc_name

    def _process_chunk(self, chunk: list[PartialPosting]) -> None:
        """
        Procesa un bloque (chunk) de documentos, construye el índice parcial y lo vuelca a disco.
        Devuelve el path al archivo de chunk generado.
        """
        # Ordenar postings por término y doc_id
        chunk.sort(
            key=lambda partial_posting: (
                partial_posting.term_id,
                partial_posting.doc_id,
            )
        )

        # Crear PostingChunk y escribir en disco
        chunk_file_path = os.path.join(self.path_index, f"chunk_{len(self.chunks)}.bin")
        chunk_obj = PostingChunk(chunk, chunk_file_path)
        chunk_obj.write_to_disk()  # WriteBlockToDisk(block) de la diapositiva
        self.chunks.append(chunk_file_path)

    def _process_skip_list(self, posting_list, posting_offsets):
        """
        Dada una posting list y sus offsets, calcula la skip list [(docid, offset_byte), ...].
        """
        df = len(posting_list)
        if df == 0:
            return []
        k = int(df**0.5)
        if k == 0:
            return []
        skips = []
        for skip_idx in range(0, df, k):
            docid = posting_list[skip_idx].doc_id
            byte_offset = posting_offsets[skip_idx]
            skips.append((docid, byte_offset))
        return skips

    def _merge_chunks(self) -> None:
        """
        Hace el merge de los chunks parciales para crear el índice final en disco, siguiendo el algoritmo multi-way merge según MAN08.
        Utiliza PostingChunk en modo lectura secuencial para cada chunk.
        """
        chunk_objs = [PostingChunk(file_path=chunk_path) for chunk_path in self.chunks]
        heap: list[tuple[int, int, int, PartialPosting]] = []
        # (term_id, doc_id, chunk_id, PartialPosting)
        for chunk_id, chunk in enumerate(chunk_objs):
            pp = chunk.get_current()
            if pp is not None:
                heapq.heappush(heap, (pp.term_id, pp.doc_id, chunk_id, pp))

        skips_dict: dict[str, list[tuple[int, int]]] = {}
        with open(
            self.path_index + f"/{self.POSTINGS_FILENAME}", "wb"
        ) as final_index_file:
            offset = 0
            current_term_id = None
            current_posting_list: list[Posting] = []
            current_posting_offsets: list[int] = []
            while heap:
                term_id, _, chunk_id, pp = heapq.heappop(heap)
                if current_term_id is None:
                    current_term_id = term_id
                if term_id != current_term_id:
                    self._write_posting_and_skips(
                        final_index_file,
                        current_term_id,
                        current_posting_list,
                        current_posting_offsets,
                        offset,
                        skips_dict,
                    )
                    offset += self.POSTING_SIZE * len(current_posting_list)
                    current_term_id = term_id
                    current_posting_list = []
                    current_posting_offsets = []
                current_posting_list.append(Posting(pp.doc_id, pp.freq))
                chunk = chunk_objs[chunk_id]
                chunk.next()
                next_pp = chunk.get_current()
                if next_pp is not None:
                    heapq.heappush(
                        heap, (next_pp.term_id, next_pp.doc_id, chunk_id, next_pp)
                    )
            else:
                if current_posting_list and current_term_id is not None:
                    self._write_posting_and_skips(
                        final_index_file,
                        current_term_id,
                        current_posting_list,
                        current_posting_offsets,
                        offset,
                        skips_dict,
                    )
        self._write_skip_lists(skips_dict)
        for chunk in chunk_objs:
            chunk.close()

    def _write_posting_and_skips(
        self,
        final_index_file,
        term_id,
        posting_list: list[Posting],
        posting_offsets: list[int],
        offset: int,
        skips_dict: dict[str, list[tuple[int, int]]],
    ):
        """
        Escribe la posting list y actualiza el vocabulario y skips_dict para el término dado.
        posting_offsets se llena correctamente con el offset en bytes de cada posting.
        """
        posting_offsets.clear()  # Asegura que esté vacía antes de empezar
        for i, posting in enumerate(posting_list):
            final_index_file.write(posting.to_bytes())
            posting_offsets.append(offset + i * self.POSTING_SIZE)
        self.vocabulary[self.id2term[term_id]] = {
            "puntero": offset,
            "df": len(posting_list),
        }
        skips = self._process_skip_list(posting_list, posting_offsets)
        if skips:
            skips_dict[self.id2term[term_id]] = skips
        posting_offsets.clear()  # Limpia para la próxima posting list

    def _write_skip_lists(self, skips_dict):
        skips_path = os.path.join(self.path_index, self.SKIPS_FILENAME)
        with open(skips_path, "wb") as f:
            print(f"Escribiendo skips en {skips_path}")
            pickle.dump(skips_dict, f)

    def _write_vocabulary(self) -> None:
        """
        Persiste el vocabulario en disco (por ejemplo, usando pickle).
        """
        vocab_path = os.path.join(self.path_index, self.VOCABULARY_FILENAME)
        with open(vocab_path, "wb") as f:
            print(f"Escribiendo vocabulario en {vocab_path}")
            pickle.dump(self.vocabulary, f)

    def _load_vocabulary(self) -> None:
        """
        Carga el vocabulario desde disco a memoria.
        """
        vocab_path = os.path.join(self.path_index, self.VOCABULARY_FILENAME)
        if os.path.exists(vocab_path):
            with open(vocab_path, "rb") as f:
                self.vocabulary = pickle.load(f)

    def get_vocabulary(self) -> Dict[str, Dict[str, int]]:
        """
        Devuelve el vocabulario cargado en memoria.
        """
        if not self.vocabulary:
            self._load_vocabulary()
        return self.vocabulary

    def _load_skips(self) -> None:
        skips_path = os.path.join(self.path_index, self.SKIPS_FILENAME)
        if os.path.exists(skips_path):
            with open(skips_path, "rb") as f:
                self.skips = pickle.load(f)

    def get_skips(self) -> dict:
        if not hasattr(self, "skips") or self.skips is None:
            self._load_skips()
        return self.skips if hasattr(self, "skips") else {}

    def index_size_on_disk(self) -> Dict[str, int]:
        """
        Devuelve el tamaño en bytes del índice en disco (postings y vocabulario).
        """
        postings_path = os.path.join(self.path_index, self.POSTINGS_FILENAME)
        vocab_path = os.path.join(self.path_index, self.VOCABULARY_FILENAME)
        size_postings = (
            os.path.getsize(postings_path) if os.path.exists(postings_path) else 0
        )
        size_vocab = os.path.getsize(vocab_path) if os.path.exists(vocab_path) else 0
        return {
            "size_postings": size_postings,
            "size_vocab": size_vocab,
        }

    def posting_list_sizes(self) -> list[int]:
        """
        Devuelve una lista con los tamaños (df) de todas las posting lists del vocabulario.
        """
        if not self.vocabulary:
            self._load_vocabulary()
        return [v["df"] for v in self.vocabulary.values()]

    def _write_metadata(self) -> None:
        """
        Persiste el doc_id_map en disco.
        """
        metadata_path = os.path.join(self.path_index, self.METADATA_FILENAME)
        with open(metadata_path, "wb") as f:
            print(f"Escribiendo metadata en {metadata_path}")
            pickle.dump(self.doc_id_map, f)

    def _load_metadata(self) -> None:
        """
        Carga el doc_id_map desde disco a memoria.
        """
        metadata_path = os.path.join(self.path_index, self.METADATA_FILENAME)
        if os.path.exists(metadata_path):
            with open(metadata_path, "rb") as f:
                self.doc_id_map = pickle.load(f)

    def get_doc_id_map(self) -> dict[int, str]:
        """
        Devuelve el doc_id_map cargado en memoria.
        """
        if not self.doc_id_map:
            self._load_metadata()
        return self.doc_id_map

    def _write_doc_vectors(self):
        """
        Guarda los vectores de documentos en un archivo pickle.
        """
        vectors_path = os.path.join(self.path_index, self.DOC_VECTORS_FILENAME)
        with open(vectors_path, "wb") as f:
            print(f"Escribiendo vectores de documentos en {vectors_path}")
            pickle.dump(self._doc_vectors, f)

    def _load_doc_vectors(self):
        if self._doc_vectors is None:
            vectors_path = os.path.join(self.path_index, self.DOC_VECTORS_FILENAME)
            if os.path.exists(vectors_path):
                with open(vectors_path, "rb") as f:
                    self._doc_vectors = pickle.load(f)
            else:
                self._doc_vectors = {}

    def get_doc_terms(self, docid: int) -> Counter:
        """
        Devuelve un Counter con los términos y frecuencias de un documento dado.
        Usa los vectores precalculados si están disponibles y activados.
        """
        self._load_doc_vectors()
        if self._doc_vectors is not None:
            return self._doc_vectors.get(docid, Counter())
        else:
            return Counter()

    # ESTO LO PUSE POR LA ABSTRACT CLASS

    def total_tokens(self) -> int:
        # No llevas la cuenta exacta, así que devolvemos 0 o podrías sumar frecuencias si lo implementas
        return 0

    def total_terminos(self) -> int:
        return len(self.term2id)
