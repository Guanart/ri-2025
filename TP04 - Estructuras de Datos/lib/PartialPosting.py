import struct

class PartialPosting:
    """
    Clase que representa un posting parcial, usado durante el proceso de indexación.
    Atributos:
        term_id: int - ID del término
        doc_id: int - ID del documento
        freq: int - frecuencia del término en el documento
    """
    def __init__(self, term_id: int, doc_id: int, freq: int):
        self.term_id: int = term_id
        self.doc_id: int = doc_id
        self.freq: int = freq

    def to_bytes(self) -> bytes:
        """
        Serializa el posting parcial a un formato binario.
        Cada atributo se empaqueta como un entero sin signo (4 bytes cada uno).
        """
        return struct.pack('III', self.term_id, self.doc_id, self.freq)

# Alternativa con tuplas (más eficiente que una clase):
# from collections import namedtuple
# PartialPosting = namedtuple('PartialPosting', ['term_id', 'doc_id', 'freq'])