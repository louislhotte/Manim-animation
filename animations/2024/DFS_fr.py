from manim import *
import os

# Set the LaTeX command manually
os.environ["PATH"] += os.pathsep + r"C:\\Users\\louis\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64"

class Youtube(Scene):
    def construct(self):
        # Load and play background music
        # bg_music = "C://Users//Louis//OneDrive//The Eggcellent//Coding Projects//2024//Youtube Downloader//download-music-jupyter//Output//Zeta.mp3"
        # self.add_sound(bg_music, gain=-3, duration=10)
        intro_group = self.introduction()
        self.play(FadeOut(intro_group))
        self.wait(0.5)
        self.explanations()
        self.Intro()
        self.conclusion()

    def introduction(self):
        header = Tex("Depth First Search Algorithm")
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)
        writer = Tex("Created by Ptolémé")
        writer_pos = [(line.get_left()[0] + line.get_right()[0]) / 2, line.get_bottom()[1] - 1, 0]
        writer.move_to(writer_pos)
        
        self.play(Write(header), Write(line))
        self.wait(0.5)
        self.play(Transform(header, Tex("DFS Algorithm")))
        self.play(Write(writer))
        self.wait(1.5)
        
        return VGroup(header, writer, line)


    def explanations(self):
        # Create the explanation VGroup
        explanation = VGroup(
            Tex("\\begin{flushleft}Étapes : \\end{flushleft}"),
            Tex("\\begin{flushleft} 1. Choisir un point de départ.\\end{flushleft}"),
            Tex("\\begin{flushleft} 2. Visiter le nœud et le marquer comme visité.\\end{flushleft}"),
            Tex("\\begin{flushleft} 3. Explorer les voisins non visités.\\end{flushleft}"),
            Tex("\\begin{flushleft} 4. Faire un appel récursif pour chaque voisin non visité.\\end{flushleft}"),
            Tex("\\begin{flushleft} 5. Revenir en arrière une fois tous les voisins explorés.\\end{flushleft}"),
            Tex("\\begin{flushleft} 6. Répéter jusqu'à ce que tous les nœuds soient visités.\\end{flushleft}")
        )
        
        # Arrange the explanation vertically with some spacing
        explanation.arrange(DOWN, aligned_edge=LEFT, buff=0.5)

        # Write each step of the explanation
        self.play(Write(explanation[0]))
        self.wait(0.5)
        for step in explanation[1:]:
            self.play(Write(step))
            self.wait(0.5)
        
        self.play(FadeOut(explanation))

    def Intro(self):
        square = Square()
        circle = Circle()

        # Define initial transformations
        self.play(Create(square))
        self.play(Transform(square, circle))

        # Create a binary tree with depth n
        tree = self.create_binary_tree(depth=4)
        
        # Adjust size and position of the graph
        tree.scale(2)  # Adjust scale as needed
        tree.move_to(ORIGIN)  # Ensure the tree is centered on the screen
        
        self.play(Transform(square, tree))
        self.bring_vertices_to_front(tree)
        # Create the legend
        legend_text = [
            "Légende des couleurs :",
            "- Bleu : sommet visité",
            "- Jaune : sommet en cours d'exploration",
            "- Rouge : sommet complètement exploré"
        ]
        
        legend = VGroup(
            Tex(legend_text[0]),
            Tex(legend_text[1]),
            Tex(legend_text[2]),
            Tex(legend_text[3])
        )

        # Arrange the legend vertically
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        legend.scale(0.5)  # Adjust the scale to fit better in the corner

        # Position the legend in the top right corner
        legend.to_corner(UR)

        # Add a surrounding rectangle
        legend_background = SurroundingRectangle(legend, color=WHITE, buff=0.2)
        
        self.play(Write(legend), Create(legend_background))

        self.wait(1.5)


        # Animate the DFS traversal
        self.animate_dfs(tree, "0")
        self.play(FadeOut(square))
        self.play(FadeOut(tree))
        self.play(FadeOut(legend))
        self.play(FadeOut(legend_background))
        self.wait(3)

    def create_binary_tree(self, depth):
        vertices = []
        edges = []
        labels = {}
        for i in range(2**depth - 1):
            vertices.append(str(i))
            labels[str(i)] = Text(str(i), font_size=14, color=BLACK)
            if 2*i + 1 < 2**depth - 1:
                edges.append((str(i), str(2*i + 1)))
            if 2*i + 2 < 2**depth - 1:
                edges.append((str(i), str(2*i + 2)))
        
        vertex_config = {vertex: {"radius": 0.2} for vertex in vertices}  
        
        graph = Graph(
            vertices,
            edges,
            labels=labels,
            layout="tree",
            root_vertex="0",
            vertex_config=vertex_config
        )
        
        return graph

    def bring_vertices_to_front(self, graph):
        for vertex in graph.vertices.values():
            self.add(vertex)
    
    def animate_dfs(self, graph, start_vertex):
        visited = set()

        def get_neighbors(vertex):
            neighbors = []
            for (v1, v2) in graph.edges:
                if v1 == vertex:
                    neighbors.append(v2)
                elif v2 == vertex:
                    neighbors.append(v1)
            return neighbors

        def dfs(vertex):
            if vertex in visited:
                return
            visited.add(vertex)
            # Colorier le sommet visité en bleu avec un remplissage transparent
            self.play(graph.vertices[vertex].animate.set_fill(BLUE, opacity=0.3), run_time=0.2)
            self.wait(0.5)
            self.bring_vertices_to_front(graph)
            neighbors = get_neighbors(vertex)
            for neighbor in neighbors:
                if neighbor not in visited:
                    # Colorier le voisin exploré en jaune
                    self.play(graph.vertices[neighbor].animate.set_fill(YELLOW, opacity=0.3), run_time=0.2)
                    self.bring_vertices_to_front(graph)
                    self.wait(0.2)
                    dfs(neighbor)
                    # Revenir à la couleur blanche après l'exploration en réinitialisant correctement
                    self.play(graph.vertices[neighbor].animate.set_fill(RED, opacity=0.3), run_time=0.2)
                    self.bring_vertices_to_front(graph)
                    self.wait(0.2)

        dfs(start_vertex)

    def conclusion(self):
        # Create the conclusion VGroup
        conclusion = VGroup(
            Tex("\\begin{flushleft}Conclusion : \\end{flushleft}"),
            Tex("\\begin{flushleft} - Compléxité : \\(O(V + E)\\), où \\(V\\) est le nombre de sommets \\end{flushleft}"),
            Tex("\\begin{flushleft} et \\(E\\) est le nombre d'arêtes.\\end{flushleft}"),
            Tex("\\begin{flushleft} - DFS est efficace pour trouver un noeud dans un graphe\\end{flushleft}"),
            Tex("\\begin{flushleft} - L'algorithme est exhaustif (tous les noeuds sont parcourus)\\end{flushleft}"),
            Tex("\\begin{flushleft} - DFS peut être utilisé pour détecter des cycles dans un graphe\\end{flushleft}"),
            Tex("\\begin{flushleft} - Applications : résolution de puzzles, analyse de réseaux,\\end{flushleft}"),
            Tex("\\begin{flushleft} recherche de chemins dans des labyrinthes, etc.\\end{flushleft}")
        )
        
        # Arrange the conclusion vertically with some spacing
        conclusion.arrange(DOWN, aligned_edge=LEFT, buff=0.5)

        # Write each part of the conclusion
        self.play(Write(conclusion[0]))
        self.wait(0.5)
        for part in conclusion[1:]:
            self.play(Write(part))
            self.wait(0.5)
        
        self.play(FadeOut(conclusion))
        self.wait(5)