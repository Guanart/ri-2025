from typing import Optional


class SkipList:
    """
    Permite saltar posiciones en una posting list para acelerar operaciones AND.
    Atributos:
        skips: list[int] - índices o offsets de salto
    Métodos:
        skip_to(doc_id)
    """

    def __init__(self, skips: list[int]):
        self.skips = skips

    def skip_to(self, doc_id: int) -> int:
        # Devuelve el índice del posting >= doc_id usando los skips
        pass


class Vocabulario:
    """
    Encapsula el diccionario de términos.
    Atributos:
        term: str
        df: int
        seek: int (puntero en el archivo de postings)
        (opcional) term_id: int
    Métodos:
        to_bytes(), from_bytes(), serialización con pickle
    """

    def __init__(self, term: str, df: int, seek: int, term_id: Optional[int] = None):
        self.term = term
        self.df = df
        self.seek = seek
        self.term_id = term_id

    def to_bytes(self) -> bytes:
        # Serializa los atributos a binario
        pass

    @staticmethod
    def from_bytes(data: bytes) -> "Vocabulario":
        # Deserializa desde binario
        pass
