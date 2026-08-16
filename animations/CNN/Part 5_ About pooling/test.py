from manim import *

class MoveLineWithUpdaters(Scene):
    def construct(self):
        # Create two dots at different positions
        rect1 = Rectangle(height=1, width=1, color=BLUE)
        rect2 = Rectangle(height=1, width=1, color=RED)
        
        rect1.move_to(LEFT * 3 + UP * 2)
        rect2.move_to(RIGHT * 3 + DOWN * 2)
        

        # Create a line and use updaters to keep it connected to the dots
        line = Line(rect1.get_corner(UR), rect2.get_corner(UL)).add_updater(
            lambda l: l.become(Line(rect1.get_corner(UR), rect2.get_corner(UL)))
        )

        # Add dots and line to the scene
        self.play(FadeIn(rect1), FadeIn(rect2))
        self.play(Create(line))
        self.wait()
        
        self.play(rect1.animate.shift(RIGHT * 2 + DOWN * 2), 
                  rect2.animate.shift(LEFT * 2 + UP * 2),
                  run_time=1)

        self.play(rect2.animate.shift(RIGHT * 2 + UP * 2), run_time=1)
        self.wait()
