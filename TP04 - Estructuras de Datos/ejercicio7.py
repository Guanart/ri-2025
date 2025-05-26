import argparse
import os
import time
from bitarray import bitarray
from lib.IRSystemBSBI import IRSystemBSBI
from lib.IndexadorBSBI import IndexadorBSBI
from lib.codecs_compresion import vbyte_encode_list, elias_gamma_encode_list, compute_dgaps

def comprimir_postings(index_dir, use_dgaps):
    tokenizer = None  # El IndexadorBSBI lo carga del disco
    indexador = IndexadorBSBI(tokenizer, path_index=index_dir)
    irsys = IRSystemBSBI(indexador)
    vocab = indexador.get_vocabulary()
    os.makedirs(os.path.join(index_dir, "comprimido"), exist_ok=True)
    docids_total = 0
    freqs_total = 0
    t0 = time.time()
    for termino, info in vocab.items():
        postings = irsys.get_term_from_posting_list(termino)
        docids = [p.doc_id for p in postings]
        freqs = [p.freq for p in postings]
        if use_dgaps:
            docids = compute_dgaps(docids)
        vbyte = vbyte_encode_list(docids)
        egamma = elias_gamma_encode_list(freqs)
        with open(os.path.join(index_dir, "comprimido", f"{termino}.docids.vb"), "wb") as f:
            f.write(vbyte)
        with open(os.path.join(index_dir, "comprimido", f"{termino}.freqs.eg"), "wb") as f:
            egamma.tofile(f)
        docids_total += len(vbyte)
        freqs_total += len(egamma.tobytes())
    t1 = time.time()
    print(f"Compresión {'con' if use_dgaps else 'sin'} DGaps terminada.")
    print(f"Tiempo total: {t1-t0:.2f} s")
    print(f"Tamaño total docIDs comprimidos: {docids_total} bytes")
    print(f"Tamaño total freqs comprimidas: {freqs_total} bytes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejercicio 7: Compresión del índice invertido usando VByte y Elias-gamma.")
    parser.add_argument("--index-dir", required=True, help="Directorio del índice (donde está el vocabulario y postings)")
    parser.add_argument("--dgaps", action="store_true", help="Usar DGaps para docIDs")
    args = parser.parse_args()
    comprimir_postings(args.index_dir, args.dgaps)
