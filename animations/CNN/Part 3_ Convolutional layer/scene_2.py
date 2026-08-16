from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene3_2(VoiceoverScene, MovingCameraScene):
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

    def construct(self):
        # Display the images

        image1 = (
            ImageMobject("images/mnist_conv1")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
            .to_edge(LEFT)
            .shift(UP * 2)
        )
        rectangle1 = SurroundingRectangle(image1, color=GRAY, stroke_width=2)
        image2 = (
            ImageMobject("images/mnist_conv2")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
            .to_edge(LEFT)
        )
        rectangle2 = SurroundingRectangle(image2, color=GRAY, stroke_width=2)
        image3 = (
            ImageMobject("images/mnist_conv3")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
            .to_edge(LEFT)
            .shift(DOWN * 2)
        )
        rectangle3 = SurroundingRectangle(image3, color=GRAY, stroke_width=2)

        image1 = Group(image1, rectangle1)
        image2 = Group(image2, rectangle2)
        image3 = Group(image3, rectangle3)

        self.play(FadeIn(image1, image2, image3))

        # Display the kernel

        matrix_content1 = np.random.rand(3, 3)
        matrix_content2 = np.random.rand(3, 3)
        matrix_content3 = np.random.rand(3, 3)

        filter_obj1 = self.create_matrix_filter(matrix_content1)
        filter_obj2 = self.create_matrix_filter(matrix_content2)
        filter_obj3 = self.create_matrix_filter(matrix_content3)

        # Rotate the filters to see them in perspective

        filter_obj1.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        filter_obj2.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        filter_obj3.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )

        filter_obj2.shift(LEFT * 0.25)
        filter_obj3.shift(-LEFT * 0.25)

        self.play(Create(filter_obj1))

        self.play(FadeIn(filter_obj2), FadeIn(filter_obj3))

        self.wait(0.5)

        # Send the filters next to the images

        self.play(
            Rotate(
                filter_obj1,
                -20 * DEGREES,
                axis=RIGHT,
                about_point=filter_obj1.get_center(),
            ),
            Rotate(
                filter_obj2,
                -20 * DEGREES,
                axis=RIGHT,
                about_point=filter_obj2.get_center(),
            ),
            Rotate(
                filter_obj3,
                -20 * DEGREES,
                axis=RIGHT,
                about_point=filter_obj3.get_center(),
            ),
        )

        self.play(
            Rotate(
                filter_obj1,
                85 * DEGREES,
                axis=UP,
                about_point=filter_obj1.get_center(),
            ),
            Rotate(
                filter_obj2,
                85 * DEGREES,
                axis=UP,
                about_point=filter_obj2.get_center(),
            ),
            Rotate(
                filter_obj3,
                85 * DEGREES,
                axis=UP,
                about_point=filter_obj3.get_center(),
            ),
        )

        self.play(
            LaggedStart(
                filter_obj1.animate.move_to(image1.get_right() + 2 * RIGHT).scale(0.6),
                filter_obj2.animate.move_to(image2.get_right() + 2 * RIGHT).scale(0.6),
                filter_obj3.animate.move_to(image3.get_right() + 2 * RIGHT).scale(0.6),
                lag_ratio=0.5,
            ),
        )

        ast1 = (
            MathTex(r"*")
            .scale(1)
            .move_to((image1.get_right() + filter_obj1.get_left()) / 2)
        )
        ast2 = (
            MathTex(r"*")
            .scale(1)
            .move_to((image2.get_right() + filter_obj2.get_left()) / 2)
        )
        ast3 = (
            MathTex(r"*")
            .scale(1)
            .move_to((image3.get_right() + filter_obj3.get_left()) / 2)
        )

        self.play(FadeIn(ast1, ast2, ast3))

        self.wait(0.5)

        # Display feature maps

        feature_map1 = (
            ImageMobject("images/mnist_conv1_2")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
            .next_to(filter_obj1.get_center() + 2 * RIGHT)
        )
        rectangle4 = SurroundingRectangle(feature_map1, color=GRAY, stroke_width=2)
        feature_map2 = (
            ImageMobject("images/mnist_conv2_2")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
            .next_to(filter_obj2.get_center() + 2 * RIGHT)
        )
        rectangle5 = SurroundingRectangle(feature_map2, color=GRAY, stroke_width=2)
        feature_map3 = (
            ImageMobject("images/mnist_conv3_2")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
            .next_to(filter_obj3.get_center() + 2 * RIGHT)
        )
        rectangle6 = SurroundingRectangle(feature_map3, color=GRAY, stroke_width=2)

        feature_map1 = Group(feature_map1, rectangle4)
        feature_map2 = Group(feature_map2, rectangle5)
        feature_map3 = Group(feature_map3, rectangle6)

        arrow1 = Arrow(filter_obj1.get_right(), feature_map1.get_left(), buff=0.2)
        arrow2 = Arrow(filter_obj2.get_right(), feature_map2.get_left(), buff=0.2)
        arrow3 = Arrow(filter_obj3.get_right(), feature_map3.get_left(), buff=0.2)

        self.play(
            FadeIn(feature_map1, feature_map2, feature_map3, arrow1, arrow2, arrow3),
        )

        self.wait(1.5)

        # Sum feature maps

        self.play(
            feature_map1.animate.shift(0.5 * UP),
            feature_map3.animate.shift(0.5 * DOWN),
        )

        plus1 = (
            MathTex(r"+")
            .scale(1)
            .move_to((feature_map1.get_bottom() + feature_map2.get_top()) / 2)
        )
        plus2 = (
            MathTex(r"+")
            .scale(1)
            .move_to((feature_map2.get_bottom() + feature_map3.get_top()) / 2)
        )

        self.play(Write(plus1), Write(plus2))

        # Merge feature maps and filter components

        sum_feature_map = (
            ImageMobject("images/mnist_sum")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
            .move_to(feature_map2.get_center())
        )
        rectangle7 = SurroundingRectangle(sum_feature_map, color=GRAY, stroke_width=2)

        sum_feature_map = Group(sum_feature_map, rectangle7)

        filter1_3d = Prism(dimensions=[2, 2, 1], fill_color=BLUE, stroke_width=1)
        filter1_3d.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        filter1_3d.move_to(filter_obj2.get_center())

        self.play(FadeOut(plus1, plus2))

        self.play(
            feature_map1.animate.move_to(sum_feature_map.get_center()),
            feature_map3.animate.move_to(sum_feature_map.get_center()),
            FadeOut(arrow1, arrow3, ast1, ast3),
        )

        self.play(
            FadeOut(feature_map1, feature_map2, feature_map3),
            FadeIn(sum_feature_map),
        )

        # Transform the filter to a 3D filter

        self.play(
            FadeOut(filter_obj1, filter_obj3),
            Transform(filter_obj2, filter1_3d),
        )

        # Brace with the dimensions of the filter

        brace = Brace(filter1_3d, DOWN)
        brace_txt = brace.get_text("3x3x3").scale(0.8)

        brace = VGroup(brace, brace_txt)

        self.play(FadeIn(brace))

        # FadeOut everything

        self.play(
            FadeOut(sum_feature_map, filter1_3d, brace, ast2, arrow2, filter_obj2),
            FadeOut(image1, image2, image3),
            run_time=1,
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene3_2()
    scene.render()
