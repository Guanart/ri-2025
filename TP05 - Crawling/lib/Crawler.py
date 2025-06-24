from typing import List, Optional, Dict
from dataclasses import dataclass, field
import urllib.parse
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from collections import deque
import pickle
import time
import networkx as nx


@dataclass
class PageTask:
    url: str
    outlinks: List[int] = field(default_factory=list)
    id: Optional[int] = None
    depth: int = 0


class Crawler:
    """
    Clase Crawler que implementa un crawler web básico.
    Permite rastrear páginas web, extraer enlaces y aplicar filtros personalizados.

    Ejemplo de uso:
    ```python
    crawler = Crawler(["https://ejemplo.com"], max_depth=3, max_dir_depth=3, max_pages_per_site=20)
    crawler.crawl()
    print(crawler.done_list)
    ```
    """

    def __init__(
        self,
        max_depth: int = 3,
        max_dir_depth: int = 3,
        max_pages_per_site: int = 20,
        domain_filter: Optional[str] = None,
        max_total_pages: int = 1000,
        preserve_query: bool = False,
    ):
        self.max_depth: int = max_depth
        self.max_dir_depth: int = max_dir_depth
        self.max_pages_per_site: int = max_pages_per_site
        self.domain_filter: Optional[str] = domain_filter
        self.max_total_pages: int = max_total_pages
        self.preserve_query: bool = preserve_query

        # Estructuras de datos
        self.todo_list: deque[PageTask] = deque()
        self.done_list: List[PageTask] = []
        self.site_page_count: Dict[str, int] = {}
        self.url_to_task: Dict[str, PageTask] = {}
        self.processed_urls: set = set()

        # Estadísticas
        self.total_processed: int = 0
        self.failed_count: int = 0

    def fetch_page(self, url: str, retries: int = 1) -> Optional[str]:
        """Descarga una página con reintentos y timeout optimizado."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }

        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, timeout=3, headers=headers)
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                if attempt < retries:
                    time.sleep(0.5)  # Pausa corta antes del reintento
                    continue
        return None

    def normalize_url(
        self, href: str, base_url: str, preserve_query: bool = False
    ) -> Optional[str]:
        """Convierte un enlace relativo a absoluto, filtra URLs válidas y opcionalmente limpia query params."""
        abs_url = urllib.parse.urljoin(base_url, href)
        if abs_url.startswith("http://") or abs_url.startswith("https://"):
            # Parsear URL
            parsed = urllib.parse.urlparse(abs_url)
            if preserve_query:
                # Mantener query params pero remover fragments
                clean_url = urllib.parse.urlunparse(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        "",  # mantener params y query, sin fragment
                    )
                )
            else:
                # Remover query params y fragments (comportamiento original)
                clean_url = urllib.parse.urlunparse(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        "",
                        "",
                        "",  # sin params, query, fragment
                    )
                )
            return clean_url
        return None

    def parse_links(self, html: str, base_url: str) -> List[str]:
        """Extrae enlaces de una página HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            links: List[str] = []
            for a in soup.find_all("a", href=True):
                if isinstance(a, Tag):
                    href = a.get("href", None)
                    if isinstance(href, str):
                        norm_url = self.normalize_url(
                            href, base_url, preserve_query=self.preserve_query
                        )
                        if norm_url and norm_url not in self.processed_urls:
                            links.append(norm_url)
            return links
        except Exception:
            return []

    def get_domain(self, url: str) -> str:
        return urllib.parse.urlparse(url).netloc

    def get_dir_depth(self, url: str) -> int:
        path = urllib.parse.urlparse(url).path
        return path.count("/")

    def is_dynamic_page(self, url: str) -> bool:
        """Determina si una página es dinámica basándose en patrones en la URL."""
        dynamic_indicators = [
            "?",
            "&",
            "=",  # Query parameters
            ".php",
            ".asp",
            ".aspx",
            ".jsp",
            ".py",  # Dynamic extensions
            "/search",
            "/query",
            "/api/",
            "/ajax",  # Dynamic paths
            "cgi-bin",
            "action=",
            "id=",
            "page=",  # Common dynamic patterns
        ]
        return any(indicator in url.lower() for indicator in dynamic_indicators)

    def _should_add_link(
        self, url: str, depth: int, dir_depth: int, domain: str
    ) -> bool:
        if self.site_page_count.get(domain, 0) >= self.max_pages_per_site:
            return False
        if depth > self.max_depth:
            return False
        if dir_depth > self.max_dir_depth:
            return False
        # Filtrar por dominio si está especificado
        if self.domain_filter and self.domain_filter not in domain:
            return False
        return True

    def crawl(self, initial_urls: List[str]) -> None:
        """Ejecuta crawling secuencial."""
        print("Iniciando crawling secuencial...")

        # Agregar URLs iniciales
        for url in initial_urls:
            if url not in self.url_to_task:
                task = PageTask(url=url, depth=0)
                task.id = len(self.url_to_task)
                self.url_to_task[url] = task
                self.todo_list.append(task)

        print(f"URLs iniciales agregadas: {len(initial_urls)}")

        # Procesar cola secuencialmente
        while self.todo_list and len(self.done_list) < self.max_total_pages:
            current = self.todo_list.popleft()

            # Verificar si ya fue procesada
            if current.url in self.processed_urls:
                continue

            # Marcar como procesada
            self.processed_urls.add(current.url)

            domain = self.get_domain(current.url)

            # Descargar página
            page = self.fetch_page(current.url)

            if page:
                # Actualizar contador de sitio
                self.site_page_count[domain] = self.site_page_count.get(domain, 0) + 1

                # Extraer enlaces
                links = self.parse_links(page, current.url)

                # Procesar enlaces
                for link in links:
                    logical_depth = current.depth + 1
                    dir_depth = self.get_dir_depth(link)
                    link_domain = self.get_domain(link)

                    if self._should_add_link(
                        link, logical_depth, dir_depth, link_domain
                    ):
                        if link not in self.url_to_task:
                            new_task = PageTask(url=link, depth=logical_depth)
                            new_task.id = len(self.url_to_task)
                            self.url_to_task[link] = new_task
                            self.todo_list.append(new_task)

                        if (
                            link in self.url_to_task
                            and self.url_to_task[link].id is not None
                        ):
                            target_id = self.url_to_task[link].id
                            if target_id is not None:
                                current.outlinks.append(target_id)

                # Agregar a lista de completadas
                self.done_list.append(current)
                self.total_processed += 1

                # Mostrar progreso cada 10 páginas
                if self.total_processed % 10 == 0:
                    print(
                        f"\rProcesadas: {self.total_processed} páginas, "
                        f"Cola: {len(self.todo_list)}, "
                        f"Última: {current.url[:40]}",
                        end="",
                        flush=True,
                    )
            else:
                self.failed_count += 1

        print(
            f"\nCrawling completado: {self.total_processed} páginas, {self.failed_count} fallos"
        )

    def save_state(self, filepath: str) -> None:
        """Guarda el estado del crawler."""
        with open(filepath, "wb") as f:
            pickle.dump(
                {
                    "done_list": self.done_list,
                    "site_page_count": self.site_page_count,
                    "max_depth": self.max_depth,
                    "max_dir_depth": self.max_dir_depth,
                    "max_pages_per_site": self.max_pages_per_site,
                    "domain_filter": self.domain_filter,
                    "preserve_query": self.preserve_query,
                    "max_total_pages": self.max_total_pages,
                    "total_processed": self.total_processed,
                    "failed_count": self.failed_count,
                },
                f,
            )

    @staticmethod
    def load_state(filepath: str) -> "Crawler":
        """Carga el estado del crawler."""
        with open(filepath, "rb") as f:
            state = pickle.load(f)

        crawler = Crawler(
            max_depth=state["max_depth"],
            max_dir_depth=state["max_dir_depth"],
            max_pages_per_site=state["max_pages_per_site"],
            domain_filter=state.get("domain_filter", None),
            preserve_query=state.get("preserve_query", False),
            max_total_pages=state.get("max_total_pages", 1000),
        )
        crawler.done_list = state["done_list"]
        crawler.site_page_count = state["site_page_count"]
        crawler.total_processed = state.get(
            "total_processed", len(state["done_list"])
        )  # Fallback al número de páginas
        crawler.failed_count = state.get("failed_count", 0)

        # Reconstruir url_to_task y processed_urls
        for task in crawler.done_list:
            crawler.url_to_task[task.url] = task
            crawler.processed_urls.add(task.url)

        # Asegurar que los IDs estén consistentes
        max_id = 0
        for task in crawler.done_list:
            if task.id is not None:
                max_id = max(max_id, task.id)
            else:
                # Asignar ID si no tiene uno
                task.id = max_id + 1
                max_id += 1

        return crawler

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del crawling realizado."""
        if not self.done_list:
            return {
                "total_pages": 0,
                "dynamic_pages": 0,
                "static_pages": 0,
                "depth_distribution": {},
                "dir_depth_distribution": {},
                "domains": {},
                "failed_pages": self.failed_count,
            }

        # Distribución por profundidad lógica
        depth_distribution = {}
        for task in self.done_list:
            depth = task.depth
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1

        # Distribución por profundidad física
        dir_depth_distribution = {}
        for task in self.done_list:
            dir_depth = self.get_dir_depth(task.url)
            dir_depth_distribution[dir_depth] = (
                dir_depth_distribution.get(dir_depth, 0) + 1
            )

        # Páginas dinámicas vs estáticas
        dynamic_count = sum(
            1 for task in self.done_list if self.is_dynamic_page(task.url)
        )
        static_count = len(self.done_list) - dynamic_count

        return {
            "total_pages": len(self.done_list),
            "dynamic_pages": dynamic_count,
            "static_pages": static_count,
            "depth_distribution": depth_distribution,
            "dir_depth_distribution": dir_depth_distribution,
            "domains": dict(self.site_page_count),
            "failed_pages": self.failed_count,
        }

    def build_networkx_graph(self):
        """Construye un grafo NetworkX a partir de los datos del crawler."""
        G = nx.DiGraph()

        # Agregar nodos
        for task in self.done_list:
            G.add_node(
                task.id,
                url=task.url,
                depth=task.depth,
                is_dynamic=self.is_dynamic_page(task.url),
            )

        # Agregar aristas
        for task in self.done_list:
            for out_id in task.outlinks:
                if G.has_node(out_id):  # Solo si el nodo destino existe
                    G.add_edge(task.id, out_id)

        return G
