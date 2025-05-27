import argparse
import os
import time
import struct
from lib.IRSystemBSBI import IRSystemBSBI
from lib.IndexadorBSBI import IndexadorBSBI
from lib.Tokenizador import Tokenizador
from lib.codecs_compresion import (
    vbyte_encode_list,
    elias_gamma_encode_list,
    compute_dgaps,
)
import matplotlib.pyplot as plt


def comprimir_postings(corpus_path, index_compressed_dir=None):
    tokenizer = Tokenizador()
    indexador = IndexadorBSBI(tokenizer)
    irsys = IRSystemBSBI(indexador)
    irsys.index_collection(corpus_path)
    vocab = indexador.get_vocabulary()
    if not vocab:
        print("[ADVERTENCIA] El vocabulario está vacío. ¿El directorio de documentos está correcto?")
        return
    # Crear index_compressed en el directorio actual si no se especifica
    if index_compressed_dir is None:
        index_compressed_dir = os.path.abspath("index_compressed")
    os.makedirs(index_compressed_dir, exist_ok=True)
    print(f"[INFO] Los archivos comprimidos se guardarán en: {os.path.abspath(index_compressed_dir)}")

    resultados = []
    tiempos_descomp = []
    for use_dgaps in [False, True]:
        modo = "con DGaps" if use_dgaps else "sin DGaps"
        subdir = os.path.join(index_compressed_dir, "dgaps" if use_dgaps else "nodgaps")
        os.makedirs(subdir, exist_ok=True)
        print(f"Iniciando compresión de postings {modo}...")
        docids_total = 0
        freqs_total = 0
        t0 = time.time()
        for termino, info in vocab.items():
            postings = irsys.get_term_from_posting_list(termino)
            docids = [p.doc_id for p in postings]
            freqs = [p.freq for p in postings]
            # Chequeo previo: mostrar si hay desajuste antes de comprimir
            if len(docids) != len(freqs):
                print(f"[ERROR][PRE-COMPRESIÓN] Término: {termino} | docids={len(docids)} | freqs={len(freqs)}")
                print(f"docids: {docids}")
                print(f"freqs: {freqs}")
                exit(1)
            if use_dgaps:
                docids = compute_dgaps(docids)
            vbyte = vbyte_encode_list(docids)
            egamma = elias_gamma_encode_list(freqs)
            with open(os.path.join(subdir, f"{termino}.docids.vb.bin"), "wb") as f:
                f.write(vbyte)
            with open(os.path.join(subdir, f"{termino}.freqs.eg.bin"), "wb") as f:
                f.write(struct.pack('I', len(freqs)))  # Escribe la cantidad de frecuencias (4 bytes)
                f.write(egamma)
            docids_total += len(vbyte)
            freqs_total += len(egamma)
        t1 = time.time()
        resultados.append(
            {
                "modo": modo,
                "tiempo": t1 - t0,
                "docids_total": docids_total,
                "freqs_total": freqs_total,
                "total": docids_total + freqs_total,
            }
        )
        print(f"Compresión {modo} terminada.")
        print(f"Tiempo total: {t1 - t0:.2f} s")
        print(f"Tamaño total docIDs comprimidos: {docids_total} bytes")
        print(f"Tamaño total freqs comprimidas: {freqs_total} bytes")
        print(f"Tamaño total comprimido: {docids_total + freqs_total} bytes")

        # Descompresión y verificación
        t_descomp, ok = descomprimir_postings(index_compressed_dir, vocab, use_dgaps)
        tiempos_descomp.append(t_descomp)
        print(f"Verificación de descompresión: {'OK' if ok else 'ERROR'}")
        
    # Comparación
    print("\n=== Comparación DGaps vs Sin DGaps ===")
    for i, r in enumerate(resultados):
        print(
            f"{r['modo']}: Tiempo compresión={r['tiempo']:.2f}s, Tiempo descompresión={tiempos_descomp[i]:.2f}s, Tamaño total={r['total']} bytes (docIDs={r['docids_total']}, freqs={r['freqs_total']})"
        )
    ahorro = (
        100 * (1 - resultados[1]["total"] / resultados[0]["total"])
        if resultados[0]["total"]
        else 0
    )
    print(f"Ahorro de espacio usando DGaps: {ahorro:.2f}%")
    graficar_histogramas(resultados, tiempos_descomp)


