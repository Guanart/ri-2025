import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel

def test_ejercicio1():
    print("=== TESTING EJERCICIO 1 ===")
    try:
        crawler = Crawler(max_depth=0, max_dir_depth=0, max_pages_per_site=1, preserve_query=True)
        url = "https://httpbin.org/html"
        page = crawler.fetch_page(url)
        if page:
            links = crawler.parse_links(page, url)
            print(f"✅ Ejercicio 1: {len(links)} enlaces encontrados")
        else:
            print("❌ Ejercicio 1: No se pudo descargar la página")
    except Exception as e:
        print(f"❌ Ejercicio 1: Error - {e}")

def test_ejercicio2():
    print("=== TESTING EJERCICIO 2 ===")
    try:
        # Test crawler secuencial
        crawler = Crawler(max_depth=1, max_dir_depth=1, max_pages_per_site=3, max_total_pages=5)
        crawler.crawl(["https://httpbin.org/html"])
        print(f"✅ Crawler secuencial: {len(crawler.done_list)} páginas")
        
        # Test crawler paralelo
        crawler_parallel = CrawlerParallel(max_depth=1, max_dir_depth=1, max_pages_per_site=3, max_total_pages=5, max_workers=2)
        crawler_parallel.crawl(["https://httpbin.org/html"])
        print(f"✅ Crawler paralelo: {len(crawler_parallel.done_list)} páginas")
        
    except Exception as e:
        print(f"❌ Ejercicio 2: Error - {e}")

if __name__ == "__main__":
    test_ejercicio1()
    test_ejercicio2()
    print("\n✅ Todos los tests completados")
