from manim import *


class Scene6_3(MovingCameraScene):
    def construct(self):

        # Opening buffer.
        self.wait(2.5)

        # "Thank you" header with an underline that extends past both ends,
        # matching the channel's intro/outro style.
        header = Tex("Thank you for watching!")
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)

        # Signature, centered under the line.
        writer = Tex(r"Created by Ptol\'em\'e").scale(0.8).set_color(BLUE)
        writer_pos = [
            (line.get_left()[0] + line.get_right()[0]) / 2,
            line.get_bottom()[1] - 1,
            0,
        ]
        writer.move_to(writer_pos)

        self.play(Write(header), Write(line), run_time=1.5)
        self.wait(1)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.2)

        # Hold on the finished card — extra buffer so the outro breathes.
        self.wait(4)

        outro = VGroup(header, line, writer)
        self.play(FadeOut(outro), run_time=1.5)

        # Closing buffer.
        self.wait(2.5)


# Render the scene
if __name__ == "__main__":

    scene = Scene6_3()
    scene.render()
