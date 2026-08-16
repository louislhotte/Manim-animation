from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene3_1(VoiceoverScene, MovingCameraScene):
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

        # Display the kernel

        matrix_content1 = np.random.rand(3, 3)
        matrix_content2 = np.random.rand(3, 3)

        filter_obj1 = self.create_matrix_filter(matrix_content1).shift(RIGHT * 3)

        neuron = Circle(radius=0.5, color=WHITE, stroke_width=2)
        dots = VGroup(
            *[
                Dot(point=neuron.get_right() + RIGHT + DOWN * 0.5 * i, color=WHITE)
                for i in range(-1, 2)
            ]
        )
        lines = VGroup(
            *[
                Line(start=neuron.get_right(), end=dot.get_center(), color=WHITE)
                for dot in dots
            ]
        )
        input_line = Line(
            start=neuron.get_left() + LEFT, end=neuron.get_left(), color=WHITE
        )

        neuron = VGroup(input_line, neuron, lines)

        txt_neuron = Tex("Neuron", color=WHITE).next_to(
            neuron, direction=DOWN, buff=0.5
        )
        txt_filter = Tex("Filter", color=WHITE).next_to(
            filter_obj1, direction=DOWN, buff=0.5
        )

        self.play(Create(neuron), FadeIn(txt_neuron))

        self.wait(0.2)

        self.play(
            neuron.animate.shift(LEFT * 3),
            txt_neuron.animate.shift(LEFT * 3),
            Create(filter_obj1),
        )

        self.wait(0.2)

        self.play(
            FadeOut(neuron, txt_neuron),
            filter_obj1.animate.shift(LEFT * 3),
            txt_filter.animate.shift(LEFT * 3),
        )

        self.wait(0.3)

        filter_obj2 = self.create_matrix_filter(matrix_content2).next_to(
            filter_obj1, direction=IN, buff=0.5
        )
        filter_obj3 = self.create_matrix_filter(matrix_content1).next_to(
            filter_obj2, direction=IN, buff=0.5
        )

        # Switch to 3D view

        self.play(
            Rotate(filter_obj1, angle=-85 * DEGREES, axis=UP, about_point=ORIGIN),
            FadeOut(txt_filter),
        )
        self.play(
            Rotate(filter_obj1, angle=20 * DEGREES, axis=RIGHT, about_point=ORIGIN),
        )

        # Add other filters

        filter_obj2.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        filter_obj3.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )

        filter_obj2.shift(LEFT * 0.25)

        self.play(
            filter_obj1.animate.shift(LEFT * 0.25),
            Create(filter_obj2),
        )

        filter_obj3.shift(LEFT * 0.5)

        self.play(
            filter_obj1.animate.shift(LEFT * 0.25),
            filter_obj2.animate.shift(LEFT * 0.25),
            Create(filter_obj3),
        )

        self.wait(0.7)

        # Replace 2D filters by prisms

        filter_block1 = Prism(dimensions=[2, 2, 0.2], fill_color=BLUE, stroke_width=1)
        filter_block1.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        filter_block1.move_to(filter_obj1.get_center())

        filter_block2 = Prism(dimensions=[2, 2, 0.2], fill_color=BLUE, stroke_width=1)
        filter_block2.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        filter_block2.move_to(filter_obj2.get_center())

        filter_block3 = Prism(dimensions=[2, 2, 0.2], fill_color=BLUE, stroke_width=1)
        filter_block3.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        filter_block3.move_to(filter_obj3.get_center())

        self.play(Transform(filter_obj1, filter_block1))
        self.play(Transform(filter_obj2, filter_block2))
        self.play(Transform(filter_obj3, filter_block3))

        self.wait()

        # Replace the whole layer by a prism

        big_filter_block = Prism(dimensions=[2, 2, 1], fill_color=BLUE, stroke_width=1)
        big_filter_block.move_to(filter_obj2.get_center())
        big_filter_block.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )

        text_filters = Tex("3 Filters", color=BLUE).next_to(
            big_filter_block, direction=DOWN, buff=0.5
        )

        self.play(
            Transform(filter_obj2, big_filter_block),
            FadeOut(filter_obj1, filter_obj3),
            FadeIn(text_filters),
            run_time=1,
        )

        # Display the input image

        img = ImageMobject("images/0_mnist.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["none"]
        )
        img.scale(10)

        img.shift(4 * LEFT)
        rect_img = SurroundingRectangle(img, color=GRAY, stroke_width=1)
        img = Group(img, rect_img)

        img_text = Tex("Input Image", color=WHITE).next_to(
            img, direction=DOWN, buff=0.5
        )

        self.play(FadeIn(img, img_text))

        arrow1 = Arrow(
            start=img.get_right(), end=big_filter_block.get_left(), color=GRAY
        )

        self.play(Create(arrow1))

        # Display the output images

        img_conv1 = ImageMobject("images/mnist_conv1.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["none"]
        )
        img_conv1.scale(8)
        img_conv2 = ImageMobject("images/mnist_conv2.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["none"]
        )
        img_conv2.scale(8)
        img_conv3 = ImageMobject("images/mnist_conv3.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["none"]
        )
        img_conv3.scale(8)

        imgs_conv = Group(img_conv1, img_conv2, img_conv3).arrange(DOWN, buff=0.5)

        rect_img_conv1 = SurroundingRectangle(img_conv1, color=GRAY, stroke_width=1)
        rect_img_conv2 = SurroundingRectangle(img_conv2, color=GRAY, stroke_width=1)
        rect_img_conv3 = SurroundingRectangle(img_conv3, color=GRAY, stroke_width=1)

        img_conv1 = Group(img_conv1, rect_img_conv1)
        img_conv2 = Group(img_conv2, rect_img_conv2)
        img_conv3 = Group(img_conv3, rect_img_conv3)

        imgs_conv = Group(img_conv1, img_conv2, img_conv3).arrange(DOWN, buff=0.1)

        imgs_conv.shift(4 * RIGHT)

        arrow2 = Arrow(
            start=big_filter_block.get_right(), end=imgs_conv.get_left(), color=GRAY
        )

        imgs_conv_text = Tex("Feature Maps", color=WHITE).next_to(
            imgs_conv, direction=DOWN, buff=0.5
        )

        self.play(
            FadeIn(imgs_conv, imgs_conv_text),
            Create(arrow2),
        )
        self.wait(2)

        # Stack the images

        stacked_imgs = Prism(dimensions=[3, 3, 1], fill_color=GRAY, stroke_width=1)
        stacked_imgs.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )

        stacked_imgs.move_to(imgs_conv.get_center())

        self.play(
            LaggedStart(
                FadeOut(img_conv1, img_conv2, img_conv3),
                FadeIn(stacked_imgs),
                lag_ratio=0.3,
            ),
        )

        # Pan camera to the right

        self.play(
            self.camera.frame.animate.move_to(stacked_imgs.get_center()),
        )

        self.wait(2)

        # Add the next arrow and next layer

        big_filter_block2 = Prism(dimensions=[2, 2, 1], fill_color=BLUE, stroke_width=1)
        big_filter_block2.rotate(-85 * DEGREES, axis=UP, about_point=ORIGIN).rotate(
            20 * DEGREES, axis=RIGHT, about_point=ORIGIN
        )
        big_filter_block2.move_to(stacked_imgs.get_center() + 4 * RIGHT)

        arrow3 = Arrow(
            start=imgs_conv.get_right(), end=big_filter_block2.get_left(), color=GRAY
        )

        self.play(Create(arrow3), FadeIn(big_filter_block2))

        next_layer_text = Tex("?", color=WHITE).move_to(big_filter_block2.get_center())

        self.play(
            Transform(big_filter_block2, next_layer_text),
        )
        # Fadeout everything

        self.wait(1)

        self.play(
            FadeOut(
                arrow1,
                arrow2,
                arrow3,
                img,
                filter_obj2,
                big_filter_block2,
                stacked_imgs,
                img_text,
                text_filters,
                imgs_conv_text,
            ),
            run_time=2,
        )

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene3_1()
    scene.render()
