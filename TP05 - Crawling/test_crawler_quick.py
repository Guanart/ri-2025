from lib.Crawler import Crawler
import os


def test_crawler():
    """Test rápido del crawler secuencial"""
    initial_urls = [
        "https://www.google.com",
        "https://www.youtube.com",
        "https://www.github.com",
    ]

    pkl_path = "test_crawler_quick.pkl"

    # Limpiar estado anterior
    if os.path.exists(pkl_path):
        os.remove(pkl_path)

    print("=== INICIANDO CRAWLING SECUENCIAL DE PRUEBA ===")

    # Configuración para crawling rápido
    crawler = Crawler(
        max_depth=1,  # Solo profundidad 1
        max_dir_depth=2,
        max_pages_per_site=5,  # Pocas páginas por sitio
        max_total_pages=20,  # Límite muy bajo
    )

    # Ejecutar crawling
    crawler.crawl(initial_urls)

    # Guardar estado
    crawler.save_state(pkl_path)

    # Mostrar estadísticas
    stats = crawler.get_statistics()
    print("=== ESTADÍSTICAS FINALES ===")
    print(f"Total de páginas: {stats['total_pages']}")
    print(f"Páginas dinámicas: {stats['dynamic_pages']}")
    print(f"Páginas estáticas: {stats['static_pages']}")
    print(
        f"Páginas fallidas: {stats.get('failed_pages', 'N/A')}"
    )  # Usar get() para compatibilidad
    print(f"Dominios únicos: {len(stats['domains'])}")

    print("\n=== PROBANDO CARGA DE ESTADO ===")
    # Probar carga de estado
    crawler2 = Crawler.load_state(pkl_path)
    stats2 = crawler2.get_statistics()
    print(f"Estado cargado - Total de páginas: {stats2['total_pages']}")
    print(f"Páginas fallidas desde estado: {stats2.get('failed_pages', 'N/A')}")

    print("✅ Prueba completada exitosamente!")


if __name__ == "__main__":
    test_crawler()
