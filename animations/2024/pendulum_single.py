from manim import *
import numpy as np

class FullVideo(Scene):
    def construct(self):
        self.play_pendulum_scene()
        self.play_explanations()

    def play_pendulum_scene(self):
        length = 3
        g = 9.8
        initial_angle = 1
        bob_radius = 0.2

        pivot = np.array([3, 2, 0])  # Move the pivot point to the right
        rod = Line(pivot, pivot + length * np.array([np.sin(initial_angle), -np.cos(initial_angle), 0]), color=BLUE)
        bob = Dot(rod.get_end(), radius=bob_radius, color=RED)

        support_line = DashedLine(pivot + np.array([0, 0.5, 0]), pivot, color=WHITE)

        pendulum = VGroup(support_line, rod, bob).to_edge(RIGHT)
        self.add(pendulum)

        energy_graph = Axes(
            x_range=[0, 10, 1],
            y_range=[-0.5, 15, 2],  # Adjusted y_range for better scaling
            x_length=7,
            y_length=4,
            axis_config={"color": DARK_BLUE},
            x_axis_config={"numbers_to_include": np.arange(0, 11, 2)},
            y_axis_config={"numbers_to_include": np.arange(-0.5, 15, 2)},  # Adjusted y-axis tick marks
        ).to_edge(LEFT)

        graph_labels = energy_graph.get_axis_labels(x_label="t", y_label="Energy")
        self.add(energy_graph, graph_labels)

        time_tracker = ValueTracker(0)

        def get_angle(t):
            return initial_angle * np.cos(np.sqrt(g / length) * t)

        def get_kinetic_energy(t):
            velocity = -initial_angle * np.sqrt(g / length) * np.sin(np.sqrt(g / length) * t) * 1.5  # Increased velocity
            return 0.5 * velocity**2

        def get_potential_energy(t):
            angle = get_angle(t)
            return g * (length * (1 - np.cos(angle)))

        def get_mechanical_energy(t):
            return get_kinetic_energy(t) + get_potential_energy(t)

        kinetic_energy_line = always_redraw(lambda: energy_graph.plot(
            lambda t: get_kinetic_energy(t), 
            x_range=[0, time_tracker.get_value()], 
            color=GREEN
        ))

        potential_energy_line = always_redraw(lambda: energy_graph.plot(
            lambda t: get_potential_energy(t), 
            x_range=[0, time_tracker.get_value()], 
            color=RED
        ))

        mechanical_energy_line = always_redraw(lambda: energy_graph.plot(
            lambda t: get_mechanical_energy(t), 
            x_range=[0, time_tracker.get_value()], 
            color=YELLOW
        ))

        self.add(kinetic_energy_line, potential_energy_line, mechanical_energy_line)

        legend = VGroup(
            VGroup(Line(color=GREEN).scale(0.5), MathTex("Kinetic", color=GREEN).scale(0.5)).arrange(RIGHT, buff=0.2),
            VGroup(Line(color=RED).scale(0.5), MathTex("Potential", color=RED).scale(0.5)).arrange(RIGHT, buff=0.2),
            VGroup(Line(color=YELLOW).scale(0.5), MathTex("Mechanical", color=YELLOW).scale(0.5)).arrange(RIGHT, buff=0.2)
        ).arrange(DOWN, buff=0.2).next_to(energy_graph, DOWN, buff=0.5)

        legend_background = SurroundingRectangle(legend, color=WHITE, buff=0.2, fill_opacity=0.1)

        self.add(legend_background, legend)

        def update_pendulum(mob):
            t = time_tracker.get_value()
            angle = get_angle(t)
            new_position = pivot + length * np.array([np.sin(angle), -np.cos(angle), 0])
            rod.put_start_and_end_on(pivot, new_position)
            bob.move_to(new_position)
            support_line.put_start_and_end_on(pivot + np.array([0, 0.5, 0]), pivot)

        pendulum.add_updater(update_pendulum)

        self.play(time_tracker.animate.set_value(5), run_time=30, rate_func=linear)

        self.wait(2)

        self.play(time_tracker.animate.set_value(10), run_time=5, rate_func=linear)
        self.wait(1)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

    def play_explanations(self):
        length = 3
        initial_angle = 0.5
        pivot = np.array([0, -2, 0])
        rod = Line(pivot, pivot + length * np.array([np.sin(initial_angle), -np.cos(initial_angle), 0]), color=BLUE)
        bob = Dot(rod.get_end(), radius=0.2, color=RED)

        pendulum = VGroup(rod, bob).shift(DOWN*2)
        self.add(pendulum)

        explanation_1 = Text("Mechanical Energy is the sum of Kinetic and Potential Energy.", font_size=24)
        explanation_2 = Text("Kinetic Energy (K) is the energy of motion:", font_size=24)
        formula_kinetic = MathTex("K = \\frac{1}{2}mv^2", font_size=32)
        explanation_3 = Text("Potential Energy (U) is the energy stored due to position:", font_size=24)
        formula_potential = MathTex("U = mgh", font_size=32)
        explanation_4 = Text("In a pendulum, the mechanical energy is conserved.", font_size=24)
        formula_mechanical = MathTex("E_{mech} = K + U", font_size=32)

        text_blocks = VGroup(
            explanation_1,
            explanation_2,
            formula_kinetic,
            explanation_3,
            formula_potential,
            explanation_4,
            formula_mechanical
        ).arrange(DOWN, buff=0.5).shift(UP*1.5)
        
        for text in text_blocks:
            print(text)
            self.play(Write(text))
            self.wait(2)
         

