from abc import ABC, abstractmethod
from typing import Any
from .CollectionAnalyzerBase import CollectionAnalyzerBase


class IRSystem(ABC):
    """
    Clase base abstracta para sistemas de recuperación de información.
    """

    analyzer: CollectionAnalyzerBase

    def __init__(self, analyzer: CollectionAnalyzerBase):
        self.analyzer = analyzer

    @abstractmethod
    def index_collection(self, path: str) -> None:
        """
        Indexa la colección de documentos en el directorio indicado.
        """
        pass

    @abstractmethod
    def query(self, text: str, **kwargs):
        pass
