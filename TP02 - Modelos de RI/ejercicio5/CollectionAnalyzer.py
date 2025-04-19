import os
import math
from collections import Counter
from bs4 import BeautifulSoup


class CollectionAnalyzer:
    """
    Indexa una colección de documentos (.txt o .html) en memoria usando la clase Tokenizador.
    Construye:
    - docs_terms: docid -> numero de tokens
    - df: término -> número de documentos
    - idf: término -> log(N/df)
    - term_index: término -> posición en vector
    """

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.docs_terms = {}  # docid -> numero de tokens
        self.df = {}  # término -> doc frequency
        self.idf = {}  # término -> inverse doc freq
        self.term_index = {}  # término -> índice en vector
        self.N = 0  # total de documentos

    def index_collection(self, path):
        # Recorre recursivamente el directorio
        for root, _, files in os.walk(path):
            for fname in files:
                if fname.endswith((".html", ".txt")):
                    docid = os.path.relpath(os.path.join(root, fname), path)
                    with open(
                        os.path.join(root, fname), encoding="utf8", errors="ignore"
                    ) as f:
                        text = f.read()
                        if fname.endswith(".html"):
                            text = BeautifulSoup(text, "html.parser").get_text(
                                separator=" "
                            )
                    tokens = self.tokenizer.tokenizar(text)
                    self.docs_terms[docid] = Counter(tokens)    # Por cada docid, crea un dict que almacena la frecuencia de cada término
        self.N = len(self.docs_terms)   # Complejidad O(1)

        # Calcular DF e IDF
        for term in {t for cnt in self.docs_terms.values() for t in cnt}:   # comprensión de conjunto -> conjunto de términos únicos
            self.df[term] = sum(1 for cnt in self.docs_terms.values() if term in cnt)
            self.idf[term] = math.log(self.N / self.df[term])   # por defecto usa logaritmo natural
        # Complejidad O(N * M) donde N es el número de documentos y M el número de términos únicos

        # Mapear términos a índices de vector
        for i, term in enumerate(sorted(self.idf.keys())):
            self.term_index[term] = i
