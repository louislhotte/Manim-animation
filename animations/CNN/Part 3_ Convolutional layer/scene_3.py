from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene3_3(VoiceoverScene, MovingCameraScene):
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
        self.wait(2)

        # More filters

        filter1_3d = Prism(dimensions=[1, 1, 0.5], fill_color=BLUE, stroke_width=1)
        filter1_3d.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )

        filter2_3d = Prism(dimensions=[1, 1, 0.5], fill_color=BLUE, stroke_width=1)
        filter2_3d.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        filter2_3d.next_to(filter1_3d, RIGHT, buff=0.5)

        filter3_3d = Prism(dimensions=[1, 1, 0.5], fill_color=BLUE, stroke_width=1)
        filter3_3d.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )

        filter2_3d.move_to(ORIGIN)
        filter1_3d.next_to(filter2_3d, LEFT, buff=0.2)
        filter3_3d.next_to(filter2_3d, RIGHT, buff=0.2)

        image_3d = Prism(dimensions=[2, 2, 1], fill_color=GRAY, stroke_width=1)
        image_3d.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )

        # Input Image

        self.play(
            Create(image_3d),
        )

        self.play(
            image_3d.animate.shift(LEFT * 4),
        )

        brace_filter = Brace(filter2_3d, direction=DOWN, color=WHITE)
        brace_filter_txt = brace_filter.get_text("(3x3x3) Filter").scale(0.5)
        brace_filter = VGroup(brace_filter, brace_filter_txt)

        arrow1 = Arrow(image_3d.get_right(), filter1_3d.get_left(), buff=0.2)

        brace_img = Brace(image_3d, direction=DOWN, color=WHITE)
        brace_img_txt = brace_img.get_text("(3x28x28) Image").scale(0.5)
        brace_img = VGroup(brace_img, brace_img_txt)

        self.play(
            LaggedStart(
                FadeIn(arrow1),
                Create(filter2_3d),
                FadeIn(brace_filter),
                FadeIn(brace_img),
                lag_ratio=0.5,
            ),
        )

        self.wait(0.5)

        # Filters

        self.play(
            Create(filter1_3d),
            Create(filter3_3d),
        )

        brace_filters = Brace(
            VGroup(filter1_3d, filter2_3d, filter3_3d), direction=DOWN, color=WHITE
        )
        brace_filters_txt = brace_filters.get_text("3 (3x3x3) Filters").scale(0.5)
        brace_filters = VGroup(brace_filters, brace_filters_txt)

        self.play(
            Transform(brace_filter, brace_filters),
        )

        # Output image

        image_3d_out = Prism(dimensions=[2, 2, 1], fill_color=GRAY, stroke_width=1)
        image_3d_out.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        image_3d_out.shift(RIGHT * 4)

        arrow2 = Arrow(filter3_3d.get_right(), image_3d_out.get_left(), buff=0.2)

        brace_img_out = Brace(image_3d_out, direction=DOWN, color=WHITE)
        brace_img_out_txt = brace_img_out.get_text("(3x28x28) Image").scale(0.5)
        brace_img_out = VGroup(brace_img_out, brace_img_out_txt)

        self.play(
            LaggedStart(FadeIn(arrow2), Create(image_3d_out), lag_ratio=0.5),
        )

        self.play(
            FadeIn(brace_img_out),
        )

        # Shift everything up by 1

        self.play(
            image_3d.animate.shift(UP * 1),
            image_3d_out.animate.shift(UP * 1),
            filter1_3d.animate.shift(UP * 1),
            filter2_3d.animate.shift(UP * 1),
            filter3_3d.animate.shift(UP * 1),
            brace_img.animate.shift(UP * 1),
            brace_filter.animate.shift(UP * 1),
            brace_img_out.animate.shift(UP * 1),
            arrow1.animate.shift(UP * 1),
            arrow2.animate.shift(UP * 1),
            run_time=1,
        )

        # Highligh input channels and filter shape

        brace_img_txt_target = brace_img_txt.copy()
        brace_img_txt_target[0][1].set_color(BLUE)
        brace_filters_txt_target = brace_filter_txt.copy()
        brace_filters_txt_target[0][2].set_color(BLUE)

        self.play(
            Transform(brace_img_txt, brace_img_txt_target),
            Transform(brace_filter_txt, brace_filters_txt_target),
        )

        # Write input channel = filter channels

        text_input = Tex("Input Channels = Filter Channels").scale(0.8).set_color(BLUE)
        text_input.move_to(DOWN * 3 + LEFT * 3.5)

        self.play(
            Create(text_input),
        )

        self.play(Indicate(text_input, scale_factor=1.2, color=BLUE), run_time=1)

        # Highlight output channels and number of filters

        brace_img_out_txt_target = brace_img_out_txt.copy()
        brace_img_out_txt_target[0][1].set_color(RED)
        brace_filters_txt_target2 = brace_filters_txt_target.copy()
        brace_filters_txt_target2[0][0].set_color(RED)

        self.play(
            Transform(brace_img_out_txt, brace_img_out_txt_target),
            Transform(brace_filter_txt, brace_filters_txt_target2),
        )

        # Write output channel = number of filters

        text_output = (
            Tex("Output Channels = Number of Filters").scale(0.8).set_color(RED)
        )
        text_output.move_to(DOWN * 3 + RIGHT * 3.5)

        self.play(
            Create(text_output),
        )

        self.play(Indicate(text_output, scale_factor=1.2, color=RED), run_time=1)

        # FadeOut everything

        self.play(
            FadeOut(image_3d, image_3d_out, filter1_3d, filter2_3d, filter3_3d),
            FadeOut(brace_img, brace_filter, brace_img_out),
            FadeOut(arrow1, arrow2),
            FadeOut(text_input, text_output),
            run_time=2,
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene3_3()
    scene.render()
