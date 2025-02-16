from manim import *

class TransformObjects(Scene):
    def construct(self):
        intro_group = self.introduction("Manim Tutorial (Part II)", 
                                        "25 Manim Animations in ONE Video")
        self.play(FadeOut(intro_group))
        self.wait(1)
        

        objects = [
            Arc(), AnnularSector(), Brace(Line(LEFT, RIGHT)), Polygon(*[LEFT, UP, RIGHT, DOWN]),
            RoundedRectangle(), Cross(), CurvedArrow(LEFT, RIGHT),
            DoubleArrow(LEFT, RIGHT), VGroup(Circle(), Square()), VGroup(Triangle(), Square()),
            VGroup(Rectangle(), Ellipse()), VGroup(Line(LEFT, RIGHT), Arrow(UP, DOWN)),
            VGroup(Star(), RegularPolygon(7)), DashedLine(LEFT, RIGHT), Axes(),
            ThreeDAxes(), Surface(lambda u, v: np.array([u, v, u**2 - v**2])), Sphere(), Cube(), Cone(), Cylinder(), Torus(), Dot(),
            Vector(UP), Matrix([[1, 2], [3, 4]]), DecimalNumber(3.14),
            Integer(42), LabeledDot("A"), BraceLabel(Line(LEFT, RIGHT), "Label"),
            Line().add_tip(), DashedVMobject(Line(LEFT, RIGHT)), VMobject(), 
            FunctionGraph(lambda x: x**2), ImplicitFunction(lambda x, y: x**2 + y**2 - 1),
            Arrow3D(ORIGIN, [1, 1, 1]),
            Annulus(), Angle(Line(LEFT, ORIGIN), Line(ORIGIN, UP)),
            Sector(), ParametricFunction(lambda t: np.array([np.cos(t), np.sin(t), 0])),
            ArcBetweenPoints(LEFT, RIGHT), CurvedDoubleArrow(LEFT, RIGHT),
            RoundedRectangle(corner_radius=0.5, height=2, width=3),
            Arc(start_angle=0, angle=PI)
        ]

        
        labels = [
            "Arc",
            "AnnularSector",
            "Brace",
            "Polygon",
            "RoundedRectangle",
            "Cross",
            "CurvedArrow",
            "DoubleArrow",
            "VGroup (Circle, Square)",
            "VGroup (Triangle, Square)",
            "VGroup (Rectangle, Ellipse)",
            "VGroup (Line, Arrow)",
            "VGroup (Star, RegularPolygon(7))",
            "DashedLine",
            "Axes",
            "ThreeDAxes",
            "Surface",
            "Sphere",
            "Cube",
            "Cone",
            "Cylinder",
            "Torus",
            "Dot",
            "Vector",
            "Matrix",
            "DecimalNumber",
            "Integer",
            "LabeledDot",
            "BraceLabel",
            "Line (with tip)",
            "DashedVMobject",
            "VMobject",
            "FunctionGraph",
            "ImplicitFunction",
            "Arrow3D",
            "Annulus",
            "Angle",
            "Sector",
            "ParametricFunction",
            "ArcBetweenPoints",
            "CurvedDoubleArrow",
            "RoundedRectangle (corner_radius=0.5, height=2, width=3)",
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
            self.wait(1)
            if i == 24:
                break
            print(i)
        
        self.wait(2)
        self.play(FadeOut(current_object, current_label, new_label, new_object))

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

