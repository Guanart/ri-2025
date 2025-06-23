from lib.Crawler import Crawler
import matplotlib.pyplot as plt
import numpy as np
import os

def main():
    pkl_path = "ejercicio5_500pages_crawl.pkl"
    
    # Si ya existe el archivo, cargar el estado, si no, hacer crawling
    if os.path.exists(pkl_path):
        print("Cargando estado guardado...")
        crawler = Crawler.load_state(pkl_path)
    else:
        print("Iniciando crawling para 500 páginas...")
        # Usar las 20 URLs de Netcraft como semilla
        initial_urls = [
            "https://www.google.com", "https://www.youtube.com", "https://mail.google.com",
            "https://outlook.office.com", "https://www.facebook.com", "https://docs.google.com",
            "https://chatgpt.com", "https://login.microsoftonline.com", "https://www.linkedin.com",
            "https://accounts.google.com", "https://x.com", "https://www.bing.com",
            "https://www.instagram.com", "https://drive.google.com", "https://github.com",
            "https://web.whatsapp.com", "https://duckduckgo.com", "https://www.reddit.com",
            "https://calendar.google.com", "https://www.wikipedia.org"
        ]
        crawler = Crawler(max_depth=2, max_dir_depth=2, max_pages_per_site=50)
        crawler.crawl(initial_urls)
        
        # Truncar a 500 páginas si es necesario
        if len(crawler.done_list) > 500:
            crawler.done_list = crawler.done_list[:500]
        
        crawler.save_state(pkl_path)
        print(f"Crawling finalizado. Páginas recolectadas: {len(crawler.done_list)}")
    
    # Calcular PageRank y HITS
    print("Calculando PageRank y HITS...")
    pagerank, hubs, authorities = crawler.calculate_pagerank_and_hits()
    
    if not pagerank:
        print("Error: No se pudieron calcular PageRank y HITS")
        return
    
    # Ordenar páginas por PageRank y por Authorities
    sorted_by_pagerank = sorted(crawler.done_list, 
                               key=lambda x: pagerank.get(x.id, 0), reverse=True)
    sorted_by_authorities = sorted(crawler.done_list, 
                                  key=lambda x: authorities.get(x.id, 0), reverse=True)
    
    # Simular crawling por PageRank
    pagerank_crawling_order = crawler.simulate_pagerank_crawling(pagerank, len(crawler.done_list))
    
    # Calcular overlap en diferentes porcentajes del top-k
    percentages = [0.1, 0.2, 0.3, 0.4, 0.5]
    overlaps_original_vs_pagerank = []
    overlaps_authorities_vs_pagerank = []
    
    for pct in percentages:
        # Overlap entre orden original y PageRank
        overlap1 = crawler.calculate_overlap(crawler.done_list, pagerank_crawling_order, pct)
        overlaps_original_vs_pagerank.append(overlap1)
        
        # Overlap entre orden por Authorities y PageRank
        overlap2 = crawler.calculate_overlap(sorted_by_authorities, pagerank_crawling_order, pct)
        overlaps_authorities_vs_pagerank.append(overlap2)
    
    # Graficar resultados
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.bar(range(len(pagerank)), [pagerank[task.id] for task in sorted_by_pagerank[:20]])
    plt.title('Top 20 PageRank Scores')
    plt.xlabel('Páginas (ordenadas por PageRank)')
    plt.ylabel('PageRank Score')
    
    plt.subplot(2, 2, 2)
    plt.bar(range(len(authorities)), [authorities[task.id] for task in sorted_by_authorities[:20]])
    plt.title('Top 20 Authority Scores')
    plt.xlabel('Páginas (ordenadas por Authorities)')
    plt.ylabel('Authority Score')
    
    plt.subplot(2, 2, 3)
    plt.plot([p*100 for p in percentages], overlaps_original_vs_pagerank, 'o-', label='Original vs PageRank')
    plt.plot([p*100 for p in percentages], overlaps_authorities_vs_pagerank, 's-', label='Authorities vs PageRank')
    plt.title('Overlap entre estrategias de crawling')
    plt.xlabel('Top-K% de páginas')
    plt.ylabel('Porcentaje de overlap')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(2, 2, 4)
    stats = crawler.get_statistics()
    depths = list(stats['depth_distribution'].keys())
    counts = list(stats['depth_distribution'].values())
    plt.bar(depths, counts)
    plt.title('Distribución por profundidad lógica')
    plt.xlabel('Profundidad')
    plt.ylabel('Número de páginas')
    
    plt.tight_layout()
    plt.savefig('pagerank_hits_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Mostrar resultados
    print(f"\n=== RESULTADOS ===")
    print(f"Total de páginas analizadas: {len(crawler.done_list)}")
    print(f"Páginas con PageRank > 0: {len([p for p in pagerank.values() if p > 0])}")
    print(f"Páginas con Authority > 0: {len([a for a in authorities.values() if a > 0])}")
    
    print(f"\nTop 5 páginas por PageRank:")
    for i, task in enumerate(sorted_by_pagerank[:5]):
        print(f"  {i+1}. {task.url[:60]} (PR: {pagerank[task.id]:.6f})")
    
    print(f"\nTop 5 páginas por Authorities:")
    for i, task in enumerate(sorted_by_authorities[:5]):
        print(f"  {i+1}. {task.url[:60]} (Auth: {authorities[task.id]:.6f})")
    
    print(f"\nOverlap entre estrategias (Top 10%):")
    print(f"  Original vs PageRank: {overlaps_original_vs_pagerank[0]:.1f}%")
    print(f"  Authorities vs PageRank: {overlaps_authorities_vs_pagerank[0]:.1f}%")

if __name__ == "__main__":
    main()
