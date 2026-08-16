from manim import *
from PIL import Image
import numpy as np


class Scene5_2(MovingCameraScene):
    def construct(self):
        self.wait(2)

        # --- Source image (28x28) + its lattice ------------------------------ #
        img = ImageMobject("images/0_mnist.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        img.scale(30)

        pool_img = ImageMobject("images/0_mnist_pooled.png").set_resampling_algorithm(
            RESAMPLING_ALGORITHMS["box"]
        )
        pool_img.scale(30)

        # Pixel intensities in [0, 1] for the source (28x28) and the pooled
        # (14x14) images. The source values drive the worked example; the pooled
        # values are dropped in cell by cell as the window sweeps.
        src_values = (
            np.asarray(Image.open("images/0_mnist.png").convert("L"), dtype=float) / 255.0
        )
        pooled_values = (
            np.asarray(Image.open("images/0_mnist_pooled.png").convert("L"), dtype=float)
            / 255.0
        )

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
            faded_line_ratio=0,
        )
        lattice_img.scale(img.get_height() / lattice_img.get_height())
        cell_src = lattice_img.get_x_unit_size()

        lattice_img_rectangle = Rectangle(
            height=cell_src * 28, width=cell_src * 28, color=GRAY, stroke_width=2
        )
        lattice_img_obj = VGroup(lattice_img, lattice_img_rectangle)

        # --- Pooled image lattice (14x14), parked on the right --------------- #
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
            faded_line_ratio=0,
        )
        lattice_img_pool.scale(pool_img.get_height() / lattice_img_pool.get_height())
        cell_pool = lattice_img_pool.get_x_unit_size()

        lattice_img_pool_rectangle = Rectangle(
            height=cell_pool * 14, width=cell_pool * 14, color=GRAY, stroke_width=2
        )
        lattice_img_pool_obj = VGroup(
            lattice_img_pool, lattice_img_pool_rectangle
        ).shift(4 * RIGHT)

        # Show the source, then slide it to the left to make room.
        self.play(FadeIn(img), FadeIn(lattice_img_obj))
        self.wait()
        self.play(
            lattice_img_obj.animate.shift(4 * LEFT).scale(0.6),
            img.animate.shift(4 * LEFT).scale(0.6),
        )

        # Geometry after the move (kept fixed for the whole sweep).
        cell_src = lattice_img.get_x_unit_size()
        cell_pool = lattice_img_pool.get_x_unit_size()
        src_ul = lattice_img.get_corner(UL)
        pool_ul = lattice_img_pool.get_corner(UL)

        def src_center(x, y):
            return src_ul + (2 * x + 1) * cell_src * RIGHT + (2 * y + 1) * cell_src * DOWN

        def pool_center(x, y):
            return pool_ul + (x + 0.5) * cell_pool * RIGHT + (y + 0.5) * cell_pool * DOWN

        # --- Pooling parameters --------------------------------------------- #
        title = Tex("Average pooling").scale(0.9)
        params = Tex(r"Window: $2\times2$ \quad Stride: 2").scale(0.7)
        params.next_to(title, DOWN, buff=0.2)
        param_group = VGroup(title, params).move_to(3.2 * UP)
        self.play(FadeIn(param_group))

        # --- The 2x2 window (a plain box, not a grid of ones) --------------- #
        # Feature one window (row 8, col 10) that straddles the digit so the
        # worked example uses a real mix of values rather than the black corner.
        fy, fx = 8, 10
        window = Square(side_length=2 * cell_src, color=RED, stroke_width=3)
        window.set_fill(RED, opacity=0.15)
        window.move_to(src_center(fx, fy))
        self.play(Create(window))

        # Output cell + the two red guide lines linking window -> output cell.
        rectangle_pool = Rectangle(
            height=cell_pool, width=cell_pool, color=RED, stroke_width=3
        ).move_to(pool_center(fx, fy))

        def link(a_corner, b_corner):
            return Line(a_corner(), b_corner(), color=RED, stroke_width=2)

        top_line = link(
            lambda: window.get_corner(UR), lambda: rectangle_pool.get_corner(UL)
        )
        top_line.add_updater(
            lambda m: m.become(
                Line(
                    window.get_corner(UR),
                    rectangle_pool.get_corner(UL),
                    color=RED,
                    stroke_width=2,
                )
            )
        )
        bottom_line = link(
            lambda: window.get_corner(DR), lambda: rectangle_pool.get_corner(DL)
        )
        bottom_line.add_updater(
            lambda m: m.become(
                Line(
                    window.get_corner(DR),
                    rectangle_pool.get_corner(DL),
                    color=RED,
                    stroke_width=2,
                )
            )
        )

        self.play(FadeIn(lattice_img_pool_obj), run_time=1)
        self.play(Create(top_line), Create(bottom_line), Create(rectangle_pool))
        self.wait(0.5)

        # --- Worked example: average of the four pixels in this window ------- #
        block = src_values[2 * fy : 2 * fy + 2, 2 * fx : 2 * fx + 2]
        vals = [[round(float(block[r, c]), 2) for c in range(2)] for r in range(2)]
        flat = [vals[0][0], vals[0][1], vals[1][0], vals[1][1]]
        avg = round(sum(flat) / 4, 2)

        # Magnified 2x2 with the actual values, shaded by intensity.
        csize = 0.85
        mag = VGroup()
        for r in range(2):
            for c in range(2):
                v = vals[r][c]
                sq = Square(
                    side_length=csize,
                    stroke_color=WHITE,
                    stroke_width=2,
                    fill_color=interpolate_color(BLACK, WHITE, v),
                    fill_opacity=1,
                )
                sq.move_to([(c - 0.5) * csize, (0.5 - r) * csize, 0])
                lab = Tex(f"{v:.2f}", color=(BLACK if v > 0.6 else WHITE)).scale(0.5)
                lab.move_to(sq)
                mag.add(VGroup(sq, lab))
        mag.move_to(1.8 * UP)
        mag_box = SurroundingRectangle(mag, color=RED, buff=0.04, stroke_width=2)

        formula = MathTex(
            r"\frac{%.2f + %.2f + %.2f + %.2f}{4} = %.2f"
            % (flat[0], flat[1], flat[2], flat[3], avg)
        ).scale(0.55)
        formula.next_to(mag, DOWN, buff=0.4)

        # Zoom-callout lines from the window up to the magnified view.
        callout1 = DashedLine(
            window.get_corner(UR), mag_box.get_corner(DL), color=GRAY, stroke_width=1.5
        )
        callout2 = DashedLine(
            window.get_corner(DR), mag_box.get_corner(DR), color=GRAY, stroke_width=1.5
        )

        self.play(Create(callout1), Create(callout2), run_time=0.6)
        self.play(FadeIn(mag, scale=0.6), FadeIn(mag_box))
        self.play(Write(formula))
        self.wait(1)

        # The result drops into the output cell as a single grey pixel.
        result_pixel = Rectangle(
            width=cell_pool,
            height=cell_pool,
            fill_color=interpolate_color(BLACK, WHITE, avg),
            fill_opacity=1,
            stroke_width=0.1,
        ).move_to(pool_center(fx, fy))
        self.play(FadeIn(result_pixel))
        self.wait(1)

        # Clear the worked example, keep the computed pixel.
        self.play(FadeOut(mag), FadeOut(mag_box), FadeOut(formula), FadeOut(callout1, callout2))

        # --- Now sweep every window and fill the pooled image --------------- #
        pixels = VGroup(result_pixel)
        for y in range(14):
            for x in range(14):
                self.play(
                    window.animate.move_to(src_center(x, y)),
                    rectangle_pool.animate.move_to(pool_center(x, y)),
                    run_time=0.05,
                )
                color = interpolate_color(BLACK, WHITE, pooled_values[y, x])
                pixel_rect = Rectangle(
                    width=cell_pool,
                    height=cell_pool,
                    fill_color=color,
                    fill_opacity=1,
                    stroke_width=0.1,
                ).move_to(pool_center(x, y))
                pixels.add(pixel_rect)
                self.add(pixel_rect)

        top_line.clear_updaters()
        bottom_line.clear_updaters()
        self.play(
            FadeOut(window, top_line, bottom_line, rectangle_pool, param_group),
        )
        self.play(
            FadeOut(lattice_img, img, lattice_img_rectangle),
            run_time=1,
        )

        # --- Center the pooled result and label its dimensions -------------- #
        self.play(
            lattice_img_pool_obj.animate.move_to(ORIGIN),
            pixels.animate.move_to(ORIGIN),
        )

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
        self.wait(1)

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

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene5_2()
    scene.render()
