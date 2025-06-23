from lib.CrawlerParallel import CrawlerParallel
from pyvis.network import Network
import os
import time
import plotly.graph_objects as go
import networkx as nx


def main():
    # 20 primeros sitios de Netcraft
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
        "https://calendar.google.com",
    ]

    pkl_path = "crawler_parallel_test.pkl"

    # Si ya existe el archivo, cargar el estado, si no, hacer crawling
    if os.path.exists(pkl_path):
        print("Cargando estado guardado...")
        crawler = CrawlerParallel.load_state(pkl_path)
        print(f"Estado cargado: {len(crawler.done_list)} páginas")
    else:
        print("=== INICIANDO CRAWLING PARALELO MASIVO ===")
        start_time = time.time()

        # Configuración agresiva para máxima velocidad
        crawler = CrawlerParallel(
            max_depth=2,  # Profundidad moderada
            max_dir_depth=3,  # Permitir más profundidad física
            max_pages_per_site=20,  # Más páginas por sitio
            max_workers=12,  # Muchos workers concurrentes
            max_total_pages=1000,  # Límite total de páginas
            preserve_query=False,
        )

        # Ejecutar crawling
        crawler.crawl(initial_urls)

        end_time = time.time()
        elapsed = end_time - start_time

        # Guardar estado
        crawler.save_state(pkl_path)

        print(f"\n=== CRAWLING COMPLETADO ===")
        print(f"Tiempo total: {elapsed:.1f} segundos")
        print(f"Páginas procesadas: {crawler.total_processed}")
        print(f"Velocidad: {crawler.total_processed / elapsed:.1f} páginas/segundo")
        print(f"Estado guardado en: {pkl_path}")

    # Mostrar estadísticas
    stats = crawler.get_statistics()
    print(f"\n=== ESTADÍSTICAS FINALES ===")
    print(f"Total de páginas: {stats['total_pages']}")
    print(
        f"Páginas dinámicas: {stats['dynamic_pages']} ({stats['dynamic_pages'] / stats['total_pages'] * 100:.1f}%)"
    )
    print(
        f"Páginas estáticas: {stats['static_pages']} ({stats['static_pages'] / stats['total_pages'] * 100:.1f}%)"
    )
    print(f"Páginas fallidas: {stats.get('failed_pages', 'N/A')}")  # Usar get() para compatibilidad
    print(f"Dominios únicos: {len(stats['domains'])}")

    print(f"\nDistribución por profundidad lógica:")
    for depth, count in sorted(stats["depth_distribution"].items()):
        print(f"  Nivel {depth}: {count} páginas")

    print(f"\nTop 10 dominios por páginas:")
    sorted_domains = sorted(stats["domains"].items(), key=lambda x: x[1], reverse=True)
    for domain, count in sorted_domains[:10]:
        print(f"  {domain}: {count} páginas")

    # NUEVA: Generar visualización rápida con Plotly
    print("\n=== GENERANDO VISUALIZACIÓN PLOTLY (RÁPIDA) ===")
    try:
        nodes_plotly, edges_plotly = visualize_with_plotly(crawler, "crawler_plotly_fast.html", max_nodes=1500)
        print(f"✅ Visualización Plotly completada: crawler_plotly_fast.html")
        print(f"   Nodos: {nodes_plotly}, Aristas: {edges_plotly}")
    except Exception as e:
        print(f"❌ Error en visualización Plotly: {e}")

    # Generar grafo con pyvis - enfoque simple
    num_nodes = len(crawler.done_list)
    print(f"\n=== GENERANDO VISUALIZACIÓN PYVIS (COMPLETA) ===")
    print(f"Generando visualización para {num_nodes} nodos...")

    # Limitar a máximo 2000 nodos para pyvis
    if num_nodes > 2000:
        print(f"Demasiados nodos ({num_nodes}), limitando a 2000...")
        tasks_to_show = crawler.done_list[:2000]
        # Mapear IDs originales a nuevos
        id_mapping = {task.id: i for i, task in enumerate(tasks_to_show)}
    else:
        tasks_to_show = crawler.done_list
        id_mapping = {task.id: task.id for task in tasks_to_show}

    # Crear red pyvis
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color=True, directed=True)
    net.repulsion()

    # Agregar nodos
    for i, task in enumerate(tasks_to_show):
        new_id = i if num_nodes > 2000 else task.id
        is_dynamic = '?' in task.url
        is_seed = task.depth == 0
        
        if is_seed:
            color = "red"
        elif is_dynamic:
            color = "deepskyblue" 
        else:
            color = "yellow"
            
        net.add_node(
            new_id,
            label=f"{new_id}",
            title=f"URL: {task.url}\nProfundidad: {task.depth}",
            color=color
        )

    # Agregar aristas
    for i, task in enumerate(tasks_to_show):
        source_id = i if num_nodes > 2000 else task.id
        for out_id in task.outlinks:
            if out_id in id_mapping:
                target_id = id_mapping[out_id]
                net.add_edge(source_id, target_id)

    # Guardar archivo
    net.write_html("crawler_parallel_graph.html")
    print("Grafo generado: crawler_parallel_graph.html")