def descomprimir_postings(index_compressed_dir, vocab, use_dgaps):
    from bitarray import bitarray
    from lib.codecs_compresion import (
        vbyte_decode_list,
        elias_gamma_decode_list,
        restore_from_dgaps,
    )
    import struct
    modo = "dgaps" if use_dgaps else "nodgaps"
    subdir = os.path.join(index_compressed_dir, modo)
    print(
        f"Iniciando descompresión de postings {'con' if use_dgaps else 'sin'} DGaps..."
    )
    t0 = time.time()
    ok = True
    for termino in vocab:
        vb_path = os.path.join(subdir, f"{termino}.docids.vb.bin")
        eg_path = os.path.join(subdir, f"{termino}.freqs.eg.bin")
        if not os.path.exists(vb_path) or not os.path.exists(eg_path):
            print(f"[WARN] Faltan archivos para término: {termino}")
            ok = False
            continue
        with open(vb_path, "rb") as f:
            vb_bytes = f.read()
        with open(eg_path, "rb") as f:
            n_freqs = struct.unpack('I', f.read(4))[0]
            eg_bytes = f.read()
            eg_bits = bitarray()
            eg_bits.frombytes(eg_bytes)
        docids = vbyte_decode_list(vb_bytes)
        if use_dgaps:
            docids = restore_from_dgaps(docids)
        freqs = elias_gamma_decode_list(eg_bits)[:n_freqs]
        # Verificación simple: misma cantidad de docids y freqs
        if len(docids) != len(freqs):
            print(
                f"[ERROR] Descompresión inconsistente para '{termino}': docids={len(docids)}, freqs={len(freqs)}"
            )
            ok = False
    t1 = time.time()
    print(
        f"Descompresión {'con' if use_dgaps else 'sin'} DGaps terminada. Tiempo total: {t1 - t0:.2f} s"
    )
    return t1 - t0, ok


def graficar_histogramas(resultados, tiempos_descomp):
    labels = [
        "DocIDs sin DGaps",
        "Freqs sin DGaps",
        "DocIDs con DGaps",
        "Freqs con DGaps"
    ]
    tamanios = [
        resultados[0]["docids_total"],
        resultados[0]["freqs_total"],
        resultados[1]["docids_total"],
        resultados[1]["freqs_total"]
    ]
    tiempos_comp = [
        resultados[0]["tiempo"],
        resultados[0]["tiempo"],
        resultados[1]["tiempo"],
        resultados[1]["tiempo"]
    ]
    tiempos_desc = [
        tiempos_descomp[0],
        tiempos_descomp[0],
        tiempos_descomp[1],
        tiempos_descomp[1]
    ]
    x = range(len(labels))
    plt.figure(figsize=(10,5))
    plt.bar(x, tamanios, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    plt.xticks(x, labels, rotation=20)
    plt.ylabel("Tamaño (bytes)")
    plt.title("Tamaño comprimido de DocIDs y Frecuencias (con/sin DGaps)")
    plt.tight_layout()
    plt.savefig("hist_tamanio_postings.png")
    plt.figure(figsize=(10,5))
    plt.bar(x, tiempos_comp, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    plt.xticks(x, labels, rotation=20)
    plt.ylabel("Tiempo de compresión (s)")
    plt.title("Tiempo de compresión de DocIDs y Frecuencias (con/sin DGaps)")
    plt.tight_layout()
    plt.savefig("hist_tiempo_compresion.png")
    plt.figure(figsize=(10,5))
    plt.bar(x, tiempos_desc, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    plt.xticks(x, labels, rotation=20)
    plt.ylabel("Tiempo de descompresión (s)")
    plt.title("Tiempo de descompresión de DocIDs y Frecuencias (con/sin DGaps)")
    plt.tight_layout()
    plt.savefig("hist_tiempo_descompresion.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ejercicio 7: Compresión del índice invertido usando VByte y Elias-gamma."
    )
    parser.add_argument(
        "--corpus-path", required=True, help="Directorio raíz de los documentos."
    )
    parser.add_argument(
        "--index-compressed",
        default=None,
        help="Directorio de salida para el índice comprimido (opcional)",
    )
    args = parser.parse_args()
    comprimir_postings(args.corpus_path, args.index_compressed)
