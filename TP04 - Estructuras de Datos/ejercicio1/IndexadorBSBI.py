from collections import Counter
import os
import pickle
import heapq
import struct
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
        # self.postings_tmp = {}  # postings temporales en memoria (opcional)

        # En algún lugar tengo que definir el tamaño de los postings (en bytes), que contendrá: nombre del archivo, DOCID y frecuencia del término, en principio. La frecuencia del término es un entero (es importante para poder rankear), el DOCID es un entero y el nombre del archivo es una cadena de caracteres.
        #
        # La estructura de cada Posting es: DocName:docID:Frecuencia.
        # Usaremos UTF-8 con caracteres ASCII para el DocName, asi ocupan 1 byte por caracter.
        # Las consultas AND, OR y NOT se hacen entre listas de postings -> AND es intersección y OR es unión.

        # 1.1) Podría hacer una clase Vocabulario (o simplemente usar Pickle y persistir el diccionario)

    def index_collection(self, docs_path: str) -> None:
        """
        Indexa la colección usando BSBI. Procesa bloques de n documentos, vuelca a disco y mergea los chunks.
        """
        os.makedirs(self.path_index, exist_ok=True)
        doc_id: int = 0
        current_chunk_postings: list = []

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

        # Procesar el último chunk
        if len(current_chunk_postings) > 0:
            self._process_chunk(current_chunk_postings)
            current_chunk_postings = []

        self._merge_chunks()
        self._write_vocabulary()

    def _process_doc(self, fname: str, root: str, path: str) -> str:
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

    def _process_chunk(self, chunk: list[PartialPosting]) -> str:
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

    def _merge_chunks(self) -> None:
        """
        Hace el merge de los chunks parciales para crear el índice final en disco, siguiendo el algoritmo multi-way merge según MAN08.
        Utiliza PostingChunk en modo lectura secuencial para cada chunk.
        """
        chunk_objs = [PostingChunk(file_path=chunk_path) for chunk_path in self.chunks]
        heap: list[tuple[int, PartialPosting]] = []

        # Leer el primer registro de cada chunk y agregarlo al heap
        for chunk_id, chunk in enumerate(chunk_objs):
            if chunk.get_current() is not None:
                pp = chunk.get_current()
                heapq.heappush(heap, (chunk_id, pp))

        # Abrir archivo final de postings en modo escritura binaria y crear el índice final
        with open(self.path_index + "/final_index.bin", "wb") as final_index_file:
            offset = 0
            current_term_id = None
            current_posting_list: list[Posting] = []

            while heap:
                chunk_id, pp = heapq.heappop(heap)
                if current_term_id is None:  # solo para la primera iteración
                    current_term_id = pp.term_id

                # Si el término actual es diferente al anterior, escribir la posting list actual (porque ya está completa) y agregar el término al vocabulario
                if pp.term_id != current_term_id:
                    for posting in current_posting_list:
                        final_index_file.write(posting.to_bytes())
                    # Guardar en vocabulario: offset y df
                    self.vocabulary[self.id2term[current_term_id]] = {
                        "puntero": offset,
                        "df": len(current_posting_list),
                    }
                    offset += 8 * len(current_posting_list)
                    # Reset
                    current_term_id = pp.term_id
                    current_posting_list = []

                current_posting_list.append(Posting(pp.doc_id, pp.freq))

                # Avanzar en el chunk correspondiente (extraido de la cabeza del heap)
                chunk = chunk_objs[chunk_id]
                chunk.next()
                if chunk.get_current() is not None:
                    next_pp = chunk.get_current()
                    # Si el chunk tiene más postings, agregar al heap para seguir procesandolo
                    heapq.heappush(heap, (chunk_id, next_pp))
            # END WHILE

            # Escribir la última posting list
            if current_posting_list:
                for posting in current_posting_list:
                    final_index_file.write(posting.to_bytes())
                self.vocabulary[self.id2term[current_term_id]] = {
                    "puntero": offset,
                    "df": len(current_posting_list),
                }

        # Cerrar todos los chunks
        for chunk in chunk_objs:
            chunk.close()
        self._write_vocabulary()

    def _write_vocabulary(self) -> None:
        """
        Persiste el vocabulario en disco (por ejemplo, usando pickle).
        """
        vocab_path = os.path.join(self.path_index, "vocabulary.pkl")
        with open(vocab_path, "wb") as f:
            pickle.dump(self.vocabulary, f)

    def _load_vocabulary(self) -> None:
        """
        Carga el vocabulario desde disco a memoria.
        """
        vocab_path = os.path.join(self.path_index, "vocabulary.pkl")
        with open(vocab_path, "rb") as f:
            self.vocabulary = pickle.load(f)

    def get_vocabulary(self) -> Dict[str, Dict[str, int]]:
        """
        Devuelve el vocabulario cargado en memoria.
        """
        if not self.vocabulary:
            self._load_vocabulary()
        return self.vocabulary

    # ESTO LO PUSE POR LA ABSTRACT CLASS

    def total_tokens(self) -> int:
        # No llevas la cuenta exacta, así que devolvemos 0 o podrías sumar frecuencias si lo implementas
        return 0

    def total_terminos(self) -> int:
        return len(self.term2id)
