import math
import CollectionAnalyzerModelLanguage

class IRSystemLanguageModel:
    """
    Sistema de RI usando modelo de lenguaje (unigramas) y Query Likelihood.
    """
    def __init__(self, analyzer: CollectionAnalyzerModelLanguage):
        self.analyzer = analyzer

    def query_likelihood(self, query, lamb=0.0, top_k=10):
        """
        Calcula ranking usando Query Likelihood (con o sin suavizado Jelinek-Mercer).
        lamb: lambda de Jelinek-Mercer (0 = sin suavizado)
        """
        tokenizer = self.analyzer.tokenizer
        q_tokens = tokenizer.tokenizar(query)
        scores = {}
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
                    p = (1-lamb)*(tf/dl if dl>0 else 0) + lamb*(cf/cl if cl>0 else 0)
                if p > 0:
                    score += math.log(p)
                else:
                    score += -100  # penalización fuerte
            scores[docid] = score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return ranked