from CollectionAnalyzer import CollectionAnalyzer
import numpy as np
import math
from collections import Counter


class IRSystemManual:
    """
    Sistema de recuperación manual
    """

    def __init__(self, analyzer: CollectionAnalyzer):
        self.analyzer = analyzer
        self.doc_vectors = {}  # docid -> np.array(tf-idf)
        self.doc_norms = {}  # docid -> norma del vector
        self._build_doc_vectors()

    def _build_doc_vectors(self):
        V = len(self.analyzer.term_index)
        for docid, tf_counter in self.analyzer.docs_terms.items():
            vec = np.zeros(V, dtype=float)
            for term, freq in tf_counter.items():
                idx = self.analyzer.term_index[term]
                tf_weight = 1 + math.log(freq)
                vec[idx] = tf_weight * self.analyzer.idf[term]
            self.doc_vectors[docid] = vec
            self.doc_norms[docid] = np.linalg.norm(
                vec
            )  # :contentReference[oaicite:9]{index=9}

    def index_collection(self, path):
        """
        Indexa la colección de documentos en el directorio indicado.
        """
        self.analyzer.index_collection(path)

    def query(self, text, top_k=10):
        """
        Ejecuta una consulta sobre la colección indexada.
        Devuelve los top_k documentos más relevantes.
        """
        # Procesar query igual que un doc
        tokens = self.analyzer.tokenizer.tokenizar(text)
        q_tf = Counter(tokens)
        V = len(self.analyzer.term_index)
        q_vec = np.zeros(V, dtype=float)
        for term, freq in q_tf.items():
            if term in self.analyzer.idf:
                idx = self.analyzer.term_index[term]
                q_vec[idx] = (1 + math.log(freq)) * self.analyzer.idf[term]
        norm_q = np.linalg.norm(q_vec)  # :contentReference[oaicite:10]{index=10}

        # Cosine similarity
        scores = {}
        for docid, d_vec in self.doc_vectors.items():
            denom = self.doc_norms[docid] * norm_q
            if denom > 0:
                scores[docid] = (
                    np.dot(d_vec, q_vec) / denom
                )  # :contentReference[oaicite:11]{index=11}
            else:
                scores[docid] = 0.0

        # Ranking descendente
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
