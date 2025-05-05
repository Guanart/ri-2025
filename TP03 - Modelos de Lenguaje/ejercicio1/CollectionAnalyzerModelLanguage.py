import os
from collections import Counter
from lib.CollectionAnalyzerBase import CollectionAnalyzerBase


class CollectionAnalyzerModelLanguage(CollectionAnalyzerBase):
    """
    Analizador para modelo de lenguaje (unigramas).
    """
    def __init__(self, tokenizer):
        super().__init__(tokenizer)
        self.docs_terms = {}  # docid -> Counter(term)
        self.term_freq = Counter()  # término -> frecuencia total
        self.doc_len = {}  # docid -> cantidad de tokens
        self.N = 0  # cantidad de documentos
        self.collection_len = 0  # tokens en la colección

    def index_collection(self, path):
        for root, _, files in os.walk(path):
            for fname in files:
                if fname.endswith(('.txt', '.html')):
                    docid = os.path.relpath(os.path.join(root, fname), path)
                    with open(os.path.join(root, fname), encoding='utf8', errors='ignore') as f:
                        text = f.read()
                    tokens = self.tokenizer.tokenizar(text)
                    self.docs_terms[docid] = Counter(tokens)
                    self.doc_len[docid] = len(tokens)
                    self.term_freq.update(tokens)
                    self.collection_len += len(tokens)
        self.N = len(self.docs_terms)