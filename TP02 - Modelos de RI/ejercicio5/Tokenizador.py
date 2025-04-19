import re


class Tokenizador:
    """
    Tokenizador:
    - Extrae URLs, emails, números (incluye negativos), nombres propios y palabras.
    - Aplica filtros de longitud y stopwords.
    """

    def __init__(
        self,
        stopwords_path: str = None,
        eliminar_stopwords: bool = False,
        min_len: int = 1,
        max_len: int = 20,
    ):
        # Configuración
        self.eliminar_stopwords = eliminar_stopwords
        self.min_len = min_len
        self.max_len = max_len
        # Cargar stopwords si corresponde
        self.stopwords = set()
        if eliminar_stopwords and stopwords_path:
            with open(stopwords_path, "r", encoding="utf-8") as f:
                for line in f:
                    self.stopwords.add(line.strip().lower())
        # Compilar patrones
        self.url_pattern = re.compile(
            r"""
            (?:(?:\b[a-zA-Z][a-zA-Z0-9+\.\-]*://           # Protocolo: http, https o ftp seguido de ://
                (?:[a-zA-Z0-9.-]+\.[A-Za-z]{2,})   # Dominio: al menos un punto y extensión (p.ej., example.com)
                (?::\d{1,5})?                     # Puerto opcional: : seguido de dígitos
                (?:\/[^\s?#]*)?               # Path opcional: barra seguida de cualquier caracter excepto espacio, ? o #
                (?:\?[^\s#]*)?                # Query string opcional: ? seguido de cualquier caracter excepto espacio o #
                (?:\#[^\s]*)?                # Fragmento opcional: # seguido de cualquier caracter excepto espacio
            )
            """
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
        self.number_pattern = re.compile(r"(?:\d+(?:[-\.,]\d+)*)")  # Números (con guiones, puntos o comas) como fechas o decimales)
        self.proper_name_pattern = re.compile(
            r"(?:(?:[A-Z][a-z]+)(?:\s+(?![A-Za-z]{2,}\.)[A-Z][a-z]+)+)" 
        )   # Nombres propios compuestos (al menos dos palabras con mayúscula inicial) como "Domingo Faustino Sarmiento"
        self.word_pattern = re.compile(r"(?:[A-Za-zÁÉÍÓÚÜÑáéíóúüñçàèìòùâêîôûäëïöü]+)")

    def tokenizar(self, texto: str) -> list:
        """
        Extrae y normaliza tokens. Después aplica min/max length y stopwords.
        """
        # Extracción
        tokens = []
        tokens += self.url_pattern.findall(texto)
        tokens += self.email_pattern.findall(texto)
        tokens += self.number_pattern.findall(texto)
        tokens += self.proper_name_pattern.findall(texto)
        tokens += self.word_pattern.findall(texto)

        # Normalización: recortar espacios y pasar a minúsculas
        tokens = [t.strip() for t in tokens if t.strip()]
        tokens = [t.lower() for t in tokens]

        # Filtrar longitud
        tokens = [t for t in tokens if self.min_len <= len(t) <= self.max_len]

        # Filtrar stopwords
        if self.eliminar_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords]

        return tokens
