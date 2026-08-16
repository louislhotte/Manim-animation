from manim import *
import matplotlib.pyplot as plt

class ImageScene(Scene):
    def construct(self):
        image = ImageMobject("images/2_mnist.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        pixel_values = plt.imread("images/2_mnist.png")[:, :]

        image.scale(35)
        border = SurroundingRectangle(image, buff=0, color=GRAY, stroke_width=2)

        grid = NumberPlane(
            x_range=(-14, 14, 1),
            y_range=(-14, 14, 1),
            background_line_style={"stroke_color": GRAY, "stroke_width": 2, "stroke_opacity": 1},
            axis_config={"stroke_color": GRAY, "stroke_width": 2, "include_numbers": False},
            faded_line_ratio=0,
        )

        grid.scale(image.get_height() / grid.get_height())

        text_values = []
        cell_size = grid.get_x_unit_size()
        for x in range(-14, 14):
            for y in range(-13, 15):
                value = int(pixel_values[14 - y][14 + x] * 255)
                text = Tex(f"{value}")
                position = grid.coords_to_point(x, y)
                text.move_to(position + RIGHT * cell_size / 2 + DOWN * cell_size / 2).scale(image.get_height() / 28)
                text_values.append(text)

        text_group = VGroup(*text_values)
        self.wait(2)

        question = Tex("How can we define an image?").scale(1.5)
        self.play(Write(question))
        self.wait()
        self.play(FadeOut(question), run_time=1)

        self.play(FadeIn(image, border))
        self.wait()
        self.play(FadeIn(grid))
        self.play(FadeOut(image), FadeIn(text_group))

        highlight_high = SurroundingRectangle(text_values[16 * 28 + 15], color=GREEN, stroke_width=3)
        highlight_low = SurroundingRectangle(text_values[5 * 28 + 20], color=RED, stroke_width=3)

        self.play(Create(highlight_high), run_time=2)
        self.play(Create(highlight_low), run_time=2)
        self.play(FadeOut(grid, border, highlight_low, highlight_high), FadeOut(text_group), run_time=2)

        explanation = Tex("An image is a 2D array of values between 0 and 255 (grayscale)")
        self.play(Write(explanation))
        self.wait(3)
        self.play(FadeOut(explanation), run_time=1)
        self.wait(2)

if __name__ == "__main__":
    scene = ImageScene()
    scene.render()