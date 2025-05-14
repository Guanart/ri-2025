import struct
from typing import Optional


class Posting:
    """
    Representa una entrada de la posting list de un término.
    Atributos:
        doc_id: int - ID del documento
        freq: int - Frecuencia del término en el documento
    Métodos:
        to_bytes() / from_bytes(): serialización/deserialización binaria
    """
    def __init__(self, doc_id: int, freq: int):
        self.doc_id = doc_id
        self.freq = freq

    def to_bytes(self) -> bytes:
        """
        Serializa doc_id y freq como enteros de 4 bytes con la librería struct y máscara (II).
        """
        return struct.pack('II', self.doc_id, self.freq)

    @staticmethod
    def from_bytes(data: bytes) -> 'Posting':
        """
        Deserializa los primeros 8 bytes de data como doc_id y freq.
        """
        doc_id, freq = struct.unpack('II', data[:8])
        return Posting(doc_id, freq)
