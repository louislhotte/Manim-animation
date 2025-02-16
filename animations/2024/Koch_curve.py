from manim import *

class KochCurve(Scene):
    def construct(self):
        intro_group = self.introduction("Koch Curve Animation", 
                                        "Python || Fractals || Manim")
        self.play(FadeOut(intro_group))
        self.wait(1)
        
        # Adding the legend on the left
        self.add_legend()

        A = np.array([0, 0, 0])
        B = np.array([4, 0, 0])
        sixty_degrees = np.pi / 3
        C = np.array([4 * np.cos(sixty_degrees), 4 * np.sin(sixty_degrees), 0])

        iterations = 4
        
        triangle = Polygon(A, B, C)
        self.play(Create(triangle))
        self.wait(1)

        lines = [Line(A, B), Line(B, C), Line(C, A)]
        for i in range(iterations):
            new_lines = []
            for line in lines:
                segments = self.koch_segment(line.get_start_and_end())
                self.play(Transform(line, segments[0]))
                self.add(*segments[1:])  
                new_lines.extend(segments)
            lines = new_lines
    
    def koch_segment(self, segment):
        """
        Generates the four segments of the Koch curve for a given line segment.
        :param segment: a tuple of two points (start, end)
        :returns: list of Line objects representing the Koch segment
        """
        start, end = segment
        
        A = start
        E = end
        B = A + (E - A) / 3
        D = E - (E - A) / 3

        angle = -np.pi / 3 
        rotation_matrix = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1]
        ])
        C = B + np.dot(rotation_matrix, D - B)

        return [
            Line(A, B),
            Line(B, C),
            Line(C, D),
            Line(D, E)
        ]

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

    def add_legend(self):
        # Text for the legend
        step1 = Tex("1. Divide the line segment into three equal parts.")
        step2 = Tex("2. Construct an equilateral triangle on the middle segment")
        step3 = Tex("3. Remove the line segment that formed the base of the triangle")

        # Grouping the steps
        legend = VGroup(step1, step2, step3).scale(0.37)
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        
        # Creating a rectangle around the legend
        legend_background = SurroundingRectangle(legend, color=WHITE, buff=0.5)
        
        # Positioning the legend on the left of the scene
        legend_group = VGroup(legend_background, legend)
        legend_group.to_corner(UL)

        # Adding the legend to the scene
        self.play(FadeIn(legend_group))

