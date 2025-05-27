import argparse
from lib.Tokenizador import Tokenizador
from lib.IndexadorBSBI import IndexadorBSBI
from lib.IRSystemBSBI import IRSystemBSBI


def main():
    parser = argparse.ArgumentParser(
        description="Procesa consultas vectoriales sobre el índice TF-IDF."
    )
    parser.add_argument(
        "--corpus-path",
        type=str,
        required=True,
        help="Directorio raíz que contiene los documentos a indexar.",
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Consulta de texto libre (modelo vectorial)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Cantidad de documentos a retornar (top-k)",
    )
    parser.add_argument(
        "--path-stopwords",
        type=str,
        required=False,
        default=None,
        help="Ruta al archivo de stopwords (opcional).",
    )
    args = parser.parse_args()

    tokenizer = Tokenizador(stopwords_path=args.path_stopwords)
    analyzer = IndexadorBSBI(tokenizer, precalc_doc_vectors=True)
    irsys = IRSystemBSBI(analyzer)
    irsys.index_collection(args.corpus_path)

    resultados: list[tuple[str, int, float]] = irsys.daat_query(
        args.query, top_k=args.top_k
    )

    if not resultados:
        print("No se encontraron documentos para la consulta.")
        return
    print(f"Resultados para la consulta '{args.query}':")
    for docname, docid, score in resultados:
        print(f"{docname}:{docid}:{score:.4f}")


if __name__ == "__main__":
    main()
