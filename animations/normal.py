from manim import *

class GaussianDistribution(Scene):
    def construct(self):
        intro_group = self.introduction("Handbook of Statistics - Part II : Gaussian distribution", 
                                        "Visualisation of parameters and expected value")
        self.play(FadeOut(intro_group))
        self.wait(1)
        # Setup the axes
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[0, 1, 0.1],
            axis_config={"color": BLUE},
        ).add_coordinates()
        
        # Add labels
        labels = axes.get_axis_labels(x_label="x", y_label="f(x)")
        
        # Function to create Gaussian graph
        def gaussian_func(mu, sigma):
            return lambda x: np.exp(-(x - mu) ** 2 / (2 * sigma ** 2)) / (sigma * np.sqrt(2 * np.pi))
        
        # Initial Gaussian curve with mu=-1 and sigma=1
        mu_start, mu_end = -1, 1
        sigma_start, sigma_end = 1, 2
        sigma_squared_start, sigma_squared_end = 1, 4
        gauss_graph = axes.plot(gaussian_func(mu_start, sigma_start), color=YELLOW)
        
        # Create a label for mean (mu)
        mu_label = MathTex(r"\mu", color=YELLOW).next_to(axes.c2p(mu_start, 0), UP)
        
        # Create a label for sigma (sigma^2)
        sigma_label = MathTex(r"\sigma^2", color=GREEN).next_to(axes.c2p(2, 0.4), RIGHT)
        
        self.play(Create(axes), Write(labels))
        self.play(Create(gauss_graph), Write(mu_label), Write(sigma_label))
        
        # Animation to shift mu from -1 to 1
        self.play(
            mu_label.animate.next_to(axes.c2p(mu_end, 0), UP),
            UpdateFromAlphaFunc(gauss_graph, lambda m, a: m.become(
                axes.plot(gaussian_func(mu_start + (mu_end - mu_start) * a, sigma_start), color=YELLOW)
            )),
            run_time=3
        )
        
        # Animation to change sigma^2 from 1 to 4 (sigma from 1 to 2)
        self.play(
            sigma_label.animate.next_to(axes.c2p(2, 0.1), RIGHT),
            UpdateFromAlphaFunc(gauss_graph, lambda m, a: m.become(
                axes.plot(gaussian_func(mu_end, sigma_start + (sigma_end - sigma_start) * a), color=YELLOW)
            )),
            run_time=3
        )
        
        # Highlight that E(X) converges to mu
        ex_label = MathTex(r"E(X) \rightarrow \mu", color=RED).to_edge(UP)
        self.play(Write(ex_label))
        
        self.wait(2)

    def introduction(self, title1, title2):
        header = Tex(title1)
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)
        writer = Tex("Created by Ptolémé")
        writer_pos = [(line.get_left()[0] + line.get_right()[0]) / 2, line.get_bottom()[1] - 1, 0]
        writer.move_to(writer_pos)
        
        self.play(Write(header), Write(line))
        self.wait(0.5)
        self.play(Transform(header, Tex(title2)))
        self.play(Write(writer))
        self.wait(1.5)
        
        return VGroup(header, writer, line)