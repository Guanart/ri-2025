import argparse
import sys
import time
from Tokenizador import Tokenizador
from CollectionAnalyzer import CollectionAnalyzer
from IRSystemManual import IRSystemManual
import pandas as pd

def main():
    parser = argparse.ArgumentParser(
        description="Indexa una colección y ejecuta consultas (hardcodeadas) similar a pyTerrier."
    )
    parser.add_argument(
        "--dir-root",
        type=str,
        required=True,
        help="Directorio raíz que contiene los archivos para la indexación.",
    )
    args = parser.parse_args()

    dir_root = args.dir_root
    if not dir_root:
        print(
            "Error: Debes proporcionar el argumento '--dir-root' con la ruta al directorio de datos."
        )
        sys.exit(1)

    # 1) Preparar tokenizador y analizador
    tkn = Tokenizador(eliminar_stopwords=True, stopwords_path='stopwords.txt')
    coll = CollectionAnalyzer(tokenizer=tkn)

    # 2) Indexar colección de ejercicios
    print("Indexando colección...")
    start_time = time.time()
    coll.index_collection(dir_root)
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Indexado completado en {elapsed:.2f} segundos.")

    # 3) Recuperar consultas de ejemplo y mostrar resultados
    print("-----------------------------------------------------------------")
    print("Generando matriz TF/IDF...")
    start_time = time.time()
    ir_manual = IRSystemManual(coll)
    end_time = time.time()
    elapsed = end_time - start_time
    print("Matriz TF/IDF generada en {elapsed:.2f} segundos.")
    print("-----------------------------------------------------------------")
    queries = [
        {"qid": 1, "query": "dog house"},
        {"qid": 2, "query": "human circulatory system parts"},
        {"qid": 3, "query": "Eiffel Tower history"},
        {"qid": 4, "query": "best jazz musicians"},
        {"qid": 5, "query": "usa presidents"}
    ]
    print("Consultas definidas para el experimento:")
    for q in queries:
        print(f"QID={q['qid']}, Query='{q['query']}'")
    print("-----------------------------------------------------------------")

    print("\n*** Resultados de búsqueda (Sistema TF/IDF) ***")
    for q in queries:
        print(f"\nConsulta (QID={q['qid']}): '{q['query']}'")
        results = list(ir_manual.query(q['query'], top_k=10))
        if not results:
            print("No se encontraron documentos relevantes.")
        else:
            # Formatear resultados como DataFrame
            df = pd.DataFrame([
                {"docno": docid, "score": score, "rank": rank-1}
                for rank, (docid, score) in enumerate(results, 1)
            ])
            print("\n[TF_IDF] Top 10 resultados:")
            print(df[["docno", "score", "rank"]])
        print("-----------------------------------------------------------------")

    # Mostrar cantidad de tokens y términos únicos
    print(f"\nCantidad total de tokens en la colección: {coll.total_tokens()}")
    print(f"Cantidad de términos únicos en la colección: {coll.total_terminos()}")
    print(f"Cantidad de documentos analizados: {coll.N}")

if __name__ == '__main__':
    main()
