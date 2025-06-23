from lib.Crawler import Crawler
from pyvis.network import Network
import os
import time
import plotly.graph_objects as go
import networkx as nx


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
            text=f"Grafo de Crawling SECUENCIAL - {len(G.nodes())} páginas, {len(G.edges())} enlaces",
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

    pkl_path = "crawler_sequential_test.pkl"

    # Si ya existe el archivo, cargar el estado, si no, hacer crawling
    if os.path.exists(pkl_path):
        print("Cargando estado guardado...")
        crawler = Crawler.load_state(pkl_path)
        print(f"Estado cargado: {len(crawler.done_list)} páginas")
    else:
        print("=== INICIANDO CRAWLING SECUENCIAL ===")
        start_time = time.time()

        # Configuración para crawling secuencial
        crawler = Crawler(
            max_depth=2,  # Profundidad moderada
            max_dir_depth=3,  # Permitir más profundidad física
            max_pages_per_site=20,  # Más páginas por sitio
            max_total_pages=1000,  # Límite total de páginas
        )

        # Ejecutar crawling
        crawler.crawl(initial_urls)

        end_time = time.time()
        elapsed = end_time - start_time

        # Guardar estado
        crawler.save_state(pkl_path)

        print("=== CRAWLING COMPLETADO ===")
        print(f"Tiempo total: {elapsed:.2f} segundos")
        print(f"Velocidad: {len(crawler.done_list)/elapsed:.2f} páginas/segundo")

    # Mostrar estadísticas
    stats = crawler.get_statistics()
    print("=== ESTADÍSTICAS FINALES ===")
    print(f"Total de páginas: {stats.get('total_pages', 0)}")
    
    if stats.get('total_pages', 0) > 0:
        print(f"Páginas dinámicas: {stats.get('dynamic_pages', 0)} ({stats.get('dynamic_pages', 0)/stats.get('total_pages', 1)*100:.1f}%)")
        print(f"Páginas estáticas: {stats.get('static_pages', 0)} ({stats.get('static_pages', 0)/stats.get('total_pages', 1)*100:.1f}%)")
    else:
        print("Páginas dinámicas: 0 (0.0%)")
        print("Páginas estáticas: 0 (0.0%)")
    
    print(f"Páginas fallidas: {stats.get('failed_pages', 0)}")
    print(f"Dominios únicos: {len(stats.get('domains', {}))}")

    print("Distribución por profundidad lógica:")
    depth_dist = stats.get("depth_distribution", {})
    if depth_dist:
        for depth in sorted(depth_dist.keys()):
            count = depth_dist[depth]
            print(f"  Nivel {depth}: {count} páginas")
    else:
        print("  No hay datos de distribución por profundidad")

    print("Top 10 dominios por páginas:")
    domains = stats.get("domains", {})
    if domains:
        sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
        for domain, count in sorted_domains[:10]:
            print(f"  {domain}: {count} páginas")
    else:
        print("  No hay datos de dominios")

    # NUEVA: Generar visualización rápida con Plotly
    print("\n=== GENERANDO VISUALIZACIÓN PLOTLY (RÁPIDA) ===")
    try:
        nodes_plotly, edges_plotly = visualize_with_plotly(crawler, "crawler_sequential_fast.html", max_nodes=1500)
        print("✅ Visualización Plotly completada: crawler_sequential_fast.html")
        print(f"   Nodos: {nodes_plotly}, Aristas: {edges_plotly}")
    except Exception as e:
        print(f"❌ Error en visualización Plotly: {e}")

    # Generar grafo con pyvis - enfoque simple
    num_nodes = len(crawler.done_list)
    print("\n=== GENERANDO VISUALIZACIÓN PYVIS (COMPLETA) ===")
    print(f"Generando visualización para {num_nodes} nodos...")

    # Limitar a máximo 2000 nodos para pyvis
    if num_nodes > 2000:
        print(f"Demasiados nodos ({num_nodes}), limitando a 2000...")
        tasks_to_show = crawler.done_list[:2000]
        # Mapear IDs originales a nuevos
        id_mapping = {task.id: i for i, task in enumerate(tasks_to_show)}
    else:
        tasks_to_show = crawler.done_list
        id_mapping = {task.id: task.id for task in tasks_to_show if task.id is not None}

    net = Network(notebook=False, directed=True, height="900px", width="100%")

    # Agregar nodos
    nodes_added = 0
    for i, task in enumerate(tasks_to_show):
        if task.id is not None:
            source_id = id_mapping.get(task.id, i)
            color = "#ff6b6b" if crawler.is_dynamic_page(task.url) else "#4ecdc4"
            size = 8 + (len(task.outlinks) // 3)  # Tamaño por número de enlaces

            net.add_node(
                source_id,
                label=str(source_id),
                title=f"ID: {task.id}\\nURL: {task.url}\\nProfundidad: {task.depth}\\nEnlaces: {len(task.outlinks)}\\nTipo: {'Dinámico' if crawler.is_dynamic_page(task.url) else 'Estático'}",
                color=color,
                size=size,
            )
            nodes_added += 1

    print(f"Nodos agregados: {nodes_added} de {len(tasks_to_show)} nodos")

    # Agregar aristas
    edges_added = 0
    edges_skipped = 0
    for task in tasks_to_show:
        if task.id is not None and task.id in id_mapping:
            source_id = id_mapping[task.id]
            for out_id in task.outlinks:
                if out_id in id_mapping:
                    target_id = id_mapping[out_id]
                    net.add_edge(source_id, target_id)
                    edges_added += 1
                else:
                    edges_skipped += 1

    print(f"Nodos: {nodes_added}, Aristas: {edges_added}, Aristas omitidas: {edges_skipped}")

    # Guardar archivo
    net.write_html("crawler_sequential_graph.html")
    print("Grafo generado: crawler_sequential_graph.html")


if __name__ == "__main__":
    main()
