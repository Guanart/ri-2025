import argparse
import os
from bitarray import bitarray
from lib.IRSystemBSBI import IRSystemBSBI
from lib.IndexadorBSBI import IndexadorBSBI
from lib.Tokenizador import Tokenizador
from lib.codecs_compresion import (
    vbyte_decode_list,
    elias_gamma_decode_list,
    restore_from_dgaps,
)
import struct


def mostrar_posting_comprimida(index_dir, termino, use_dgaps):
    tokenizer = Tokenizador()
    indexador = IndexadorBSBI(tokenizer, path_index=index_dir)
    irsys = IRSystemBSBI(indexador)
    # Posting original
    postings = irsys.get_term_from_posting_list(termino)
    print(f"Postings originales para '{termino}':")
    for p in postings:
        print(f"  {p.doc_id}:{p.freq}")
    # Buscar la versión comprimida (en index_compressed/nodgaps o dgaps)
    modo = "dgaps" if use_dgaps else "nodgaps"
    comp_dir = os.path.abspath(os.path.join(index_dir, "..", "index_compressed", modo))
    docids_path = os.path.join(comp_dir, f"{termino}.docids.vb.bin")
    freqs_path = os.path.join(comp_dir, f"{termino}.freqs.eg.bin")
    if not os.path.exists(docids_path) or not os.path.exists(freqs_path):
        print("No se encontró la versión comprimida para ese término.")
        return
    with open(docids_path, "rb") as f:
        vbyte = f.read()
    with open(freqs_path, "rb") as f:
        n_freqs = struct.unpack("I", f.read(4))[0]
        eg_bytes = f.read()
        egamma = bitarray()
        egamma.frombytes(eg_bytes)
    docids = vbyte_decode_list(vbyte)
    if use_dgaps:
        docids = restore_from_dgaps(docids)
    freqs_decoded_full = elias_gamma_decode_list(egamma)
    freqs = freqs_decoded_full[:n_freqs]
    print(f"\n[DEBUG] n_freqs leído del archivo: {n_freqs}")
    print(f"[DEBUG] Cantidad de docids decodificados: {len(docids)}")
    print(
        f"[DEBUG] Cantidad de frecuencias decodificadas (crudo): {len(freqs_decoded_full)}"
    )
    print(
        f"[DEBUG] Primeros 10 valores decodificados crudos de Elias-gamma: {freqs_decoded_full[:10]}"
    )
    print(f"[DEBUG] Primeros 10 valores originales: {[p.freq for p in postings[:10]]}")
    print(f"\nPostings comprimidas (decodificadas) para '{termino}':")
    for d, f in zip(docids, freqs):
        print(f"  {d}:{f}")
    # Comparación detallada
    print("\nDiferencias (índice, docID, freq_original, freq_decodificada):")
    iguales = True
    for i, (p, d, f) in enumerate(zip(postings, docids, freqs)):
        if p.doc_id != d or p.freq != f:
            print(f"  {i}: {p.doc_id} vs {d}, {p.freq} vs {f}  <-- DIFERENTE")
            iguales = False
        # else:  # Si quieres ver todos, descomenta
        #     print(f"  {i}: {p.doc_id} vs {d}, {p.freq} vs {f}")
    if iguales:
        print("\n¿La posting comprimida-descomprimida coincide con la original? SI")
    else:
        print("\n¿La posting comprimida-descomprimida coincide con la original? NO")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ejercicio 7.1: Mostrar posting list comprimida y original para un término."
    )
    parser.add_argument("--index-dir", required=True, help="Directorio del índice")
    parser.add_argument("--termino", required=True, help="Término a consultar")
    parser.add_argument(
        "--dgaps", action="store_true", help="Usar DGaps para decodificar docIDs"
    )
    args = parser.parse_args()
    mostrar_posting_comprimida(args.index_dir, args.termino, args.dgaps)
