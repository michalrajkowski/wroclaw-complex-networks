import osmnx as ox
G = ox.graph_from_place('Wrocław, Poland', network_type='drive')
ox.plot_graph(G)
plt.show()