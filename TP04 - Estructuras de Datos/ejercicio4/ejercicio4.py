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
    args = parser.parse_args()

    tokenizer = Tokenizador()
    analyzer = IndexadorBSBI(tokenizer)
    irsys = IRSystemBSBI(analyzer)
    irsys.index_collection(args.corpus_path)

    resultados = irsys.query(args.query, top_k=args.top_k)

    if not resultados:
        print("No se encontraron documentos para la consulta.")
        return
    print(f"Resultados para la consulta '{args.query}':")
    for docid, score in resultados:
        print(f"{docid}:{score:.4f}")

if __name__ == "__main__":
    main()
