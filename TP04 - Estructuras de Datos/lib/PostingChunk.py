from typing import Optional
from .PartialPosting import PartialPosting
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
    def __init__(self, partial_postings=None, file_path=None):
        """
        Si partial_postings es provisto, se usa para escritura (guardar el chunk en disco).
        Si solo se provee file_path, se usa para lectura secuencial (merge multi-way).
        """
        self.file_path = file_path
        self.partial_postings: Optional[PartialPosting] = partial_postings
        self.file = None
        self.current: PartialPosting = None
        self.eof: bool = False
        if partial_postings is None and file_path is not None:
            # Modo lectura secuencial
            self.file = open(file_path, 'rb')
            self._read_next()
        # Si partial_postings está definido, se usará write_to_disk para guardar

    def _read_next(self):
        """
        Lee el siguiente PartialPosting del archivo y lo guarda en self.current.
        Si llega al final, marca self.eof = True.
        """
        data = self.file.read(12)  # 3 enteros de 4 bytes: term_id, doc_id, freq
        if data and len(data) == 12:
            term_id, doc_id, freq = struct.unpack('III', data)
            self.current = PartialPosting(term_id, doc_id, freq)
        else:
            self.current = None
            self.eof = True

    def next(self):
        """
        Avanza al siguiente PartialPosting. Si no hay más, self.eof = True.
        """
        if not self.eof:
            self._read_next()

    def has_next(self) -> bool:
        """
        Devuelve True si hay un PartialPosting actual, False si terminó el archivo.
        """
        return not self.eof

    def get_current(self) -> Optional[PartialPosting]:
        """
        Devuelve el PartialPosting actual (o None si terminó).
        """
        return self.current

    def close(self):
        if self.file:
            self.file.close()

    def reset(self) -> None:
        self.pos = 0

    def write_to_disk(self) -> None:
        """
        Escribe el chunk en disco en formato binario puro.
        Cada posting se serializa como tres enteros (term_id, doc_id, freq), 12 bytes por posting.
        """
        if not self.file_path:
            raise ValueError("file_path no especificado para PostingChunk.")
        if self.partial_postings is None:
            raise ValueError("No hay postings en memoria para escribir.")
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
