import argparse
import time
from collections import defaultdict


def load_vocabulary(corpus_path):
    print(f"Cargando vocabulario desde {corpus_path}...")
    vocabulario = {}
    with open(corpus_path, "r", encoding="utf8") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) < 3:
                continue
            term = parts[0]
            postings = [int(doc_id) for doc_id in parts[2].split(",") if doc_id]
            vocabulario[term] = postings
    print(f"Vocabulario cargado: {len(vocabulario)} términos.")
    return vocabulario


def taat(postings_lists: list[list[int]], top_k=10):
    """TAAT (Term At A Time) para ranking: suma scores parciales (TF crudo) por docid. Devuelve top_k."""
    from collections import defaultdict

    scores = defaultdict(int)
    for plist in postings_lists:
        for docid in plist:
            scores[docid] += 1
    # Devolver top_k docid ordenados por score descendente y docid ascendente
    sorted_scores = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return sorted_scores[:top_k]


def daat(postings_lists: list[list[int]], top_k=10):
    """DAAT (Document At A Time) para ranking: suma scores parciales (TF crudo) por docid usando heap. Devuelve top_k."""
    candidate_docids = sorted({doc_id for plist in postings_lists for doc_id in plist})
    from heapq import heappush, heappushpop

    heap = []
    pointers = [0] * len(postings_lists)
    for doc_id in candidate_docids:
        score = 0
        for i, plist in enumerate(postings_lists):
            while pointers[i] < len(plist) and plist[pointers[i]] < doc_id:
                pointers[i] += 1
            if pointers[i] < len(plist) and plist[pointers[i]] == doc_id:
                score += 1
        if len(heap) < top_k:
            heappush(heap, (score, doc_id))
        else:
            if score > heap[0][0]:
                heappushpop(heap, (score, doc_id))
    # Devolver top_k docid ordenados por score descendente y docid ascendente
    return sorted(heap, key=lambda x: (-x[0], x[1]))


def load_queries(filepath):
    print(f"Cargando queries desde {filepath}...")
    with open(filepath, "r", encoding="utf8") as f:
        queries = [line.strip() for line in f if 2 <= len(line.strip().split()) <= 4]
    print(f"Queries cargadas: {len(queries)}.")
    return queries


def print_summary(results, title):
    if not results:
        print(f"\nNo hay resultados para {title}.")
        return
    results = sorted(results, key=lambda x: x[2])
    print(f"\n{'=' * 20} {title} {'=' * 20}")
    print("{:<40} {:>10} {:>12}".format("Query", "Resultados", "Tiempo (s)"))
    print("-" * 70)
    for q, nres, t, _, _ in results[:10]:
        print("{:<40} {:>10} {:>12.6f}".format(q, nres, t))
    if len(results) > 20:
        print("...")
    for q, nres, t, _, _ in results[-10:]:
        print("{:<40} {:>10} {:>12.6f}".format(q, nres, t))


