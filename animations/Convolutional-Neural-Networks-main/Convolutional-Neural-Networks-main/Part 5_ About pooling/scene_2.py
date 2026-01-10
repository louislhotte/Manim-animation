from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene5_2(VoiceoverScene, MovingCameraScene):
    def create_matrix_filter(self, matrix_content):
        matrix_grid = NumberPlane(
            x_range=[-1, 1],
            y_range=[-1, 1],
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
        for i in range(2):
            for j in range(2):
                coords = matrix_grid.coords_to_point(j, i)
                val = matrix_content[j][i]
                text = Tex(f"{val:.0f}", color=BLUE)
                text.move_to(
                    coords + LEFT * cell_width_filter / 2 + DOWN * cell_width_filter / 2
                ).scale(0.5)
                filter_text.add(text)

        return matrix_grid, filter_text, rectangle

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

        img = ImageMobject("images/0_mnist.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        img.scale(30)
        img_values = plt.imread("images/0_mnist.png")[:, :, 0]

        pool_img = ImageMobject("images/0_mnist_pooled.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        pool_img.scale(30)
        blur_image_values = plt.imread("images/0_mnist_pooled.png")

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

        lattice_img_pool = NumberPlane(
            x_range=(-7, 7, 1),
            y_range=(-7, 7, 1),
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

        lattice_img_pool.scale(pool_img.get_height() / lattice_img_pool.get_height())
        cell_width_lattice = lattice_img_pool.get_x_unit_size()

        lattice_img_pool_rectangle = Rectangle(
            height=cell_width_lattice * 14,
            width=cell_width_lattice * 14,
            color=GRAY,
            stroke_width=2,
        )
        lattice_img_pool_obj = VGroup(
            lattice_img_pool, lattice_img_pool_rectangle
        ).shift(4 * RIGHT)

        # Display the images

        self.play(
            FadeIn(img),
            FadeIn(lattice_img_obj),
        )

        self.wait()
        self.play(
            lattice_img_obj.animate.shift(4 * LEFT).scale(0.6),
            img.animate.shift(4 * LEFT).scale(0.6),
        )

        # Display the kernel

        matrix_content1 = [
            [1, 1],
            [1, 1],
        ]

        matrix_grid, filter_text1, filter_rectangle = self.create_matrix_filter(
            matrix_content1
        )
        filter_obj1 = VGroup(matrix_grid, filter_text1, filter_rectangle)
        filter_obj1.shift(RIGHT * 2).scale(2)

        # Display the parameters

        text_stride = Tex("Stride: 2").scale(0.9)
        text_width = Tex("Width: 2").scale(0.9).next_to(text_stride, LEFT)

        parameters = VGroup(text_stride, text_width)
        parameters.move_to(ORIGIN + 3 * UP)

        self.play(FadeIn(parameters), run_time=1)

        self.play(FadeIn(filter_obj1), run_time=1)

        # Move the kernel to the image

        cell_width_lattice = lattice_img.get_x_unit_size()
        cell_width_lattice_pool = lattice_img_pool.get_x_unit_size()
        cell_width_filter = matrix_grid.get_x_unit_size()

        coords = (
            lattice_img.get_corner(UL)
            + cell_width_lattice * RIGHT
            + cell_width_lattice * DOWN
        )
        self.play(
            filter_obj1.animate.move_to(coords).scale(
                cell_width_lattice / cell_width_filter
            ),
            run_time=1,
        )

        # Create individual pixels of the blurred image

        self.play(filter_obj1.animate.set_color(RED), run_time=0.3)

        rectangle_pool = Rectangle(
            height=cell_width_lattice_pool,
            width=cell_width_lattice_pool,
            color=RED,
            stroke_width=2,
        ).move_to(
            lattice_img_pool.get_corner(UL)
            + 0.5 * cell_width_lattice_pool * RIGHT
            + 0.5 * cell_width_lattice_pool * DOWN
        )

        kernel_top_line = Line(
            filter_obj1.get_corner(UR),
            rectangle_pool.get_corner(UL),
            color=RED,
            stroke_width=2,
        ).add_updater(
            lambda l: l.become(
                Line(
                    filter_obj1.get_corner(UR),
                    rectangle_pool.get_corner(UL),
                    color=RED,
                    stroke_width=2,
                )
            )
        )

        kernel_bottom_line = Line(
            filter_obj1.get_corner(DR),
            rectangle_pool.get_corner(DL),
            color=RED,
            stroke_width=2,
        ).add_updater(
            lambda l: l.become(
                Line(
                    filter_obj1.get_corner(DR),
                    rectangle_pool.get_corner(DL),
                    color=RED,
                    stroke_width=2,
                )
            )
        )

        kernel_top_line.z_index = 1
        kernel_bottom_line.z_index = 1

        self.play(Create(kernel_top_line), Create(kernel_bottom_line), run_time=1)
        self.play(Create(rectangle_pool), run_time=1)
        self.play(FadeIn(lattice_img_pool_obj), run_time=1)

        self.wait(2)

        pixels = VGroup()

        for y in range(14):

            for x in range(14):

                self.play(
                    filter_obj1.animate.shift(2 * cell_width_lattice * RIGHT),
                    rectangle_pool.animate.shift(cell_width_lattice_pool * RIGHT),
                    run_time=0.05,
                )

                # Map the intensity to a grayscale value (0 to 1)
                intensity = blur_image_values[y, x]
                color = interpolate_color(BLACK, WHITE, intensity)

                # Calculate the position based on the lattice
                pos = (
                    lattice_img_pool.get_corner(UL)
                    + (x + 0.5) * cell_width_lattice_pool * RIGHT
                    + (y + 0.5) * cell_width_lattice_pool * DOWN
                )

                # Create a rectangle for the pixel
                pixel_rect = Rectangle(
                    width=cell_width_lattice_pool,
                    height=cell_width_lattice_pool,
                    fill_color=color,
                    fill_opacity=1,
                    stroke_width=0.1,
                ).move_to(pos)

                # Add the rectangle to the scene
                pixels.add(pixel_rect)
                self.add(pixel_rect)

            if y == 13:
                break

        self.play(
            filter_obj1.animate.shift(
                28 * cell_width_lattice * LEFT + 2 * cell_width_lattice * DOWN
            ),
            rectangle_pool.animate.shift(
                14 * cell_width_lattice_pool * LEFT + cell_width_lattice_pool * DOWN
            ),
            run_time=0.05,
        )

        self.play(
            FadeOut(
                filter_obj1,
                filter_text1,
                kernel_top_line,
                kernel_bottom_line,
                rectangle_pool,
            ),
            FadeOut(text_width),
            FadeOut(text_stride),
        )

        self.play(
            FadeOut(lattice_img),
            FadeOut(img),
            FadeOut(lattice_img_rectangle),
            run_time=1,
        )

        # Move the pooled img to the center

        self.play(
            lattice_img_pool_obj.animate.move_to(ORIGIN),
            pixels.animate.move_to(ORIGIN),
        )

        # Brace to indicate the width and height

        brace_width = Brace(lattice_img_pool, direction=UP, color=WHITE)
        brace_width_txt = brace_width.get_text("Width = 14", buff=0.1).scale(0.5)

        brace_height = Brace(lattice_img_pool, direction=LEFT, color=WHITE)
        brace_height_txt = brace_height.get_text("Height = 14", buff=0.1).scale(0.5)

        self.play(
            Create(brace_width),
            Create(brace_height),
            FadeIn(brace_width_txt),
            FadeIn(brace_height_txt),
        )

        self.play(
            FadeOut(
                pixels,
                lattice_img_pool_obj,
                brace_height,
                brace_width,
                brace_height_txt,
                brace_width_txt,
            ),
        )

        txt = Tex("Receptive field", color=WHITE)
        self.play(Write(txt))

        txt_target = Tex("Like and subscribe !").scale(2)
        self.play(Transform(txt, txt_target))
        self.play(FadeOut(txt))

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene5_2()
    scene.render()
