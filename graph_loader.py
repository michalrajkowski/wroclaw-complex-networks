import osmnx as ox
import os

GRAPHS_FOLDER = "graphs/"

def generate_graph(place_name, filename):
    G = ox.graph_from_place(place_name, network_type='drive')
    ox.save_graphml(G, filepath=filename)

def save_graph(graph,filename):
    path = os.path.join(GRAPHS_FOLDER, filename)
    ox.save_graphml(graph, filepath=path)

def get_graph(place_name, filename):
    path = os.path.join(GRAPHS_FOLDER, filename)
    if os.path.exists(path):
        print(f"Loading graph from {path}")
        G = ox.load_graphml(path)
    else:
        print(f"Graph not found!")
        G = None
    return G