class Explanations(Scene):
    def construct(self):
        length = 3
        initial_angle = 0.5
        pivot = np.array([0, -2, 0])
        rod = Line(pivot, pivot + length * np.array([np.sin(initial_angle), -np.cos(initial_angle), 0]), color=BLUE)
        bob = Dot(rod.get_end(), radius=0.2, color=RED)

        pendulum = VGroup(rod, bob).shift(DOWN*2)
        self.add(pendulum)

        explanation_1 = Text("Mechanical Energy is the sum of Kinetic and Potential Energy.", font_size=24)
        explanation_2 = Text("Kinetic Energy (K) is the energy of motion:", font_size=24)
        formula_kinetic = MathTex("K = \\frac{1}{2}mv^2", font_size=32)
        explanation_3 = Text("Potential Energy (U) is the energy stored due to position:", font_size=24)
        formula_potential = MathTex("U = mgh", font_size=32)
        explanation_4 = Text("In a pendulum, the mechanical energy is conserved.", font_size=24)
        formula_mechanical = MathTex("E_{mech} = K + U", font_size=32)

        text_blocks = VGroup(
            explanation_1,
            explanation_2,
            formula_kinetic,
            explanation_3,
            formula_potential,
            explanation_4,
            formula_mechanical
        ).arrange(DOWN, buff=0.5).shift(UP*1.5)
        
        for text in text_blocks:
            print(text)
            self.play(Write(text))
            self.wait(2)

class PendulumEnergyGraph(Scene):
    def construct(self):
        length = 3
        g = 9.8
        initial_angle = 1
        bob_radius = 0.2

        pivot = np.array([3, 2, 0])  # Move the pivot point to the right
        rod = Line(pivot, pivot + length * np.array([np.sin(initial_angle), -np.cos(initial_angle), 0]), color=BLUE)
        bob = Dot(rod.get_end(), radius=bob_radius, color=RED)

        support_line = DashedLine(pivot + np.array([0, 0.5, 0]), pivot, color=WHITE)

        pendulum = VGroup(support_line, rod, bob).to_edge(RIGHT)
        self.add(pendulum)

        energy_graph = Axes(
            x_range=[0, 10, 1],
            y_range=[-0.5, 15, 2],  # Adjusted y_range for better scaling
            x_length=7,
            y_length=4,
            axis_config={"color": DARK_BLUE},
            x_axis_config={"numbers_to_include": np.arange(0, 11, 2)},
            y_axis_config={"numbers_to_include": np.arange(-0.5, 15, 2)},  # Adjusted y-axis tick marks
        ).to_edge(LEFT)
        graph_labels = energy_graph.get_axis_labels(x_label="t", y_label="Energy")
        self.add(energy_graph, graph_labels)
        time_tracker = ValueTracker(0)
        def get_angle(t):
            return initial_angle * np.cos(np.sqrt(g / length) * t)
        def get_kinetic_energy(t):
            velocity = -initial_angle * np.sqrt(g / length) * np.sin(np.sqrt(g / length) * t) * 1.5  # Increased velocity
            return 0.5 * velocity**2
        def get_potential_energy(t):
            angle = get_angle(t)
            return g * (length * (1 - np.cos(angle)))
        def get_mechanical_energy(t):
            return get_kinetic_energy(t) + get_potential_energy(t)
        kinetic_energy_line = always_redraw(lambda: energy_graph.plot(
            lambda t: get_kinetic_energy(t), 
            x_range=[0, time_tracker.get_value()], 
            color=GREEN
        ))
        potential_energy_line = always_redraw(lambda: energy_graph.plot(
            lambda t: get_potential_energy(t), 
            x_range=[0, time_tracker.get_value()], 
            color=RED
        ))
        mechanical_energy_line = always_redraw(lambda: energy_graph.plot(
            lambda t: get_mechanical_energy(t), 
            x_range=[0, time_tracker.get_value()], 
            color=YELLOW
        ))
        self.add(kinetic_energy_line, potential_energy_line, mechanical_energy_line)
        legend = VGroup(
            VGroup(Line(color=GREEN).scale(0.5), MathTex("Kinetic", color=GREEN).scale(0.5)).arrange(RIGHT, buff=0.2),
            VGroup(Line(color=RED).scale(0.5), MathTex("Potential", color=RED).scale(0.5)).arrange(RIGHT, buff=0.2),
            VGroup(Line(color=YELLOW).scale(0.5), MathTex("Mechanical", color=YELLOW).scale(0.5)).arrange(RIGHT, buff=0.2)
        ).arrange(DOWN, buff=0.2).next_to(energy_graph, DOWN, buff=0.5)
        legend_background = SurroundingRectangle(legend, color=WHITE, buff=0.2, fill_opacity=0.1)
        self.add(legend_background, legend)
        def update_pendulum(mob):
            t = time_tracker.get_value()
            angle = get_angle(t)
            new_position = pivot + length * np.array([np.sin(angle), -np.cos(angle), 0])
            rod.put_start_and_end_on(pivot, new_position)
            bob.move_to(new_position)
            support_line.put_start_and_end_on(pivot + np.array([0, 0.5, 0]), pivot)
        pendulum.add_updater(update_pendulum)
        self.play(time_tracker.animate.set_value(5), run_time=10, rate_func=linear)
        self.wait(2)
        self.play(time_tracker.animate.set_value(10), run_time=5, rate_func=linear)
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
