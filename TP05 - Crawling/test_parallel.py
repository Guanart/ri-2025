from lib.CrawlerParallel import CrawlerParallel
from pyvis.network import Network
import os
import time


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
        )

        # Ejecutar crawling
        # crawler.crawl(initial_urls)

        end_time = time.time()
        elapsed = end_time - start_time

        # Guardar estado
        # crawler.save_state(pkl_path)

        print(f"\n=== CRAWLING COMPLETADO ===")
        print(f"Tiempo total: {elapsed:.1f} segundos")
        print(f"Páginas procesadas: {crawler.total_processed}")
        print(f"Velocidad: {crawler.total_processed/elapsed:.1f} páginas/segundo")
        print(f"Estado guardado en: {pkl_path}")

    # Mostrar estadísticas
    stats = crawler.get_statistics()
    print(f"\n=== ESTADÍSTICAS FINALES ===")
    print(f"Total de páginas: {stats['total_pages']}")
    print(
        f"Páginas dinámicas: {stats['dynamic_pages']} ({stats['dynamic_pages']/stats['total_pages']*100:.1f}%)"
    )
    print(
        f"Páginas estáticas: {stats['static_pages']} ({stats['static_pages']/stats['total_pages']*100:.1f}%)"
    )
    print(f"Páginas fallidas: {stats['failed_pages']}")
    print(f"Dominios únicos: {len(stats['domains'])}")

    print(f"\nDistribución por profundidad lógica:")
    for depth, count in sorted(stats["depth_distribution"].items()):
        print(f"  Nivel {depth}: {count} páginas")

    print(f"\nTop 10 dominios por páginas:")
    sorted_domains = sorted(stats["domains"].items(), key=lambda x: x[1], reverse=True)
    for domain, count in sorted_domains[:10]:
        print(f"  {domain}: {count} páginas")

    # Generar grafo con diferentes estrategias según tamaño
    num_nodes = len(crawler.done_list)
    print(f"\nGenerando visualización para {num_nodes} nodos...")
    print(num_nodes)
    if num_nodes <= 6000:
        # Grafo completo para tamaños manejables
        print("Generando grafo completo...")
        net = Network(notebook=False, directed=True, height="900px", width="100%")

        # Configuración optimizada para grafos grandes
        if num_nodes > 1000:
            # Nodos más pequeños y menos información para grafos grandes
            node_size_base = 5
            show_labels = False
            physics_iterations = 50
        else:
            node_size_base = 8
            show_labels = True
            physics_iterations = 100

        # Agregar nodos
        for task in crawler.done_list:
            color = "#ff6b6b" if crawler.is_dynamic_page(task.url) else "#4ecdc4"
            size = node_size_base + (task.depth * 2)
            label = str(task.id) if show_labels else ""

            net.add_node(
                task.id,
                label=label,
                title=f"ID: {task.id}\nURL: {task.url}\nProfundidad: {task.depth}\nEnlaces: {len(task.outlinks)}\nTipo: {'Dinámico' if crawler.is_dynamic_page(task.url) else 'Estático'}",
                color=color,
                size=size,
            )

        # Agregar aristas
        edge_count = 0
        for task in crawler.done_list:
            for out_id in task.outlinks:
                if out_id < len(crawler.done_list):
                    net.add_edge(task.id, out_id)
                    edge_count += 1

        print(f"Nodos: {num_nodes}, Aristas: {edge_count}")

        # Configuración optimizada según tamaño
        net.set_options(
            f"""
        var options = {{
          "physics": {{
            "enabled": true,
            "forceAtlas2Based": {{
              "gravitationalConstant": {-50 if num_nodes > 1000 else -100},
              "centralGravity": {0.001 if num_nodes > 1000 else 0.005},
              "springLength": {200 if num_nodes > 1000 else 150},
              "springConstant": {0.02 if num_nodes > 1000 else 0.05}
            }},
            "maxVelocity": {50 if num_nodes > 1000 else 100},
            "solver": "forceAtlas2Based",
            "timestep": 0.4,
            "stabilization": {{"iterations": {physics_iterations}}}
          }},
          "nodes": {{
            "font": {{"size": {6 if num_nodes > 1000 else 8}}}
          }},
          "edges": {{
            "arrows": {{"to": {{"enabled": true, "scaleFactor": 0.3}}}},
            "width": {0.5 if num_nodes > 1000 else 1}
          }},
          "interaction": {{
            "hideEdgesOnDrag": {str(num_nodes > 1000).lower()},
            "hideNodesOnDrag": {str(num_nodes > 1000).lower()}
          }}
        }}
        """
        )

        net.show("crawler_parallel_graph.html")
        print("Grafo completo generado: crawler_parallel_graph.html")

    else:
        # Para grafos muy grandes, generar una muestra representativa
        print(
            f"Grafo demasiado grande ({num_nodes} nodos). Generando muestra de 2000 nodos más importantes..."
        )

        # Seleccionar nodos más importantes (con más enlaces)
        tasks_by_importance = sorted(
            crawler.done_list, key=lambda t: len(t.outlinks), reverse=True
        )
        sample_tasks = tasks_by_importance[:2000]

        # Crear mapeo de IDs originales a nuevos
        id_mapping = {task.id: i for i, task in enumerate(sample_tasks)}

        net = Network(notebook=False, directed=True, height="900px", width="100%")

        # Agregar nodos de la muestra
        for i, task in enumerate(sample_tasks):
            color = "#ff6b6b" if crawler.is_dynamic_page(task.url) else "#4ecdc4"
            size = 8 + (len(task.outlinks) // 2)  # Tamaño por importancia

            net.add_node(
                i,
                label=str(i),
                title=f"ID Original: {task.id}\nURL: {task.url}\nProfundidad: {task.depth}\nEnlaces: {len(task.outlinks)}\nTipo: {'Dinámico' if crawler.is_dynamic_page(task.url) else 'Estático'}",
                color=color,
                size=size,
            )

        # Agregar aristas entre nodos de la muestra
        for i, task in enumerate(sample_tasks):
            for out_id in task.outlinks:
                if out_id in id_mapping:
                    net.add_edge(i, id_mapping[out_id])

        net.set_options(
            """
        var options = {
          "physics": {
            "enabled": true,
            "forceAtlas2Based": {
              "gravitationalConstant": -80,
              "centralGravity": 0.003,
              "springLength": 120,
              "springConstant": 0.04
            },
            "maxVelocity": 80,
            "solver": "forceAtlas2Based",
            "timestep": 0.4,
            "stabilization": {"iterations": 80}
          }
        }
        """
        )

        net.show("crawler_parallel_sample.html")
        print("Muestra representativa generada: crawler_parallel_sample.html")


if __name__ == "__main__":
    main()
