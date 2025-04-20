import os
from bs4 import BeautifulSoup
import pyterrier as pt
import pandas as pd
from scipy.stats import spearmanr, kendalltau


class IRSystem:
    def __init__(self, index_path: str):
        # pt.init()  # Inicializa Terrier (deprecated)
        self.index_path = index_path
        self.indexref = None

    def index_collection(self, dir_root: str):
        """
        Recorre dir_root recursivamente, parsea cada .html y construye el índice.
        """

        def gen_docs(root_dir):
            for root, _, files in os.walk(
                root_dir
            ):  # os.walk recorre el árbol de directorios y subdirectorios
                for fname in files:
                    if fname.endswith(".html"):
                        path = os.path.join(root, fname)
                        with open(path, "r", encoding="utf8") as f:
                            text = BeautifulSoup(f, "html.parser").get_text(
                                separator=" "
                            )  # Concatena el texto de los distintos nodos (tags) HTML con espacios en blanco
                            """
                            ACÁ SE PODRÍA HACER UN PARSEO MÁS COMPLEJO DEL HTML (usando BeautifulSoup)
                            """
                        docno = os.path.relpath(path, root_dir)  # Relativo a root_dir
                        yield {
                            "docno": docno,
                            "text": text,
                        }  # Uso de yield para generar un iterable (iter) de diccionarios (gen_docs() es una función generadora)

        if os.path.exists(self.index_path + "/data.properties"):
            self.index = pt.IndexFactory.of(self.index_path + "/data.properties")
        else:
            indexer = pt.IterDictIndexer(
                self.index_path, meta={"docno": 50}
            )  # Índice iterable de dicts
            # DUDA: no se puede paralelizar?
            # UserWarning: Using multiple threads results in a non-deterministic ordering of document in the index. For deterministic behavior, use threads=1
            indexref = indexer.index(gen_docs(dir_root))
            self.index = pt.IndexFactory.of(indexref)

    def retrieve(self, topics: pd.DataFrame, model: str) -> pd.DataFrame:
        """
        topics: DataFrame con columnas [qid, query].
        model: string con valor "TF_IDF" o "BM25".
        Retorna un DataFrame con columnas [qid, docno, score, rank].
        """
        model_batch = pt.BatchRetrieve(self.index, wmodel=model)
        return model_batch.transform(topics)

    def compute_correlation(
        self, res1: pd.DataFrame, res2: pd.DataFrame, qid: int, k: int
    ):
        """
        Calcula Coef. de Spearman entre los top-k de res1 y res2 para la consulta qid.
        """
        # Extraer docnos en orden
        r1 = res1[res1.qid == qid].head(k)["docno"].tolist()
        r2 = res2[res2.qid == qid].head(k)["docno"].tolist()
        # Unificar lista de candidatos
        top_results = list(dict.fromkeys(r1 + r2))
        # Rangos (si no está, rank=k+1)
        ranks1 = [r1.index(d) + 1 if d in r1 else k + 1 for d in top_results]
        ranks2 = [r2.index(d) + 1 if d in r2 else k + 1 for d in top_results]
        return spearmanr(ranks1, ranks2)[0]

    def get_index_lexicon(self):
        return self.index.getLexicon()
