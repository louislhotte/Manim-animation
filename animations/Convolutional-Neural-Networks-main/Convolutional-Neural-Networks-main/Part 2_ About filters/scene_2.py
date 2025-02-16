from manim import *
import matplotlib.pyplot as plt
import numpy as np


class Scene2_2(MovingCameraScene):
    def construct(self):
        self.wait(2)

        # Convolution formula animation

        sum = MathTex(
            r"(f * k)(i, j) = \sum_{m=0}^{M} \sum_{n=0}^{N} f(i, j) \cdot k(i - m, j - n)",
            font_size=42,
        )

        text_conv = Tex("Convolution Formula")

        self.play(FadeIn(text_conv))
        self.wait()

        self.play(
            LaggedStart(text_conv.animate.shift(DOWN * 2), Write(sum), lag_ratio=0.1),
        )
        self.wait(0.5)

        self.play(FadeOut(text_conv, sum))
        self.wait(0.5)

        # Filter animation

        matrix_content1 = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]

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
            matrix_grid.get_corner(UL),
            matrix_grid.get_corner(UR),
            color=GRAY,
            stroke_width=2,
        )
        bottomline = Line(
            matrix_grid.get_corner(DL),
            matrix_grid.get_corner(DR),
            color=GRAY,
            stroke_width=2,
        )
        leftline = Line(
            matrix_grid.get_corner(UL),
            matrix_grid.get_corner(DL),
            color=GRAY,
            stroke_width=2,
        )
        rightline = Line(
            matrix_grid.get_corner(UR),
            matrix_grid.get_corner(DR),
            color=GRAY,
            stroke_width=2,
        )

        filter = VGroup(matrix_grid, topline, bottomline, leftline, rightline)
        filter_text1 = VGroup()

        cell_width_filter = matrix_grid.get_x_unit_size()

        for i in range(0, 3):
            for j in range(0, 3):
                coords = matrix_grid.coords_to_point(j, i)

                val = matrix_content1[j][i]
                text = Tex(f"{val}")
                text.move_to(
                    coords + LEFT * cell_width_filter / 2 + DOWN * cell_width_filter / 2
                ).scale(0.5)
                filter_text1.add(text)
                self.wait(0.25)

        filter_obj1 = VGroup(filter, filter_text1)

        # Load the image

        img = ImageMobject("images/2_mnist.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        img.scale(30)
        img_values = plt.imread("images/2_mnist.png")[:, :]

        # Lattice going on top of the image

        lattice = NumberPlane(
            x_range=(-14, 14, 1),
            y_range=(-14, 14, 1),
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
        )

        lattice.scale(img.get_height() / lattice.get_height())

        # Create a TexMobject with the coordinate values
        values = []

        cell_width_lattice = lattice.get_x_unit_size()
        for i in range(-14, 14):
            for j in range(-13, 15):

                val = int(img_values[14 - j][14 + i] * 255)
                text = Tex(f"{val}")

                coords = lattice.coords_to_point(i, j)
                text.move_to(
                    coords
                    + RIGHT * cell_width_lattice / 2
                    + DOWN * cell_width_lattice / 2
                ).scale(img.get_height() / 28)

                values.append(text)

        # Add the lines

        lattice_topline = Line(
            lattice.get_corner(UL), lattice.get_corner(UR), color=GRAY, stroke_width=2
        )
        lattice_bottomline = Line(
            lattice.get_corner(DL), lattice.get_corner(DR), color=GRAY, stroke_width=2
        )
        lattice_leftline = Line(
            lattice.get_corner(UL), lattice.get_corner(DL), color=GRAY, stroke_width=2
        )
        lattice_rightline = Line(
            lattice.get_corner(UR), lattice.get_corner(DR), color=GRAY, stroke_width=2
        )

        lattice = VGroup(
            lattice,
            lattice_topline,
            lattice_bottomline,
            lattice_leftline,
            lattice_rightline,
        )

        # Add the values to the scene
        values = VGroup(*values)

        self.play(
            Create(filter_obj1),
        )
        self.play(
            filter_obj1.animate.move_to(img.get_left() + 3 * LEFT + UP).scale(
                cell_width_lattice / cell_width_filter
            ),
        )
        self.play(FadeIn(img, lattice))

        # Pan camera to the top of the image

        self.play(
            self.camera.frame.animate.scale(0.5).move_to(img.get_left()),
        )

        filter_text3 = filter_text1.copy()

        # Filter weights

        cell_width_filter = matrix_grid.get_x_unit_size()

        filter_text2 = VGroup()

        # Constants
        scale_factor = 0.2
        offset = LEFT * cell_width_filter / 2 + DOWN * cell_width_filter / 2

        # Values in the filter matrix, assuming top-left to bottom-right fill
        filter_values = [
            [7, 8, 9],  # Top row
            [4, 5, 6],  # Middle row
            [1, 2, 3],  # Bottom row
        ]

        for i, row in enumerate(filter_values):
            for j, val in enumerate(row):
                # Calculate position
                coords = matrix_grid.coords_to_point(j, i)
                # Create and configure the text object
                text = (
                    Tex(f"$w_{{{val}}}$").move_to(coords + offset).scale(scale_factor)
                )
                # Add to the group
                filter_text2.add(text)

        self.play(Transform(filter_text1, filter_text2), run_time=1)

        # Transform image into values

        self.play(FadeOut(img), FadeIn(values), run_time=1)

        # Filter and latice highlight

        connection_line1 = Line(
            filter.get_corner(UR),
            lattice.get_corner(UL)
            + 15 * DOWN * cell_width_lattice
            + 13 * RIGHT * cell_width_lattice,
            stroke_color=RED,
            stroke_width=2,
        )
        connection_line2 = Line(
            filter.get_corner(DR),
            lattice.get_corner(UL)
            + 18 * DOWN * cell_width_lattice
            + 13 * RIGHT * cell_width_lattice,
            stroke_color=RED,
            stroke_width=2,
        )

        topline_filter = Line(
            matrix_grid.get_corner(UL),
            matrix_grid.get_corner(UR),
            color=RED,
            stroke_width=2,
        )
        bottomline_filter = Line(
            matrix_grid.get_corner(DL),
            matrix_grid.get_corner(DR),
            color=RED,
            stroke_width=2,
        )
        leftline_filter = Line(
            matrix_grid.get_corner(UL),
            matrix_grid.get_corner(DL),
            color=RED,
            stroke_width=2,
        )
        rightline_filter = Line(
            matrix_grid.get_corner(UR),
            matrix_grid.get_corner(DR),
            color=RED,
            stroke_width=2,
        )

        highlight_filter = VGroup(
            topline_filter, bottomline_filter, leftline_filter, rightline_filter
        )

        topline_latice = Line(
            lattice.get_corner(UL)
            + 15 * DOWN * cell_width_lattice
            + 13 * RIGHT * cell_width_lattice,
            lattice.get_corner(UL)
            + 15 * DOWN * cell_width_lattice
            + 16 * RIGHT * cell_width_lattice,
            color=RED,
            stroke_width=2,
        )
        bottomline_lattice = Line(
            lattice.get_corner(UL)
            + 18 * DOWN * cell_width_lattice
            + 13 * RIGHT * cell_width_lattice,
            lattice.get_corner(UL)
            + 18 * DOWN * cell_width_lattice
            + 16 * RIGHT * cell_width_lattice,
            color=RED,
            stroke_width=2,
        )
        leftline_lattice = Line(
            lattice.get_corner(UL)
            + 15 * DOWN * cell_width_lattice
            + 13 * RIGHT * cell_width_lattice,
            lattice.get_corner(UL)
            + 18 * DOWN * cell_width_lattice
            + 13 * RIGHT * cell_width_lattice,
            color=RED,
            stroke_width=2,
        )
        rightline_lattice = Line(
            lattice.get_corner(UL)
            + 15 * DOWN * cell_width_lattice
            + 16 * RIGHT * cell_width_lattice,
            lattice.get_corner(UL)
            + 18 * DOWN * cell_width_lattice
            + 16 * RIGHT * cell_width_lattice,
            color=RED,
            stroke_width=2,
        )

        highlight_lattice = VGroup(
            topline_latice, bottomline_lattice, leftline_lattice, rightline_lattice
        )

        # Convolution computation

        formula = MathTex(
            r"&0 {{w_1}} + 184 {{w_2}} + 253 {{w_3}} \\\\ \
                          + &107 {{w_4}} + 255 {{w_5}} + 211 {{w_6}} \\\\ \
                          + &212 {{w_7}} + 254 {{w_8}} + 98 {{w_9}}",
            font_size=12,
        )

        formula.move_to(filter_obj1.get_bottom() + DOWN + 0.5 * RIGHT)

        self.play(
            Create(highlight_filter),
            Create(highlight_lattice),
        )
        self.play(
            Write(connection_line1),
            Write(connection_line2),
        )
        self.play(Create(formula))

        formula_target = MathTex(
            r"&0 \cdot 1 + 184 \cdot 1 + 253 \cdot 1 \\\\ \
                                    + &107 \cdot 1 + 255 \cdot 1 + 211 \cdot 1 \\\\ \
                                    + &212 \cdot 1 + 254 \cdot 1 + 98 \cdot 1",
            font_size=12,
        ).move_to(formula.get_center())

        self.wait(0.8)

        self.play(
            LaggedStart(
                Transform(filter_text1, filter_text3),
                Transform(formula, formula_target),
                lag_ratio=0.3,
            ),
            run_time=1,
        )

        divide_line = Line(
            formula.get_corner(DL) + 0.2 * DOWN,
            formula.get_corner(DR) + 0.2 * DOWN,
            color=WHITE,
            stroke_width=2,
        )

        normalization = MathTex(r"9 * 1", font_size=12).next_to(
            divide_line, DOWN, buff=0.2
        )

        self.play(
            LaggedStart(Create(divide_line), Write(normalization), lag_ratio=0.2),
        )

        result = MathTex(r"= 175", font_size=12).next_to(normalization, DOWN, buff=0.2) # (0+184+253+107+255+211+212+254+98) / 9*1=175

        self.play(Write(result))
        self.wait()

        formula = VGroup(formula, divide_line, normalization, result)

        self.play(FadeOut(formula), run_time=2)

        # Get back to the original position

        self.play(
            LaggedStart(
                self.camera.frame.animate.move_to(ORIGIN).scale(2),
                FadeOut(
                    highlight_filter,
                    highlight_lattice,
                    connection_line1,
                    connection_line2,
                ),
                FadeOut(filter_obj1),
                lag_ratio=0.1,
            ),
        )

        self.play(FadeOut(values, lattice), run_time=1)

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene2_2()
    scene.render()
