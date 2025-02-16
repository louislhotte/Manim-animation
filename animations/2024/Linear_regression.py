import numpy as np
from manim import *

class LinearRegression(Scene):
    def construct(self):
        intro_group = self.introduction("Linear Regression Animation", 
                                        "Python || Maths || Manim")
        self.play(FadeOut(intro_group))
        self.wait(1)
        
        # Create axes
        axes = Axes(
            x_range=[0, 1000, 100],
            y_range=[0, 1000, 100],
            axis_config={"color": BLUE},
        )
        axes_labels = axes.get_axis_labels(x_label="Time (hours)", y_label="Revenue (eur)")
        
        np.random.seed(42)
        x_values = np.random.uniform(100, 1000, 200)
        y_values = 1.5 * x_values + np.random.normal(0, 200, 200)  # Adding noise to y-values
        points = list(zip(x_values, y_values))
        point_dots = VGroup(*[Dot(axes.coords_to_point(x, y), color=YELLOW) for x, y in points])
        
        # Initial guesses for the linear regression parameters
        def linear_regression_1(x):
            return 3 * x
        
        def linear_regression_2(x):
            return x
        
        def linear_regression_3(x):
            return 2 * x
        
        regression_line_1 = axes.plot(linear_regression_1, x_range=[0, 1000], color=RED)
        regression_line_2 = axes.plot(linear_regression_2, x_range=[0, 1000], color=GREEN)
        regression_line_3 = axes.plot(linear_regression_3, x_range=[0, 1000], color=BLUE)
        
        def gradient_descent(x_vals, y_vals, learning_rate=0.000001, epochs=1000):
            a, b = np.random.rand(), np.random.rand()
            regression_lines = []
            for epoch in range(epochs):
                y_preds = a * x_vals + b
                a_grad = -2 * np.mean(x_vals * (y_vals - y_preds))
                b_grad = -2 * np.mean(y_vals - y_preds)
                a -= learning_rate * a_grad
                b -= learning_rate * b_grad
                
                if epoch in [0, 1, 2, 3, 5, 10, 20, 50, 100, 250, 500, 1000]:
                    regression_lines.append(axes.plot(lambda x: a * x + b, x_range=[0, 1000], color=PURPLE))
            
            return a, b, regression_lines

        
        # Perform gradient descent to find the best fit line
        best_a, best_b, regression_lines = gradient_descent(x_values, y_values)
        
        def best_fit_line(x):
            return best_a * x + best_b
        
        regression_line_best = axes.plot(best_fit_line, x_range=[0, 1000], color=PURPLE)
        
        # Add all elements to the scene
        self.play(Create(axes), Write(axes_labels))
        self.play(FadeIn(point_dots))
        self.play(Create(regression_line_1), run_time=3)
        self.wait(2)
        self.play(Create(regression_line_2), run_time=3)
        self.wait(2)
        self.play(Create(regression_line_3), run_time=3)
        self.wait(2)
        self.play(FadeOut(regression_line_2), FadeOut(regression_line_3))

        # Show the process of gradient descent
        for i, line in enumerate(regression_lines):
            self.play(Transform(regression_line_1, line), run_time=1)
            self.wait(1)
        self.wait(10)

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
        self.wait(4)
        
        return VGroup(header, writer, line)