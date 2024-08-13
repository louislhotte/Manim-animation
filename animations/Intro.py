from manim import *

class Intro(Scene):
    def construct(self):
        intro_group = self.introduction("Koch Curve Animation", 
                                            "Manim CE - Python ")
        self.play(FadeOut(intro_group))
        self.wait(1)

    def introduction(self, title1, title2):
        header = Tex(title1)
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)
        writer = Tex("Created by Ptolémé")
        writer_pos = [(line.get_left()[0] + line.get_right()[0]) / 2, line.get_bottom()[1] - 1, 0]
        writer.move_to(writer_pos)
        
        self.play(Write(header), Write(line))
        self.wait(0.5)
        self.play(Transform(header, Tex(title2)))
        self.play(Write(writer))
        self.wait(4)
        
        return VGroup(header, writer, line)