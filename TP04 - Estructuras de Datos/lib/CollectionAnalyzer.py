import os
import math
from collections import Counter
from bs4 import BeautifulSoup
from .CollectionAnalyzerBase import CollectionAnalyzerBase
from .Tokenizador import Tokenizador
from typing import Dict, Counter as CounterType


class CollectionAnalyzer(CollectionAnalyzerBase):
    """
    Indexa una colección de documentos (.txt o .html) en memoria usando la clase Tokenizador.
    Construye:
    - docs_terms: docid -> numero de tokens
    - df: término -> número de documentos
    - idf: término -> log(N/df)
    - term_index: término -> posición en vector
    """

    docs_terms: Dict[str, CounterType[str]]
    df: CounterType[str]
    idf: Dict[str, float]
    term_index: Dict[str, int]
    N: int

    def __init__(self, tokenizer: Tokenizador):
        super().__init__(tokenizer)
        self.docs_terms: Dict[str, CounterType[str]] = {}  # docid -> numero de tokens
        self.df: CounterType[str] = Counter()  # término -> doc frequency
        self.idf: Dict[str, float] = {}  # término -> inverse doc freq
        self.term_index: Dict[str, int] = {}  # término -> índice en vector
        self.N: int = 0  # total de documentos

    def index_collection(self, path: str) -> None:
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
                            """
                            ACÁ SE PODRÍA HACER UN PARSEO MÁS COMPLEJO DEL HTML (usando BeautifulSoup)
                            """
                    tokens = self.tokenizer.tokenizar(text)
                    self.docs_terms[docid] = Counter(
                        tokens
                    )  # Por cada docid, crea un dict que almacena la frecuencia de cada término
        self.N = len(self.docs_terms)  # Complejidad O(1)

        # Calcular DF e IDF
        for cnt in self.docs_terms.values():
            for term in cnt.keys():
                self.df[term] += 1
        for term in self.df:
            self.idf[term] = math.log(
                self.N / self.df[term]
            )  # por defecto usa logaritmo natural

        # Mapear términos a índices de vector
        for i, term in enumerate(
            sorted(self.idf.keys())
        ):  # Los ordena alfabéticamente para que la asignación de índices sea determinística (siempre la misma posición para cada término).
            self.term_index[term] = (
                i  # Guarda el índice numérico que ocupará ese término en los vectores TF–IDF
            )
            # En el espacio vectorial, cada documento (y cada consulta) se representa con un vector de longitud V (tamaño del vocabulario). Para saber en qué posición del vector colocar el peso de un cada término, necesitamos un mapeo término→índice único.

    def total_tokens(self) -> int:
        return sum(sum(cnt.values()) for cnt in self.docs_terms.values())

    def total_terminos(self) -> int:
        return len(self.term_index)
