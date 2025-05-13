import re
from typing import List, Set


class Tokenizador:
    """
    Tokenizador:
    - Extrae URLs, emails, números (incluye negativos), nombres propios y palabras.
    - Aplica filtros de longitud y stopwords.
    """

    eliminar_stopwords: bool
    min_len: int
    max_len: int
    stopwords: Set[str]
    url_pattern: re.Pattern
    email_pattern: re.Pattern
    acronym_pattern: re.Pattern
    abreviations_pattern: re.Pattern
    number_pattern: re.Pattern
    proper_name_pattern: re.Pattern
    word_pattern: re.Pattern

    def __init__(
        self,
        stopwords_path: str = None,
        min_len: int = 1,
        max_len: int = 20,
    ):
        # Configuración
        self.eliminar_stopwords = stopwords_path is not None
        self.min_len = min_len
        self.max_len = max_len
        # Cargar stopwords si corresponde
        self.stopwords = set()
        if self.eliminar_stopwords:
            with open(stopwords_path, "r", encoding="utf-8") as f:
                for line in f:
                    self.stopwords.add(line.strip().lower())
        # Compilar patrones
        self.url_pattern = re.compile(
            r"""
            (?:\b[a-zA-Z][a-zA-Z0-9+\.\-]*://           # Protocolo: http, https o ftp seguido de ://
                (?:[a-zA-Z0-9.-]+\.[A-Za-z]{2,})   # Dominio: al menos un punto y extensión (p.ej., example.com)
                (?::\d{1,5})?                     # Puerto opcional: : seguido de dígitos
                (?:/[^\s?#]*)?                    # Path opcional: barra seguida de cualquier caracter excepto espacio, ? o #
                (?:\?[^\s#]*)?                    # Query string opcional: ? seguido de cualquier caracter excepto espacio o #
                (?:\#[^\s]*)?                     # Fragmento opcional: # seguido de cualquier caracter excepto espacio
            )
            """,
            re.VERBOSE,
        )
        self.email_pattern = re.compile(
            r"(?:[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,})"
        )
        self.acronym_pattern = re.compile(
            r"(?:(?:[A-Za-z]+(?:\.[A-Za-z]+)+)\.?)"
        )  # Acrónimos como "U.S.A.", "EE.UU.
        self.abreviations_pattern = re.compile(
            r"(?:[A-Za-z]{2,}\.)"
        )  # Abreviaturas como "Dr.", "Lic.", "Sra."
        self.number_pattern = re.compile(
            r"(?:\d+(?:[-\.,]\d+)*)"
        )  # Números (con guiones, puntos o comas) como fechas o decimales)
        self.proper_name_pattern = re.compile(
            r"(?:(?:[A-Z][a-z]+)(?:\s+(?![A-Za-z]{2,}\.)[A-Z][a-z]+)+)"
        )  # Nombres propios compuestos (al menos dos palabras con mayúscula inicial) como "Domingo Faustino Sarmiento"
        self.word_pattern = re.compile(r"(?:[A-Za-zÁÉÍÓÚÜÑáéíóúüñçàèìòùâêîôûäëïöü]+)")

    def tokenizar(self, texto: str) -> List[str]:
        """
        Tokenización compatible con pyTerrier: solo palabras y números, sin duplicidad.
        """
        # Extraer URLs/emails y eliminarlos del texto
        texto = self.url_pattern.sub(" ", texto)
        texto = self.email_pattern.sub(" ", texto)
        # Extraer palabras y números
        tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñçàèìòùâêîôûäëïöü0-9]+", texto)
        # Normalizar
        tokens = [t.lower() for t in tokens if t.strip()]
        # Filtrar longitud
        tokens = [t for t in tokens if self.min_len <= len(t) <= self.max_len]
        # Filtrar stopwords
        if self.eliminar_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords]
        return tokens
