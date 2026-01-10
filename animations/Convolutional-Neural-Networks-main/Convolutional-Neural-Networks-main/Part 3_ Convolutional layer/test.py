from manim import *

class HighlightAndBoldText(Scene):
    def construct(self):
        # Create a MarkupText object with bold and colored styles
        text = MarkupText(
            'Hello, <span weight="normal" foreground="red">World</span>!',
            font_size=48
        )

        # Display the text
        self.add(text)

        # Hold the scene
        self.wait(2)

        # To animate the transition to another style:
        # Create a target text object with different style settings
        text_target = MarkupText(
            'Hello, <span weight="heavy" foreground="blue">World</span>!',
            font_size=48
        )

        # Animate the change from the initial text to the target text
        self.play(Transform(text, text_target))

        # Hold the scene with the new style
        self.wait(2)
