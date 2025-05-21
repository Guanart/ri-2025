import heapq
import os
from collections import Counter

import boolean
import numpy as np
from lib.IRSystem import IRSystem
from lib.Posting import Posting
from lib.IndexadorBSBI import IndexadorBSBI
from lib.SkipList import SkipList


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

        if self.analyzer.get_vocabulary() is not None:
            self._make_term_index()


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

    def index_collection(self, path: str) -> None:
        if os.path.exists(self.index_dir):
            print("El índice ya existe. No se realizará la indexación.\n")
            return
        self.analyzer.index_collection(path)
        if self.analyzer.get_vocabulary() is not None:
            self._make_term_index()
        print()

    def query(self, text: str, **kwargs: object):
        return super().query(text, **kwargs)

    def daat_query(
        self, text: str, top_k: int = 10, **kwargs
    ) -> list[tuple[str, int, float]]:
        """
        Ejecuta una consulta vectorial DAAT sobre el índice BSBI usando solo TF crudo.
        Devuelve los top-k documentos con mayor score coseno.
        """
        # 1) Construir vector de consulta y su norma
        tokens = self.analyzer.tokenizer.tokenizar(text)
        tf_query = Counter(tokens)
        if not tf_query:
            return []
        q_vec = self._make_vector(tf_query)
        norm_q = np.linalg.norm(q_vec)
        if norm_q == 0:
            return []

        # 2) Recuperar posting‐lists de cada término de la query
        posting_lists = {
            term: self.get_term_from_posting_list(term) for term in tf_query
        }

        # 3) Construir el set de candidatos (docIDs)
        candidate_docids = sorted(
            {p.doc_id for plist in posting_lists.values() for p in plist}
        )

        # 4) Calcula el score para cada documento candidato
        heap: list[tuple[float, int, str]] = []
        for docid in candidate_docids:
            tf_doc = self.analyzer.get_doc_terms(
                docid
            )
            d_vec = self._make_vector(tf_doc)
            norm_d = np.linalg.norm(d_vec)
            if norm_d == 0:
                continue

            score = float(np.dot(q_vec, d_vec) / (norm_q * norm_d))
            docname = self.analyzer.doc_id_map.get(docid, str(docid))

            # 5) Modificar Top-k
            if len(heap) < top_k:
                heapq.heappush(heap, (score, docid, docname))
            else:
                # si el nuevo score supera el mínimo actual, lo reemplazamos
                if score > heap[0][0]:
                    heapq.heapreplace(heap, (score, docid, docname))

        # 6) Ordenar los k resultados y devolver [(docname, docid, score), ...]
        heap.sort(key=lambda x: -x[0])
        return [(docname, docid, score) for score, docid, docname in heap]
    
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

    def get_skip_list_from_term(self, term: str) -> list[tuple[int, int]]:
        skips_dict = self.analyzer.get_skips()
        return skips_dict.get(term, [])

    def taat_query_with_skips(self, query: str) -> list[tuple[int, str]]:
        """
        Evalúa una consulta TAAT AND entre dos términos usando skips (offsets en bytes).
        Utiliza la clase SkipList para saltar en disco.
        Devuelve los documentos que la satisfacen (docid, docname).
        Solo soporta queries AND de dos términos.
        """
        import re
        m = re.match(r"^(\w+)\s+AND\s+(\w+)$", query.strip(), re.IGNORECASE)
        if not m:
            raise ValueError("Solo se soportan queries AND de dos términos para skips.")

        t1, t2 = m.group(1), m.group(2)
        vocabulary = self.analyzer.get_vocabulary()
        skips_dict = self.analyzer.get_skips()
        doc_id_map = self.analyzer.get_doc_id_map()
        postings_path = os.path.join(self.index_dir, self.analyzer.POSTINGS_FILENAME)
        posting_size = self.analyzer.POSTING_SIZE

        info1 = vocabulary.get(t1)
        info2 = vocabulary.get(t2)
        if not info1 or not info2:
            return []
        skips1 = SkipList(skips_dict.get(t1, []))
        skips2 = SkipList(skips_dict.get(t2, []))

        # Inicializar punteros y límites
        i_ptr = info1["puntero"]
        j_ptr = info2["puntero"]
        i_end = i_ptr + info1["df"] * posting_size
        j_end = j_ptr + info2["df"] * posting_size

        res = []
        with open(postings_path, "rb") as f:
            while i_ptr < i_end and j_ptr < j_end:
                # Leer postings actuales
                f.seek(i_ptr)
                p1 = Posting.from_bytes(f.read(posting_size))
                f.seek(j_ptr)
                p2 = Posting.from_bytes(f.read(posting_size))

                if p1.doc_id == p2.doc_id:
                    res.append((p1.doc_id, doc_id_map[p1.doc_id]))
                    i_ptr += posting_size
                    j_ptr += posting_size
                elif p1.doc_id < p2.doc_id:
                    # Usar skip list real para saltar en pl1
                    next_skip_ptr = skips1.skip_to_offset(p2.doc_id, i_ptr)
                    if next_skip_ptr and next_skip_ptr < i_end:
                        i_ptr = next_skip_ptr
                    else:
                        i_ptr += posting_size
                else:
                    # Usar skip list real para saltar en pl2
                    next_skip_ptr = skips2.skip_to_offset(p1.doc_id, j_ptr)
                    if next_skip_ptr and next_skip_ptr < j_end:
                        j_ptr = next_skip_ptr
                    else:
                        j_ptr += posting_size
        return res