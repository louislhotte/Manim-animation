from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService

from elevenlabs import set_api_key


class Scene1(VoiceoverScene):
    def construct(self):

        # Create the initial rectangle
        rect = Rectangle(height=1, width=1, color=WHITE)
        # Create a larger rectangle
        rect2 = Rectangle(height=2, width=2, color=WHITE)

        # Keep a copy of the original rectangle before any transformations
        rect_original = rect.copy()

        self.wait(1)
        # Create the smaller rectangle on the scene
        self.play(Create(rect))
        # Transform the smaller rectangle into the larger rectangle
        self.play(Transform(rect, rect2))
        # Revert the transformation by transforming back to the original rectangle
        self.play(Transform(rect, rect_original))

        self.play(rect.animate.shift(RIGHT))
        # Fade out the rectangle
        self.play(FadeOut(rect))
        self.wait(1)


# Render the scene
if __name__ == "__main__":

    scene = Scene1()
    scene.render()
