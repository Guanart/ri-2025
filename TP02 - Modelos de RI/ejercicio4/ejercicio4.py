#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Gonzalo Benito

import time
import pandas as pd
from IRSystem import IRSystem
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Indexa una colección y ejecuta consultas (hardcodeadas) utilizando PyTerrier."
    )
    parser.add_argument(
        "--dir-root",
        type=str,
        required=True,
        help="Directorio raíz que contiene los archivos .html para la indexación.",
    )
    args = parser.parse_args()

    # Verificar si el argumento fue proporcionado
    dir_root = args.dir_root
    if not dir_root:
        print(
            "Error: Debes proporcionar el argumento '--dir-root' con la ruta al directorio de datos."
        )
        sys.exit(1)

    # 1. Indexar el corpus con pyTerrier
    ir = IRSystem(index_path="./wikismall_index")
    print("Indexando colección...")
    start_time = time.time()
    ir.index_collection(dir_root=dir_root)
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Indexado completado en {elapsed:.2f} segundos.")

    # lex = ir.get_index_lexicon()
    # for i, kv in enumerate(lex):
    #     # print("%s -> %s" % (kv.getKey(), kv.getValue().toString()))
    #     # print("%s" % (kv.getKey()), end=', ')
    #     # print(kv.getFrequency())
    #     if i > 100000:
    #         break

    # 2. Ejecutar un experimento de recuperación (y evaluación)
    # 2.1. Definir 5 queries (topics)
    topics = pd.DataFrame(
        [
            {"qid": 1, "query": "dog house"},
            {"qid": 2, "query": "human circulatory system parts"},
            {"qid": 3, "query": "Eiffel Tower history"},
            {"qid": 4, "query": "best jazz musicians"},
            {"qid": 5, "query": "usa presidents"},
        ]
    )
    print("Consultas definidas para el experimento:")
    for _, row in topics.iterrows():
        print(f"QID={row.qid}, Query='{row.query}'")
    print("-----------------------------------------------------------------")

    # 2.2. Recuperar con TF/IDF y BM25
    print("Recuperando documentos con TF_IDF y BM25...")
    results_tfidf = ir.retrieve(
        topics, model="TF_IDF"
    )  # DataFrame con columnas [qid, docno, score, rank]
    results_bm25 = ir.retrieve(topics, model="BM25")

    # 3. Resultados
    print("\n*** Resultados de búsqueda ***")
    for qid in topics.qid:
        query_text = topics[topics.qid == qid]["query"].values[0]
        print("-----------------------------------------------------------------")
        print(f"\nConsulta (QID={qid}): '{query_text}'")
        # Top 10 TF_IDF
        top10_tfidf = results_tfidf[results_tfidf.qid == qid].head(10)
        print("\n[TF_IDF] Top 10 resultados:")
        print(top10_tfidf[["docno", "score", "rank"]])

        # Top 10 BM25
        top10_bm25 = results_bm25[results_bm25.qid == qid].head(10)
        print("\n[BM25] Top 10 resultados:")
        print(top10_bm25[["docno", "score", "rank"]])

    # 3.1. Calcular correlación de Spearman entre los rankings
    print("\n----------------------------------------------------------------------")
    print("Cálculo de correlaciones de Spearman para los rankings TF_IDF y BM25")
    print("----------------------------------------------------------------------")
    results = []
    for qid in topics.qid:
        for k in (10, 25, 50):
            corr = ir.compute_correlation(results_tfidf, results_bm25, qid, k)
            results.append({"qid": qid, "k": k, "spearman": corr})

    df_correlaciones = pd.DataFrame(results)
    print(df_correlaciones)

    print("\n*** Interpretación del coeficiente ***")
    print("Si el valor de correlación es cercano a 1, los rankings son muy similares.")
    print(
        "Si es cercano a 0 (o negativo), hay diferencias más marcadas entre los modelos."
    )


if __name__ == "__main__":
    main()
