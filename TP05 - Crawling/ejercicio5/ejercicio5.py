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
    # Elegir tipo de crawler
    use_parallel = input("¿Usar crawler paralelo? (s/N): ").lower().strip() == "s"

    pkl_path = "ejercicio5_500pages_crawl.pkl"

    # Si ya existe el archivo, cargar el estado, si no, hacer crawling
    if os.path.exists(pkl_path):
        print("Cargando estado guardado...")
        # Determinar qué tipo de crawler usar basado en el archivo
        if use_parallel:
            crawler = CrawlerParallel.load_state(pkl_path)
        else:
            crawler = Crawler.load_state(pkl_path)
    else:
        print("Iniciando crawling para 500 páginas...")
        # Usar las 20 URLs de Netcraft como semilla
        initial_urls = [
            "https://www.google.com",
            "https://www.youtube.com",
            "https://mail.google.com",
            "https://outlook.office.com",
            "https://www.facebook.com",
            "https://docs.google.com",
            "https://chatgpt.com",
            "https://login.microsoftonline.com",
            "https://www.linkedin.com",
            "https://accounts.google.com",
            "https://x.com",
            "https://www.bing.com",
            "https://www.instagram.com",
            "https://drive.google.com",
            "https://github.com",
            "https://web.whatsapp.com",
            "https://duckduckgo.com",
            "https://www.reddit.com",
            "https://calendar.google.com",
            "https://www.wikipedia.org",
        ]

        if use_parallel:
            print("Usando CrawlerParallel...")
            crawler = CrawlerParallel(
                max_depth=2,
                max_dir_depth=2,
                max_pages_per_site=25,
                max_total_pages=500,
                max_workers=8,
            )
        else:
            print("Usando Crawler secuencial...")
            crawler = Crawler(
                max_depth=2, max_dir_depth=2, max_pages_per_site=25, max_total_pages=500
            )

        crawler.crawl(initial_urls)

        # Asegurar que tenemos exactamente 500 páginas
        crawler = truncate_crawler_results(crawler, 500)

        crawler.save_state(pkl_path)
        print(f"Crawling finalizado. Páginas recolectadas: {len(crawler.done_list)}")

    # Calcular PageRank y HITS
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
    percentages = [0.1, 0.2, 0.3, 0.4, 0.5]
    overlaps_pagerank_vs_authorities = []

    for pct in percentages:
        # Overlap entre PageRank y Authorities (esto es lo que pide la consigna)
        overlap = crawler.calculate_overlap(
            sorted_by_pagerank, sorted_by_authorities, pct
        )
        overlaps_pagerank_vs_authorities.append(overlap)

    # Graficar resultados
    plt.figure(figsize=(15, 10))

    # Gráfico 1: Top 20 PageRank Scores
    plt.subplot(2, 3, 1)
    top_pagerank_scores = [pagerank.get(task.id, 0) for task in sorted_by_pagerank[:20]]
    plt.bar(range(20), top_pagerank_scores)
    plt.title("Top 20 PageRank Scores")
    plt.xlabel("Páginas (ordenadas por PageRank)")
    plt.ylabel("PageRank Score")
    plt.xticks(range(0, 20, 2))

    # Gráfico 2: Top 20 Authority Scores
    plt.subplot(2, 3, 2)
    top_authority_scores = [
        authorities.get(task.id, 0) for task in sorted_by_authorities[:20]
    ]
    plt.bar(range(20), top_authority_scores)
    plt.title("Top 20 Authority Scores")
    plt.xlabel("Páginas (ordenadas por Authorities)")
    plt.ylabel("Authority Score")
    plt.xticks(range(0, 20, 2))

    # Gráfico 3: Overlap entre PageRank y Authorities
    plt.subplot(2, 3, 3)
    plt.plot(
        [p * 100 for p in percentages],
        overlaps_pagerank_vs_authorities,
        "o-",
        color="red",
        linewidth=2,
        markersize=8,
        label="PageRank vs Authorities",
    )
    plt.title("Overlap entre PageRank y Authorities")
    plt.xlabel("Top-K% de páginas")
    plt.ylabel("Porcentaje de overlap")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Gráfico 4: Distribución por profundidad lógica
    plt.subplot(2, 3, 4)
    stats = crawler.get_statistics()
    depths = list(stats.get("depth_distribution", {}).keys())
    counts = list(stats.get("depth_distribution", {}).values())
    if depths and counts:
        plt.bar(depths, counts)
        plt.title("Distribución por profundidad lógica")
        plt.xlabel("Profundidad")
        plt.ylabel("Número de páginas")

    # Gráfico 5: Distribución dinámicas vs estáticas
    plt.subplot(2, 3, 5)
    dynamic_pages = stats.get("dynamic_pages", 0)
    static_pages = stats.get("static_pages", 0)
    plt.pie(
        [dynamic_pages, static_pages],
        labels=["Dinámicas", "Estáticas"],
        autopct="%1.1f%%",
        startangle=90,
    )
    plt.title("Páginas Dinámicas vs Estáticas")

    # Gráfico 6: Distribución por dominio (top 10)
    plt.subplot(2, 3, 6)
    domains = stats.get("domains", {})
    if domains:
        sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]
        domain_names = [
            d[0][:20] + "..." if len(d[0]) > 20 else d[0] for d in sorted_domains
        ]
        domain_counts = [d[1] for d in sorted_domains]
        plt.barh(range(len(domain_names)), domain_counts)
        plt.yticks(range(len(domain_names)), domain_names)
        plt.title("Top 10 Dominios")
        plt.xlabel("Número de páginas")

    plt.tight_layout()
    plt.savefig("pagerank_hits_analysis.png", dpi=300, bbox_inches="tight")
    plt.show()

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

    print("\nOverlap entre PageRank y Authorities:")
    for i, pct in enumerate(percentages):
        print(f"  Top {pct*100:.0f}%: {overlaps_pagerank_vs_authorities[i]:.1f}%")


if __name__ == "__main__":
    main()
