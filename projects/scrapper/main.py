import matplotlib.pyplot as plt
import networkx as nx

# Create a directed graph
G = nx.DiGraph()

# Add the root and its children
G.add_node("Root")
vowels = ["a", "e", "i", "o", "u"]
for vowel in vowels:
    G.add_edge("Root", vowel)

# Define positions for the nodes
pos = nx.spring_layout(G)

# Draw the nodes
nx.draw_networkx_nodes(G, pos, node_size=2000, node_color="skyblue")

# Draw the edges
nx.draw_networkx_edges(G, pos, arrowstyle="-|>", arrowsize=20, edge_color="black")

# Draw the labels
nx.draw_networkx_labels(G, pos, font_size=15, font_weight="bold", font_color="darkblue")

# Set the title
plt.title("Tree Visualization: Root with Vowels", fontsize=15)

# Hide the axes
plt.axis("off")

# Show the plot
plt.show()
