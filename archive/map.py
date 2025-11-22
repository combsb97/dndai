import networkx as nx
import matplotlib.pyplot as plt

class Location:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __str__(self):
        return f"Location(name={self.name}, description={self.description})"

class Path:
    def __init__(self, from_location, to_location, distance=1):
        self.from_location = from_location
        self.to_location = to_location
        self.distance = distance

    def __str__(self):
        return f"Path(from={self.from_location}, to={self.to_location}, distance={self.distance})"

class Map:
    def __init__(self):
        self.adjacency_list = {}
        self.locations = {}
        self.paths = []

    def add_location(self, name, description):
        location = Location(name, description)
        self.locations[name] = location
        if name not in self.adjacency_list:
            self.adjacency_list[name] = []

    def add_path(self, from_location, to_location, distance=1):
        if from_location not in self.locations or to_location not in self.locations:
            raise ValueError("Both locations must be added to the map before adding a path.")
        
        path = Path(from_location, to_location, distance)
        self.paths.append(path)
        self.adjacency_list[from_location].append(to_location)
        self.adjacency_list[to_location].append(from_location)

    def __str__(self):
        return str(self.adjacency_list)

    def visualize(self):
        G = nx.Graph()
        for location, edges in self.adjacency_list.items():
            for edge in edges:
                G.add_edge(location, edge)
        
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=10, font_weight="bold")
        plt.show()