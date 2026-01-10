from manim import *
import matplotlib.pyplot as plt
import numpy as np


class Scene2_1(Scene):
    def construct(self):
        matrix_content1 = [[0, 2, 9], [4, 3, 1], [-1, 4, 2]]

        matrix_grid = NumberPlane(
            x_range=[-1, 2],  # These ranges cover 3 units on the x-axis
            y_range=[-1, 2],  # And 3 units on the y-axis
            x_length=2,  # Width of the plane
            y_length=2,  # Height of the plane
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
            faded_line_ratio=0,  # Disable fading of grid lines
        ).move_to(ORIGIN)

        topline = Line(
            matrix_grid.get_corner(UL), matrix_grid.get_corner(UR), color=GRAY
        )
        bottomline = Line(
            matrix_grid.get_corner(DL), matrix_grid.get_corner(DR), color=GRAY
        )
        leftline = Line(
            matrix_grid.get_corner(UL), matrix_grid.get_corner(DL), color=GRAY
        )
        rightline = Line(
            matrix_grid.get_corner(UR), matrix_grid.get_corner(DR), color=GRAY
        )

        filter = VGroup(matrix_grid, topline, bottomline, leftline, rightline)
        filter_text1 = VGroup()

        cell_width = matrix_grid.get_x_unit_size()

        for i in range(0, 3):
            for j in range(0, 3):
                coords = matrix_grid.coords_to_point(i, j)

                val = matrix_content1[j][i]
                text = Tex(f"{val}")
                text.move_to(
                    coords + LEFT * cell_width / 2 + DOWN * cell_width / 2
                ).scale(0.5)
                filter_text1.add(text)

        self.wait(2)

        text21 = Tex("What is a filter ?")
        self.play(Write(text21))

        self.wait(0.5)

        self.play(FadeOut(text21))
        filter_title = Tex("Filter").scale(0.5).next_to(filter, DOWN)

        self.play(
            FadeIn(filter, filter_text1, filter_title),
        )

        self.wait()

        img_ref = ImageMobject("images/flower.jpg").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["none"]
        )
        img_ref_rect = SurroundingRectangle(
            img_ref, buff=0, color=WHITE, stroke_width=2
        )
        img_ref = Group(img_ref, img_ref_rect)
        img_ref.next_to(filter, LEFT, buff=3.0)

        img_edge_x = ImageMobject("images/edge_x_flower.jpg").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["none"]
        )
        img_edge_x_rect = SurroundingRectangle(
            img_edge_x, buff=0, color=WHITE, stroke_width=2
        )
        img_edge_x = Group(img_edge_x, img_edge_x_rect)
        img_edge_x.shift(RIGHT * 3.5 + 2 * DOWN)

        img_blur = ImageMobject("images/blur_flower.jpg").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["none"]
        )
        img_blur_rect = SurroundingRectangle(
            img_blur, buff=0, color=WHITE, stroke_width=2
        )
        img_blur = Group(img_blur, img_blur_rect)
        img_blur.shift(RIGHT * 3.5 + 2 * UP)

        self.play(
            filter.animate.shift(LEFT),
            filter_text1.animate.shift(LEFT),
            filter_title.animate.shift(LEFT),
        )

        self.play(FadeIn(img_ref))

        ast = MathTex(r"\ast").scale(2).next_to(img_ref, RIGHT, buff=0.8)

        self.play(Write(ast))
        self.play(Indicate(ast, scale_factor=1.5))

        # Blur filter animation

        filter_text2 = VGroup()
        matrix_content2 = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]

        for i in range(0, 3):
            for j in range(0, 3):
                coords = matrix_grid.coords_to_point(i, j)

                val = matrix_content2[j][i]
                text = Tex(f"{val}")
                text.move_to(
                    coords + LEFT * cell_width / 2 + DOWN * cell_width / 2
                ).scale(0.5)
                filter_text2.add(text)

        arrow_blur = Arrow(
            filter.get_right(), img_blur.get_left(), color=WHITE, stroke_width=2
        )

        self.play(
            LaggedStart(
                GrowArrow(arrow_blur),
                FadeIn(img_blur),
                Transform(filter_text1, filter_text2),
                lag_ratio=0.05,
            ),
        )

        # Sobel filter animation

        filter_text3 = VGroup()
        matrix_content3 = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]

        for i in range(0, 3):
            for j in range(0, 3):
                coords = matrix_grid.coords_to_point(i, j)

                val = matrix_content3[j][i]
                text = Tex(f"{val}")
                text.move_to(
                    coords + LEFT * cell_width / 2 + DOWN * cell_width / 2
                ).scale(0.5)
                filter_text3.add(text)

        arrow_sobel = Arrow(
            filter.get_right(), img_edge_x.get_left(), color=WHITE, stroke_width=2
        )

        self.play(
            LaggedStart(
                GrowArrow(arrow_sobel),
                FadeIn(img_edge_x),
                Transform(filter_text1, filter_text3),
                lag_ratio=0.05,
            ),
        )

        self.play(
            FadeOut(
                filter,
                filter_text1,
                filter_title,
                img_ref,
                img_edge_x,
                img_blur,
                ast,
                arrow_blur,
                arrow_sobel,
            ),
            run_time=1,
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene2_1()
    scene.render()
