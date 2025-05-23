from abc import ABC, abstractmethod
from .Tokenizador import Tokenizador


class CollectionAnalyzerBase(ABC):
    """
    Clase base abstracta para analizadores de colecciones.
    """

    tokenizer: Tokenizador

    def __init__(self, tokenizer: Tokenizador):
        self.tokenizer = tokenizer

    @abstractmethod
    def index_collection(self, docs_path: str) -> None:
        """
        Indexa la colección de documentos en el directorio docs_path.
        """
        pass

    @abstractmethod
    def total_tokens(self) -> int:
        """
        Devuelve la cantidad total de tokens en la colección.
        """
        pass

    @abstractmethod
    def total_terminos(self) -> int:
        """
        Devuelve la cantidad de términos únicos en la colección.
        """
        pass
