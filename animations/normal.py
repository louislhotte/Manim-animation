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
        
        # Initial Gaussian curve with mu=-3 and sigma=sqrt(0.5)
        mu_start, mu_end = -3, 2
        sigma_start, sigma_end = np.sqrt(0.5), np.sqrt(3)
        sigma_squared_start, sigma_squared_end = 0.5, 3
        gauss_graph = axes.plot(gaussian_func(mu_start, sigma_start), color=YELLOW)
        
        # Create a label for mean (mu)
        mu_label = MathTex(r"\mu =", color=YELLOW).next_to(axes.c2p(mu_start, 0), UP)
        mu_value_label = DecimalNumber(mu_start, num_decimal_places=1, color=YELLOW).next_to(mu_label, RIGHT)
        mu_group = VGroup(mu_label, mu_value_label)
        
        # Create a label for sigma (sigma^2)
        sigma_label = MathTex(r"\sigma^2 =", color=GREEN).next_to(axes.c2p(3, 0.7), UP)
        sigma_value_label = DecimalNumber(sigma_squared_start, num_decimal_places=1, color=GREEN).next_to(sigma_label, RIGHT)
        sigma_group = VGroup(sigma_label, sigma_value_label)
        
        self.play(Create(axes), Write(labels))
        self.play(Create(gauss_graph), Write(mu_group), Write(sigma_group))
        
        # Animation to shift mu from -3 to 2
        self.play(
            mu_group.animate.next_to(axes.c2p(mu_end, 0), UP),
            UpdateFromAlphaFunc(mu_value_label, lambda m, a: m.set_value(mu_start + (mu_end - mu_start) * a)),
            UpdateFromAlphaFunc(gauss_graph, lambda m, a: m.become(
                axes.plot(gaussian_func(mu_start + (mu_end - mu_start) * a, sigma_start), color=YELLOW)
            )),
            run_time=12
        )
        
        # Animation to change sigma^2 from 0.5 to 3 (sigma from sqrt(0.5) to sqrt(3))
        self.play(
            sigma_group.animate.next_to(axes.c2p(2, 0.3), UP),
            UpdateFromAlphaFunc(sigma_value_label, lambda m, a: m.set_value(sigma_squared_start + (sigma_squared_end - sigma_squared_start) * a)),
            UpdateFromAlphaFunc(gauss_graph, lambda m, a: m.become(
                axes.plot(gaussian_func(mu_end, sigma_start + (sigma_end - sigma_start) * a), color=YELLOW)
            )),
            run_time=12
        )
        
        # Highlight that E(X) converges to mu
        ex_label = MathTex(r"E(X) \rightarrow \mu", color=RED).to_corner(UR, buff = 1.5)
        self.play(Write(ex_label))
        self.wait(5)


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
        self.wait(8)
        
        return VGroup(header, writer, line)