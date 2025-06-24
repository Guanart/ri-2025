import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel
import matplotlib.pyplot as plt
import networkx as nx
import os


def main():
    print("=== EJERCICIO 5: ANÁLISIS DE PAGERANK Y HITS ===")
    print("Consigna: Recolección de 500 páginas para análisis de PageRank y HITS")
    
    # Elegir tipo de crawler
    use_parallel = input("¿Usar crawler paralelo? (s/N): ").lower().strip() == "s"
    
    # Elegir si preservar query strings
    preserve_query = input("¿Preservar query strings en las URLs? (s/N): ").lower().strip() == "s"
    
    # Fijar en 500 páginas según la consigna
    max_pages = 500
    print(f"Páginas objetivo: {max_pages} (según consigna del ejercicio)")
    
    # Elegir cantidad de páginas (opcional para experimentar)
    change_pages = input("¿Cambiar cantidad de páginas para experimentar? (s/N): ").lower().strip() == "s"
    if change_pages:
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
    
    # URLs semilla
    initial_urls = [
        "https://www.google.com"
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
        
        # Crear crawler
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
        
        # Guardar estado
        crawler.save_state(pkl_path)
        
        print("\n=== CRAWLING COMPLETADO ===")
        print(f"Tiempo total: {elapsed:.2f} segundos")
        print(f"Páginas obtenidas: {len(crawler.done_list)}")
        if elapsed > 0:
            print(f"Velocidad: {len(crawler.done_list)/elapsed:.2f} páginas/segundo")

######################################################################################
#   Calcular PageRank y HITS usando el grafo completo como root set
######################################################################################
    print("Calculando PageRank y HITS usando el grafo completo como root set...")
    G = crawler.build_networkx_graph()

    if len(G.nodes()) == 0:
        print("Error: No se pudo construir el grafo")
        return

    # Calcular PageRank y HITS
    pagerank = nx.pagerank(G, alpha=0.85)
    hits_auth, _ = nx.hits(G, max_iter=1000)

    # Ordenamientos
    orden_pr = [
        node for node, _ in sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    ]
    orden_auth = [
        node for node, _ in sorted(hits_auth.items(), key=lambda x: x[1], reverse=True)
    ]

    # Calcular overlap para ambos enfoques
    ks = list(range(10, min(501, len(G.nodes())), 10))
    overlap_pr = []

    for k in ks:
        top_auth = set(orden_auth[:k])
        top_pr = set(orden_pr[:k])
        inter_pr = top_auth & top_pr
        overlap_pr.append(len(inter_pr) / k)

    # Graficar comparación
    plt.figure(figsize=(10, 6))
    plt.plot(ks, overlap_pr, label="Crawling por PageRank vs Authority", marker="x")
    plt.xlabel("k (top páginas consideradas)")
    plt.ylabel("Porcentaje de overlap con Authority")
    plt.title("Evolución del overlap con Authority para dos estrategias de crawling")
    plt.grid(True)
    plt.legend()
    
    # Guardar con nombre descriptivo
    graph_filename = f"overlap_analysis_{crawler_type}_{max_pages}p_{query_suffix}.png"
    plt.savefig(graph_filename)
    print(f"Gráfico guardado como: {graph_filename}")

    print("\n\nOverlap graficado y guardado.")

    # Mostrar algunos resultados básicos
    print(f"\nTotal de páginas analizadas: {len(crawler.done_list)}")
    print(f"Páginas con PageRank > 0: {len([p for p in pagerank.values() if p > 0])}")
    print(f"Páginas con Authority > 0: {len([a for a in hits_auth.values() if a > 0])}")

    print("\nTop 5 páginas por PageRank:")
    for i, node_id in enumerate(orden_pr[:5]):
        # Buscar la tarea correspondiente
        for task in crawler.done_list:
            if task.id == node_id:
                print(f"  {i+1}. {task.url[:80]} (PR: {pagerank[node_id]:.6f})")
                break

    print("\nTop 5 páginas por Authorities:")
    for i, node_id in enumerate(orden_auth[:5]):
        # Buscar la tarea correspondiente
        for task in crawler.done_list:
            if task.id == node_id:
                print(f"  {i+1}. {task.url[:80]} (Auth: {hits_auth[node_id]:.6f})")
                break


if __name__ == "__main__":
    main()
