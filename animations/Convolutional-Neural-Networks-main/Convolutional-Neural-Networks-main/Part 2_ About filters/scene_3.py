from manim import *
import matplotlib.pyplot as plt
import numpy as np


class Scene2_3(MovingCameraScene):
    def construct(self):

        self.wait(2)

        img = ImageMobject("images/2_mnist.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        img.scale(30)
        img_values = plt.imread("images/2_mnist.png")[:, :, 0]

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

        lattice_rectangle = Rectangle(
            height=cell_width_lattice * 28,
            width=cell_width_lattice * 28,
            color=GRAY,
            stroke_width=2,
        )

        lattice = VGroup(lattice, lattice_rectangle)
        values = VGroup(*values)

        # Display the three parameters

        text_size = Tex("Kernel Size", color=WHITE)
        text_stride = Tex("Stride", color=WHITE)
        text_padding = Tex("Padding", color=WHITE)

        text_obj = (
            VGroup(text_size, text_stride, text_padding)
            .arrange(RIGHT, buff=1)
            .move_to(ORIGIN)
        )

        self.play(
            FadeIn(text_size, text_stride, text_padding),
        )

        self.play(
            Indicate(text_size, color=WHITE),
        )
        self.play(
            Indicate(text_stride, color=WHITE),
        )
        self.play(
            Indicate(text_padding, color=WHITE),
        )

        # Start with the size

        self.play(
            LaggedStart(
                FadeOut(text_stride),
                FadeOut(text_padding),
                text_size.animate.move_to(ORIGIN),
                lag_ratio=0.1,
            ),
        )
        self.play(FadeOut(text_size))

        # Display the image and zoom at the top

        self.play(FadeIn(lattice, values), run_time=1)
        self.play(
            self.camera.frame.animate.scale(0.5).move_to(lattice.get_top()), run_time=2
        )

        # Highlight the neighborhood of the pixel

        rect_width = 3 * cell_width_lattice
        rect_height = 3 * cell_width_lattice

        # Create a rectangle
        filter1 = Rectangle(
            width=rect_width, height=rect_height, color=RED, stroke_width=2
        ).move_to(
            lattice.get_corner(UL)
            + 11.5 * cell_width_lattice * RIGHT
            + 1.5 * cell_width_lattice * DOWN
        )

        filter = filter1.copy()

        width_brace = Brace(
            filter, direction=UP, color=WHITE, stroke_width=0.3
        ).stretch(0.5, dim=1)
        width_brace_obj = VGroup(
            width_brace, width_brace.get_text("Size = 3", buff=0.1).scale(0.5)
        )

        center1 = Rectangle(
            width=cell_width_lattice,
            height=cell_width_lattice,
            color=YELLOW,
            stroke_width=2,
        ).move_to(
            lattice.get_corner(UL)
            + 11.5 * cell_width_lattice * RIGHT
            + 1.5 * cell_width_lattice * DOWN
        )

        # Change size of the filter

        rect_width2 = 5 * cell_width_lattice
        rect_height2 = 5 * cell_width_lattice

        filter2 = Rectangle(
            width=rect_width2, height=rect_height2, color=RED, stroke_width=2
        ).move_to(
            lattice.get_corner(UL)
            + 11.5 * cell_width_lattice * RIGHT
            + 1.5 * cell_width_lattice * DOWN
        )

        width_brace2 = Brace(
            filter2, direction=UP, color=WHITE, stroke_width=0.3
        ).stretch(0.5, dim=1)
        width_brace_obj2 = VGroup(
            width_brace2, width_brace2.get_text("Size = 5", buff=0.1).scale(0.5)
        )

        self.play(
            LaggedStart(
                Create(center1),
                Create(filter),
                FadeIn(width_brace_obj),
                lag_ratio=0.1,
            ),
        )
        self.play(
            Transform(filter, filter2),
            Transform(width_brace_obj, width_brace_obj2),
        )

        # Go back to size 3

        self.play(Transform(filter, filter1), FadeOut(width_brace_obj), run_time=1)

        # Animation for stride 1

        center2 = Rectangle(
            width=cell_width_lattice,
            height=cell_width_lattice,
            color=YELLOW,
            stroke_width=2,
        ).move_to(
            lattice.get_corner(UL)
            + 11.5 * cell_width_lattice * RIGHT
            + 1.5 * cell_width_lattice * DOWN
            + cell_width_lattice * RIGHT
        )

        left_dashed_line = DashedLine(
            center1.get_center(),
            center1.get_center() + UP,
            color=YELLOW,
            stroke_width=2,
        )
        right_dashed_line = DashedLine(
            center2.get_center(),
            center2.get_center() + UP,
            color=YELLOW,
            stroke_width=2,
        )

        stride_brace = BraceBetweenPoints(
            left_dashed_line.get_top() + 0.1 * DOWN,
            right_dashed_line.get_top() + 0.1 * DOWN,
            direction=UP,
            color=WHITE,
            stroke_width=0.3,
        ).stretch(0.3, dim=1)
        stride_brace_txt = stride_brace.get_text("Stride = 1", buff=0.1).scale(0.5)

        self.play(Create(center2), run_time=1)

        self.play(
            LaggedStart(
                Create(left_dashed_line),
                Create(right_dashed_line),
                Create(stride_brace),
                Write(stride_brace_txt),
                lag_ratio=0.05,
            ),
        )

        self.play(
            filter.animate.shift(cell_width_lattice * RIGHT),
        )
        self.play(
            filter.animate.shift(cell_width_lattice * RIGHT),
        )
        self.play(
            filter.animate.shift(cell_width_lattice * LEFT),
        )
        self.play(
            filter.animate.shift(cell_width_lattice * LEFT),
        )

        # Animation for stride 2

        stride_brace2 = BraceBetweenPoints(
            left_dashed_line.get_top() + 0.1 * DOWN,
            right_dashed_line.get_top() + 0.1 * DOWN + cell_width_lattice * RIGHT,
            direction=UP,
            color=WHITE,
            stroke_width=0.3,
        ).stretch(0.3, dim=1)
        stride_brace_txt2 = stride_brace2.get_text("Stride = 2", buff=0.1).scale(0.5)

        self.play(
            center2.animate.shift(cell_width_lattice * RIGHT),
            right_dashed_line.animate.shift(cell_width_lattice * RIGHT),
            LaggedStart(
                Transform(stride_brace, stride_brace2),
                Transform(stride_brace_txt, stride_brace_txt2),
                lag_ratio=0.05,
            ),
        )

        self.play(
            filter.animate.shift(2 * cell_width_lattice * RIGHT),
        )
        self.play(
            filter.animate.shift(2 * cell_width_lattice * RIGHT),
        )
        self.play(
            filter.animate.shift(2 * cell_width_lattice * LEFT),
        )
        self.play(
            filter.animate.shift(2 * cell_width_lattice * LEFT),
        )

        self.play(
            FadeOut(stride_brace),
            FadeOut(stride_brace_txt),
            FadeOut(center2),
            FadeOut(left_dashed_line),
            FadeOut(right_dashed_line),
            run_time=1,
        )

        # Animation for padding

        self.play(Transform(filter, filter2), run_time=1)

        lines = []
        padding_text = []
        for i in range(4):
            vertical_line = Line(
                start=filter.get_corner(UL)
                + cell_width_lattice * DOWN
                + (i + 1) * cell_width_lattice * RIGHT,
                end=filter.get_corner(UL) + (i + 1) * cell_width_lattice * RIGHT,
                color=GRAY,
                stroke_width=2,
            )
            lines.append(vertical_line)
            text = (
                Tex("?", color=WHITE)
                .scale(img.get_height() / 28)
                .move_to(vertical_line.get_center() + (cell_width_lattice / 2) * LEFT)
            )
            padding_text.append(text)

            if i == 3:
                text = (
                    Tex("?", color=WHITE)
                    .scale(img.get_height() / 28)
                    .move_to(
                        vertical_line.get_center() + (cell_width_lattice / 2) * RIGHT
                    )
                )
                padding_text.append(text)

        padding_text_obj = VGroup(*padding_text)

        self.play(
            LaggedStart(*[Create(line) for line in lines], lag_ratio=0.05),
        )
        self.play(
            LaggedStart(*[Create(text) for text in padding_text], lag_ratio=0.05),
        )

        self.play(
            Indicate(padding_text_obj, scale_factor=1.1),
        )

        # Zero padding

        zero_padding = (
            Tex("Zero Padding", color=WHITE)
            .scale(0.5)
            .next_to(filter, direction=UP, buff=0.5)
        )

        zero_padding_text = []
        for i in range(5):
            text = (
                Tex("0", color=WHITE)
                .scale(img.get_height() / 28)
                .move_to(padding_text[i].get_center())
            )
            zero_padding_text.append(text)

        zero_padding_text_obj = VGroup(*zero_padding_text)

        self.play(Write(zero_padding))

        self.play(
            Transform(padding_text_obj, zero_padding_text_obj),
        )

        self.play(FadeOut(zero_padding), run_time=1)

        # Constant padding

        constant_padding = (
            Tex("Constant Padding", color=WHITE)
            .scale(0.5)
            .next_to(filter, direction=UP, buff=0.5)
        )

        constant_padding_text = []
        for i in range(5):
            text = (
                Tex("1", color=WHITE)
                .scale(img.get_height() / 28)
                .move_to(padding_text[i].get_center())
            )
            constant_padding_text.append(text)

        constant_padding_text_obj = VGroup(*constant_padding_text)

        self.play(
            Write(constant_padding),
        )

        self.play(
            Transform(padding_text_obj, constant_padding_text_obj),
        )

        self.play(FadeOut(constant_padding), run_time=1)

        # Reflect padding

        reflect_padding = (
            Tex("Reflect Padding", color=WHITE)
            .scale(0.5)
            .next_to(filter, direction=UP, buff=0.5)
        )

        self.play(Write(reflect_padding))
        self.play(
            Transform(padding_text_obj, zero_padding_text_obj),
        )

        self.play(FadeOut(reflect_padding))
        self.wait()

        # Clean up and camera goes back to origin

        self.play(
            LaggedStart(
                FadeOut(center1),
                FadeOut(filter),
                FadeOut(VGroup(*lines)),
                FadeOut(padding_text_obj),
                lag_ratio=0.05,
            ),
            self.camera.frame.animate.scale(2).move_to(ORIGIN),
            run_time=2,
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene2_3()
    scene.render()
