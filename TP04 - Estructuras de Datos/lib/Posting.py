import struct


class Posting:
    """
    Representa una entrada de la posting list de un término.
    Atributos:
        doc_id: int - ID del documento
        freq: int - Frecuencia del término en el documento
    Métodos:
        to_bytes() / from_bytes(): serialización/deserialización binaria
    """

    STRUCT_FORMAT = "II"  # 2 unsigned ints
    SIZE = 8  # 2 * 4 bytes
    doc_id_map = None  # Mapping global para doc_id -> doc_name

    def __init__(self, doc_id: int, freq: int):
        self.doc_id = doc_id
        self.freq = freq

    @classmethod
    def set_doc_id_map(cls, doc_id_map):
        cls.doc_id_map = doc_id_map

    @property
    def doc_name(self):
        if self.doc_id_map:
            return self.doc_id_map.get(self.doc_id, str(self.doc_id))
        return str(self.doc_id)

    def to_bytes(self) -> bytes:
        """
        Serializa doc_id y freq como enteros de 4 bytes con la librería struct y la máscara definida en STRUCT_FORMAT.
        """
        return struct.pack(self.STRUCT_FORMAT, self.doc_id, self.freq)

    @staticmethod
    def from_bytes(data: bytes) -> "Posting":
        """
        Deserializa los primeros N bytes de data como doc_id y freq, usando el formato STRUCT_FORMAT.
        """
        doc_id, freq = struct.unpack(Posting.STRUCT_FORMAT, data[: Posting.SIZE])
        return Posting(doc_id, freq)
