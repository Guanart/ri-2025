from .IndexadorBSBI import IndexadorBSBI
from lib.IRSystem import IRSystem
from lib.Posting import Posting
import os
import boolean
import numpy as np
import math
from collections import Counter


class IRSystemBSBI(IRSystem):
    """
    Sistema de recuperación para índice BSBI persistido en disco.
    Permite cargar el vocabulario y recuperar posting lists de manera sencilla.
    """
    # analyzer: IndexadorBSBI
    def __init__(self, analyzer: IndexadorBSBI):
        super().__init__(analyzer)
        self.analyzer: IndexadorBSBI = analyzer # type: ignore
        self.index_dir = analyzer.path_index
        # Setear el doc_id_map global en Posting para que cada Posting pueda resolver su doc_name
        Posting.set_doc_id_map(analyzer.doc_id_map)

        # Para el modelo vectorial:
        self.term_index: dict[str, int] = {}
        self.doc_vectors: dict[str, np.ndarray] = {}
        self.doc_norms: dict[str, float] = {}
        self._make_term_index()
        # self._build_doc_vectors()

    def _make_term_index(self) -> None:
        """
        Mapear términos a índices de vector
        """
        for i, term in enumerate(self.analyzer.get_vocabulary().keys()):
            self.term_index[term] = i  # Guarda el índice numérico que ocupará ese término en los vectores
            # En el espacio vectorial, cada documento (y cada consulta) se representa con un vector de longitud V (tamaño del vocabulario). Para saber en qué posición del vector colocar el peso de un cada término, necesitamos un mapeo término→índice único.

    def _make_vector(self, tf_counter: Counter) -> np.ndarray:
        """
        Construye un vector tf-idf a partir de un Counter de términos.
        """
        V = len(self.term_index)
        vec = np.zeros(V, dtype=float)
        for term, freq in tf_counter.items():
            if term in self.analyzer.vocabulary:
                # No implementado el IDF
                idx = self.term_index[term]
                # tf_weight = 1 + math.log(freq)
                tf_weight = freq
                # vec[idx] = tf_weight * self.analyzer.vocabulary[term]["idf"]
                vec[idx] = tf_weight
        return vec

    # def _build_doc_vectors(self) -> None:
    #     """
    #     Construye los vectores de documentos y sus normas (genera el espacio vectorial).
    #     Usa self.analyzer.get_doc_terms() para obtener los términos y frecuencias de cada documento.
    #     """
    #     doc_terms = self.analyzer.get_doc_terms()  # doc_terms ==  {docid: Counter(term: freq)}
    #     for docid, tf_counter in doc_terms.items():
    #         vec = self._make_vector(tf_counter)
    #         self.doc_vectors[docid] = vec
    #         self.doc_norms[docid] = np.linalg.norm(vec)

    def index_collection(self, path: str) -> None:
        if os.path.exists(self.index_dir):
            print("El índice ya existe. No se realizará la indexación.")
            return
        self.analyzer.index_collection(path)

    def query(self, text: str, top_k: int = 10, **kwargs) -> list[tuple[str, int, float]]:
        """
        Ejecuta una consulta vectorial DAAT sobre el índice BSBI usando solo TF crudo.
        Devuelve los top-k documentos con mayor score coseno.
        """
        tokens = self.analyzer.tokenizer.tokenizar(text)
        tf_query = Counter(tokens)
        q_vec = self._make_vector(tf_query)
        norm_q = np.linalg.norm(q_vec)
        # Recupera posting lists de los términos de la consulta
        posting_lists: dict[str, list[Posting]] = {term: self.get_term_from_posting_list(term) for term in tf_query}
        # Junta todos los docIDs candidatos
        candidate_docids = set()
        for plist in posting_lists.values():
            for posting in plist:
                candidate_docids.add(posting.doc_id)
        # Calcula el score para cada documento candidato
        results = []
        for docid in candidate_docids:
            tf_doc = Counter()
            for term, plist in posting_lists.items():
                for posting in plist:
                    if posting.doc_id == docid:
                        tf_doc[term] = posting.freq
            d_vec = self._make_vector(tf_doc)
            norm_d = np.linalg.norm(d_vec)
            if norm_d == 0 or norm_q == 0:
                continue
            score = np.dot(q_vec, d_vec) / (norm_q * norm_d)
            docname = self.analyzer.doc_id_map.get(docid, str(docid))
            results.append((docname, docid, score))
        results.sort(key=lambda x: -x[2])
        return results[:top_k]

    def taat_query(self, query: str) -> list[tuple[int, str]]:
        """
        Evalúa una consulta booleana TAAT (Term At A Time) y devuelve los documentos que la satisfacen.
        """
        algebra: boolean.BooleanAlgebra = boolean.BooleanAlgebra()
        expr = algebra.parse(query.lower())

        def get_docid_set(term: str) -> set[int]:
            postings = self.get_term_from_posting_list(term)
            return set(p.doc_id for p in postings)

        def eval_expr(e) -> set[int]:
            if e.isliteral:
                return get_docid_set(str(e))
            op = getattr(e, "operator", None)
            if op in ("AND", "&"):
                sets = [eval_expr(arg) for arg in e.args]
                return set.intersection(*sets)
            elif op in ("OR", "|"):
                sets = [eval_expr(arg) for arg in e.args]
                return set.union(*sets)
            elif op in ("NOT", "~"):
                all_docids = set(self.analyzer.doc_id_map.keys())
                return all_docids - eval_expr(e.args[0])
            else:
                raise ValueError(f"Operador no soportado: {op}")

        docids = eval_expr(expr)
        doc_id_map = self.analyzer.get_doc_id_map()
        return [(docid, doc_id_map[docid]) for docid in sorted(docids)]

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
        resultado: list[Posting] = []
        with open(postings_path, "rb") as f:
            f.seek(puntero)
            for _ in range(df):
                data = f.read(posting_size)
                posting = Posting.from_bytes(data)
                resultado.append(posting)
        return resultado
