from manim import *
import numpy as np
from sklearn.metrics import mean_squared_error
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
import warnings

# Suppress ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)

class CombinedNeuralNetworkScene(Scene):
    def construct(self):
        # points = self.play_function_graph()
        # self.play_neural_network_approximation()
        self.play_explanations()

    def play_function_graph(self):
        return PointGraph.construct(self)

    def play_neural_network_approximation(self):
        PlayNeuralNetworkApproximation.construct(self)

    def play_explanations(self):
        Explanations.construct(self)
    
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
    
    def Outro(self, text):
        header = Tex(text)
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)        
        self.play(Write(header), Write(line))
        self.wait(0.5)



class Explanations(Scene):
    def construct(self):
        text = Text("But...How does it work really?").scale(0.5)
        self.play(FadeIn(text))
        self.wait(1)
        self.play(Transform(text, Text("Let's dive into the maths of neural networks").scale(0.5)))
        self.wait(2)
        self.play(FadeOut(text))

        header = Tex("Neural Network").scale(0.4)
        header.set_width(8)
        header.to_edge(UP)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.25, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.25, 0]
        line = Line(from_pos, to_pos)
        self.play(Write(header), Write(line))
        self.wait(0.5)

        input_layer = 2
        hidden_layers = [10, 10]
        output_layer = 1

        layers = [input_layer] + hidden_layers + [output_layer]

        neuron_circles = []
        connections = []

        neuron_radius = 0.15
        layer_spacing = 2
        neuron_spacing = 0.45

        center_offset = 3

        all_neurons = VGroup().to_edge(DOWN, buff=1)

        for i, layer_size in enumerate(layers):
            layer_neurons = []
            for j in range(layer_size):
                neuron = Circle(radius=neuron_radius, color=BLUE)
                neuron.move_to(np.array([i * layer_spacing - center_offset + 0.5, j * neuron_spacing - (layer_size - 1) / 2 * neuron_spacing - 1.5, 0]))
                layer_neurons.append(neuron)
                all_neurons.add(neuron)
            neuron_circles.append(layer_neurons)

        self.play(FadeIn(all_neurons))

        for i in range(len(neuron_circles) - 1):
            for neuron1 in neuron_circles[i]:
                for neuron2 in neuron_circles[i + 1]:
                    connection = Line(neuron1.get_center(), neuron2.get_center(), stroke_width=1, color=GRAY)
                    self.play(FadeIn(connection), run_time=0.1)
                    connections.append(connection)
        all_connections = VGroup(*connections)
        self.wait(20)
        self.play(FadeOut(all_connections), FadeOut(all_neurons))

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
        ax.to_edge(DOWN, buff=2)
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
            y_range=[-6, 6, 2], 
            x_length=10, 
            y_length=5,
            axis_config={"include_numbers": True}
        )
        ax.to_edge(DOWN, buff=1)
        x_values = np.linspace(-10, 10, 1000)
        y_values = 0.5 * x_values * np.sin(x_values) + np.random.uniform(-0.1, 0.1, size=1000)
        points = [ax.coords_to_point(x, y) for x, y in zip(x_values, y_values)]
        
        dots = VGroup(*[Dot(point, color=BLUE, radius=0.015) for point in points])
        
        mse_text = Tex("MSE:").scale(0.7).next_to(ax, np.array([-1.5, 0.5, 0.0]))
        mse_value = DecimalNumber(0, num_decimal_places=2).scale(0.7).next_to(mse_text, RIGHT)
        mse_group = VGroup(mse_text, mse_value)
        
        iter_text = Tex("Iterations:").scale(0.7).next_to(mse_text, DOWN, buff=0.15)
        iter_value = DecimalNumber(1, num_decimal_places=0).scale(0.7).next_to(iter_text, RIGHT)
        iter_group = VGroup(iter_text, iter_value)
        
        self.play(FadeIn(ax))
        self.play(FadeIn(dots))
        self.play(FadeIn(mse_group), FadeIn(iter_group))
        
        X = x_values.reshape(-1, 1)
        y = y_values
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        future_x = np.linspace(-10, 10, 1000).reshape(-1, 1)
        future_x_scaled = scaler.transform(future_x)
        
        max_iters = [1, 5, 10, 20, 50, 100, 150, 200, 250, 300, 400, 500, 1000]
        approx_line = None
        
        legend = VGroup(
            Dot(color=BLUE).scale(1.2),
            Tex("Training Data Points").scale(0.7),
            Line(color=RED).scale(0.7),
            Tex("NN Predictions").scale(0.7)
        ).arrange(RIGHT, buff=0.5).to_corner(DR)
        self.play(FadeIn(legend))

        for idx, max_iter in enumerate(max_iters):
            model = MLPRegressor(hidden_layer_sizes=(50, 50), activation='relu', solver='adam', 
                                 alpha=0.001, learning_rate='adaptive', max_iter=max_iter, random_state=42)
            model.fit(X_scaled, y)
            y_pred = model.predict(future_x_scaled)
            new_approx_line = ax.plot_line_graph(
                future_x.flatten(), 
                y_pred, 
                add_vertex_dots=False,
                line_color=RED,
            )
            mse = mean_squared_error(y, model.predict(X_scaled))
            mse_value.set_value(mse)
            iter_value.set_value(max_iter)
            if idx == 0:
                self.play(Create(new_approx_line))
                approx_line = new_approx_line
            else:
                self.play(Transform(approx_line, new_approx_line))
            self.wait(1)
        
        self.wait(2)
        self.play(FadeOut(ax), FadeOut(dots), FadeOut(mse_group), 
                  FadeOut(iter_group), FadeOut(approx_line), FadeOut(legend), FadeOut(header), FadeOut(line))
