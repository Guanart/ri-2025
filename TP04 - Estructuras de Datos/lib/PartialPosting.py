import struct


class PartialPosting:
    """
    Clase que representa un posting parcial, usado durante el proceso de indexación.
    Atributos:
        term_id: int - ID del término
        doc_id: int - ID del documento
        freq: int - frecuencia del término en el documento
    """

    STRUCT_FORMAT = "III"  # 3 unsigned ints
    SIZE = 4 * 3  # 3 enteros de 4 bytes

    def __init__(self, term_id: int, doc_id: int, freq: int):
        self.term_id: int = term_id
        self.doc_id: int = doc_id
        self.freq: int = freq

    def to_bytes(self) -> bytes:
        """
        Serializa el posting parcial a un formato binario.
        """
        return struct.pack(self.STRUCT_FORMAT, self.term_id, self.doc_id, self.freq)

    @staticmethod
    def from_bytes(data: bytes) -> "PartialPosting":
        term_id, doc_id, freq = struct.unpack(
            PartialPosting.STRUCT_FORMAT, data[: PartialPosting.SIZE]
        )
        return PartialPosting(term_id, doc_id, freq)


# Alternativa con tuplas (más eficiente que una clase):
# from collections import namedtuple
# PartialPosting = namedtuple('PartialPosting', ['term_id', 'doc_id', 'freq'])
