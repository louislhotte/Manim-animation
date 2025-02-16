from manim import *

class TransformObjects(Scene):
    def construct(self):
        intro_group = self.introduction("Manim Tutorial (Part I)", 
                                        "Learn How to Display 10 Objects in 60 seconds")
        self.play(FadeOut(intro_group))
        self.wait(1)
        objects = [
            Circle(),
            Square(),
            Triangle(),
            RegularPolygon(5),  # Pentagon
            RegularPolygon(6),  # Hexagon
            Star(),
            Ellipse(),
            Rectangle(),
            Line(start=ORIGIN, end=UP),
            Arrow(start=ORIGIN, end=UP),
        ]
        
        labels = [
            "Circle",
            "Square",
            "Triangle",
            "Pentagon",
            "Hexagon",
            "Star",
            "Ellipse",
            "Rectangle",
            "Line",
            "Arrow",
        ]
        
        # Initialize first object and label
        current_object = objects[0]
        current_label = Text(labels[0]).next_to(current_object, DOWN)
        
        self.add(current_object, current_label)
        self.wait(1)

        # Loop through the remaining objects
        for i in range(1, len(objects)):
            new_object = objects[i]
            new_label = Text(labels[i]).next_to(new_object, DOWN)
            
            self.play(Transform(current_object, new_object), Transform(current_label, new_label))
            self.wait(3)
        
        self.wait(2)
        self.play(FadeOut(current_object, current_label, new_label, new_object))
        self.display_code(r'''
class TransformObjects(Scene):
    def construct(self):
        objects = [
            Circle(), Square(), Triangle(),
            RegularPolygon(5), RegularPolygon(6),
            Star(), Ellipse(), Rectangle(),
            Line(start=ORIGIN, end=UP), Arrow(start=ORIGIN, end=UP),
        ]
        
        labels = [
            "Circle", "Square", "Triangle", "Pentagon", 
            "Hexagon", "Star", "Ellipse", "Rectangle", "Line", "Arrow",
        ]
        
        current_object = objects[0]
        current_label = Text(labels[0]).next_to(current_object, DOWN)
        
        self.add(current_object, current_label)
        self.wait(1)

        for i in range(1, len(objects)):
            new_object = objects[i]
            new_label = Text(labels[i]).next_to(new_object, DOWN)
            self.play(Transform(current_object, new_object), Transform(current_label, new_label))
            self.wait(3)
        
        self.wait(2))''')


    def display_code(self, code_text):
        code = Code(
            code=code_text,
            tab_width=4,
            font="Monospace",
            background="window",  # "window" to keep syntax highlighting
            insert_line_no=True,
            language="Python"
        ).scale(0.5)
        code.background_mobject.set_fill(opacity=0) 

        self.play(Write(code, run_time=15))  
        self.wait(2)
        self.play(FadeOut(code))


    def define_neural_network():
        # Create the neural network (simplified representation)
        layers = VGroup()
        input_layer = VGroup(*[Dot() for _ in range(4)]).arrange(DOWN, buff=0.5)
        hidden_layer = VGroup(*[Dot() for _ in range(10)]).arrange(DOWN, buff=0.5)
        output_layer = VGroup(*[Dot() for _ in range(2)]).arrange(DOWN, buff=0.5)

        layers.add(input_layer, hidden_layer, output_layer).arrange(RIGHT, buff=1.5)

        edges = VGroup()
        for start_layer, end_layer in zip(layers[:-1], layers[1:]):
            for start_dot in start_layer:
                for end_dot in end_layer:
                    edges.add(Line(start_dot.get_center(), end_dot.get_center()))

        neural_network = VGroup(layers, edges)
        return neural_network
    
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
        self.wait(8)
        
        return VGroup(header, writer, line)

