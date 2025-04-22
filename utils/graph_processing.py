import networkx as nx
import pandas as pd
from typing import List, Dict
import numbers
from numpy import mean

class GraphProcessor:

    def __init__(self, G:nx.Graph):
        self.G = G


    def get_simple(self, inplace=False):
        G_simple = nx.Graph()

        for u, v, data in self.G.edges(data=True):

            w = data.get('weight', -1)

            if G_simple.has_edge(u, v):
                if w > G_simple[u][v]['weight']:
                    G_simple[u][v].update(data)
            else:
                G_simple.add_edge(u, v, **data)

        if inplace: self.G = G_simple

        return G_simple


    def reduce_to_supergraph(self, inplace=False):
        partition = nx.community.louvain.best_partition(self.G)

        supergraph = nx.Graph()

        for u, v, data in self.G.edges(data=True):

            comm_u = partition[u]
            comm_v = partition[v]

            weight = data.get('weight', 1)

            if supergraph.has_edge(comm_u, comm_v):
                supergraph[comm_u][comm_v]['weight'] += weight
            else:
                supergraph.add_edge(comm_u, comm_v, weight=weight)

        for node, comm in partition.items():
            if supergraph.has_node(comm):
                if 'members' in supergraph.nodes[comm]:
                    supergraph.nodes[comm]['members'].append(node)
                else:
                    supergraph.nodes[comm]['members'] = [node]
            else:
                supergraph.add_node(comm, members=[node])

        if inplace: self.G = supergraph

        return supergraph


    def fill(self, cols:Dict, collection_values:Dict, k=0.5, inplace=False):

        G_copy = self.G if inplace else self.G.copy()

        edges = G_copy.edges(data=True)

        maxspeeds = []
        lanes = []

        for edge in edges:
            edge_attr = edge[2]

            if 'maxspeed' in edge_attr:

                if isinstance(edge_attr['maxspeed'], (list, tuple)):
                    speed_numeric = [int(s) for s in edge_attr['maxspeed']]
                    strategy = collection_values['maxspeed']

                    if strategy == 'max': edge_attr['maxspeed'] = max(speed_numeric)
                    elif strategy == 'min': edge_attr['maxspeed'] = min(speed_numeric)
                    else: edge_attr['maxspeed'] = mean(speed_numeric)

                elif isinstance(edge_attr['maxspeed'], str):
                    edge_attr['maxspeed'] = int(edge_attr['maxspeed'])

                maxspeeds.append(edge_attr['maxspeed'])


            if 'lanes' in edge_attr:

                if isinstance(edge_attr['lanes'], (list, tuple)):
                    lanes_numeric = [int(s) for s in edge_attr['lanes']]
                    strategy = collection_values['lanes']

                    if strategy == 'max': edge_attr['lanes'] = max(lanes_numeric)
                    elif strategy == 'min': edge_attr['lanes'] = min(lanes_numeric)
                    else: edge_attr['lanes'] = round(mean(lanes_numeric))

                elif isinstance(edge_attr['lanes'], str):
                    edge_attr['lanes'] = int(edge_attr['lanes'])

                lanes.append(edge_attr['lanes'])


        for edge in edges:
            edge_attr = edge[2]

            if 'maxspeed' not in edge_attr:
                strategy = cols['maxspeed']

                if isinstance(strategy, numbers.Number): edge_attr['maxspeed'] = strategy
                elif strategy == 'max': edge_attr['maxspeed'] = max(maxspeeds)
                elif strategy == 'min': edge_attr['maxspeed'] = min(maxspeeds)
                else: edge_attr['maxspeed'] = mean(maxspeeds)

            if 'lanes' not in edge_attr:
                strategy = cols['lanes']

                if isinstance(strategy, numbers.Number): edge_attr['lanes'] = strategy
                elif strategy == 'max': edge_attr['lanes'] = max(lanes)
                elif strategy == 'min': edge_attr['lanes'] = min(lanes)
                else: edge_attr['lanes'] = mean(lanes)

            speed_mps = edge_attr['maxspeed'] * 1000 / 3600
            drive_time = edge_attr['length'] / speed_mps
            drive_time_one_km = 1000 / speed_mps
            rate = 1 / (1 + k * (edge_attr['lanes'] - 1))

            edge_attr['driving_time'] = drive_time
            edge_attr['driving_time_one_km'] = drive_time_one_km
            edge_attr['weight'] = 1 / (drive_time_one_km * rate)

        return G_copy


    def to_dataframe(self, cols:List = None) -> pd.DataFrame:

        df = nx.to_pandas_edgelist(self.G, 'source', 'target')

        # nodes_df = pd.DataFrame.from_dict(dict(self.G.nodes(data=True)), orient='index')
        #
        # nodes_df = nodes_df[['x', 'y']]
        #
        # df = df.merge(nodes_df, left_on='source', right_index=True)
        # df.rename(columns={'x': 'source_x', 'y': 'source_y'}, inplace=True)
        #
        # df = df.merge(nodes_df, left_on='target', right_index=True)
        # df.rename(columns={'x': 'target_x', 'y': 'target_y'}, inplace=True)
        #
        # cols_to_retrieve = ['source_x', 'source_y', 'target_x', 'target_y']
        # cols_to_retrieve.extend(cols)

        if cols is not None: df = df.loc[:, cols]

        return df

    def to_filled_dataframe(self, cols:Dict, collection_values:Dict) -> pd.DataFrame:

        columns_to_retrieve = ['source', 'target', 'source_x', 'source_y']
        columns_to_retrieve.extend(cols.keys())

        df = self.to_dataframe(cols=columns_to_retrieve)

        for col, collection_strategy in collection_values.items():
            if collection_strategy == 'max':
                fun = lambda x: self.safe_aggregate(x, max)
            elif collection_strategy == 'min':
                fun = lambda x: self.safe_aggregate(x, min)
            elif collection_strategy == 'mean':
                fun = lambda x: self.safe_aggregate(x, mean)
            else:
                fun = lambda x: x
            df[col] = df[col].apply(fun)

        for col, fill_strategy in cols.items():
            if isinstance(fill_strategy, numbers.Real):
                df[col] = df[col].fillna(fill_strategy)
            elif fill_strategy == 'mean':
                df[col] = df[col].fillna(df[col].mean())
            elif fill_strategy == 'median':
                df[col] = df[col].fillna(df[col].median())
            elif fill_strategy == 'max':
                df[col] = df[col].fillna(df[col].max())
            elif fill_strategy == 'min':
                df[col] = df[col].fillna(df[col].min())

        return df

    def safe_aggregate(self, x, fun, result_type=int):
        if isinstance(x, (list, tuple)):
            try:
                numeric_values = [result_type(i) for i in x]
                return fun(numeric_values)
            except Exception as e:
                print("Aggregation Error:", e)
                return x
        else:
            return x



def get_weights(edges: pd.DataFrame) -> pd.DataFrame:
    def get_weight(length, speed, number_of_lanes, k=0.5):
        speed_mps = speed * 1000 / 3600
        drive_time = length / speed_mps
        rate = 1 / (1 + k * (number_of_lanes - 1))
        weight = drive_time * rate
        return weight

    edges['weight'] = edges.apply(
        lambda row: get_weight(
            row['length'],
            row['maxspeed'],
            row['lanes']
        ),
        axis=1
    )

    return edges


def create_multidigraph_from_df(df: pd.DataFrame) -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()

    nodes_attr = {}

    for _, row in df.iterrows():
        src = row['source']
        if src not in nodes_attr:
            nodes_attr[src] = {'x': row['source_x'], 'y': row['source_y']}

        trg = row['target']
        if trg not in nodes_attr:
            nodes_attr[trg] = {'x': row['target_x'], 'y': row['target_y']}

    for node, attr in nodes_attr.items():
        G.add_node(node, **attr)

    for _, row in df.iterrows():
        G.add_edge(
            row['source'],
            row['target'],
            maxspeed=row['maxspeed'],
            lanes=row['lanes'],
            lenght=row['length'],
            weight=row['weight']
        )

    return G