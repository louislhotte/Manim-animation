from manim import *

class MarkovChain(Scene):
    def construct(self):
        states = ["A", "B", "C"]
        positions = {
            "A": [-2, 2, 0],
            "B": [2, 2, 0],
            "C": [0, -2, 0]
        }
        
        graph = Graph(
            vertices=states,
            edges=[("A", "B"), ("B", "C"), ("C", "A")],
            layout=positions,
            labels=True,
            vertex_config={
                "A": {"fill_color": BLUE},
                "B": {"fill_color": GREEN},
                "C": {"fill_color": RED}
            }
        )
        
        self.play(Create(graph))
        self.wait(1)
        self.play(graph["A"].animate.move_to(graph["B"].get_center()), run_time=1)
        self.wait(1)
        self.play(graph["B"].animate.move_to(graph["C"].get_center()), run_time=1)
        self.wait(1)
        self.play(graph["C"].animate.move_to(graph["A"].get_center()), run_time=1)
        self.wait(1)
        self.play(Indicate(graph["A"], color=YELLOW), run_time=1)
        self.wait(1)
        self.play(FadeOut(graph))

if __name__ == "__main__":
    from manim import config
    config.media_width = "100%"
    config.verbosity = "WARNING"
    scene = MarkovChain()
    scene.render()
