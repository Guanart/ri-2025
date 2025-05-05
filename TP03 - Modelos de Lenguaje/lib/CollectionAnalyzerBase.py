class CollectionAnalyzerBase:
    """
    Clase base para analizadores de colecciones.
    """
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer