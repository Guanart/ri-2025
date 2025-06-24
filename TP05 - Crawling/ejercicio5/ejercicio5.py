import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel
import matplotlib.pyplot as plt
import os


def truncate_crawler_results(crawler, max_pages=500):
    """Función auxiliar para truncar resultados de manera type-safe"""
    if len(crawler.done_list) > max_pages:
        # Usar slicing para crear una nueva lista
        crawler.done_list = crawler.done_list[:max_pages]
    return crawler


def main():
    print("=== EJERCICIO 5: ANÁLISIS DE PAGERANK Y HITS ===")
    
    # Elegir tipo de crawler
    use_parallel = input("¿Usar crawler paralelo? (s/N): ").lower().strip() == "s"
    
    # Elegir si preservar query strings
    preserve_query = input("¿Preservar query strings en las URLs? (s/N): ").lower().strip() == "s"
    
    # Elegir cantidad de páginas
    while True:
        try:
            max_pages = int(input("Ingresa número de páginas para análisis (recomendado 200-1000): "))
            if 50 <= max_pages <= 5000:
                break
            else:
                print("Por favor ingresa un número entre 50 y 5000")
        except ValueError:
            print("Por favor ingresa un número válido")
    
    # Si es paralelo, elegir número de workers
    max_workers = 4  # Default
    if use_parallel:
        while True:
            try:
                max_workers = int(input("Número de workers paralelos (recomendado 2-12): "))
                if 2 <= max_workers <= 12:
                    break
                else:
                    print("Por favor ingresa un número entre 2 y 12")
            except ValueError:
                print("Por favor ingresa un número válido")
    
    # Configurar archivos con nombres que incluyan los parámetros
    crawler_type = "parallel" if use_parallel else "sequential"
    query_suffix = "query" if preserve_query else "noquery"
    pkl_path = f"ejercicio5_{crawler_type}_{max_pages}p_{query_suffix}.pkl"
    
    # URLs semilla (top 20 Netcraft) - https://trends.netcraft.com/topsites
    initial_urls = [
        "https://unlu.edu.ar"
    ]

    # Si ya existe el archivo, cargar el estado, si no, hacer crawling
    if os.path.exists(pkl_path):
        print("Cargando estado guardado...")
        if use_parallel:
            crawler = CrawlerParallel.load_state(pkl_path)
        else:
            crawler = Crawler.load_state(pkl_path)
        print(f"Estado cargado: {len(crawler.done_list)} páginas")
    else:
        print(f"=== INICIANDO CRAWLING {'PARALELO' if use_parallel else 'SECUENCIAL'} ===")
        print("Configuración:")
        print(f"  - Tipo: {'Paralelo' if use_parallel else 'Secuencial'}")
        print(f"  - Páginas objetivo: {max_pages}")
        print(f"  - Preservar query: {'Sí' if preserve_query else 'No'}")
        if use_parallel:
            print(f"  - Workers: {max_workers}")
        
        # Crear crawler según configuración
        if use_parallel:
            crawler = CrawlerParallel(
                max_depth=3,
                max_dir_depth=3,
                max_pages_per_site=20,
                max_total_pages=max_pages,
                max_workers=max_workers,
                preserve_query=preserve_query
            )
        else:
            crawler = Crawler(
                max_depth=3,
                max_dir_depth=3,
                max_pages_per_site=20,
                max_total_pages=max_pages,
                preserve_query=preserve_query
            )
        
        import time
        start_time = time.time()
        crawler.crawl(initial_urls)
        elapsed = time.time() - start_time
        
        # Asegurar que no excedemos el límite usando la función auxiliar
        crawler = truncate_crawler_results(crawler, max_pages)
        
        # Guardar estado
        crawler.save_state(pkl_path)
        
        print("\n=== CRAWLING COMPLETADO ===")
        print(f"Tiempo total: {elapsed:.2f} segundos")
        print(f"Páginas obtenidas: {len(crawler.done_list)}")
        if elapsed > 0:
            print(f"Velocidad: {len(crawler.done_list)/elapsed:.2f} páginas/segundo")

