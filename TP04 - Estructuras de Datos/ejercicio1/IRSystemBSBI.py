from .IndexadorBSBI import IndexadorBSBI
from lib.IRSystem import IRSystem
from lib.Posting import Posting
import os


class IRSystemBSBI(IRSystem):
    """
    Sistema de recuperación para índice BSBI persistido en disco.
    Permite cargar el vocabulario y recuperar posting lists de manera sencilla.
    """

    def __init__(self, analyzer: IndexadorBSBI):
        super().__init__(analyzer)
        self.index_dir = analyzer.path_index
        # Setear el doc_id_map global en Posting para que cada Posting pueda resolver su doc_name
        Posting.set_doc_id_map(analyzer.doc_id_map)

    def index_collection(self, path: str) -> None:
        self.analyzer.index_collection(path)

    def query(self, text, **kwargs):
        pass

    def get_term_from_posting_list(self, termino: str) -> list[Posting]:
        """
        Devuelve la posting list de un término como lista de objetos Posting.
        """
        vocabulary = self.analyzer.get_vocabulary()
        postings_path = os.path.join(self.index_dir, self.analyzer.POSTINGS_FILENAME)
        posting_size = self.analyzer.POSTING_SIZE
        if termino not in vocabulary:
            return []
        puntero, df = vocabulary[termino]["puntero"], vocabulary[termino]["df"]
        resultado = []
        with open(postings_path, "rb") as f:
            f.seek(puntero)
            for _ in range(df):
                data = f.read(posting_size)
                posting = Posting.from_bytes(data)
                resultado.append(posting)
        return resultado
