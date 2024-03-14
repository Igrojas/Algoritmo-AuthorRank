import networkx as nx
import pandas as pd
import json

def create_graph(data, min_articulos_autor, min_articulos_coautor):
    G = nx.Graph()
    for autor_id, autor_datos in data.items():
        if autor_datos['n_articulos'] >= min_articulos_autor:
            G.add_node(autor_id)
            for coautor_id, n in autor_datos['coautores'].items():
                if n >= min_articulos_coautor:
                    G.add_edge(autor_id, coautor_id)
    return G

class AuthorRank:
    def __init__(self, data_autores, data_papers, min_articulos_autor, min_articulos_coautor):
        G = create_graph(data_autores, min_articulos_autor, min_articulos_coautor)
        self.lengthG = G.number_of_nodes()
        self.authorrank_dict = self.CalculateRank(G, data_papers)
        self.df = self.to_dataframe(data_autores)

    def GrandesProductores(self, G_autor, top_n=None):
        NodeArt = [(data_autores[node]['nombre_autor'], data_autores[node]['n_articulos']) for node in G_autor.nodes()]
        NodeArt_ordenada = sorted(NodeArt, key=lambda x: x[1], reverse=True)
        return NodeArt_ordenada[:top_n] if top_n else NodeArt_ordenada

    def WeigthG(self, G, data_papers):
        lista_paper = set()
        for node, node_data in data_autores.items():
            lista_paper.update(node_data["articulos"])

        exclusividad = {}
        for paper in lista_paper:
            if len(data_papers[paper]) > 1:
                pares = [(str(a), str(b)) for a in data_papers[paper] for b in data_papers[paper] if a != b]
                pares_en_g = set(pares) & set(G.edges())
                exclusividad[paper] = {"pares": pares_en_g, "score": 1 / (len(data_papers[paper]) - 1)}

        deleted_paper = [paper for paper, data in exclusividad.items() if not data]
        for paper in deleted_paper:
            del exclusividad[paper]

        peso_c = {}
        for edge in G.edges():
            suma = sum(data["score"] for paper, data in exclusividad.items() if edge in data["pares"])
            peso_c[edge] = peso_c[(edge[1], edge[0])] = suma

        peso_w = {edge: peso_c[edge] / sum(peso_c[e] for e in G.edges(node)) for node in G for edge in G.edges(node)}

        return peso_w

    def CalculateRank(self, G, data_papers, damping=0.85, max_iter=1000):
        peso_w = self.WeigthG(G, data_papers)
        largo = G.number_of_nodes()
        authorrank = {node: (1 / largo) for node in G.nodes()}
        iterr = 0
        while iterr < max_iter:
            iterr += 1
            for node_i in G.nodes():
                suma = 0
                for nodo_j in G.edges(node_i):
                    suma += authorrank[nodo_j[1]] * peso_w[(nodo_j[1], node_i)]
                authorrank[node_i] = (1 - damping) / largo + damping * suma
        return authorrank

    def to_dataframe(self, data_autores):
        data = [{'Nodo': node, 'Nombre': data_autores[node]['nombre_autor'], 'Rank': rank} for node, rank in
                self.authorrank_dict.items()]
        df = pd.DataFrame(data)
        df = df.sort_values(by='Rank', ascending=False)
        return df

if __name__ == "__main__":

    # Cargar datos
    with open('data/data_autores_prueba.json', 'r', encoding='utf-8') as f:
        data_autores = json.load(f)

    with open('data/data_papers_prueba.json', 'r', encoding='utf-8') as f:
        data_papers = json.load(f)

    # Crear instancia de AuthorRank
    author_rank_instance = AuthorRank(data_autores, data_papers, 1, 1)

    # Obtener el DataFrame ordenado descendente

    df_result = author_rank_instance.df

    # Imprimir el DataFrame
    print(df_result)



