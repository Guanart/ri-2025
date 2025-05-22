import argparse
import time
from collections import defaultdict
from lib.Tokenizador import Tokenizador
from lib.IRSystemBSBI import IRSystemBSBI
from lib.IndexadorBSBI import IndexadorBSBI

class IRSystemDump10k(IRSystemBSBI):
    """
    Extiende IRSystemBSBI para soportar dump10k.txt (sin docnames ni frecuencias).
    """
    def __init__(self, analyzer):
        super().__init__(analyzer)

    def taat_and(self, terms):
        # AND puro, sin boolean.py, sobre listas de docIDs
        postings_lists = [self.analyzer.vocabulary.get(t, {}).get("postings", []) for t in terms]
        if not postings_lists or any(len(pl)==0 for pl in postings_lists):
            return []
        result = postings_lists[0]
        for plist in postings_lists[1:]:
            i, j = 0, 0
            temp = []
            while i < len(result) and j < len(plist):
                if result[i] == plist[j]:
                    temp.append(result[i])
                    i += 1
                    j += 1
                elif result[i] < plist[j]:
                    i += 1
                else:
                    j += 1
            result = temp
            if not result:
                break
        return result

    def daat_and(self, terms):
        postings_lists = [self.analyzer.vocabulary.get(t, {}).get("postings", []) for t in terms]
        if not postings_lists or any(len(pl)==0 for pl in postings_lists):
            return []
        pointers = [0] * len(postings_lists)
        result = []
        while True:
            current_ids = []
            ended = False
            for idx, plist in enumerate(postings_lists):
                if pointers[idx] >= len(plist):
                    ended = True
                    break
                current_ids.append(plist[pointers[idx]])
            if ended:
                break
            if all(x == current_ids[0] for x in current_ids):
                result.append(current_ids[0])
                pointers = [p+1 for p in pointers]
            else:
                max_id = max(current_ids)
                for idx in range(len(pointers)):
                    while pointers[idx] < len(postings_lists[idx]) and postings_lists[idx][pointers[idx]] < max_id:
                        pointers[idx] += 1
        return result

def load_queries(filepath):
    with open(filepath, "r", encoding="utf8") as f:
        return [line.strip() for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(
        description="Evalúa TAAT y DAAT sobre dump10k.txt y compara tiempos."
    )
    parser.add_argument("--index-file", required=True, help="Archivo dump10k.txt")
    parser.add_argument("--queries-file", required=True, help="Archivo de queries")
    args = parser.parse_args()

    # Instanciar Tokenizador aunque no se use
    tokenizer = Tokenizador()
    indexador = IndexadorBSBI(tokenizer)
    # Cargar el vocabulario desde dump10k.txt (sin docnames ni frecuencias, frecuencia=1)
    indexador.vocabulary = {}
    with open(args.index_file, "r", encoding="utf8") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) < 3:
                continue
            term = parts[0]
            postings = [int(doc_id) for doc_id in parts[2].split(",") if doc_id]
            # Frecuencia 1 para todos (no se usa)
            indexador.vocabulary[term] = {"postings": postings, "df": len(postings)}    # no se usa la key "puntero", porque no almacenamos en disco -> usamos postings directamente
    irsys = IRSystemDump10k(indexador)

    queries = load_queries(args.queries_file)

    results_taat = []
    results_daat = []

    for q in queries:
        terms = q.strip().split()
        postings_lists = []
        postlens = []
        for t in terms:
            plist = indexador.vocabulary.get(t, {}).get("postings", [])
            postings_lists.append(plist)
            postlens.append(len(plist))
        if len(postings_lists) < 2:
            continue  # Solo queries de 2+ términos

        # TAAT usando IRSystemDump10k
        t0 = time.time()
        res_taat = irsys.taat_and(terms)
        t1 = time.time()
        results_taat.append((q, len(res_taat), t1-t0, len(terms), postlens))

        # DAAT usando IRSystemDump10k
        t0 = time.time()
        res_daat = irsys.daat_and(terms)
        t1 = time.time()
        results_daat.append((q, len(res_daat), t1-t0, len(terms), postlens))

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

    def analyze_by_length(results):
        by_q_len = defaultdict(list)
        by_post_len = defaultdict(list)
        for q, nres, t, qlen, postlens in results:
            by_q_len[qlen].append(t)
            for plen in postlens:
                by_post_len[plen].append(t)
        print("\n--- Análisis por longitud de query ---")
        for qlen in sorted(by_q_len):
            times = by_q_len[qlen]
            print(f"Query len={qlen}: {len(times)} queries, tiempo promedio={sum(times)/len(times):.6f}s")
        print("\n--- Análisis por longitud de posting list ---")
        for plen in sorted(by_post_len):
            times = by_post_len[plen]
            print(f"Posting len={plen}: {len(times)} apariciones, tiempo promedio={sum(times)/len(times):.6f}s")

    print_summary(results_taat, "TAAT (AND)")
    print_summary(results_daat, "DAAT (AND)")
    print("\n--- Comparación de tiempos promedio ---")
    if results_taat and results_daat:
        avg_taat = sum(t for _,_,t,_,_ in results_taat)/len(results_taat)
        avg_daat = sum(t for _,_,t,_,_ in results_daat)/len(results_daat)
        print(f"TAAT promedio: {avg_taat:.6f}s")
        print(f"DAAT promedio: {avg_daat:.6f}s")
    analyze_by_length(results_taat)
    analyze_by_length(results_daat)

if __name__ == "__main__":
    main()
