from manim import *
import matplotlib.pyplot as plt
import math


class Scene1_2(Scene):
    def construct(self):

        input_img = (
            ImageMobject("images/2_mnist.png")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
            .shift(LEFT * 3)
        )
        input_img_rect = SurroundingRectangle(input_img, color=GRAY, stroke_width=0.5)
        input_img = Group(input_img, input_img_rect)

        output_img = (
            ImageMobject("images/2_visualization_resized.png")
            .set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
            .scale(8)
        )
        output_img_rect = SurroundingRectangle(output_img, color=GRAY, stroke_width=0.5)
        output_img = Group(output_img, output_img_rect)

        # First column
        first_column = VGroup(
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(3)],
            *[Dot(color=WHITE, radius=0.02) for _ in range(3)],
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(3)]
        )

        first_column.arrange(DOWN, buff=0.1).next_to(input_img, RIGHT, buff=1.0)

        # Second column configuration
        second_column = VGroup(
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(10)]
        )
        second_column.arrange(DOWN, buff=0.1).next_to(first_column, RIGHT, buff=1.0)

        # Draw lines from each circle in the first column to each circle in the second column
        lines1 = VGroup()
        for first_elem in first_column:
            if not isinstance(first_elem, Dot):  # Check to only connect circles
                for second_elem in second_column:
                    line = Line(
                        first_elem.get_right(),
                        second_elem.get_left(),
                        stroke_width=0.5,
                        color=GREY,
                    )
                    lines1.add(line)

        # Third column configuration
        third_column = VGroup(
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(10)]
        )
        third_column.arrange(DOWN, buff=0.1).next_to(second_column, RIGHT, buff=1.0)

        # Draw lines from each circle in the second column to each circle in the third column
        lines2 = VGroup()
        for second_elem in second_column:
            for third_elem in third_column:
                line = Line(
                    second_elem.get_right(),
                    third_elem.get_left(),
                    stroke_width=0.5,
                    color=GREY,
                )
                lines2.add(line)

        # Fourth column configuration
        fourth_column = VGroup(
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(10)]
        )
        fourth_column.arrange(DOWN, buff=0.1).next_to(third_column, RIGHT, buff=1.0)

        # Draw lines from each circle in the third column to each circle in the fourth column
        lines3 = VGroup()
        for third_elem in third_column:
            for fourth_elem in fourth_column:
                line = Line(
                    third_elem.get_right(),
                    fourth_elem.get_left(),
                    stroke_width=0.5,
                    color=GREY,
                )
                lines3.add(line)

        # Fifth column configuration
        fifth_column = VGroup(
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(3)],
            *[Dot(color=WHITE, radius=0.02) for _ in range(3)],
            *[Circle(radius=0.1, color=WHITE, stroke_width=0.8) for _ in range(3)]
        )

        fifth_column.arrange(DOWN, buff=0.1).next_to(fourth_column, RIGHT, buff=1.0)

        lines4 = VGroup()
        for fourth_elem in fourth_column:
            for fifth_elem in fifth_column:
                if not isinstance(fifth_column, Dot):
                    line = Line(
                        fourth_elem.get_right(),
                        fifth_elem.get_left(),
                        stroke_width=0.5,
                        color=GREY,
                    )
                    lines4.add(line)

        output_img.next_to(fifth_column, RIGHT, buff=1.0)

        # Arrows
        arrow1 = Arrow(
            input_img.get_right(), first_column.get_left(), color=WHITE, buff=0.1
        )
        arrow2 = Arrow(
            fifth_column.get_right(), output_img.get_left(), color=WHITE, buff=0.1
        )

        convnet = VGroup(
            first_column,
            second_column,
            third_column,
            fourth_column,
            fifth_column,
            lines1,
            lines2,
            lines3,
            lines4,
        )

        total = Group(input_img, output_img, convnet, arrow1, arrow2)
        total.move_to(ORIGIN)

        self.play(
            LaggedStart(
                FadeIn(input_img),
                GrowArrow(arrow1),
                FadeIn(convnet),
                GrowArrow(arrow2),
                FadeIn(output_img),
                lag_ratio=0.3,
            ),
        )

        self.wait(0.5)

        self.play(
            LaggedStart(
                Indicate(lines1, scale_factor=1.05, color=WHITE),
                Indicate(lines2, scale_factor=1.05, color=WHITE),
                Indicate(lines3, scale_factor=1.05, color=WHITE),
                Indicate(lines4, scale_factor=1.05, color=WHITE),
                lag_ratio=0.3,
            ),
        )

        self.wait(0.5)

        # Braces img

        brace_height = Brace(input_img, direction=LEFT, color=WHITE).stretch(0.5, dim=0)
        brace_height_text = brace_height.get_text("28").scale(0.5)
        brace_height = VGroup(brace_height, brace_height_text)

        brace_width = Brace(input_img, direction=DOWN, color=WHITE).stretch(0.5, dim=1)
        brace_width_text = brace_width.get_text("28").scale(0.5)
        brace_width = VGroup(brace_width, brace_width_text)

        self.play(FadeIn(brace_height, brace_width))

        self.play(
            Indicate(first_column, scale_factor=1.05, color=WHITE),
        )

        self.wait(0.5)

        # Brace parameters

        brace_parameters = Brace(lines1, direction=DOWN, color=WHITE).stretch(
            0.5, dim=1
        )
        brace_parameters_text = brace_parameters.get_text("Parameters Explosion").scale(0.5)
        brace_parameters = VGroup(brace_parameters, brace_parameters_text)

        self.play(
            Indicate(lines1, scale_factor=1.05, color=WHITE),
        )

        self.play(FadeIn(brace_parameters))
        self.play(
            Indicate(brace_parameters_text, scale_factor=1.05, color=WHITE),
        )

        txt = Tex("Pixels treated as independant features!").shift(DOWN * 3)
        self.play(Create(txt))

        self.wait(10)

        self.play(
            FadeOut(convnet),
            FadeOut(
                input_img,
                output_img,
                arrow1,
                arrow2,
                brace_height,
                brace_width,
                brace_parameters,
                brace_parameters,
            ),
            FadeOut(txt),
        )

        self.wait()


# Render the scene
if __name__ == "__main__":

    scene = Scene1_2()
    scene.render()
