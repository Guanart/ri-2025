class SkipList:
    """
    Clase para manejar la skip list de un término, almacenada como lista de (docid, offset_byte).
    Permite buscar el mayor skip cuyo docid <= target_docid y obtener el offset correspondiente.
    """

    def __init__(self, skips: list[tuple[int, int]]):
        self.skips = skips  # lista de (docid, offset_byte)
        self.idx = 0  # índice actual en la skip list

    def skip_to_offset(self, target_docid: int, current_offset: int) -> int | None:
        """
        Devuelve el offset en bytes al que se puede saltar (o None si no corresponde saltar).
        """
        while (
            self.idx + 1 < len(self.skips)
            and self.skips[self.idx + 1][0] <= target_docid
        ):
            self.idx += 1
        if (
            self.idx < len(self.skips)
            and self.skips[self.idx][0] <= target_docid
            and self.skips[self.idx][1] > current_offset
        ):
            return self.skips[self.idx][1]
        return None