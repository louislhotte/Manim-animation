from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene6_2(VoiceoverScene, MovingCameraScene):
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

        # Convnet Layers

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

        input_img.shift(LEFT * 5 + UP * 1)
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

        braces = VGroup(
            brace_img,
            brace_filter1,
            brace_filter2,
            brace_filter3,
            brace_filter4,
            brace_output,
        )
        arrows = VGroup(arrow1, arrow2, arrow3, arrow4, arrow5)
        convnet = Group(layer_1, act_1, layer_2, act_2, layer_3, act_3, layer_4, act_4)

        conv_side = Group(braces, arrows, convnet, legend, input_img, output_img)

        self.play(FadeIn(conv_side))

        self.play(conv_side.animate.scale(0.5).shift(3 * LEFT + UP))

        self.wait(0.75)

        # Fully connected network

        # Input image

        input_img_fc = input_img.copy()
        input_img_fc.next_to(output_img, RIGHT, buff=1.0)

        # First column
        first_column = VGroup(
            *[Circle(radius=0.05, color=WHITE, stroke_width=0.8) for _ in range(3)],
            *[Dot(color=WHITE, radius=0.02) for _ in range(3)],
            *[Circle(radius=0.05, color=WHITE, stroke_width=0.8) for _ in range(3)],
        )

        first_column.arrange(DOWN, buff=0.1).next_to(input_img_fc, RIGHT, buff=0.7)

        # Second column configuration
        second_column = VGroup(
            *[Circle(radius=0.05, color=WHITE, stroke_width=0.8) for _ in range(10)]
        )
        second_column.arrange(DOWN, buff=0.05).next_to(first_column, RIGHT, buff=0.7)

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
            *[Circle(radius=0.05, color=WHITE, stroke_width=0.8) for _ in range(10)]
        )
        third_column.arrange(DOWN, buff=0.05).next_to(second_column, RIGHT, buff=0.7)

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
            *[Circle(radius=0.05, color=WHITE, stroke_width=0.8) for _ in range(10)]
        )
        fourth_column.arrange(DOWN, buff=0.05).next_to(third_column, RIGHT, buff=0.7)

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
            *[Circle(radius=0.05, color=WHITE, stroke_width=0.8) for _ in range(3)],
            *[Dot(color=WHITE, radius=0.02) for _ in range(3)],
            *[Circle(radius=0.05, color=WHITE, stroke_width=0.8) for _ in range(3)],
        )

        fifth_column.arrange(DOWN, buff=0.1).next_to(fourth_column, RIGHT, buff=0.7)

        # Draw lines from each circle in the fourth column to each circle in the fifth column
        lines4 = VGroup()
        for fourth_elem in fourth_column:
            for fifth_elem in fifth_column:
                if not isinstance(fifth_elem, Dot):
                    line = Line(
                        fourth_elem.get_right(),
                        fifth_elem.get_left(),
                        stroke_width=0.5,
                        color=GREY,
                    )
                    lines4.add(line)

        # Output image
        output_img_fc = output_img.copy()
        output_img_fc.next_to(fifth_column, RIGHT, buff=0.7)

        # Arrows

        arrowin = Arrow(
            start=input_img_fc.get_right(),
            end=first_column.get_left(),
            color=WHITE,
            buff=0.1,
        )
        arrowout = Arrow(
            start=fifth_column.get_right(),
            end=output_img_fc.get_left(),
            color=WHITE,
            buff=0.1,
        )
        arrows = VGroup(arrowin, arrowout)

        # Braces

        brace_img_fc = Brace(
            input_img_fc, direction=DOWN, color=WHITE, buff=0.1
        ).stretch(0.15, dim=1)
        brace_img_txt_fc = brace_img_fc.get_text("(1x28x28)").scale(0.2).shift(UP * 0.4)
        brace_img_fc = VGroup(brace_img_fc, brace_img_txt_fc)

        brace_output_fc = Brace(
            output_img_fc, direction=DOWN, color=WHITE, buff=0.1
        ).stretch(0.15, dim=1)
        brace_output_txt_fc = (
            brace_output_fc.get_text("(1x28x28)").scale(0.2).shift(UP * 0.4)
        )
        brace_output_fc = VGroup(brace_output_fc, brace_output_txt_fc)

        brace_lines1 = Brace(lines1, direction=DOWN, color=WHITE, buff=0.1).stretch(
            0.15, dim=1
        )
        brace_lines1_txt = brace_lines1.get_text("7840").scale(0.2).shift(UP * 0.35)
        brace_lines1 = VGroup(brace_lines1, brace_lines1_txt)

        brace_lines2 = Brace(lines2, direction=DOWN, color=WHITE, buff=0.1).stretch(
            0.15, dim=1
        )
        brace_lines2_txt = brace_lines2.get_text("100").scale(0.2).shift(UP * 0.35)
        brace_lines2 = VGroup(brace_lines2, brace_lines2_txt)

        brace_lines3 = Brace(lines3, direction=DOWN, color=WHITE, buff=0.1).stretch(
            0.15, dim=1
        )
        brace_lines3_txt = brace_lines3.get_text("100").scale(0.2).shift(UP * 0.35)
        brace_lines3 = VGroup(brace_lines3, brace_lines3_txt)

        brace_lines4 = Brace(lines4, direction=DOWN, color=WHITE, buff=0.1).stretch(
            0.15, dim=1
        )
        brace_lines4_txt = brace_lines4.get_text("7840").scale(0.2).shift(UP * 0.35)
        brace_lines4 = VGroup(brace_lines4, brace_lines4_txt)

        braces = VGroup(
            brace_img_fc,
            brace_output_fc,
            brace_lines1,
            brace_lines2,
            brace_lines3,
            brace_lines4,
        )

        # Fully connected network

        fcnet = VGroup(
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

        fc_side = Group(input_img_fc, fcnet, output_img_fc, arrows, braces)

        self.play(FadeIn(fc_side))

        # Convnet weights

        conv_weight_txt = (
            Tex("810 parameters", color=BLUE).scale(0.8).shift(3 * DOWN + LEFT * 3)
        )
        self.play(Write(conv_weight_txt))

        # Fully connected weights

        fc_weight_txt = (
            Tex("15 880 parameters", color=RED).scale(0.8).shift(3 * DOWN + RIGHT * 3)
        )
        self.play(Write(fc_weight_txt))

        # Images of different scales

        input_img_large = ImageMobject("images/face.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["none"]
        )
        input_img_large_rect = SurroundingRectangle(input_img_large, buff=0, color=GRAY)
        input_img_large = Group(input_img_large, input_img_large_rect).scale(0.5)

        output_img_large = ImageMobject(
            "images/face_output.png"
        ).set_resampling_algorithm(RESAMPLING_ALGORITHMS["none"])
        output_img_large_rect = SurroundingRectangle(
            output_img_large, buff=0, color=GRAY
        )
        output_img_large = Group(output_img_large, output_img_large_rect).scale(0.5)

        input_img_large.move_to(input_img.get_center())
        output_img_large.move_to(output_img.get_center())

        input_img_large_fc = input_img_large.copy()
        input_img_large_fc.move_to(input_img_fc.get_center())
        output_img_large_fc = output_img_large.copy()
        output_img_large_fc.move_to(output_img_fc.get_center())

        brace_input_large = Brace(input_img_large, direction=DOWN, color=WHITE).stretch(
            0.3, dim=1
        )
        brace_input_large_txt = (
            brace_input_large.get_text("(1x256x256)").scale(0.4).shift(UP * 0.2)
        )
        brace_input_large = VGroup(brace_input_large, brace_input_large_txt)

        brace_output_large = Brace(
            output_img_large, direction=DOWN, color=WHITE
        ).stretch(0.3, dim=1)
        brace_output_large_txt = (
            brace_output_large.get_text("(1x256x256)").scale(0.4).shift(UP * 0.2)
        )
        brace_output_large = VGroup(brace_output_large, brace_output_large_txt)

        brace_input_fc_large = Brace(
            input_img_large_fc, direction=DOWN, color=WHITE
        ).stretch(0.3, dim=1)
        brace_input_fc_large_txt = (
            brace_input_fc_large.get_text("(1x256x256)").scale(0.4).shift(UP * 0.2)
        )
        brace_input_fc_large = VGroup(brace_input_fc_large, brace_input_fc_large_txt)

        brace_output_fc_large = Brace(
            output_img_large_fc, direction=DOWN, color=WHITE
        ).stretch(0.3, dim=1)
        brace_output_fc_large_txt = (
            brace_output_fc_large.get_text("(1x256x256)").scale(0.4).shift(UP * 0.2)
        )
        brace_output_fc_large = VGroup(brace_output_fc_large, brace_output_fc_large_txt)

        self.play(
            LaggedStart(
                FadeOut(
                    input_img,
                    arrow1,
                    brace_img,
                    brace_img_fc,
                    input_img_fc,
                    arrowin,
                ),
                FadeIn(
                    input_img_large,
                    input_img_large_fc,
                    brace_input_large,
                    brace_input_fc_large,
                ),
                lag_ratio=0.5,
            ),
        )

        self.play(
            LaggedStart(
                FadeOut(
                    output_img,
                    arrow5,
                    brace_output,
                    brace_output_fc,
                    output_img_fc,
                    arrowout,
                ),
                FadeIn(
                    output_img_large,
                    output_img_large_fc,
                    brace_output_large,
                    brace_output_fc_large,
                ),
                lag_ratio=0.5,
            ),
        )

        brace_lines1_large = Brace(
            lines1, direction=DOWN, color=WHITE, buff=0.1
        ).stretch(0.15, dim=1)
        brace_lines1_txt_large = (
            brace_lines1_large.get_text("655 360").scale(0.2).shift(UP * 0.35)
        )
        brace_lines1_large = VGroup(brace_lines1_large, brace_lines1_txt_large)

        brace_lines4_large = Brace(
            lines4, direction=DOWN, color=WHITE, buff=0.1
        ).stretch(0.15, dim=1)
        brace_lines4_txt_large = (
            brace_lines4_large.get_text("655 360").scale(0.2).shift(UP * 0.35)
        )
        brace_lines4_large = VGroup(brace_lines4_large, brace_lines4_txt_large)

        self.play(
            LaggedStart(
                FadeOut(brace_lines1, brace_lines4),
                FadeIn(brace_lines1_large, brace_lines4_large),
                lag_ratio=0.5,
            ),
        )

        fc_weight_large_txt = (
            Tex("1 million + parameters !", color=RED)
            .scale(0.8)
            .shift(3 * DOWN + RIGHT * 3)
        )
        self.play(
            Transform(fc_weight_txt, fc_weight_large_txt),
        )

        # FadeOut everything

        self.play(
            FadeOut(
                input_img_large,
                output_img_large,
                input_img_large_fc,
                output_img_large_fc,
                brace_input_large,
                brace_output_large,
                brace_input_fc_large,
                brace_output_fc_large,
                brace_lines1_large,
                brace_lines4_large,
                brace_filter1,
                brace_filter2,
                brace_filter3,
                brace_filter4,
                brace_lines2,
                brace_lines3,
                arrow2,
                arrow3,
                arrow4,
                convnet,
                fcnet,
                conv_weight_txt,
                fc_weight_txt,
                legend,
            ),
            run_time=2,
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene6_2()
    scene.render()