def visualize_with_plotly(crawler, filename="crawler_plotly_graph.html", max_nodes=1000):
    """
    Genera una visualización interactiva eficiente usando Plotly y NetworkX.
    Mucho más rápida que pyvis para grafos grandes.
    """
    print(f"Generando visualización con Plotly para {len(crawler.done_list)} nodos...")
    
    # Crear grafo NetworkX
    G = nx.DiGraph()
    
    # Filtrar y seleccionar nodos válidos
    valid_tasks = [task for task in crawler.done_list if task.id is not None]
    
    # Si hay demasiados nodos, tomar una muestra de los más importantes
    if len(valid_tasks) > max_nodes:
        print(f"Demasiados nodos ({len(valid_tasks)}), tomando muestra de los {max_nodes} más conectados...")
        valid_tasks = sorted(valid_tasks, key=lambda t: len(t.outlinks), reverse=True)[:max_nodes]
    
    # Crear mapeo de IDs
    id_to_index = {task.id: i for i, task in enumerate(valid_tasks)}
    
    # Agregar nodos al grafo
    for i, task in enumerate(valid_tasks):
        is_dynamic = crawler.is_dynamic_page(task.url)
        color = 'red' if is_dynamic else 'lightblue'
        G.add_node(i, 
                  url=task.url, 
                  domain=task.url.split('/')[2] if '://' in task.url else task.url,
                  depth=task.depth,
                  is_dynamic=is_dynamic,
                  outlinks_count=len(task.outlinks),
                  color=color)
    
    # Agregar aristas
    edges_added = 0
    for i, task in enumerate(valid_tasks):
        for out_id in task.outlinks:
            if out_id in id_to_index:
                target_idx = id_to_index[out_id]
                G.add_edge(i, target_idx)
                edges_added += 1
    
    print(f"Grafo creado: {len(G.nodes())} nodos, {len(G.edges())} aristas")
    
    # Calcular layout usando algoritmo eficiente
    print("Calculando layout del grafo...")
    if len(G.nodes()) > 500:
        # Para grafos grandes, usar layout más rápido
        pos = nx.spring_layout(G, k=1.5, iterations=30, seed=42)
    else:
        # Para grafos pequeños, usar layout de mejor calidad
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Preparar datos para Plotly
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Datos de nodos
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    node_colors = [G.nodes[node]['color'] for node in G.nodes()]
    node_sizes = [min(15, 8 + G.nodes[node]['outlinks_count'] // 3) for node in G.nodes()]
    
    # Crear texto de hover
    hover_text = []
    for node in G.nodes():
        data = G.nodes[node]
        text = f"<b>Dominio:</b> {data['domain']}<br>"
        text += f"<b>Profundidad:</b> {data['depth']}<br>"
        text += f"<b>Enlaces:</b> {data['outlinks_count']}<br>"
        text += f"<b>Tipo:</b> {'Dinámico' if data['is_dynamic'] else 'Estático'}<br>"
        text += f"<b>URL:</b> {data['url'][:80]}{'...' if len(data['url']) > 80 else ''}"
        hover_text.append(text)
    
    # Crear figura de Plotly
    fig = go.Figure()
    
    # Agregar aristas
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        showlegend=False,
        name='Enlaces'
    ))
    
    # Agregar nodos
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=1, color='white'),
            opacity=0.8
        ),
        text=hover_text,
        hoverinfo='text',
        showlegend=False,
        name='Páginas'
    ))
    
    # Configurar layout
    fig.update_layout(
        title=dict(
            text=f"Grafo de Crawling PARALELO - {len(G.nodes())} páginas, {len(G.edges())} enlaces",
            font=dict(size=16)
        ),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[
            dict(
                text="Azul: Páginas estáticas | Rojo: Páginas dinámicas<br>Tamaño: Número de enlaces salientes",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002, xanchor='left', yanchor='bottom',
                font=dict(size=12, color='#666')
            )
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        width=1200,
        height=800
    )
    
    # Guardar archivo HTML
    fig.write_html(filename, include_plotlyjs='cdn')
    print(f"Visualización Plotly guardada: {filename}")
    
    return len(G.nodes()), len(G.edges())


if __name__ == "__main__":
    main()
