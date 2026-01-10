from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene4_1(VoiceoverScene, MovingCameraScene):
    def create_prism(self, dimensions, fill_color, stroke_width):
        prism = Prism(
            dimensions=dimensions, fill_color=fill_color, stroke_width=stroke_width
        )
        prism.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        return prism

    def construct(self):

        def relu(x):
            return max(0, x)

        def sigmoid(x):
            return 1 / (1 + np.exp(-x))

        def tanh(x):
            return np.tanh(x)

        def leaky_relu(x, alpha=0.3):
            return np.maximum(alpha * x, x)

        def elu(x, alpha=1):
            return np.where(x > 0, x, alpha * (np.exp(x) - 1))

        self.wait(2)

        # Create a number plane
        plane = NumberPlane(
            x_range=[-2, 2, 1],  # X-axis from -2 to 2
            y_range=[-2, 2, 1],  # Y-axis from -2 to 2
            background_line_style={
                "stroke_color": GRAY,
                "stroke_width": 2,
                "stroke_opacity": 0.5,
            },
        )

        relu_graph = plane.plot(relu, color=GREEN)
        graph_title = MathTex(
            r"ReLU(x) = \max(0, x)", font_size=32, color=GREEN
        ).next_to(plane, DOWN, buff=1.0)
        surrounding_rectangle = SurroundingRectangle(plane, color=GRAY)

        static_group = VGroup(surrounding_rectangle, plane, graph_title)

        # Draw ReLU graph
        self.play(FadeIn(static_group))
        self.play(Create(relu_graph))

        graph = VGroup(static_group, relu_graph)

        self.wait()

        # Send the graph to the left and shrink it

        self.play(
            graph.animate.shift(4 * LEFT).scale(0.8),
        )

        # Display the input image along with the conv layer

        input_image = (
            ImageMobject("images/0_mnist.png")
            .scale(6)
            .shift(RIGHT)
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
        )
        input_image_rect = SurroundingRectangle(
            input_image, color=GRAY, stroke_width=0.5
        )
        input_image = Group(input_image, input_image_rect)

        conv_layer = self.create_prism(
            dimensions=[1.5, 1.5, 0.5], fill_color=BLUE, stroke_width=0.5
        ).next_to(input_image, RIGHT, buff=1.0)
        activation_layer = self.create_prism(
            dimensions=[1.5, 1.5, 0.2], fill_color=GREEN, stroke_width=0.5
        ).next_to(conv_layer, RIGHT, buff=0.1)

        output_img = (
            ImageMobject("images/mnist_relu.png")
            .scale(6)
            .next_to(activation_layer, RIGHT, buff=1.0)
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
        )
        output_img_rect = SurroundingRectangle(output_img, color=GRAY, stroke_width=0.5)
        output_img = Group(output_img, output_img_rect)

        arrow1 = Arrow(
            start=input_image.get_right(),
            end=conv_layer.get_left(),
            color=WHITE,
            buff=0.1,
        )
        arrow2 = Arrow(
            start=activation_layer.get_right(),
            end=output_img.get_left(),
            color=WHITE,
            buff=0.1,
        )

        self.play(FadeIn(input_image))
        self.play(
            LaggedStart(GrowArrow(arrow1), Create(conv_layer), lag_ratio=0.1),
        )

        self.play(Create(activation_layer))

        self.play(
            LaggedStart(GrowArrow(arrow2), FadeIn(output_img), lag_ratio=0.1),
        )

        # Add legend

        legend_conv = (
            MathTex(r"\text{Convolutional Layer}", color=WHITE)
            .next_to(conv_layer, DOWN, buff=1.0)
            .scale(0.5)
        )

        legend_conv_rect = Rectangle(
            width=0.25, height=0.25, color=BLUE, fill_opacity=0.5
        ).next_to(legend_conv, LEFT, buff=0.5)
        legend_activation_rect = Rectangle(
            width=0.25, height=0.25, color=GREEN, fill_opacity=0.5
        ).next_to(legend_conv_rect, DOWN, buff=0.5)

        legend_activation = (
            MathTex(r"\text{Activation Layer}", color=WHITE)
            .scale(0.5)
            .next_to(legend_activation_rect, RIGHT, buff=0.5)
        )

        legend = VGroup(
            legend_conv, legend_activation, legend_conv_rect, legend_activation_rect
        )
        self.play(FadeIn(legend))

        self.play(FadeOut(arrow1, arrow2))

        self.wait(0.5)

        # Draw sigmoid graph

        sigmoid_graph = plane.plot(sigmoid, color=GREEN)
        graph_title_sigmoid = MathTex(
            r"Sigmoid(x) = \frac{1}{1 + e^{-x}}", font_size=32, color=GREEN
        ).next_to(plane, DOWN, buff=0.5)

        output_img_sigmoid = (
            ImageMobject("images/mnist_sigmoid.png")
            .scale(6)
            .next_to(activation_layer, RIGHT, buff=1.0)
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
        )
        output_img_sigmoid_rect = SurroundingRectangle(
            output_img_sigmoid, color=GRAY, stroke_width=0.5
        )
        output_img_sigmoid = Group(output_img_sigmoid, output_img_sigmoid_rect)

        self.play(FadeOut(relu_graph))
        self.play(
            LaggedStart(
                Create(sigmoid_graph),
                Transform(graph_title, graph_title_sigmoid),
                GrowArrow(arrow1),
                GrowArrow(arrow2),
                FadeOut(output_img),
                FadeIn(output_img_sigmoid),
                lag_ratio=0.3,
            ),
        )

        self.play(FadeOut(arrow1, arrow2))

        # Draw tanh graph

        tanh_graph = plane.plot(tanh, color=GREEN)
        graph_title_tanh = MathTex(
            r"\tanh(x) = \frac{e^{x} - e^{-x}}{e^{x} + e^{-x}}",
            font_size=32,
            color=GREEN,
        ).next_to(plane, DOWN, buff=0.5)

        output_img_tanh = (
            ImageMobject("images/mnist_tanh.png")
            .scale(6)
            .next_to(activation_layer, RIGHT, buff=1.0)
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
        )
        output_img_tanh_rect = SurroundingRectangle(
            output_img_tanh, color=GRAY, stroke_width=0.5
        )
        output_img_tanh = Group(output_img_tanh, output_img_tanh_rect)

        self.play(FadeOut(sigmoid_graph))
        self.play(
            LaggedStart(
                Create(tanh_graph),
                Transform(graph_title, graph_title_tanh),
                GrowArrow(arrow1),
                GrowArrow(arrow2),
                FadeOut(output_img_sigmoid),
                FadeIn(output_img_tanh),
                lag_ratio=0.3,
            ),
        )

        self.play(FadeOut(arrow1, arrow2))

        self.wait(0.5)

        # Draw leaky ReLU graph

        leaky_relu_graph = plane.plot(leaky_relu, color=GREEN)
        graph_title_leaky_relu = MathTex(
            r"LeakyReLU(x) = \max(\alpha x, x)", font_size=32, color=GREEN
        ).next_to(plane, DOWN, buff=0.5)

        output_img_leaky = (
            ImageMobject("images/mnist_leaky.png")
            .scale(6)
            .next_to(activation_layer, RIGHT, buff=1.0)
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
        )
        output_img_leaky_rect = SurroundingRectangle(
            output_img_leaky, color=GRAY, stroke_width=0.5
        )
        output_img_leaky = Group(output_img_leaky, output_img_leaky_rect)

        self.play(FadeOut(tanh_graph))

        self.play(
            LaggedStart(
                Create(leaky_relu_graph),
                Transform(graph_title, graph_title_leaky_relu),
                GrowArrow(arrow1),
                GrowArrow(arrow2),
                FadeOut(output_img_tanh),
                FadeIn(output_img_leaky),
                lag_ratio=0.3,
            ),
        )

        self.play(FadeOut(arrow1, arrow2))

        # Draw ELU graph

        elu_graph = plane.plot(elu, color=GREEN)
        graph_title_elu = MathTex(
            r"ELU(x) = \begin{cases} x & \text{if } x > 0 \\ \alpha(e^{x} - 1) & \text{if } x \leq 0 \end{cases}",
            font_size=32,
            color=GREEN,
        ).next_to(plane, DOWN, buff=0.5)

        output_img_elu = (
            ImageMobject("images/mnist_elu.png")
            .scale(6)
            .next_to(activation_layer, RIGHT, buff=1.0)
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
        )
        output_img_elu_rect = SurroundingRectangle(
            output_img_elu, color=GRAY, stroke_width=0.5
        )
        output_img_elu = Group(output_img_elu, output_img_elu_rect)

        self.play(FadeOut(leaky_relu_graph))

        self.play(
            LaggedStart(
                Create(elu_graph),
                Transform(graph_title, graph_title_elu),
                GrowArrow(arrow1),
                GrowArrow(arrow2),
                FadeOut(output_img_leaky),
                FadeIn(output_img_elu),
                lag_ratio=0.3,
            ),
        )

        # Fade out everything

        self.play(
            FadeOut(graph),
            FadeOut(elu_graph),
            FadeOut(legend),
            FadeOut(arrow1, arrow2),
            FadeOut(activation_layer),
            FadeOut(conv_layer),
            FadeOut(input_image),
            FadeOut(output_img_elu),
            run_time=1,
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene4_1()
    scene.render()
