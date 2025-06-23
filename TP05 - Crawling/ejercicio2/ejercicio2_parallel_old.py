from lib.Crawler import Crawler
from pyvis.network import Network
import os

def main():
    # 20 primeros sitios de Netcraft (actualizado)
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
        "https://campus-1001.ammon.cloud",
        "https://github.com",
        "https://web.whatsapp.com",
        "https://duckduckgo.com",
        "https://www.reddit.com",
        "https://calendar.google.com"
    ]
    pkl_path = "ejercicio2_parallel_crawl.pkl"

    # Si ya existe el archivo, cargar el estado, si no, hacer crawling paralelo
    if os.path.exists(pkl_path):
        print("Cargando estado guardado...")
        crawler = Crawler.load_state(pkl_path)
    else:
        print("Iniciando crawling paralelo optimizado...")
        crawler = Crawler(max_depth=3, max_dir_depth=3, max_pages_per_site=20)
        
        # Usar crawling paralelo para URLs iniciales
        crawler.crawl_parallel_seeds(initial_urls, max_workers=8)
        
        crawler.save_state(pkl_path)
        print(f"Crawling finalizado y guardado en {pkl_path}. Nodos: {len(crawler.done_list)}")

    # Graficar directamente con pyvis desde done_list
    print("Generando grafo...")
    net = Network(notebook=False, directed=True, height="800px", width="100%")
    
    # Configurar visualización
    for node in crawler.done_list:
        # Color según tipo de página
        color = "#ff6b6b" if crawler.is_dynamic_page(node.url) else "#4ecdc4"
        size = 10 + (node.depth * 5)  # Tamaño según profundidad
        net.add_node(node.id, 
                    label=f"{node.id}",
                    title=f"URL: {node.url}\nProfundidad: {node.depth}\nTipo: {'Dinámico' if crawler.is_dynamic_page(node.url) else 'Estático'}",
                    color=color,
                    size=size)
        
        for out_id in node.outlinks:
            net.add_edge(node.id, out_id)
    
    # Optimizar layout para mejor rendimiento
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08)
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 150,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {"iterations": 150}
      }
    }
    """)
    
    net.show('grafo_crawling_optimized.html')
    
    # Mostrar estadísticas
    stats = crawler.get_statistics()
    print(f"\n=== ESTADÍSTICAS ===")
    print(f"Total de páginas: {stats['total_pages']}")
    print(f"Páginas dinámicas: {stats['dynamic_pages']} ({stats['dynamic_pages']/stats['total_pages']*100:.1f}%)")
    print(f"Páginas estáticas: {stats['static_pages']} ({stats['static_pages']/stats['total_pages']*100:.1f}%)")
    print(f"Dominios crawleados: {len(stats['domains'])}")
    print("Grafo generado: grafo_crawling_optimized.html")

if __name__ == "__main__":
    main()
