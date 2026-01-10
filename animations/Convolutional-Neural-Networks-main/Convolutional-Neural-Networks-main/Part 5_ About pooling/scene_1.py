from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene5_1(VoiceoverScene, MovingCameraScene):
    def create_matrix_filter(self, matrix_content):
        matrix_grid = NumberPlane(
            x_range=[-1, 2],
            y_range=[-1, 2],
            x_length=2,
            y_length=2,
            background_line_style={
                "stroke_color": GRAY,
                "stroke_width": 2,
                "stroke_opacity": 1,
            },
            axis_config={
                "stroke_color": GRAY,
                "stroke_width": 2,
                "include_numbers": False,
            },
            faded_line_ratio=0,
        ).move_to(ORIGIN)

        # Directly using x_length and y_length for rectangle
        rectangle = Rectangle(width=2, height=2, color=GRAY, stroke_width=2).move_to(
            ORIGIN
        )
        cell_width_filter = matrix_grid.get_x_unit_size()

        filter_text = VGroup()
        for i in range(3):
            for j in range(3):
                coords = matrix_grid.coords_to_point(j, i)
                val = matrix_content[j][i]
                text = Tex(f"{val:.2f}", color=BLUE)
                text.move_to(
                    coords + LEFT * cell_width_filter / 2 + DOWN * cell_width_filter / 2
                ).scale(0.5)
                filter_text.add(text)

        return VGroup(matrix_grid, rectangle, filter_text)

    def create_prism(self, dimensions, fill_color, stroke_width):
        prism = Prism(
            dimensions=dimensions, fill_color=fill_color, stroke_width=stroke_width
        )
        prism.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        return prism

    def construct(self):

        self.wait(2)

        # Input image

        input_img = (
            ImageMobject("images/0_mnist.png")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(4)
        )
        img_rectangle = SurroundingRectangle(input_img, buff=0.1, color=GRAY)
        input_img = Group(input_img, img_rectangle)

        # Legend

        legend_conv = MathTex(r"\text{Convolutional Layer}", color=WHITE).scale(0.5)
        legend_conv_rect = Rectangle(
            width=0.25, height=0.25, color=BLUE, fill_opacity=0.5
        ).next_to(legend_conv, LEFT, buff=0.5)
        legend_activation_rect = Rectangle(
            width=0.25, height=0.25, color=GREEN, fill_opacity=0.5
        ).next_to(legend_conv_rect, DOWN, buff=0.25)
        legend_activation = (
            MathTex(r"\text{Activation Layer}", color=WHITE)
            .scale(0.5)
            .next_to(legend_activation_rect, RIGHT, buff=0.5)
        )

        legend = VGroup(
            legend_conv, legend_activation, legend_conv_rect, legend_activation_rect
        )
        rect_legend = SurroundingRectangle(
            legend, buff=0.2, color=WHITE, stroke_width=1
        )
        legend.add(rect_legend)

        legend.shift(DOWN * 3)

        # Layers

        layer_1 = self.create_prism(
            dimensions=[1, 1, 0.3], fill_color=BLUE, stroke_width=1
        )
        layer_2 = self.create_prism(
            dimensions=[1, 1, 0.9], fill_color=BLUE, stroke_width=1
        )
        layer_3 = self.create_prism(
            dimensions=[1, 1, 0.6], fill_color=BLUE, stroke_width=1
        )
        layer_4 = self.create_prism(
            dimensions=[1, 1, 0.1], fill_color=BLUE, stroke_width=1
        )

        act_1 = self.create_prism(
            dimensions=[1, 1, 0.1], fill_color=GREEN, stroke_width=1
        )
        act_2 = self.create_prism(
            dimensions=[1, 1, 0.1], fill_color=GREEN, stroke_width=1
        )
        act_3 = self.create_prism(
            dimensions=[1, 1, 0.1], fill_color=GREEN, stroke_width=1
        )
        act_4 = self.create_prism(
            dimensions=[1, 1, 0.1], fill_color=GREEN, stroke_width=1
        )

        input_img.shift(LEFT * 6 + UP * 1)
        layer_1.next_to(input_img, RIGHT, buff=1.0)
        act_1.next_to(layer_1, RIGHT, buff=0.1)
        layer_2.next_to(act_1, RIGHT, buff=1.0)
        act_2.next_to(layer_2, RIGHT, buff=0.1)
        layer_3.next_to(act_2, RIGHT, buff=1.0)
        act_3.next_to(layer_3, RIGHT, buff=0.1)
        layer_4.next_to(act_3, RIGHT, buff=1.0)
        act_4.next_to(layer_4, RIGHT, buff=0.1)

        # Output image

        output_img = (
            ImageMobject("images/mnist_relu.png")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(4)
        )
        img_rectangle = SurroundingRectangle(output_img, buff=0.1, color=GRAY)
        output_img = Group(output_img, img_rectangle)
        output_img.next_to(act_4, RIGHT, buff=1.0)

        # Arrows

        arrow1 = Arrow(start=input_img.get_right(), end=layer_1.get_left(), color=WHITE)
        arrow2 = Arrow(start=act_1.get_right(), end=layer_2.get_left(), color=WHITE)
        arrow3 = Arrow(start=act_2.get_right(), end=layer_3.get_left(), color=WHITE)
        arrow4 = Arrow(start=act_3.get_right(), end=layer_4.get_left(), color=WHITE)
        arrow5 = Arrow(start=act_4.get_right(), end=output_img.get_left(), color=WHITE)

        # Braces

        brace_img = Brace(input_img, direction=DOWN, color=WHITE).stretch(0.3, dim=1)
        brace_img_txt = brace_img.get_text("(1x28x28)").scale(0.4)
        brace_img = VGroup(brace_img, brace_img_txt)

        brace_filter1 = Brace(layer_1, direction=DOWN, color=WHITE).stretch(0.3, dim=1)
        brace_filter1_txt = brace_filter1.get_text("3 (3 x 3)").scale(0.4)
        brace_filter1 = VGroup(brace_filter1, brace_filter1_txt)

        brace_filter2 = Brace(layer_2, direction=DOWN, color=WHITE).stretch(0.3, dim=1)
        brace_filter2_txt = brace_filter2.get_text("9 (3x3x3)").scale(0.4)
        brace_filter2 = VGroup(brace_filter2, brace_filter2_txt)

        brace_filter3 = Brace(layer_3, direction=DOWN, color=WHITE).stretch(0.3, dim=1)
        brace_filter3_txt = brace_filter3.get_text("6 (9x3x3)").scale(0.4)
        brace_filter3 = VGroup(brace_filter3, brace_filter3_txt)

        brace_filter4 = Brace(layer_4, direction=DOWN, color=WHITE).stretch(0.3, dim=1)
        brace_filter4_txt = brace_filter4.get_text("1 (6 x 3 x 3)").scale(0.4)
        brace_filter4 = VGroup(brace_filter4, brace_filter4_txt)

        brace_output = Brace(output_img, direction=DOWN, color=WHITE).stretch(
            0.3, dim=1
        )
        brace_output_txt = brace_output.get_text("(1x28x28)").scale(0.4)
        brace_output = VGroup(brace_output, brace_output_txt)

        self.play(
            FadeIn(legend),
        )

        self.play(
            FadeIn(input_img),
            FadeIn(brace_img),
        )

        self.play(
            LaggedStart(
                Create(arrow1),
                Create(layer_1),
                Create(act_1),
                FadeIn(brace_filter1),
                lag_ratio=0.5,
            ),
        )

        self.play(
            LaggedStart(
                Create(arrow2),
                Create(layer_2),
                Create(act_2),
                FadeIn(brace_filter2),
                lag_ratio=0.5,
            ),
        )

        self.play(
            LaggedStart(
                Create(arrow3),
                Create(layer_3),
                Create(act_3),
                FadeIn(brace_filter3),
                lag_ratio=0.5,
            )
        )

        self.play(
            LaggedStart(
                Create(arrow4),
                Create(layer_4),
                Create(act_4),
                FadeIn(brace_filter4),
                lag_ratio=0.5,
            )
        )

        self.play(
            LaggedStart(
                Create(arrow5), FadeIn(output_img), FadeIn(brace_output), lag_ratio=0.5
            )
        )

        scalar = MathTex(r"0", color=WHITE).scale(0.5).move_to(output_img)

        self.play(
            FadeOut(output_img, brace_output),
        )

        self.play(
            FadeIn(scalar),
        )

        self.play(
            FadeOut(scalar),
        )
        # Replace output with a flatten + dense layer

        first_column = VGroup(
            *[Circle() for _ in range(3)],
            *[Dot() for _ in range(3)],
            *[Circle() for _ in range(3)],
        )

        first_column.arrange(DOWN, buff=0.2).shift(LEFT * 3)

        # Second column configuration

        # First column configuration
        first_column = VGroup(
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(3)],
            *[Dot(color=WHITE, radius=0.02) for _ in range(3)],
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(3)],
        )
        first_column.arrange(DOWN, buff=0.1).next_to(arrow5, RIGHT, buff=0.2)

        # Second column configuration
        second_column = VGroup(
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(10)]
        )
        second_column.arrange(DOWN, buff=0.1).next_to(first_column, RIGHT, buff=1.0)

        # Draw lines from each circle in the first column to each circle in the second column
        lines = VGroup()
        for first_elem in first_column:
            if isinstance(first_elem, Circle):  # Check to only connect circles
                for second_elem in second_column:
                    line = Line(
                        first_elem.get_right(),
                        second_elem.get_left(),
                        stroke_width=0.5,
                        color=GREY,
                    )
                    lines.add(line)

        fc_layer = VGroup(first_column, second_column, lines)

        self.play(Create(fc_layer))

        # Output scalar

        lines = VGroup()
        output_scalar = Circle(radius=0.1, color=WHITE, stroke_width=0.8).next_to(
            second_column, RIGHT, buff=1.0
        )
        for c in second_column:
            line = Line(
                c.get_right(),
                output_scalar.get_left(),
                color=GREY,
                stroke_width=0.5,
            )
            lines.add(line)

        output_layer = VGroup(output_scalar, lines)

        self.play(Create(output_layer))

        # Scalar

        scalar = (
            MathTex(r"0", color=WHITE)
            .scale(0.5)
            .next_to(output_scalar, RIGHT, buff=1.0)
        )
        arrow_out = Arrow(
            start=output_scalar.get_right(), end=scalar.get_left(), color=WHITE
        )

        self.play(
            LaggedStart(GrowArrow(arrow_out), Write(scalar), lag_ratio=0.2),
        )

        self.wait(1)

        self.play(
            Indicate(fc_layer, scale_factor=1.05, color=WHITE),
        )

        fc_layer_rect = SurroundingRectangle(
            fc_layer, buff=0.2, color=WHITE, stroke_width=1
        )
        fc_layer_rect_txt = (
            Text("7840 parameters !", color=WHITE)
            .scale(0.5)
            .next_to(fc_layer_rect, DOWN, buff=0.2)
        )

        self.play(
            Create(fc_layer_rect),
            Write(fc_layer_rect_txt),
        )

        self.wait(1)

        # Fadeout everything

        self.play(
            FadeOut(input_img),
            FadeOut(layer_1),
            FadeOut(layer_2),
            FadeOut(layer_3),
            FadeOut(layer_4),
            FadeOut(output_layer),
            FadeOut(scalar),
            FadeOut(act_1),
            FadeOut(act_2),
            FadeOut(act_3),
            FadeOut(act_4),
            FadeOut(arrow1),
            FadeOut(arrow2),
            FadeOut(arrow3),
            FadeOut(arrow4),
            FadeOut(arrow5),
            FadeOut(arrow_out),
            FadeOut(brace_img),
            FadeOut(brace_filter1),
            FadeOut(brace_filter2),
            FadeOut(brace_filter3),
            FadeOut(brace_filter4),
            FadeOut(fc_layer),
            FadeOut(fc_layer_rect),
            FadeOut(fc_layer_rect_txt),
            FadeOut(legend),
            run_time=1,
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene5_1()
    scene.render()
