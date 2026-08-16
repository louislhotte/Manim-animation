from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene2_4(VoiceoverScene, MovingCameraScene):
    def construct(self):

        self.wait(2)

        img = ImageMobject("images/0_mnist.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        img.scale(30)
        img_values = plt.imread("images/0_mnist.png")[:, :, 0]

        blur_img = ImageMobject("images/blur_0_mnist.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        blur_img.scale(30)
        blur_image_values = plt.imread("images/blur_0_mnist.png")

        # Lattice going on top of the image

        lattice_img = NumberPlane(
            x_range=(-14, 14, 1),
            y_range=(-14, 14, 1),
            background_line_style={
                "stroke_color": GRAY,
                "stroke_width": 1,
                "stroke_opacity": 1,
            },
            axis_config={
                "stroke_color": GRAY,
                "stroke_width": 1,
                "include_numbers": False,
            },
            faded_line_ratio=0,  # Disable fading of grid lines
        )

        lattice_img.scale(img.get_height() / lattice_img.get_height())
        cell_width_lattice = lattice_img.get_x_unit_size()

        lattice_img_rectangle = Rectangle(
            height=cell_width_lattice * 28,
            width=cell_width_lattice * 28,
            color=GRAY,
            stroke_width=2,
        )
        lattice_img_obj = VGroup(lattice_img, lattice_img_rectangle)

        # Lattice going on top of the blurred image

        lattice_blur_img = NumberPlane(
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

        lattice_blur_img.scale(blur_img.get_height() / lattice_blur_img.get_height())
        cell_width_lattice = lattice_blur_img.get_x_unit_size()

        lattice_blur_img_rectangle = Rectangle(
            height=cell_width_lattice * 28,
            width=cell_width_lattice * 28,
            color=GRAY,
            stroke_width=2,
        )
        lattice_blur_img_obj = VGroup(lattice_blur_img, lattice_blur_img_rectangle)

        # Display the images

        self.play(FadeIn(img), FadeIn(lattice_img_obj))

        self.play(
            lattice_img_obj.animate.shift(4 * LEFT + DOWN).scale(0.6),
            img.animate.shift(4 * LEFT + DOWN).scale(0.6),
            run_time=2,
        )

        lattice_blur_img_obj.shift(4 * RIGHT + DOWN).scale(0.6)
        blur_img.shift(4 * RIGHT + DOWN).scale(0.6)

        # Display the kernel

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
                text = Tex(f"{val}", color=BLUE)
                text.move_to(
                    coords + LEFT * cell_width_filter / 2 + DOWN * cell_width_filter / 2
                ).scale(0.5)
                filter_text1.add(text)

        filter_obj1 = VGroup(filter, filter_text1)
        filter_obj1.shift(ORIGIN).scale(1.0)

        # Display the parameters

        text_stride = Tex("Stride: 1").scale(0.5).shift(3 * UP)
        text_width = Tex("Width: 3").scale(0.5).next_to(text_stride, LEFT)
        text_padding = Tex("Padding: 0").scale(0.5).next_to(text_stride, RIGHT)

        self.play(
            LaggedStart(
                FadeIn(text_width),
                FadeIn(text_stride),
                FadeIn(text_padding),
                lag_ratio=0.1,
            ),
        )

        self.play(FadeIn(filter_obj1))

        # Move the kernel to the image

        cell_width_lattice = lattice_img.get_x_unit_size()
        cell_width_filter = matrix_grid.get_x_unit_size()

        coords = (
            lattice_img.get_corner(UL)
            + 0.5 * cell_width_lattice * RIGHT
            + 0.5 * cell_width_lattice * DOWN
        )
        self.play(
            filter_obj1.animate.move_to(coords).scale(
                cell_width_lattice / cell_width_filter
            ),
            run_time=2,
        )

        # Create lattice and rectangle of blurred image

        self.play(FadeIn(lattice_blur_img_obj), run_time=1)

        # Create individual pixels of the blurred image

        cell_width_lattice = lattice_blur_img.get_x_unit_size()

        self.play(filter_obj1.animate.set_color(RED), run_time=0.1)

        kernel_top_line = Line(
            filter_obj1.get_corner(UR),
            lattice_blur_img.get_corner(UL),
            color=RED,
            stroke_width=2,
        )
        kernel_bottom_line = Line(
            filter_obj1.get_corner(DR),
            lattice_blur_img.get_corner(UL) + DOWN * cell_width_lattice,
            color=RED,
            stroke_width=2,
        )
        kernel_top_line.z_index = 1
        kernel_bottom_line.z_index = 1

        self.play(Create(kernel_top_line), Create(kernel_bottom_line), run_time=1)
        filter_obj1.add(kernel_top_line, kernel_bottom_line)

        pixels = VGroup()

        for y in range(28):
            for x in range(28):

                self.play(
                    filter_obj1.animate.shift(cell_width_lattice * RIGHT),
                    run_time=0.001,
                )

                # Map the intensity to a grayscale value (0 to 1)
                intensity = blur_image_values[y, x]
                color = interpolate_color(BLACK, WHITE, intensity)

                # Calculate the position based on the lattice
                pos = (
                    lattice_blur_img.get_corner(UL)
                    + (x + 0.5) * cell_width_lattice * RIGHT
                    + (y + 0.5) * cell_width_lattice * DOWN
                )

                # Create a rectangle for the pixel
                pixel_rect = Rectangle(
                    width=cell_width_lattice,
                    height=cell_width_lattice,
                    fill_color=color,
                    fill_opacity=1,
                    stroke_width=0.1,
                ).move_to(pos)

                # Add the rectangle to the scene
                pixels.add(pixel_rect)
                self.add(pixel_rect)

            if y == 27:
                break

            self.play(
                filter_obj1.animate.shift(
                    28 * cell_width_lattice * LEFT + cell_width_lattice * DOWN
                ),
                run_time=0.1,
            )

        self.play(
            FadeOut(filter, filter_text1, kernel_top_line, kernel_bottom_line),
            FadeOut(text_width),
            FadeOut(text_stride),
            FadeOut(text_padding),
        )

        self.play(FadeOut(pixels, lattice_blur_img_obj))
        self.play(
            FadeOut(lattice_img),
            FadeOut(img),
            FadeOut(lattice_img_rectangle),
        )

        text = Tex(
            "How to integrate filters into neural networks ?", color=WHITE
        ).scale(0.7)

        self.play(Create(text))

        self.wait(1)

        self.play(FadeOut(text), run_time=1)

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene2_4()
    scene.render()
