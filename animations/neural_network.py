from manim import *
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
import warnings

# Suppress ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)

class CombinedNeuralNetworkScene(Scene):
    def construct(self):
        # points = self.play_function_graph()
        self.play_neural_network_approximation()

    def play_function_graph(self):
        return PointGraph.construct(self)

    def play_neural_network_approximation(self):
        PlayNeuralNetworkApproximation.construct(self)


class PointGraph(Scene):
    def construct(self):
        header = Tex("Representation of our data").scale(0.5)
        header.set_width(8)
        header.to_edge(UP)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.25, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.25, 0]
        line = Line(from_pos, to_pos)
        self.play(Write(header), Write(line))
        self.wait(0.5)
        
        ax = Axes(
            x_range=[-10, 10, 2], 
            y_range=[-3, 6, 1], 
            x_length=10, 
            y_length=5,
            axis_config={"include_numbers": True}
        )
        ax.to_edge(DOWN, buff=1)
        points = [
            ax.coords_to_point(x, 0.5 * x * np.sin(x) + np.random.uniform(-0.1, 0.1)) 
            for x in np.linspace(-10, 10, 1000)
        ]
        dots = VGroup(*[Dot(point, color=BLUE, radius=0.015) for point in points])
        
        formula = MathTex("y \\approx 2\\sin(x) + \\cos(x)").scale(0.5).next_to(ax, UP)
        formula_rect = SurroundingRectangle(formula, color=WHITE)
        
        x_label = MathTex("x").scale(0.7).next_to(ax, RIGHT, buff=0.1)
        
        legend = VGroup(
            Line(color=BLUE).scale(0.5),
            MathTex("y \\approx 2\\sin(x) + \\cos(x)").scale(0.7)
        ).arrange(RIGHT, buff=0.2).to_corner(DR)
        
        self.play(FadeIn(ax))
        self.play(FadeIn(x_label))
        self.wait(2)
        self.play(FadeIn(dots))
        self.wait(3)
        self.play(FadeIn(formula), Create(formula_rect))
        self.wait(2)
        self.play(FadeIn(legend))
        self.wait(20)
        self.play(FadeOut(ax), FadeOut(dots), FadeOut(formula), FadeOut(formula_rect), FadeOut(legend), 
                  FadeOut(x_label), FadeOut(header), FadeOut(line))        
        return [(x, 2 * np.sin(x) + np.cos(x) + np.random.uniform(-0.1, 0.1), 0) for x in np.linspace(-10, 10, 1000)]

class PlayNeuralNetworkApproximation(Scene):
    def construct(self):
        header = Tex("Neural Network Approximation").scale(0.5)
        header.set_width(8)
        header.to_edge(UP)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.25, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.25, 0]
        line = Line(from_pos, to_pos)
        self.play(Write(header), Write(line))
        self.wait(0.5)

        
        ax = Axes(
            x_range=[-12, 12, 2], 
            y_range=[-3, 6, 1], 
            x_length=10, 
            y_length=5,
            axis_config={"include_numbers": True}
        )
        ax.to_edge(DOWN, buff=1)
        points = [
            ax.coords_to_point(x, 0.5 * x * np.sin(x) + np.random.uniform(-0.1, 0.1)) 
            for x in np.linspace(-10, 10, 1000)
        ]
        
        dots = VGroup(*[Dot([x, y, 0], color=BLUE, radius=0.015) for x, y, z in points])
        
        mse_text = Tex("MSE:").scale(0.7).next_to(ax, UL)
        mse_value = DecimalNumber(0, num_decimal_places=2).scale(0.7).next_to(mse_text, RIGHT)
        mse_group = VGroup(mse_text, mse_value)

        epoch_text = Tex("Epoch:").scale(0.7).next_to(mse_text, DOWN, buff = 0.15)
        epoch_value = DecimalNumber(1, num_decimal_places=0).scale(0.7).next_to(epoch_text, RIGHT)
        epoch_group = VGroup(epoch_text, epoch_value)

        self.play(FadeIn(ax))
        self.play(FadeIn(dots))
        self.play(FadeIn(mse_group), FadeIn(epoch_group))
        
        mlp = MLPRegressor(hidden_layer_sizes=(50, 50), activation='relu', solver='adam', 
                   alpha=0.001, learning_rate='adaptive', max_iter=2000, random_state=42)

        X = np.array([x for x, y, z in points]).reshape(-1, 1)
        y = np.array([y for x, y, z in points])
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        future_x = np.linspace(-10, 10, 1000).reshape(-1, 1)
        future_x_scaled = scaler.transform(future_x)

        approx_line = None
        for epoch in range(1, 51):
            model.fit(X_scaled, y)
            y_pred = model.predict(future_x_scaled)
            new_approx_line = ax.plot_line_graph(
                [x for x in future_x.flatten()], 
                [y for y in y_pred], 
                add_vertex_dots=False,
                line_color=RED,
                vertex_dot_style={'color': RED, 'radius': 0.05}
            )
            
            mse = np.mean([(y_true - model.predict(scaler.transform([[x]]))[0])**2 for x, y_true, z in points])
            
            mse_value.set_value(mse)
            epoch_value.set_value(epoch)
            if epoch == 1:
                self.play(Create(new_approx_line))
                self.play(Transform(mse_value, mse_value), Transform(epoch_value, epoch_value))
                approx_line = new_approx_line
                self.wait(1)
                legend = VGroup(
                    Dot(color=BLUE).scale(1.2),
                    Tex("Training Data Points").scale(0.7),
                    Line(color=RED).scale(0.7),
                    Tex("Neural Network Predictions").scale(0.7)
                ).arrange(RIGHT, buff=0.5).to_corner(DR)
                self.play(FadeIn(legend))
            elif epoch in [1, 10, 20, 50, 100, 200, 500, 1000, 1800, 3000, 5000]:
                print("EPOCH = ", epoch)
                self.play(Transform(approx_line, new_approx_line))
                self.play(Transform(mse_value, mse_value), Transform(epoch_value, epoch_value))
                self.wait(0.5)
        
        self.wait(20)
        self.play(FadeOut(ax), FadeOut(dots), FadeOut(mse_group), FadeOut(epoch_group), FadeOut(approx_line), FadeOut(legend))
