from .IndexadorBSBI import IndexadorBSBI
from lib.IRSystem import IRSystem
from lib.Posting import Posting
import os
import pickle

class IRSystemBSBI(IRSystem):
    """
    Sistema de recuperación para índice BSBI persistido en disco.
    Permite cargar el vocabulario y recuperar posting lists de manera sencilla.
    """
    def __init__(self, analyzer: IndexadorBSBI):
        super().__init__(analyzer)

    def index_collection(self, path: str) -> None:
        self.analyzer.index_collection(path)

    def query(self, text, **kwargs):
        pass

    def get_term_from_posting_list(self, termino: str) -> list[Posting]:
        """
        Devuelve la posting list de un término como lista de objetos Posting.
        """
        vocabulary = self.analyzer.get_vocabulary()
        postings_path = os.path.join(self.index_dir, "final_index.bin")
        
        if termino not in vocabulary:
            return []
        
        puntero, df = vocabulary[termino]["puntero"], vocabulary[termino]["df"]
        
        resultado = []
        with open(postings_path, "rb") as f:
            f.seek(puntero)
            for _ in range(df):
                data = f.read(8)
                posting = Posting.from_bytes(data)
                resultado.append(posting)
        return resultado
