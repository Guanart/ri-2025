import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.Crawler import Crawler
from lib.CrawlerParallel import CrawlerParallel
import time
import plotly.graph_objects as go
import networkx as nx


def create_simple_visualization(crawler, filename="crawler_graph.html"):
    """Genera una visualización simple con Plotly"""
    print(f"Generando visualización para {len(crawler.done_list)} nodos...")
    
    # Crear grafo NetworkX
    G = nx.DiGraph()
    
    # Usar todos los nodos - sin limitaciones
    tasks_to_show = crawler.done_list
    
    # Agregar nodos
    for i, task in enumerate(tasks_to_show):
        if task.id is not None:
            G.add_node(i, 
                      url=task.url,
                      depth=task.depth,
                      is_dynamic=crawler.is_dynamic_page(task.url))
    
    # Agregar aristas
    id_to_index = {task.id: i for i, task in enumerate(tasks_to_show) if task.id is not None}
    edges_added = 0
    
    for i, task in enumerate(tasks_to_show):
        if task.id is not None:
            for out_id in task.outlinks:
                if out_id in id_to_index:
                    target_idx = id_to_index[out_id]
                    G.add_edge(i, target_idx)
                    edges_added += 1
    
    # Layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Preparar datos para Plotly
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    node_colors = ['red' if G.nodes[node]['is_dynamic'] else 'lightblue' for node in G.nodes()]
    
    # Crear figura
    fig = go.Figure()
    
    # Aristas
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y,
                            line=dict(width=0.5, color='#888'),
                            hoverinfo='none',
                            mode='lines'))
    
    # Nodos
    fig.add_trace(go.Scatter(x=node_x, y=node_y,
                            mode='markers',
                            hoverinfo='text',
                            text=[f"ID: {i}<br>Profundidad: {G.nodes[i]['depth']}<br>URL: {G.nodes[i]['url'][:50]}..." 
                                  for i in G.nodes()],
                            marker=dict(size=8,
                                       color=node_colors,
                                       line=dict(width=2))))
    
    fig.update_layout(title=dict(text=f'Grafo del Crawler - {len(G.nodes())} nodos, {edges_added} aristas',
                                font=dict(size=16)),
                     showlegend=False,
                     hovermode='closest',
                     margin=dict(b=20,l=5,r=5,t=40),
                     annotations=[ dict(
                         text="Rojo: páginas dinámicas | Azul: páginas estáticas",
                         showarrow=False,
                         xref="paper", yref="paper",
                         x=0.005, y=-0.002 ) ],
                     xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                     yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    
    fig.write_html(filename)
    return len(G.nodes()), edges_added


def main():
    # Elegir tipo de crawler
    use_parallel = input("¿Usar crawler paralelo? (s/N): ").lower().strip() == 's'
    
    # Si es paralelo, configurar workers
    if use_parallel:
        while True:
            try:
                max_workers = int(input("¿Cuántos workers paralelos? (2-12): "))
                if 2 <= max_workers <= 12:
                    break
                else:
                    print("Por favor ingresa un número entre 2 y 12")
            except ValueError:
                print("Por favor ingresa un número válido")
    else:
        max_workers = 1  # No se usa en crawler secuencial, pero se define
    
    # Elegir si preservar query strings
    preserve_query = input("\n¿Preservar query strings en las URLs? (s/N): ").lower().strip() == 's'
    
    # Elegir cantidad de páginas
    while True:
        try:
            max_pages = int(input("Ingresa número de páginas (recomendado de 10 a 2000): "))
            if 10 <= max_pages <= 10000:
                break
            else:
                print("Por favor ingresa un número entre 10 y 10000")
        except ValueError:
            print("Por favor ingresa un número válido")
    
    # Elegir páginas por sitio
    while True:
        try:
            pages_per_site = int(input("\n¿Cuántas páginas máximo por sitio/dominio? (20-50): "))
            if 20 <= pages_per_site <= 50:
                break
            else:
                print("Por favor ingresa un número entre 20 y 50")
        except ValueError:
            print("Por favor ingresa un número válido")
    
    # URLs semilla (top 20 Netcraft) - https://trends.netcraft.com/topsites
    initial_urls = [
        "https://www.google.com", "https://www.youtube.com", "https://mail.google.com",
        "https://outlook.office.com", "https://www.facebook.com", "https://docs.google.com",
        "https://chatgpt.com", "https://login.microsoftonline.com", "https://www.linkedin.com",
        "https://accounts.google.com", "https://x.com", "https://www.bing.com",
        "https://www.instagram.com", "https://drive.google.com", "https://campus-1001.ammon.cloud",
        "https://github.com", "https://web.whatsapp.com", "https://duckduckgo.com",
        "https://www.reddit.com", "https://calendar.google.com"
    ]

    # Configurar archivos con nombres que incluyan la cantidad de páginas y preserve_query
    pkl_suffix = "parallel" if use_parallel else "sequential"
    query_suffix = "query" if preserve_query else "noquery"
    pkl_path = f"ejercicio2_{pkl_suffix}_{max_pages}p_{query_suffix}.pkl"
    html_filename = f"ejercicio2_{pkl_suffix}_{max_pages}p_{query_suffix}_graph.html"

    # Cargar estado existente o hacer crawling
    if os.path.exists(pkl_path):
        print(f"Cargando estado guardado desde {pkl_path}...")
        if use_parallel:
            crawler = CrawlerParallel.load_state(pkl_path)
        else:
            crawler = Crawler.load_state(pkl_path)
        print(f"Estado cargado: {len(crawler.done_list)} páginas")
    else:
        print(f"=== INICIANDO CRAWLING {'PARALELO' if use_parallel else 'SECUENCIAL'} ===")
        print(f"Objetivo: {max_pages} páginas")
        print(f"Páginas por sitio: {pages_per_site}")
        print(f"Preservar query strings: {preserve_query}")
        if use_parallel:
            print(f"Workers paralelos: {max_workers}")
        start_time = time.time()

        # Configuración del crawler con parámetros configurables
        if use_parallel:
            crawler = CrawlerParallel(
                max_depth=3,
                max_dir_depth=3,
                max_pages_per_site=pages_per_site,
                max_total_pages=max_pages,
                max_workers=max_workers,
                preserve_query=preserve_query
            )
        else:
            crawler = Crawler(
                max_depth=3,
                max_dir_depth=3,
                max_pages_per_site=pages_per_site,
                max_total_pages=max_pages,
                preserve_query=preserve_query
            )

        # Ejecutar crawling
        crawler.crawl(initial_urls)
        
        # Guardar estado
        crawler.save_state(pkl_path)
        
        elapsed_time = time.time() - start_time
        print(f"Crawling completado en {elapsed_time:.2f} segundos")
        print(f"Estado guardado en: {pkl_path}")

    # Mostrar estadísticas básicas
    stats = crawler.get_statistics()
    print("\n=== ESTADÍSTICAS ===")
    print(f"Total de páginas: {stats.get('total_pages', 0)}")
    print(f"Páginas dinámicas: {stats.get('dynamic_pages', 0)}")
    print(f"Páginas estáticas: {stats.get('static_pages', 0)}")
    print(f"Páginas fallidas: {stats.get('failed_pages', 0)}")
    print(f"Dominios únicos: {len(stats.get('domains', {}))}")

    # Distribución por profundidad
    depth_dist = stats.get('depth_distribution', {})
    if depth_dist:
        print("\nDistribución por profundidad:")
        for depth in sorted(depth_dist.keys()):
            print(f"  Nivel {depth}: {depth_dist[depth]} páginas")

    # Top dominios
    domains = stats.get('domains', {})
    if domains:
        print("\nTop 5 dominios:")
        sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
        for domain, count in sorted_domains[:5]:
            print(f"  {domain}: {count} páginas")

    # Generar visualización
    print("\n=== GENERANDO VISUALIZACIÓN ===")
    try:
        nodes, edges = create_simple_visualization(crawler, html_filename)
        print(f"✅ Visualización guardada: {html_filename}")
        print(f"   Nodos: {nodes}, Aristas: {edges}")
    except Exception as e:
        print(f"❌ Error en visualización: {e}")

    print("\n✅ Ejercicio 2 completado")
    print("Archivos generados:")
    print(f"  - Estado: {pkl_path}")
    print(f"  - Visualización: {html_filename}")


if __name__ == "__main__":
    main()
