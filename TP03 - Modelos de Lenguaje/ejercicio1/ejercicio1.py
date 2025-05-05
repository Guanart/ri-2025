import argparse
import sys
import os
import time
import CollectionAnalyzerModelLanguage
import IRSystemLanguageModel
from lib.Tokenizador import Tokenizador


def main():
    parser = argparse.ArgumentParser(
        description="Indexa una colección y ejecuta consultas usando el modelo de lenguaje."
    )
    parser.add_argument(
        "--corpus-path",
        type=str,
        required=True,
        help="Directorio raíz que contiene los archivos para la indexación.",
    )
    args = parser.parse_args()

    corpus_path = args.corpus_path
    if not corpus_path:
        print("Error: Debes proporcionar el argumento '--corpus-path' con la ruta al directorio de datos.")
        sys.exit(1)

    # Inicializar tokenizer y analizador
    tokenizer = Tokenizador()
    analyzer = CollectionAnalyzerModelLanguage(tokenizer)

    print("Indexando colección...")
    start_time = time.time()
    analyzer.index_collection(corpus_path)
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Indexado completado en {elapsed:.2f} segundos.")

    # Inicializar sistema de RI
    irsys = IRSystemLanguageModel(analyzer)

    # Consultas
    consultas = [
        "país cultura",
        "país libre cultura",
        "software propietario licencia"
    ]
    print("\nConsultas definidas para el experimento:")
    for idx, q in enumerate(consultas, 1):
        print(f"Q{idx}: '{q}'")
    print("-----------------------------------------------------------------")

    print("\n*** Resultados de búsqueda (Query Likelihood sin suavizado) ***")
    for idx, q in enumerate(consultas, 1):
        print(f"\nConsulta Q{idx}: '{q}'")
        ranking = irsys.query_likelihood(q, lamb=0.0)
        if not ranking:
            print("No se encontraron documentos relevantes.")
        else:
            for rank, (docid, score) in enumerate(ranking, 1):
                print(f"{rank}. {docid}: {score:.2f}")
        print("-----------------------------------------------------------------")

    print("\n*** Resultados de búsqueda (Jelinek-Mercer, lambda=0.7) ***")
    for idx, q in enumerate(consultas, 1):
        print(f"\nConsulta Q{idx}: '{q}'")
        ranking = irsys.query_likelihood(q, lamb=0.7)
        if not ranking:
            print("No se encontraron documentos relevantes.")
        else:
            for rank, (docid, score) in enumerate(ranking, 1):
                print(f"{rank}. {docid}: {score:.2f}")
        print("-----------------------------------------------------------------")

    # Mostrar estadísticas de la colección
    if hasattr(analyzer, 'total_tokens') and hasattr(analyzer, 'total_terminos') and hasattr(analyzer, 'N'):
        print(f"\nCantidad total de tokens en la colección: {analyzer.total_tokens()}")
        print(f"Cantidad de términos únicos en la colección: {analyzer.total_terminos()}")
        print(f"Cantidad de documentos analizados: {analyzer.N}")

if __name__ == '__main__':
    main()