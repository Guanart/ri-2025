import argparse
from .IRSystemBSBI import IRSystemBSBI
from .IndexadorBSBI import IndexadorBSBI
from lib.Tokenizador import Tokenizador
from lib.Posting import Posting


def main():
    parser = argparse.ArgumentParser(
        description="Recupera la posting list de un término desde el índice en disco usando IRSystemBSBI."
    )
    # parser.add_argument("--index-dir", type=str, required=True, help="Directorio donde está el índice (vocabulario y postings.bin)")
    parser.add_argument(
        "--corpus-path",
        type=str,
        required=True,
        help="Directorio raíz que contiene los archivos para la indexación.",
    )
    parser.add_argument(
        "--termino", type=str, required=True, help="Término a buscar en el vocabulario"
    )
    args = parser.parse_args()

    # Instanciar el sistema de recuperación
    tokenizer = Tokenizador()
    indexador = IndexadorBSBI(tokenizer)
    irsys = IRSystemBSBI(indexador)
    irsys.index_collection(args.corpus_path)

    posting_list: list[Posting] = irsys.get_term_from_posting_list(args.termino)
    if not posting_list:
        print(f"El término '{args.termino}' no está en el vocabulario.")
        return
    print("Postings para el término '{}':".format(args.termino))
    for posting in posting_list:
        print(
            f"Documento: {posting.doc_name}, ID: {posting.doc_id}, Frecuencia: {posting.freq}"
        )


if __name__ == "__main__":
    main()
