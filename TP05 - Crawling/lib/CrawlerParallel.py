from typing import List, Optional, Dict, Set
from dataclasses import dataclass, field
import urllib.parse
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import pickle
import time
import threading
import concurrent.futures
from queue import Queue, Empty
import networkx as nx


@dataclass
class PageTask:
    url: str
    outlinks: List[int] = field(default_factory=list)
    id: Optional[int] = None
    depth: int = 0


class CrawlerParallel:
    """
    Clase Crawler completamente paralela que maximiza la velocidad de crawling.
    Utiliza múltiples workers concurrentes para procesar la cola de URLs.
    """
    
    def __init__(
        self,
        max_depth: int = 3,
        max_dir_depth: int = 3,
        max_pages_per_site: int = 20,
        domain_filter: Optional[str] = None,
        max_workers: int = 10,
        max_total_pages: int = 1000,
        preserve_query: bool = False,
    ):
        self.max_depth: int = max_depth
        self.max_dir_depth: int = max_dir_depth
        self.max_pages_per_site: int = max_pages_per_site
        self.domain_filter: Optional[str] = domain_filter
        self.max_workers: int = max_workers
        self.max_total_pages: int = max_total_pages
        self.preserve_query: bool = preserve_query
        
        # Estructuras thread-safe
        self.todo_queue: Queue = Queue()
        self.done_list: List[PageTask] = []
        self.site_page_count: Dict[str, int] = {}
        self.url_to_task: Dict[str, PageTask] = {}
        self.processed_urls: Set[str] = set()
        
        # Locks para sincronización
        self.done_lock = threading.Lock()
        self.task_lock = threading.Lock()
        self.count_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Estadísticas
        self.total_processed: int = 0
        self.failed_count: int = 0
        
        # Control de parada
        self.should_stop = threading.Event()
        self.active_workers = 0
        self.workers_lock = threading.Lock()

    def fetch_page(self, url: str, retries: int = 1) -> Optional[str]:
        """Descarga una página con reintentos optimizado para paralelización."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, timeout=2, headers=headers)
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                if attempt < retries:
                    time.sleep(0.2)  # Pausa muy corta
                    continue
        return None

    def normalize_url(self, href: str, base_url: str, preserve_query: bool = False) -> Optional[str]:
        """Convierte un enlace relativo a absoluto, filtra URLs válidas y opcionalmente limpia query params."""
        try:
            abs_url = urllib.parse.urljoin(base_url, href)
            if abs_url.startswith("http://") or abs_url.startswith("https://"):
                # Parsear URL
                parsed = urllib.parse.urlparse(abs_url)
                if preserve_query:
                    # Mantener query params pero remover fragments
                    clean_url = urllib.parse.urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path, 
                        parsed.params, parsed.query, ''  # mantener params y query, sin fragment
                    ))
                else:
                    # Remover query params y fragments (comportamiento original)
                    clean_url = urllib.parse.urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path, 
                        '', '', ''  # sin params, query, fragment
                    ))
                return clean_url
        except:
            pass
        return None

    def parse_links(self, html: str, base_url: str) -> List[str]:
        """Extrae enlaces de una página HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                if isinstance(a, Tag):
                    href = a.get("href", None)
                    if isinstance(href, str):
                        norm_url = self.normalize_url(href, base_url, self.preserve_query)
                        if norm_url and norm_url not in self.processed_urls:
                            links.append(norm_url)
            return links
        except:
            return []

    def get_domain(self, url: str) -> str:
        """Extrae el dominio de una URL."""
        try:
            return urllib.parse.urlparse(url).netloc
        except:
            return ""

    def get_dir_depth(self, url: str) -> int:
        """Calcula la profundidad física (directorio) de una URL."""
        try:
            path = urllib.parse.urlparse(url).path
            return path.count("/")
        except:
            return 0

    def is_dynamic_page(self, url: str) -> bool:
        """Determina si una página es dinámica."""
        dynamic_indicators = [
            '?', '&', '=', '.php', '.asp', '.aspx', '.jsp', '.py',
            '/search', '/query', '/api/', '/ajax', 'cgi-bin'
        ]
        return any(indicator in url.lower() for indicator in dynamic_indicators)

    def should_add_link(self, url: str, depth: int, dir_depth: int, domain: str) -> bool:
        """Determina si se debe agregar un enlace a la cola."""
        with self.count_lock:
            if self.site_page_count.get(domain, 0) >= self.max_pages_per_site:
                return False
        
        if depth > self.max_depth:
            return False
        if dir_depth > self.max_dir_depth:
            return False
        if self.domain_filter and self.domain_filter not in domain:
            return False
        
        return True

    def add_task(self, url: str, depth: int) -> Optional[PageTask]:
        """Agrega una nueva tarea de forma thread-safe."""
        with self.task_lock:
            if url in self.url_to_task:
                return self.url_to_task[url]
            
            task = PageTask(url=url, depth=depth)
            task.id = len(self.url_to_task)
            self.url_to_task[url] = task
            self.todo_queue.put(task)
            return task

    def worker(self, worker_id: int):
        """Worker que procesa URLs de la cola."""
        with self.workers_lock:
            self.active_workers += 1
        
        try:
            while not self.should_stop.is_set():
                try:
                    # Verificar si se alcanzó el límite total
                    if len(self.done_list) >= self.max_total_pages:
                        break
                    
                    # Obtener tarea con timeout
                    current = self.todo_queue.get(timeout=2)
                    if current is None:  # Señal de parada
                        break
                    
                    # Verificar si ya fue procesada
                    if current.url in self.processed_urls:
                        self.todo_queue.task_done()
                        continue
                    
                    # Marcar como procesada
                    with self.stats_lock:
                        self.processed_urls.add(current.url)
                    
                    domain = self.get_domain(current.url)
                    
                    # Descargar página
                    page = self.fetch_page(current.url)
                    
                    if page:
                        # Actualizar contador de sitio
                        with self.count_lock:
                            self.site_page_count[domain] = self.site_page_count.get(domain, 0) + 1
                        
                        # Extraer enlaces
                        links = self.parse_links(page, current.url)
                        
                        # Procesar enlaces
                        for link in links:
                            logical_depth = current.depth + 1
                            dir_depth = self.get_dir_depth(link)
                            link_domain = self.get_domain(link)
                            
                            if self.should_add_link(link, logical_depth, dir_depth, link_domain):
                                new_task = self.add_task(link, logical_depth)
                                if new_task and new_task.id is not None:
                                    current.outlinks.append(new_task.id)
                        
                        # Agregar a lista de completadas
                        with self.done_lock:
                            self.done_list.append(current)
                        
                        with self.stats_lock:
                            self.total_processed += 1
                            if self.total_processed % 10 == 0:  # Actualizar cada 10 páginas
                                print(f"\rWorker-{worker_id}: {self.total_processed} páginas, "
                                      f"Cola: {self.todo_queue.qsize()}, "
                                      f"Última: {current.url[:40]}", end="", flush=True)
                    else:
                        with self.stats_lock:
                            self.failed_count += 1
                    
                    self.todo_queue.task_done()
                    
                except Empty:
                    # Verificar si hay workers activos o cola vacía
                    if self.todo_queue.empty():
                        time.sleep(0.1)
                        if self.todo_queue.empty():  # Doble verificación
                            break
                    continue
                except Exception as e:
                    print(f"Error en worker {worker_id}: {e}")
                    continue
        
        finally:
            with self.workers_lock:
                self.active_workers -= 1

    def crawl(self, initial_urls: List[str]) -> None:
        """Ejecuta crawling completamente paralelo."""
        print(f"Iniciando crawling paralelo con {self.max_workers} workers...")
        
        # Agregar URLs iniciales
        for url in initial_urls:
            self.add_task(url, depth=0)
        
        print(f"URLs iniciales agregadas: {len(initial_urls)}")
        
        # Crear y lanzar workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Lanzar workers
            futures = [executor.submit(self.worker, i) for i in range(self.max_workers)]
            
            try:
                # Esperar a que terminen todos los workers
                concurrent.futures.wait(futures, timeout=None)
            except KeyboardInterrupt:
                print("\nInterrumpido por usuario...")
                self.should_stop.set()
        
        print(f"\nCrawling completado: {self.total_processed} páginas, {self.failed_count} fallos")

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del crawling."""
        if not self.done_list:
            return {}
        
        depth_distribution = {}
        dir_depth_distribution = {}
        
        for task in self.done_list:
            # Distribución por profundidad lógica
            depth = task.depth
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
            
            # Distribución por profundidad física
            dir_depth = self.get_dir_depth(task.url)
            dir_depth_distribution[dir_depth] = dir_depth_distribution.get(dir_depth, 0) + 1
        
        # Páginas dinámicas vs estáticas
        dynamic_count = sum(1 for task in self.done_list if self.is_dynamic_page(task.url))
        static_count = len(self.done_list) - dynamic_count
        
        return {
            'total_pages': len(self.done_list),
            'dynamic_pages': dynamic_count,
            'static_pages': static_count,
            'depth_distribution': depth_distribution,
            'dir_depth_distribution': dir_depth_distribution,
            'domains': dict(self.site_page_count),
            'failed_pages': self.failed_count
        }

    def save_state(self, filepath: str) -> None:
        """Guarda el estado del crawler."""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'done_list': self.done_list,
                'site_page_count': self.site_page_count,
                'max_depth': self.max_depth,
                'max_dir_depth': self.max_dir_depth,
                'max_pages_per_site': self.max_pages_per_site,
                'domain_filter': self.domain_filter,
                'preserve_query': self.preserve_query,
                'total_processed': self.total_processed,
                'failed_count': self.failed_count
            }, f)

    @staticmethod
    def load_state(filepath: str) -> "CrawlerParallel":
        """Carga el estado del crawler."""
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        crawler = CrawlerParallel(
            max_depth=state['max_depth'],
            max_dir_depth=state['max_dir_depth'],
            max_pages_per_site=state['max_pages_per_site'],
            domain_filter=state.get('domain_filter', None),
            preserve_query=state.get('preserve_query', False)
        )
        crawler.done_list = state['done_list']
        crawler.site_page_count = state['site_page_count']
        crawler.total_processed = state.get('total_processed', 0)
        crawler.failed_count = state.get('failed_count', 0)
        
        # Reconstruir url_to_task
        for task in crawler.done_list:
            crawler.url_to_task[task.url] = task
            crawler.processed_urls.add(task.url)
        
        return crawler

    def build_networkx_graph(self):
        """Construye un grafo NetworkX."""
        G = nx.DiGraph()
        
        for task in self.done_list:
            G.add_node(task.id, url=task.url, depth=task.depth, 
                      is_dynamic=self.is_dynamic_page(task.url))
        
        for task in self.done_list:
            for out_id in task.outlinks:
                if G.has_node(out_id):
                    G.add_edge(task.id, out_id)
        
        return G

    def calculate_pagerank_and_hits(self):
        """Calcula PageRank y HITS."""
        G = self.build_networkx_graph()
        
        if len(G.nodes()) == 0:
            return {}, {}, {}
        
        try:
            pagerank = nx.pagerank(G, alpha=0.85, max_iter=100)
            hubs, authorities = nx.hits(G, max_iter=100)
            return pagerank, hubs, authorities
        except Exception:
            return {}, {}, {}
