from manim import *

class TaylorSeriesApproximation(Scene):
    def construct(self):
        intro_group = self.introduction("Handbook of Statistics - Part III : Taylor series", 
                                        "Visualisation of exponential taylor series")
        self.play(FadeOut(intro_group))
        self.wait(1)
        # Define the function and its Taylor series
        func = lambda x: np.exp(x)
        taylor_series = [
            lambda x: 1,
            lambda x: 1 + x,
            lambda x: 1 + x + (x**2)/2,
            lambda x: 1 + x + (x**2)/2 + (x**3)/6,
            lambda x: 1 + x + (x**2)/2 + (x**3)/6 + (x**4)/24,
        ]

        # Define the axes
        axes = Axes(
            x_range=[-3, 3, 1], y_range=[0, 20, 5],
            axis_config={"color": WHITE}
        )

        # Labels for axes
        axes_labels = axes.get_axis_labels(x_label="x", y_label="f(x)")

        # Graph of the original function
        graph = axes.plot(func, color=BLUE, x_range=[-3, 3])

        # Animations
        self.play(Create(axes), Create(axes_labels))
        self.play(Create(graph), run_time=2)

        # Colors for each Taylor series approximation
        colors = [RED, ORANGE, GREEN, PURPLE, YELLOW]

        legend_items = [
            (r"Order 0: $1 + o(x)$", colors[0]),
            (r"Order 1: $1 + x + o(x)$", colors[1]),
            (r"Order 2: $1 + x + \frac{x^2}{2} + o(x)$", colors[2]),
            (r"Order 3: $1 + x + \frac{x^2}{2} + \frac{x^3}{6} + o(x)$", colors[3]),
            (r"Order 4: $1 + x + \frac{x^2}{2} + \frac{x^3}{6} + \frac{x^4}{24} + o(x)$", colors[4]),
            (r"Exponential: $e^x$", BLUE)
        ]

        legend = VGroup(*[
            VGroup(Dot(color=color), Tex(formula, font_size=24)).arrange(RIGHT)
            for formula, color in legend_items
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.5).to_corner(UL, buff=1)

        legend_rect = SurroundingRectangle(legend, color=WHITE, buff=0.5)
        self.play(Create(legend_rect), Create(legend))

        # Plot each Taylor series approximation
        for i, series in enumerate(taylor_series):
            taylor_graph = axes.plot(series, color=colors[i], x_range=[-3, 3])
            self.play(Create(taylor_graph), run_time=2)
            self.wait(1)

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