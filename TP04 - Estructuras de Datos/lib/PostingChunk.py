from typing import Optional
from PartialPosting import PartialPosting
import struct

class PostingChunk:
    """
    Maneja un bloque (chunk) de postings parciales en disco.
    Atributos:
        partial_postings: list[PartialPosting]
        pos: int - posición actual en el chunk
        file_path: str - ruta al archivo en disco
    Métodos:
        next(), reset(), merge_with(), read/write en binario
    """
    def __init__(self, partial_postings: list[PartialPosting], file_path: Optional[str] = None):
        self.partial_postings: list[PartialPosting] = partial_postings
        self.pos: int = 0
        self.file_path: str = file_path

    def next(self) -> Optional[PartialPosting]:
        if self.pos < len(self.partial_postings):
            p = self.partial_postings[self.pos]
            self.pos += 1
            return p
        return None

    def reset(self) -> None:
        self.pos = 0

    def write_to_disk(self) -> None:
        """
        Escribe el chunk en disco en formato binario puro.
        Cada posting se serializa como tres enteros (term_id, doc_id, freq), 12 bytes por posting.
        """
        if not self.file_path:
            raise ValueError("file_path no especificado para PostingChunk.")
        with open(self.file_path, 'wb') as f:
            for posting in self.partial_postings:
                f.write(posting.to_bytes())

    @staticmethod
    def read_from_disk(file_path: str) -> 'PostingChunk':
        # Lee un chunk desde disco y devuelve un PostingChunk
        pass

    def merge_with(self, other: 'PostingChunk') -> 'PostingChunk':
        # Devuelve un nuevo PostingChunk con la fusión ordenada de self y other
        pass
