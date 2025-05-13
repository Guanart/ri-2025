from lib.CollectionAnalyzerBase import CollectionAnalyzerBase
from lib.Tokenizador import Tokenizador
from typing import Dict


class IndexadorBSBI(CollectionAnalyzerBase):
    def __init__(self, tokenizer: Tokenizador, memory_limit: int = 1000, path_index: str = "index"):
        super().__init__(tokenizer)
        self.memory_limit: int = memory_limit
        self.path_index: str = path_index
        self.vocabulario: Dict[int, int] = {}  # término -> [df, puntero]
        self.doc_id_map: Dict[int] = {}   # docName -> docID
        self.chunks = []       # paths a los archivos de chunks
        # self.postings_tmp = {}  # postings temporales en memoria (opcional)

        # En algún lugar tengo que definir el tamaño de los postings (en bytes), que contendrá: nombre del archivo, DOCID y frecuencia del término, en principio. La frecuencia del término es un entero (es importante para poder rankear), el DOCID es un entero y el nombre del archivo es una cadena de caracteres.
        # 
        # La estructura de cada Posting es: DocName:docID:Frecuencia.
        # Usaremos UTF-8 con caracteres ASCII para el DocName, asi ocupan 1 byte por caracter.
        # Las consultas AND, OR y NOT se hacen entre listas de postings -> AND es intersección y OR es unión.

        # 1.1) Podría hacer una clase Vocabulario (o simplemente usar Pickle y persistir el diccionario)

    def index_collection(self, path: str, n: int = 100) -> None:
        """
        Indexa la colección usando BSBI. Procesa bloques de n documentos, vuelca a disco y mergea los chunks.
        """
        pass

    def _process_block(self, docs: list, block_id: int) -> str:
        """
        Procesa un bloque de documentos, construye el índice parcial y lo vuelca a disco.
        Devuelve el path al archivo de chunk generado.
        """
        pass

    def _merge_chunks(self) -> None:
        """
        Hace el merge de los chunks parciales para crear el índice final en disco.
        """
        pass

    def _write_vocabulary(self) -> None:
        """
        Persiste el vocabulario en disco (por ejemplo, usando pickle).
        """
        pass

    def _write_postings(self, postings: dict, file_path: str) -> None:
        """
        Escribe las posting lists en disco en formato binario.
        """
        pass

    def _load_vocabulary(self) -> None:
        """
        Carga el vocabulario desde disco a memoria.
        """
        pass

