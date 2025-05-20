import argparse
from lib.Tokenizador import Tokenizador
from lib.IndexadorBSBI import IndexadorBSBI
from lib.IRSystemBSBI import IRSystemBSBI

def main():
    parser = argparse.ArgumentParser(
        description="Muestra la skip list de un término (docName:docID ordenados)."
    )
    parser.add_argument("--corpus-path", type=str, required=True)
    parser.add_argument("--termino", type=str, required=True)
    args = parser.parse_args()

    tokenizer = Tokenizador()
    indexador = IndexadorBSBI(tokenizer)
    irsys = IRSystemBSBI(indexador)
    irsys.index_collection(args.corpus_path)
    doc_id_map = indexador.get_doc_id_map()

    skips = irsys.get_skip_list_from_term(args.termino)
    if not skips:
        print(f"No hay skips para el término '{args.termino}'")
        return
    lista = [(doc_id_map[docid], docid) for docid, _ in skips]
    
    lista.sort(key=lambda x: x[0])  # COMENTAR ESTA LINEA PARA VER EL ORDEN ORIGINAL (como en la PPT)
    
    print(f"Skip list para el término '{args.termino}':")
    for docname, docid in lista:
        print(f"{docname}:{docid}")


if __name__ == "__main__":
    main()
