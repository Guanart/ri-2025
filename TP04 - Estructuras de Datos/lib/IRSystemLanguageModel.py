import math
from .IRSystem import IRSystem
from .CollectionAnalyzerLM import CollectionAnalyzerLM
from typing import List, Tuple


class IRSystemLanguageModel(IRSystem):
    """
    Sistema de RI usando modelo de lenguaje (unigramas) y Query Likelihood.
    """

    def __init__(self, analyzer: CollectionAnalyzerLM):
        super().__init__(analyzer)

    def query(
        self, text: str, top_k: int = 10, lamb: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Ejecuta una consulta sobre la colección indexada usando Query Likelihood.
        Parámetros:
            text: texto de la consulta
            top_k: cantidad de documentos a retornar
            lamb: parámetro de suavizado Jelinek-Mercer (0 = sin suavizado)
        """
        tokenizer = self.analyzer.tokenizer
        q_tokens = tokenizer.tokenizar(text)
        scores: dict[str, float] = {}
        for docid, tf_counter in self.analyzer.docs_terms.items():
            score = 0.0
            for t in q_tokens:
                tf = tf_counter[t]
                dl = self.analyzer.doc_len[docid]
                cf = self.analyzer.term_freq[t]
                cl = self.analyzer.collection_len
                if lamb == 0.0:
                    # Sin suavizado
                    p = tf / dl if dl > 0 else 0
                else:
                    # Jelinek-Mercer
                    p = (1 - lamb) * (tf / dl if dl > 0 else 0) + lamb * (
                        cf / cl if cl > 0 else 0
                    )
                if p > 0:
                    score += math.log(p)
                else:
                    score += -100  # penalización fuerte
            scores[docid] = score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return ranked

    def index_collection(self, path: str) -> None:
        self.analyzer.index_collection(path)
