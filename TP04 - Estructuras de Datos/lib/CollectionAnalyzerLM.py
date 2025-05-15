import os
from collections import Counter
from .CollectionAnalyzerBase import CollectionAnalyzerBase
from .Tokenizador import Tokenizador
from typing import Dict, Counter as CounterType


class CollectionAnalyzerLM(CollectionAnalyzerBase):
    """
    Analizador para modelo de lenguaje (unigramas).
    """

    docs_terms: Dict[str, CounterType[str]]
    term_freq: CounterType[str]
    doc_len: Dict[str, int]
    N: int
    collection_len: int

    def __init__(self, tokenizer: Tokenizador):
        super().__init__(tokenizer)
        self.docs_terms: Dict[str, CounterType[str]] = {}  # docid -> Counter(term)
        self.term_freq: CounterType[str] = Counter()  # término -> frecuencia total
        self.doc_len: Dict[str, int] = {}  # docid -> cantidad de tokens
        self.N: int = 0  # cantidad de documentos
        self.collection_len: int = 0  # tokens en la colección

    def index_collection(self, docs_path: str) -> None:
        for root, _, files in os.walk(docs_path):
            for fname in files:
                if fname.endswith((".txt", ".html")):
                    docid = os.path.relpath(os.path.join(root, fname), docs_path)
                    with open(
                        os.path.join(root, fname), encoding="utf8", errors="ignore"
                    ) as f:
                        text = f.read()
                    tokens = self.tokenizer.tokenizar(text)
                    self.docs_terms[docid] = Counter(tokens)
                    self.doc_len[docid] = len(tokens)
                    self.term_freq.update(tokens)
                    self.collection_len += len(tokens)
        self.N = len(self.docs_terms)

    def total_tokens(self) -> int:
        return self.collection_len

    def total_terminos(self) -> int:
        return len(self.term_freq)
