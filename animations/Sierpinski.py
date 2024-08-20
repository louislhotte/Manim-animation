from manim import *
import numpy as np

class SierpinskiCurve(VMobject):
    def __init__(self, order=1, scale_factor=1, **kwargs):
        super().__init__(**kwargs)
        self.order = order
        self.scale_factor = scale_factor
        self.angle = 45 * DEGREES
        self.create_curve()

    def create_curve(self):
        instructions = self.generate_l_system(self.order)
        self.build_path(instructions)

    def generate_l_system(self, order):
        if order == 0:
            return "X"
        else:
            prev = self.generate_l_system(order - 1)
            return prev.replace("X", "XF+G+XF--F--XF+G+X").replace("G", "GG")

    def build_path(self, instructions):
        current_point = ORIGIN
        direction = np.array(RIGHT)  # Convert to numpy array for manipulation
        path_points = [current_point]

        for command in instructions:
            if command in "FG":
                next_point = current_point + direction * self.scale_factor
                path_points.append(next_point)
                current_point = next_point
            elif command == "+":
                direction = self.rotate_vector(direction, self.angle)  # Rotate by +45 degrees
            elif command == "-":
                direction = self.rotate_vector(direction, -self.angle)  # Rotate by -45 degrees

        self.set_points_as_corners(path_points)

    def rotate_vector(self, vector, angle):
        """Rotate a 3D vector by a given angle around the z-axis."""
        rotation_matrix = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1]
        ])
        return rotation_matrix @ vector  # Apply rotation to the vector

class SierpinskiCurveScene(Scene):
    def construct(self):
        intro_group = self.introduction("Sierpinski Curve", 
                                        "Manim - Python Animation")
        self.play(FadeOut(intro_group))
        self.wait(1)
        max_order = 6  # Maximum order to display
        colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]  # Gradient colors

        for n in range(1, max_order + 1):
            sierpinski_curve = SierpinskiCurve(order=n, scale_factor=0.1)
            sierpinski_curve.set_height(5)
            sierpinski_curve.move_to(ORIGIN)  # Centre la figure au milieu de la scène
            gradient_colors = color_gradient(colors, len(sierpinski_curve.points))
            sierpinski_curve.set_color_by_gradient(gradient_colors)
            
            # Titre indiquant l'ordre avec une taille réduite
            header = Text(f"Order = {n}", font_size=15)
            header.set_width(4)
            header.to_edge(UL)
            from_pos = [header.get_left()[0] - 0.5, header.get_bottom()[1] - 0.25, 0]
            to_pos = [header.get_right()[0] + 0.5, header.get_bottom()[1] - 0.25, 0]
            line = Line(from_pos, to_pos)

            self.play(Write(header), Write(line))
            self.wait(0.5)
            self.play(Create(sierpinski_curve), run_time=4)
            self.wait(1)
            
            if n < max_order:
                self.play(FadeOut(sierpinski_curve), FadeOut(header), FadeOut(line))

        self.play(FadeOut(sierpinski_curve), FadeOut(header), FadeOut(line))
        self.wait(2)
        self.explanations()
        self.Outro("Thanks for watching") 
        self.wait(5) 

    def explanations(self):
        # Initial statement about the simplicity of the formula
        text = Text("The formula to build this is actually quite simple.").scale(0.5)
        self.play(FadeIn(text))
        self.wait(3)

        # Displaying the formula
        formula = MathTex(r"X \rightarrow XF+G+XF--F--XF+G+X").scale(0.8)
        self.play(Transform(text, formula))

        # Explanation of the formula, positioned below the formula
        explanation = Text(
            "X is replaced with a pattern of moves and rotations:\n"
            "F: Move forward\n"
            "+: Turn right (45 degrees)\n"
            "-: Turn left (45 degrees)\n"
            "G: Move forward without drawing"
        ).scale(0.4)
        explanation.next_to(formula, DOWN, buff=0.5) 
        self.play(Write(explanation))
        self.wait(5)

        # Fade out to conclude the explanation
        self.play(FadeOut(text), FadeOut(explanation), FadeOut(formula))



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
    
    def Outro(self, text):
        header = Tex(text)
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)        
        self.play(Write(header), Write(line))
        self.wait(0.5)