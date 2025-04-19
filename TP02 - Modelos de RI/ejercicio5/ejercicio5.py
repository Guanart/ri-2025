from Tokenizador import Tokenizador
from CollectionAnalyzer import CollectionAnalyzer
from IRSystemManual import IRSystemManual

if __name__ == '__main__':
    # 1) Preparar tokenizador y analizador
    tkn = Tokenizador(eliminar_stopwords=True, stopwords_path='stopwords.txt')
    coll = CollectionAnalyzer(tokenizer=tkn)

    # 2) Indexar colección de ejercicios (carpeta en/articles)
    coll.index_collection('../datos/en/articles')

    # 3) Recuperar consultas de ejemplo y comparar con PyTerrier
    ir_manual = IRSystemManual(coll)
    queries = [
        "dog house",
        "human circulatory system parts",
        "Eiffel Tower history",
        "best jazz musicians",
        "usa presidents"
    ]
    for q in queries:
        print("\nQuery:", q)
        for rank, (docid, score) in enumerate(ir_manual.query(q, top_k=10), 1):
            print(f" {rank:2d}. {docid} (score={score:.4f})")
