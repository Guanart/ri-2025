import argparse
import sys
import os
from ejercicio1.IRSystemBSBI import IRSystemBSBI
from ejercicio1.IndexadorBSBI import IndexadorBSBI
from lib.Tokenizador import Tokenizador
from lib.Posting import Posting


def main():
    parser = argparse.ArgumentParser(
        description="Carga el vocabulario y recupera la posting list de un término desde el índice en disco usando IRSystemBSBI. Se muestra con el formato 'doc_name:doc_id:freq'."
    )
    # parser.add_argument("--index-dir", type=str, required=True, help="Directorio donde está el índice (vocabulario y postings)")
    parser.add_argument(
        "--corpus-path",
        type=str,
        required=True,
        help="Directorio raíz que contiene los documentos a indexar.",
    )
    parser.add_argument(
        "--termino",
        type=str,
        required=True,
        help="Término a buscar en el vocabulario",
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
    print(f"Postings para el término '{args.termino}':")
    for posting in posting_list:
        print(f"{posting.doc_name}:{posting.doc_id}:{posting.freq}")


if __name__ == "__main__":
    main()
