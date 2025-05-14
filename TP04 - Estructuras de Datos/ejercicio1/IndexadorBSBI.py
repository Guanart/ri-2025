from collections import Counter
import os
import pickle

from bs4 import BeautifulSoup
from lib.CollectionAnalyzerBase import CollectionAnalyzerBase
from lib.Tokenizador import Tokenizador
from lib.PartialPosting import PartialPosting
from lib.PostingChunk import PostingChunk
from typing import Dict


class IndexadorBSBI(CollectionAnalyzerBase):
    def __init__(self, tokenizer: Tokenizador, memory_limit: int = 1000, path_index: str = "index"):
        super().__init__(tokenizer)
        self.memory_limit: int = memory_limit
        self.memory_usage: int = 0
        self.path_index: str = path_index
        self.vocabulario: Dict[int, int] = {}  # término -> [df, puntero]
        self.doc_id_map: Dict[int, str] = {}   # doc_id -> nombre del archivo
        self.chunks = []       # paths a los archivos de chunks
        # self.postings_tmp = {}  # postings temporales en memoria (opcional)

        # En algún lugar tengo que definir el tamaño de los postings (en bytes), que contendrá: nombre del archivo, DOCID y frecuencia del término, en principio. La frecuencia del término es un entero (es importante para poder rankear), el DOCID es un entero y el nombre del archivo es una cadena de caracteres.
        # 
        # La estructura de cada Posting es: DocName:docID:Frecuencia.
        # Usaremos UTF-8 con caracteres ASCII para el DocName, asi ocupan 1 byte por caracter.
        # Las consultas AND, OR y NOT se hacen entre listas de postings -> AND es intersección y OR es unión.

        # 1.1) Podría hacer una clase Vocabulario (o simplemente usar Pickle y persistir el diccionario)

    def index_collection(self, path: str) -> None:
        """
        Indexa la colección usando BSBI. Procesa bloques de n documentos, vuelca a disco y mergea los chunks.
        """
        # Recorre recursivamente el directorio
        doc_id: int = 0
        term2id: Dict[str, int] = {}
        current_chunk_postings: list  = []
        for root, _, files in os.walk(path):
            for fname in files:
                # Validar memoria. Si se supera el límite, procesar el chunk actual y reiniciar
                if self.memory_usage > self.memory_limit:
                    self._process_chunk(current_chunk_postings) # BSBI-Invert(block) de la diapositiva
                    current_chunk_postings = []
                    self.memory_usage = 0

                if fname.endswith((".html", ".txt")):
                    # ParseNextBlock() de la diapositiva
                    tokens, doc_name = self._process_doc(fname, root, path)
                    self.memory_usage += 1
                    doc_id += 1
                    terms_freq = Counter(tokens)
                    for token, freq in terms_freq.items():
                        if token not in term2id:
                            term2id[token] = len(term2id) + 1
                        term_id = term2id[token]
                        current_chunk_postings.append(PartialPosting(term_id, doc_id, freq))
                    self.doc_id_map[doc_id] = doc_name
        
        # Procesar el último chunk
        if current_chunk_postings:
            self._process_chunk(current_chunk_postings)
            current_chunk_postings = []
        self._merge_chunks()
        self._write_vocabulary()

    def _process_doc(self, fname: str, root: str, path: str) -> str:
        with open(
            os.path.join(root, fname), encoding="utf8", errors="ignore"
        ) as f:
            text = f.read()
            if fname.endswith(".html"):
                text: str = BeautifulSoup(text, "html.parser").get_text(
                    separator=" "
                )
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
        chunk.sort(key=lambda x: (x.term_id, x.doc_id))

        # Crear PostingChunk y escribir en disco
        chunk_file_path = os.path.join(self.path_index, f"chunk_{len(self.chunks)}.bin")
        chunk_obj = PostingChunk(chunk, chunk_file_path)
        chunk_obj.write_to_disk()       # WriteBlockToDisk(block) de la diapositiva
        self.chunks.append(chunk_file_path)

    def _merge_chunks(self) -> None:
        """
        Hace el merge de los chunks parciales para crear el índice final en disco.
        """
        pass

    def _write_vocabulary(self) -> None:
        """
        Persiste el vocabulario en disco (por ejemplo, usando pickle).
        """
        vocab_path = os.path.join(self.path_index, "vocabulario.pkl")
        with open(vocab_path, "wb") as f:
            pickle.dump(self.vocabulario, f)

    def _load_vocabulary(self) -> None:
        """
        Carga el vocabulario desde disco a memoria.
        """
        vocab_path = os.path.join(self.path_index, "vocabulario.pkl")
        with open(vocab_path, "rb") as f:
            self.vocabulario = pickle.load(f)

