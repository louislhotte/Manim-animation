from manim import *
import matplotlib.pyplot as plt
from manim_voiceover import VoiceoverScene
import numpy as np


class Scene6_3(VoiceoverScene, MovingCameraScene):
    def construct(self):

        self.wait(2)

        txt = Tex("Thank you !").shift(UP)
        self.play(Write(txt))
        self.wait()

        self.play(FadeOut(txt), run_time=1)

        self.wait(2)


# Render the scene
if __name__ == "__main__":

    scene = Scene6_3()
    scene.render()
