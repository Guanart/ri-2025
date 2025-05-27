import argparse
import os
from bitarray import bitarray
from lib.IRSystemBSBI import IRSystemBSBI
from lib.IndexadorBSBI import IndexadorBSBI
from lib.codecs_compresion import vbyte_decode_list, elias_gamma_decode_list, restore_from_dgaps

def mostrar_posting_comprimida(index_dir, termino, use_dgaps):
    tokenizer = None
    indexador = IndexadorBSBI(tokenizer, path_index=index_dir)
    irsys = IRSystemBSBI(indexador)
    # Posting original
    postings = irsys.get_term_from_posting_list(termino)
    print(f"Postings originales para '{termino}':")
    for p in postings:
        print(f"  {p.doc_id}:{p.freq}")
    # Comprimidas
    docids_path = os.path.join(index_dir, "comprimido", f"{termino}.docids.vb")
    freqs_path = os.path.join(index_dir, "comprimido", f"{termino}.freqs.eg")
    if not os.path.exists(docids_path) or not os.path.exists(freqs_path):
        print("No se encontró la versión comprimida para ese término.")
        return
    with open(docids_path, "rb") as f:
        vbyte = f.read()
    with open(freqs_path, "rb") as f:
        egamma = bitarray()
        egamma.fromfile(f)
    docids = vbyte_decode_list(vbyte)
    if use_dgaps:
        docids = restore_from_dgaps(docids)
    freqs = elias_gamma_decode_list(egamma)
    print(f"Postings comprimidas para '{termino}':")
    for d, f in zip(docids, freqs):
        print(f"  {d}:{f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejercicio 7.1: Mostrar posting list comprimida y original para un término.")
    parser.add_argument("--index-dir", required=True, help="Directorio del índice")
    parser.add_argument("--termino", required=True, help="Término a consultar")
    parser.add_argument("--dgaps", action="store_true", help="Usar DGaps para decodificar docIDs")
    args = parser.parse_args()
    mostrar_posting_comprimida(args.index_dir, args.termino, args.dgaps)