def analyze_by_length(results_taat, results_daat):
    import numpy as np
    import matplotlib.pyplot as plt

    def print_query_stats(results, label):
        print(f"\n{'=' * 10} Análisis por longitud de query [{label}] {'=' * 10}")
        by_q_len = defaultdict(list)
        for q, nres, t, qlen, postlens in results:
            by_q_len[qlen].append(t)
        for qlen in sorted(by_q_len):
            times = by_q_len[qlen]
            print(
                f"Query len={qlen}: {len(times)} queries, tiempo promedio={sum(times) / len(times):.6f}s"
            )

    # Mostrar análisis por longitud de query y posting list
    print_query_stats(results_taat, "TAAT")
    print_query_stats(results_daat, "DAAT")

    # Binning de longitudes de posting list para promedios de tiempo
    all_postlens = []
    for q, nres, t, qlen, postlens in results_taat:
        all_postlens.extend(postlens)
    if not all_postlens:
        return
    n_bins = 10
    bin_edges = np.histogram_bin_edges(all_postlens, bins=n_bins)
    taat_bin_times = [[] for _ in range(len(bin_edges) - 1)]
    daat_bin_times = [[] for _ in range(len(bin_edges) - 1)]
    # Asignar cada tiempo a su bin correspondiente para TAAT
    for q, nres, t, qlen, postlens in results_taat:
        for plen in postlens:
            for i in range(len(bin_edges) - 1):
                if bin_edges[i] <= plen < bin_edges[i + 1] or (
                    i == len(bin_edges) - 2 and plen == bin_edges[-1]
                ):
                    taat_bin_times[i].append(t)
                    break
    # Asignar cada tiempo a su bin correspondiente para DAAT
    for q, nres, t, qlen, postlens in results_daat:
        for plen in postlens:
            for i in range(len(bin_edges) - 1):
                if bin_edges[i] <= plen < bin_edges[i + 1] or (
                    i == len(bin_edges) - 2 and plen == bin_edges[-1]
                ):
                    daat_bin_times[i].append(t)
                    break
    print(
        "\nPromedio de tiempos por rango de longitud de posting list (comparativo TAAT vs DAAT):"
    )
    print(
        "{:<20} {:>10} {:>15} {:>15}".format(
            "Rango", "#Apariciones", "TAAT (s)", "DAAT (s)"
        )
    )
    print("-" * 65)
    taat_avg_times = []
    daat_avg_times = []
    bin_labels = []
    for i in range(len(bin_edges) - 1):
        left = int(bin_edges[i])
        right = (
            int(bin_edges[i + 1]) - 1
            if i < len(bin_edges) - 2
            else int(bin_edges[i + 1])
        )
        count = max(len(taat_bin_times[i]), len(daat_bin_times[i]))
        avg_taat = (
            sum(taat_bin_times[i]) / len(taat_bin_times[i]) if taat_bin_times[i] else 0
        )
        avg_daat = (
            sum(daat_bin_times[i]) / len(daat_bin_times[i]) if daat_bin_times[i] else 0
        )
        print(
            f"[{left:>7}, {right:>7}]: {count:>10} {avg_taat:>15.6f} {avg_daat:>15.6f}"
        )
        taat_avg_times.append(avg_taat)
        daat_avg_times.append(avg_daat)
        bin_labels.append(f"{left}-{right}")
    # Exportar histograma comparativo
    plt.figure(figsize=(10, 5))
    width = 0.4
    x = np.arange(len(bin_labels))
    plt.bar(
        x - width / 2,
        taat_avg_times,
        width=width,
        label="TAAT",
        color="orange",
        edgecolor="black",
    )
    plt.bar(
        x + width / 2,
        daat_avg_times,
        width=width,
        label="DAAT",
        color="blue",
        edgecolor="black",
    )
    plt.xticks(x, bin_labels, rotation=45, ha="right")
    plt.title("Tiempo promedio por rango de longitud de posting list (TAAT vs DAAT)")
    plt.xlabel("Rango de longitud de posting list")
    plt.ylabel("Tiempo promedio (s)")
    plt.legend()
    plt.tight_layout()
    filename = "hist_tiempo_postinglist_comparativo.png"
    plt.savefig(filename)
    print(f"[INFO] Histograma comparativo guardado en: {filename}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Evalúa TAAT y DAAT sobre dump10k.txt y compara tiempos."
    )
    parser.add_argument("--corpus-path", required=True, help="Archivo dump10k.txt")
    parser.add_argument("--queries-file", required=True, help="Archivo de queries")
    parser.add_argument(
        "--top-k", type=int, default=10, help="Cantidad de resultados top-k a devolver"
    )
    args = parser.parse_args()

    vocabulario = load_vocabulary(args.corpus_path)
    queries = load_queries(args.queries_file)

    results_taat = []
    results_daat = []

    print("Procesando queries...")
    for idx, q in enumerate(queries):
        print(f"Procesando query {idx + 1}/{len(queries)}: '{q}'")
        terms = q.strip().split()
        postings_lists: list[list[int]] = []
        postlens = []
        for t in terms:
            plist = vocabulario.get(t, [])
            postings_lists.append(plist)
            postlens.append(len(plist))
        if len(postings_lists) < 2:
            print("  - Query ignorada (menos de 2 términos con postings)")
            continue  # Solo queries de 2+ términos

        # TAAT
        t0 = time.time()
        res_taat = taat(postings_lists, top_k=args.top_k)
        t1 = time.time()
        results_taat.append((q, len(res_taat), t1 - t0, len(terms), postlens))
        print(f"  - TAAT: {len(res_taat)} resultados, tiempo: {t1 - t0:.6f}s")

        # DAAT
        t0 = time.time()
        res_daat = daat(postings_lists, top_k=args.top_k)
        t1 = time.time()
        results_daat.append((q, len(res_daat), t1 - t0, len(terms), postlens))
        print(f"  - DAAT: {len(res_daat)} resultados, tiempo: {t1 - t0:.6f}s")

    print_summary(results_taat, "TAAT")
    print_summary(results_daat, "DAAT")
    print("\n--- Comparación de tiempos promedio ---")
    if results_taat and results_daat:
        avg_taat = sum(t for _, _, t, _, _ in results_taat) / len(results_taat)
        avg_daat = sum(t for _, _, t, _, _ in results_daat) / len(results_daat)
        print(f"TAAT promedio: {avg_taat:.6f}s")
        print(f"DAAT promedio: {avg_daat:.6f}s")
    analyze_by_length(results_taat, results_daat)


if __name__ == "__main__":
    main()
