import argparse
from lib.Tokenizador import Tokenizador
from lib.IndexadorBSBI import IndexadorBSBI
from lib.IRSystemBSBI import IRSystemBSBI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Muestra la posting list y skip list del término con posting list más corta."
    )
    parser.add_argument(
        "--index-path", required=True, help="Directorio raíz del índice BSBI."
    )
    args = parser.parse_args()

    tokenizer = Tokenizador()
    indexador = IndexadorBSBI(tokenizer, path_index=args.index_path)
    irsys = IRSystemBSBI(indexador)
    vocab = indexador.get_vocabulary()

    # Buscar un término con posting list entre 50 y 100 items (50 <= df <= 100)
    min_term = None
    min_df = float("inf")
    for term, info in vocab.items():
        if 50 <= info["df"] <= 100 and info["df"] < min_df:
            min_term = term
            min_df = info["df"]

    if not min_term:
        print("No se encontró término con posting list.")
        exit(1)

    print(f"Término con posting list más corta: '{min_term}' (df={min_df})\n")
    postings = irsys.get_term_from_posting_list(min_term)
    print("Posting list:")
    for p in postings:
        print(f"  doc_id={p.doc_id}, freq={p.freq}")

    skips = irsys.get_skip_list_from_term(min_term)
    print("\nSkip list:")
    for docid, offset in skips:
        print(f"  doc_id={docid}, offset_byte={offset}")
