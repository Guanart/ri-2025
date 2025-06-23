#!/usr/bin/env python3
"""
Script para probar la funcionalidad preserve_query del CrawlerParallel.
Compara el comportamiento con y sin query parameters.
"""

from lib.CrawlerParallel import CrawlerParallel
import time
import os


def test_preserve_query():
    """Prueba el crawling con y sin query parameters."""

    # URLs de prueba que típicamente tienen query parameters
    test_urls = [
        "https://www.amazon.com",
        "https://www.google.com",
        "https://github.com/search?q=python",
    ]

    print("=== PRUEBA: PRESERVE_QUERY = FALSE (por defecto) ===")
    print("Query parameters y fragments serán removidos")

    # Test 1: Sin preservar query params (comportamiento por defecto)
    crawler_no_query = CrawlerParallel(
        max_depth=1,
        max_pages_per_site=5,
        max_workers=4,
        max_total_pages=20,
        preserve_query=False,
    )

    start_time = time.time()
    crawler_no_query.crawl(test_urls)
    time_no_query = time.time() - start_time

    print(f"\nResultados SIN query params:")
    print(f"  Tiempo: {time_no_query:.2f}s")
    print(f"  Páginas: {len(crawler_no_query.done_list)}")
    print(f"  Ejemplo URLs procesadas:")

    for i, task in enumerate(crawler_no_query.done_list[:5]):
        print(f"    {i+1}. {task.url}")

    # Analizar URLs únicas
    urls_no_query = set(task.url for task in crawler_no_query.done_list)

    print("\n" + "=" * 60)
    print("=== PRUEBA: PRESERVE_QUERY = TRUE ===")
    print("Query parameters serán mantenidos (solo fragments removidos)")

    # Test 2: Preservando query params
    crawler_with_query = CrawlerParallel(
        max_depth=1,
        max_pages_per_site=5,
        max_workers=4,
        max_total_pages=20,
        preserve_query=True,  # Preservar query params
    )

    start_time = time.time()
    crawler_with_query.crawl(test_urls)
    time_with_query = time.time() - start_time

    print(f"\nResultados CON query params:")
    print(f"  Tiempo: {time_with_query:.2f}s")
    print(f"  Páginas: {len(crawler_with_query.done_list)}")
    print(f"  Ejemplo URLs procesadas:")

    for i, task in enumerate(crawler_with_query.done_list[:5]):
        print(f"    {i+1}. {task.url}")

    # Analizar URLs únicas
    urls_with_query = set(task.url for task in crawler_with_query.done_list)

    print("\n" + "=" * 60)
    print("=== ANÁLISIS COMPARATIVO ===")

    # Detectar URLs con query parameters
    urls_with_params_no_query = [url for url in urls_no_query if "?" in url]
    urls_with_params_with_query = [url for url in urls_with_query if "?" in url]

    print(
        f"URLs con query params (preserve_query=False): {len(urls_with_params_no_query)}"
    )
    print(
        f"URLs con query params (preserve_query=True): {len(urls_with_params_with_query)}"
    )

    print(f"\nTotal URLs únicas (preserve_query=False): {len(urls_no_query)}")
    print(f"Total URLs únicas (preserve_query=True): {len(urls_with_query)}")

    # Mostrar ejemplos de URLs con query params cuando preserve_query=True
    if urls_with_params_with_query:
        print(f"\nEjemplos de URLs con query params preservados:")
        for url in list(urls_with_params_with_query)[:3]:
            print(f"  • {url}")

    # Estadísticas detalladas
    stats_no_query = crawler_no_query.get_statistics()
    stats_with_query = crawler_with_query.get_statistics()

    print(
        f"\nPáginas dinámicas (preserve_query=False): {stats_no_query.get('dynamic_pages', 0)}"
    )
    print(
        f"Páginas dinámicas (preserve_query=True): {stats_with_query.get('dynamic_pages', 0)}"
    )

    print(
        f"\nPáginas estáticas (preserve_query=False): {stats_no_query.get('static_pages', 0)}"
    )
    print(
        f"Páginas estáticas (preserve_query=True): {stats_with_query.get('static_pages', 0)}"
    )

    print("\n=== RECOMENDACIÓN ===")
    print("• preserve_query=False: Mejor para crawling general, menos duplicados")
    print("• preserve_query=True: Mejor para análisis de páginas dinámicas específicas")


if __name__ == "__main__":
    test_preserve_query()
