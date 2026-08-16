from manim import *

class ChangeNumbers(Scene):
    def construct(self):
        # Create a Text object for the word 'parameters'
        word = Text("parameters", color=BLUE).scale(0.7).shift(LEFT*1.5)
        
        # Create Tex objects for the numbers
        first_number = Tex("7840", color=RED).next_to(word, LEFT, buff=0.2)
        second_number = Tex("15000", color=RED).move_to(first_number, LEFT)
        
        # Add the first number and the word 'parameters' to the scene
        self.add(first_number, word)
        
        # Animate the change from the first number to the second number
        self.play(ReplacementTransform(first_number, second_number))

        # Keep the final state displayed
        self.wait(2)
