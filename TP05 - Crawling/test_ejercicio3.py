from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel


def test_import():
    print("Imports funcionando correctamente")

    # Test básico de inicialización
    crawler = Crawler(
        max_depth=1, max_dir_depth=1, max_pages_per_site=5, max_total_pages=10
    )
    print(f"Crawler creado: {type(crawler)}")

    crawler_parallel = CrawlerParallel(
        max_depth=1, max_dir_depth=1, max_pages_per_site=5, max_total_pages=10
    )
    print(f"CrawlerParallel creado: {type(crawler_parallel)}")


if __name__ == "__main__":
    test_import()
