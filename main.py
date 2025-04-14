from graph_loader import get_graph, save_graph, generate_graph

import matplotlib.pyplot as plt
import osmnx as ox

# G = generate_graph("Wrocław, Poland", "wroclaw.graphml")
G = get_graph("Wrocław, Poland", "wroclaw.graphml")
ox.plot_graph(G)
plt.show()