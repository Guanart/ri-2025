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
    args = parser.parse_args()

    tokenizer = Tokenizador()
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


if __name__ == "__main__":
    main()
