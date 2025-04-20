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

    def _make_vector(self, tf_counter):
        """
        Construye un vector tf-idf a partir de un Counter de términos.
        """
        V = len(self.analyzer.term_index)
        vec = np.zeros(V, dtype=float)
        for term, freq in tf_counter.items():
            if term in self.analyzer.idf:
                idx = self.analyzer.term_index[term]
                tf_weight = 1 + math.log(freq)
                vec[idx] = tf_weight * self.analyzer.idf[term]
        return vec

    def _build_doc_vectors(self):
        """
        Construye los vectores de documentos y sus normas (genera el espacio vectorial).
        """
        for docid, tf_counter in self.analyzer.docs_terms.items():
            vec = self._make_vector(tf_counter)
            self.doc_vectors[docid] = vec
            self.doc_norms[docid] = np.linalg.norm(vec)

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
        tokens = self.analyzer.tokenizer.tokenizar(text)
        q_tf = Counter(tokens)
        q_vec = self._make_vector(q_tf)
        norm_q = np.linalg.norm(q_vec)

        # Calcula la similitud coseno entre la consulta y los documentos
        scores = {}
        for docid, d_vec in self.doc_vectors.items():
            denom = self.doc_norms[docid] * norm_q  # producto de las normas de los vectores
            if denom > 0:
                scores[docid] = np.dot(d_vec, q_vec) / denom   # similitud coseno -> producto escalar entre los vectores dividido por el producto de sus normas
            else:
                scores[docid] = 0.0

        # Ranking descendente (de mayor similitud/score a menor)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
