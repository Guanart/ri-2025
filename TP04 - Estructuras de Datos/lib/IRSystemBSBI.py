from .IndexadorBSBI import IndexadorBSBI
from lib.IRSystem import IRSystem
from lib.Posting import Posting
import os
import boolean


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

    def index_collection(self, path: str) -> None:
        if os.path.exists(self.index_dir):
            print("El índice ya existe. No se realizará la indexación.")
            return
        self.analyzer.index_collection(path)

    def query(self, text: str, **kwargs: object):
        pass

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
