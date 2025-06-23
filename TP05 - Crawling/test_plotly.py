import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.Crawler import Crawler
import plotly.graph_objects as go
import networkx as nx

def test_visualization():
    """Test rápido de la visualización de Plotly"""
    print("Probando visualización de Plotly...")
    
    # Crear un grafo simple de prueba
    G = nx.DiGraph()
    G.add_node(0, url="https://test1.com", depth=0, is_dynamic=False)
    G.add_node(1, url="https://test2.com", depth=1, is_dynamic=True)
    G.add_edge(0, 1)
    
    # Layout simple
    pos = nx.spring_layout(G, seed=42)
    
    # Datos para Plotly
    edge_x = [pos[0][0], pos[1][0], None]
    edge_y = [pos[0][1], pos[1][1], None]
    node_x = [pos[0][0], pos[1][0]]
    node_y = [pos[0][1], pos[1][1]]
    node_colors = ['lightblue', 'red']
    
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
                            text=["Test 1", "Test 2"],
                            marker=dict(size=8,
                                       color=node_colors,
                                       line=dict(width=2))))
    
    # Layout con sintaxis corregida
    fig.update_layout(title=dict(text='Test Grafo - 2 nodos, 1 arista',
                                font=dict(size=16)),
                     showlegend=False,
                     hovermode='closest',
                     margin=dict(b=20,l=5,r=5,t=40),
                     xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                     yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    
    # Guardar archivo de prueba
    fig.write_html("test_plotly.html")
    print("✅ Test de visualización exitoso: test_plotly.html creado")

if __name__ == "__main__":
    test_visualization()
