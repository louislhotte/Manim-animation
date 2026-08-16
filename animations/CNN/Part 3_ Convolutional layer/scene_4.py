from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene3_4(VoiceoverScene, MovingCameraScene):
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

        input_img.shift(LEFT * 4)
        layer_1.next_to(input_img, RIGHT, buff=1.0)
        layer_2.next_to(layer_1, RIGHT, buff=1.0)
        layer_3.next_to(layer_2, RIGHT, buff=1.0)
        layer_4.next_to(layer_3, RIGHT, buff=1.0)

        # Output image

        output_img = (
            ImageMobject("images/mnist_sum.png")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(4)
        )
        img_rectangle = SurroundingRectangle(output_img, buff=0.1, color=GRAY)
        output_img = Group(output_img, img_rectangle)
        output_img.next_to(layer_4, RIGHT, buff=1.0)

        # Arrows

        arrow1 = Arrow(start=input_img.get_right(), end=layer_1.get_left(), color=WHITE)
        arrow2 = Arrow(start=layer_1.get_right(), end=layer_2.get_left(), color=WHITE)
        arrow3 = Arrow(start=layer_2.get_right(), end=layer_3.get_left(), color=WHITE)
        arrow4 = Arrow(start=layer_3.get_right(), end=layer_4.get_left(), color=WHITE)
        arrow5 = Arrow(
            start=layer_4.get_right(), end=output_img.get_left(), color=WHITE
        )

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

        self.play(FadeIn(input_img), run_time=1)

        self.play(
            LaggedStart(
                Create(arrow1), Create(layer_1), FadeIn(brace_img), lag_ratio=0.5
            ),
        )

        self.play(
            LaggedStart(
                Create(arrow2),
                Create(layer_2),
                FadeIn(brace_filter1),
                lag_ratio=0.5,
            ),
        )

        self.play(
            LaggedStart(
                Create(arrow3),
                Create(layer_3),
                FadeIn(brace_filter2),
                lag_ratio=0.5,
            ),
        )

        self.play(
            LaggedStart(
                Create(arrow4),
                Create(layer_4),
                FadeIn(brace_filter3),
                lag_ratio=0.5,
            ),
        )

        self.play(
            LaggedStart(
                Create(arrow5),
                FadeIn(output_img),
                FadeIn(brace_filter4),
                FadeIn(brace_output),
                lag_ratio=0.5,
            ),
        )

        # Fadeout everything

        self.wait()

        self.play(
            FadeOut(input_img),
            FadeOut(layer_1),
            FadeOut(layer_2),
            FadeOut(layer_3),
            FadeOut(layer_4),
            FadeOut(output_img),
            FadeOut(arrow1),
            FadeOut(arrow2),
            FadeOut(arrow3),
            FadeOut(arrow4),
            FadeOut(arrow5),
            FadeOut(brace_img),
            FadeOut(brace_filter1),
            FadeOut(brace_filter2),
            FadeOut(brace_filter3),
            FadeOut(brace_filter4),
            FadeOut(brace_output),
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene3_4()
    scene.render()
