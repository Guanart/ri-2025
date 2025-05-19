import argparse
from lib.Tokenizador import Tokenizador
from lib.IRSystemBSBI import IRSystemBSBI
from lib.IndexadorBSBI import IndexadorBSBI


def main():
    parser = argparse.ArgumentParser(
        description="Procesa consultas booleanas TAAT sobre el índice BSBI."
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
        help="Consulta booleana (ejemplo: '(perro AND gato) OR raton')",
    )
    args = parser.parse_args()

    tokenizer = Tokenizador()
    indexador = IndexadorBSBI(tokenizer)
    irsys = IRSystemBSBI(indexador)
    irsys.index_collection(args.corpus_path)

    docids: list[tuple[int, str]] = irsys.taat_query(args.query)

    if not docids:
        print("No se encontraron documentos para la consulta.")
        return
    print(f"Resultados para la consulta '{args.query}':")
    for docid in sorted(docids):
        print(f"{docid[1]}:{docid[0]}")


if __name__ == "__main__":
    main()
