import argparse
import time
from lib.Tokenizador import Tokenizador
from lib.IRSystemBSBI import IRSystemBSBI
from lib.IndexadorBSBI import IndexadorBSBI


def load_queries(filepath):
    with open(filepath, "r", encoding="utf8") as f:
        # Si la línea tiene ":", devolver solo la parte después de ":"
        return [
            line.split(":", 1)[1].strip() if ":" in line else line.strip()
            for line in f
            if line.strip()
        ]


def main():
    parser = argparse.ArgumentParser(
        description="Evalúa queries booleanas TAAT y mide tiempos."
    )
    parser.add_argument(
        "--corpus-path", required=True, help="Directorio raíz de los documentos."
    )
    parser.add_argument("--queries-file", required=True, help="Archivo de queries.")
    parser.add_argument(
        "--stopwords", default=None, help="Archivo de stopwords (opcional, por defecto usa ../ejercicio3/stopwords.txt)"
    )
    args = parser.parse_args()

    # Determinar ruta de stopwords (solo si se pasa el argumento)
    stopwords_path = args.stopwords
    if stopwords_path:
        print(f"[INFO] Usando stopwords de: {stopwords_path}")
    else:
        print("[INFO] No se usan stopwords.")

    # Pasar la ruta al tokenizador (None si no se usa stopwords)
    tokenizer = Tokenizador(stopwords_path=stopwords_path)
    indexador = IndexadorBSBI(tokenizer)
    irsys = IRSystemBSBI(indexador)
    irsys.index_collection(args.corpus_path)
    vocabulary = set(indexador.get_vocabulary().keys())

    queries = load_queries(args.queries_file)
    patterns_2 = [
        "{0} AND {1}",
        "{0} OR {1}",
        "{0} AND NOT {1}",  # <-- corregido: no reconocia los queries sin el AND antes del NOT
    ]
    patterns_3 = [
        "{0} AND {1} AND {2}",
        "({0} OR {1}) AND NOT {2}",  # <-- corregido
        "({0} AND {1}) OR {2}",
    ]

    results_2 = []
    results_3 = []

    for q in queries:
        terms = tokenizer.tokenizar(q)
        if len(terms) == 2 and all(t in vocabulary for t in terms):
            for pat in patterns_2:
                query_str = pat.format(*terms)
                try:
                    t0 = time.time()
                    res = irsys.taat_query(query_str)
                    t1 = time.time()
                    results_2.append((query_str, len(res), t1 - t0))
                except Exception as e:
                    print(f"Query inválida o no parseable: '{query_str}' ({e})")
        elif len(terms) == 3 and all(t in vocabulary for t in terms):
            for pat in patterns_3:
                query_str = pat.format(*terms)
                try:
                    t0 = time.time()
                    res = irsys.taat_query(query_str)
                    t1 = time.time()
                    results_3.append((query_str, len(res), t1 - t0))
                except Exception as e:
                    print(f"Query inválida o no parseable: '{query_str}' ({e})")

    def print_summary(results, title):
        if not results:
            print(f"\nNo hay resultados para queries de {title} términos.")
            return
        # Ordenar por tiempo de ejecución
        results = sorted(results, key=lambda x: x[2])
        n = len(results)
        print(f"\n{'='*20} {title} términos ({n} queries) {'='*20}")
        print("{:<40} {:>10} {:>12}".format("Query", "Resultados", "Tiempo (s)"))
        print("-" * 70)
        # Mostrar primeros 10
        for q, nres, t in results[:10]:
            print("{:<40} {:>10} {:>12.6f}".format(q, nres, t))
        if n > 20:
            print("...")  # Separador
        # Mostrar últimos 10
        for q, nres, t in results[-10:]:
            print("{:<40} {:>10} {:>12.6f}".format(q, nres, t))

    print_summary(results_2, 2)
    print_summary(results_3, 3)

    # --- Análisis de relación tamaño de listas vs tiempo ---
    import matplotlib.pyplot as plt
    all_results = results_2 + results_3
    postings_sizes = []
    tiempos = []
    for q, nres, t in all_results:
        terms = tokenizer.tokenizar(q)
        # Suma de tamaños de las listas de postings de la query
        sizes = [len(irsys.get_term_from_posting_list(term)) for term in terms]
        postings_sizes.append(sum(sizes))
        tiempos.append(t)
    if postings_sizes and tiempos:
        plt.scatter(postings_sizes, tiempos, alpha=0.3)
        plt.xlabel("Suma de tamaños de listas de postings en la query")
        plt.ylabel("Tiempo de ejecución (s)")
        plt.title("Relación entre tamaño de listas de postings y tiempo de ejecución")
        plt.tight_layout()
        plt.savefig("relacion_tamanio_tiempo.png")
        plt.close()
        print("[INFO] Gráfico guardado en relacion_tamanio_tiempo.png")
        # Mostrar promedios por bins
        import numpy as np
        bins = np.histogram_bin_edges(postings_sizes, bins=10)
        bin_times = [[] for _ in range(len(bins)-1)]
        for size, t in zip(postings_sizes, tiempos):
            for i in range(len(bins)-1):
                if bins[i] <= size < bins[i+1] or (i == len(bins)-2 and size == bins[-1]):
                    bin_times[i].append(t)
                    break
        print("\nPromedio de tiempos por rango de suma de tamaños de postings:")
        for i in range(len(bins)-1):
            left = int(bins[i])
            right = int(bins[i+1])-1 if i < len(bins)-2 else int(bins[i+1])
            avg = sum(bin_times[i])/len(bin_times[i]) if bin_times[i] else 0
            print(f"[{left:>7}, {right:>7}]: {len(bin_times[i]):>6} queries, tiempo promedio={avg:.6f}s")


if __name__ == "__main__":
    main()
