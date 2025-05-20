import argparse
import time
from lib.Tokenizador import Tokenizador
from lib.IRSystemBSBI import IRSystemBSBI
from lib.IndexadorBSBI import IndexadorBSBI


def load_queries(filepath):
    with open(filepath, "r", encoding="utf8") as f:
        return [
            line.split(":", 1)[1].strip() if ":" in line else line.strip()
            for line in f
            if line.strip()
        ]


def main():
    parser = argparse.ArgumentParser(
        description="Evalúa queries booleanas TAAT y mide tiempos (con y sin skips)."
    )
    parser.add_argument(
        "--corpus-path", required=True, help="Directorio raíz de los documentos."
    )
    parser.add_argument("--queries-file", required=True, help="Archivo de queries.")
    args = parser.parse_args()

    tokenizer = Tokenizador()
    indexador = IndexadorBSBI(tokenizer)
    irsys = IRSystemBSBI(indexador)
    irsys.index_collection(args.corpus_path)
    vocabulary = set(indexador.get_vocabulary().keys())

    queries = load_queries(args.queries_file)
    patterns_2 = [
        "{0} AND {1}",
    ]

    results_taat: list[tuple[str, int, float]] = []
    results_skips: list[tuple[str, int, float]] = []

    for q in queries:
        terms = tokenizer.tokenizar(q)
        if len(terms) == 2 and all(t in vocabulary for t in terms):
            for pat in patterns_2:
                query_str = pat.format(*terms)
                try:
                    # TAAT clásico
                    t0 = time.time()
                    res = irsys.taat_query(query_str)
                    t1 = time.time()
                    results_taat.append((query_str, len(res), t1 - t0))
                    # TAAT con skips
                    t0 = time.time()
                    res_skips = irsys.taat_query_with_skips(query_str)
                    t1 = time.time()
                    results_skips.append((query_str, len(res_skips), t1 - t0))
                except Exception as e:
                    print(f"Query inválida o no parseable: '{query_str}' ({e})")

    def print_summary(results, title):
        if not results:
            print(f"\nNo hay resultados para {title}.")
            return
        results = sorted(results, key=lambda x: x[2])
        print(f"\n{'=' * 20} {title} {'=' * 20}")
        print("{:<40} {:>10} {:>12}".format("Query", "Resultados", "Tiempo (s)"))
        print("-" * 70)
        for q, nres, t in results[:10]:
            print("{:<40} {:>10} {:>12.6f}".format(q, nres, t))
        if len(results) > 20:
            print("...")
        for q, nres, t in results[-10:]:
            print("{:<40} {:>10} {:>12.6f}".format(q, nres, t))

    print_summary(results_taat, "TAAT clásico")
    print_summary(results_skips, "TAAT con skips")


if __name__ == "__main__":
    main()
