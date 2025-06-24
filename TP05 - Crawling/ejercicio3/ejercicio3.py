import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel


def main():
    # Elegir tipo de crawler
    use_parallel = input("¿Usar crawler paralelo? (s/N): ").lower().strip() == "s"

    # Crawling de MercadoLibre con filtro de dominio
    initial_urls = ["https://www.mercadolibre.com.ar"]

    if use_parallel:
        print("Usando CrawlerParallel...")
        crawler = CrawlerParallel(
            max_depth=3,
            max_dir_depth=3,
            max_pages_per_site=500,
            domain_filter="mercadolibre.com.ar",
            preserve_query=True,  # Preservar query params
            max_total_pages=500,
            max_workers=5,  # Número de workers para crawling paralelo
        )
    else:
        print("Usando Crawler secuencial...")
        crawler = Crawler(
            max_depth=3,
            max_dir_depth=3,
            max_pages_per_site=500,
            domain_filter="mercadolibre.com.ar",
            preserve_query=True,  # Preservar query params
            max_total_pages=500,
        )

    print("Iniciando crawling de mercadolibre.com.ar...")
    crawler.crawl(initial_urls)

    # Guardar estado
    crawler.save_state("ejercicio3_mercadolibre_crawl.pkl")

    # Obtener estadísticas
    stats = crawler.get_statistics()

    print("\n=== ANÁLISIS DE MERCADOLIBRE.COM.AR ===")
    print(f"Total de páginas: {stats.get('total_pages', 0)}")

    total_pages = stats.get("total_pages", 0)
    if total_pages > 0:
        print(
            f"Páginas dinámicas: {stats.get('dynamic_pages', 0)} ({stats.get('dynamic_pages', 0)/total_pages*100:.1f}%)"
        )
        print(
            f"Páginas estáticas: {stats.get('static_pages', 0)} ({stats.get('static_pages', 0)/total_pages*100:.1f}%)"
        )
    else:
        print("Páginas dinámicas: 0 (0.0%)")
        print("Páginas estáticas: 0 (0.0%)")

    print(f"Páginas fallidas: {stats.get('failed_pages', 0)}")

    print("\nDistribución por profundidad lógica:")
    depth_dist = stats.get("depth_distribution", {})
    if depth_dist:
        for depth, count in sorted(depth_dist.items()):
            print(f"  Profundidad {depth}: {count} páginas")
    else:
        print("  No hay datos de distribución por profundidad")

    print("\nDistribución por profundidad física:")
    dir_depth_dist = stats.get("dir_depth_distribution", {})
    if dir_depth_dist:
        for dir_depth, count in sorted(dir_depth_dist.items()):
            print(f"  Directorio nivel {dir_depth}: {count} páginas")
    else:
        print("  No hay datos de distribución por directorio")


if __name__ == "__main__":
    main()