######################################################################################
#   Calcular PageRank y HITS
######################################################################################
    print("Calculando PageRank y HITS...")
    pagerank, hubs, authorities = crawler.calculate_pagerank_and_hits()

    if not pagerank:
        print("Error: No se pudieron calcular PageRank y HITS")
        return

    # Ordenar páginas por PageRank y por Authorities
    sorted_by_pagerank = sorted(
        crawler.done_list, key=lambda x: pagerank.get(x.id, 0), reverse=True
    )
    sorted_by_authorities = sorted(
        crawler.done_list, key=lambda x: authorities.get(x.id, 0), reverse=True
    )

    # Calcular overlap en diferentes porcentajes del top-k
    k_values = list(range(10, 501, 10))  # De 10 a 500 de 10 en 10
    overlaps_pagerank_vs_authorities = []
    overlaps_real_vs_authority = []

    for k in k_values:
        if k <= len(crawler.done_list):
            # Overlap PageRank vs Authority
            overlap_pr_auth = crawler.calculate_overlap(
                sorted_by_pagerank, sorted_by_authorities, k / len(crawler.done_list)
            )
            overlaps_pagerank_vs_authorities.append(overlap_pr_auth)
            
            # Simular "Crawling real vs Authority" - usar orden de crawling vs authority
            crawling_order = crawler.done_list  # Orden en que se crawlearon
            overlap_real_auth = crawler.calculate_overlap(
                crawling_order, sorted_by_authorities, k / len(crawler.done_list)
            )
            overlaps_real_vs_authority.append(overlap_real_auth)
        else:
            break

    # Ajustar k_values al número real de datos
    k_values = k_values[:len(overlaps_pagerank_vs_authorities)]

    # Crear el gráfico de overlap como en la imagen
    plt.figure(figsize=(10, 6))
    
    # Línea azul: Crawling real vs Authority
    plt.plot(
        k_values,
        [o / 100 for o in overlaps_real_vs_authority],  # Convertir a decimal
        'o-',
        color='steelblue',
        linewidth=2,
        markersize=4,
        label='Crawling real vs Authority'
    )
    
    # Línea naranja: Crawling por PageRank vs Authority  
    plt.plot(
        k_values,
        [o / 100 for o in overlaps_pagerank_vs_authorities],  # Convertir a decimal
        's-',
        color='orange',
        linewidth=2,
        markersize=4,
        label='Crawling por PageRank vs Authority'
    )
    
    plt.title('Evolución del overlap con Authority para dos estrategias de crawling', fontsize=14)
    plt.xlabel('k (top páginas consideradas)', fontsize=12)
    plt.ylabel('Porcentaje de overlap con Authority', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11)
    plt.xlim(0, max(k_values))
    plt.ylim(0, 1.0)
    
    # Configurar el eje Y para mostrar de 0.0 a 1.0
    plt.gca().set_ylim(0, 1.0)
    plt.gca().set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    
    plt.tight_layout()
    plt.savefig("overlap_analysis.png", dpi=300, bbox_inches="tight")

    # Mostrar resultados
    print("\n=== RESULTADOS ===")
    print(f"Total de páginas analizadas: {len(crawler.done_list)}")
    print(f"Páginas con PageRank > 0: {len([p for p in pagerank.values() if p > 0])}")
    print(
        f"Páginas con Authority > 0: {len([a for a in authorities.values() if a > 0])}"
    )

    print("\nTop 5 páginas por PageRank:")
    for i, task in enumerate(sorted_by_pagerank[:5]):
        print(f"  {i+1}. {task.url[:60]} (PR: {pagerank.get(task.id, 0):.6f})")

    print("\nTop 5 páginas por Authorities:")
    for i, task in enumerate(sorted_by_authorities[:5]):
        print(f"  {i+1}. {task.url[:60]} (Auth: {authorities.get(task.id, 0):.6f})")

    print("\nOverlap entre estrategias (valores seleccionados):")
    sample_indices = [4, 9, 19, 29, 49]  # k=50, 100, 200, 300, 500
    for idx in sample_indices:
        if idx < len(k_values):
            k = k_values[idx]
            overlap_real = overlaps_real_vs_authority[idx]
            overlap_pr = overlaps_pagerank_vs_authorities[idx]
            print(f"  Top {k}: Real vs Auth = {overlap_real:.1f}%, PageRank vs Auth = {overlap_pr:.1f}%")


if __name__ == "__main__":
    main()
