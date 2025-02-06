import numpy as np
import random
import math
from manim import *

# Increase the frame width if you like a bigger scene.
FRAME_WIDTH = 2

class CompoundInterestPopulationAndEpidemic(Scene):
    def construct(self):
        # Add a title to emphasize the compound growth/company growth theme.
        title = Text("Compound Interest & Company Growth", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(2)
        
        # Create a time tracker that increments automatically.
        time_tracker = ValueTracker(0)
        time_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(time_tracker)

        # Generate random points inside a disc.
        N = 1660
        points = 2 * np.random.random((N, 3)) - 1
        points[:, 2] = 0
        points = points[[self.get_norm(p) < 1 for p in points]]
        points *= 2 * FRAME_WIDTH
        points = np.array(list(sorted(
            points, key=lambda p: self.get_norm(p) + 0.5 * random.random()
        )))

        # Create the objects that will represent the phases of growth.
        # Here, a dollar sign for initial capital, a person for a growing company,
        # and a virus for market disruption.
        dollar = Text("$", font_size=36)
        dollar.set_fill(GREEN)
        person = SVGMobject("C:/Users/Louis/OneDrive/TheEggcellent/Coding Projects/2024/Manim/animations/Svg/person.svg")
        person.set_fill(GREY_B, opacity=1)
        virus = SVGMobject("C:/Users/Louis/OneDrive/TheEggcellent/Coding Projects/2024/Manim/animations/Svg/virus.svg")
        virus.set_fill([RED, RED_D])
        # Clean up virus: remove extra parts and reset points.
        virus.remove(*virus[1:])
        virus[0].set_points(virus[0].get_subpaths()[0])
        templates = [dollar, person, virus]
        mob_height = 0.35

        # Set stroke and size for each template.
        for mob in templates:
            mob.set_stroke(BLACK, width=1, background=True)
            mob.set_height(mob_height)

        # Create groups for dollars, people, and viruses.
        dollars, people, viruses = groups = [
            VGroup(*(mob.copy().move_to(point) for point in points))
            for mob in templates
        ]

        # Optionally restrict the number of objects in each group to emphasize early stages.
        dollars.set_submobjects(list(dollars[:30]))
        people.set_submobjects(list(people[:600]))
        # We let viruses use all the points to show later explosive change.

        start_time = time_tracker.get_value()

        # This function uses a compound-interest-like growth formula.
        # Instead of math.exp(0.75*t), we use a slower rate initially.
        def get_n():
            elapsed_time = time_tracker.get_value() - start_time
            # For compound interest, P = P0 * (1 + r)^t; we take logarithms.
            # Here, we choose r = 0.4 so that growth is slower at first.
            n = int((1.4 ** elapsed_time) * 10)
            return min(n, len(points))

        # Updater for groups: sets objects' opacities based on elapsed time.
        def update_group(group, dt):
            group.set_opacity(0)
            for mob in group[:get_n()]:
                mob.set_opacity(0.9)

        # Updater for scaling the height of objects in a group.
        def update_height(group, alpha):
            for mob in group:
                mob.set_height(max(alpha * mob_height, 1e-4))

        # Add the updater to each group.
        for group in groups:
            group.add_updater(update_group)

        # Bring in the first group (dollars) for the initial phase.
        self.add(dollars)
        # Let the "capital" grow slowly for a longer time.
        self.wait(6)

        # Transition from dollars to people to represent company growth.
        self.play(
            UpdateFromAlphaFunc(people, update_height, run_time=4),
            UpdateFromAlphaFunc(dollars, update_height, rate_func=lambda t: self.smooth(1 - t), run_time=4, remover=True),
        )
        self.wait(8)

        # Transition from people to viruses to symbolize disruption or a market shift.
        self.play(
            UpdateFromAlphaFunc(viruses, update_height, run_time=4),
            UpdateFromAlphaFunc(people, update_height, rate_func=lambda t: self.smooth(1 - t), run_time=4, remover=True),
        )
        self.wait(8)

        # Optionally, fade out the final scene and the title.
        self.play(FadeOut(viruses), FadeOut(title))
        self.wait(2)

    def get_norm(self, point):
        return np.sqrt(np.sum(point**2))

    def smooth(self, alpha):
        return alpha * (2 - alpha)
