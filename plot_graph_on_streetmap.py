import osmnx as ox
import matplotlib.pyplot as plt
import contextily as ctx


G = ox.graph_from_place('Wrocław, Poland', network_type='drive')

m = ox.plot_graph_folium(G, popup_attribute='name', weight=2, color='blue')

m.save('wroclaw_map.html')