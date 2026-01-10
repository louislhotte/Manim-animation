from manim import *

class LightUpArrow(Scene):
    def construct(self):
        # Create an arrow
        arrow = Arrow(start=LEFT*4, end=RIGHT*4, buff=0, color=BLUE)

        # Animate the arrow being lit in white from left to right
        self.play(Create(arrow, rate_func=linear), run_time=2)
        self.wait(2)

        # If you want the arrow to change color to white as it lights up
        # We can create a white arrow and use TransformFromCopy with a linear rate_func
        white_arrow = Arrow(start=LEFT*4, end=RIGHT*4, buff=0, color=WHITE)
        self.play(TransformFromCopy(arrow, white_arrow, rate_func=linear), run_time=2)
        self.wait(2)
