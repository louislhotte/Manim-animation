from manim import *

class PendulumEnergyGraph(Scene):
    def construct(self):
        # Constants for the pendulum
        length = 3
        g = 9.8
        initial_angle = 0.3  # Initial angle (in radians)
        bob_radius = 0.2

        # Create the pivot point
        pivot = np.array([0, 2, 0])

        # Create the pendulum bob and rod
        rod = Line(pivot, pivot + length * np.array([np.sin(initial_angle), -np.cos(initial_angle), 0]), color=BLUE)
        bob = Dot(rod.get_end(), radius=bob_radius, color=RED)

        # Add rod and bob to the scene
        pendulum = VGroup(rod, bob)
        self.add(pendulum)

        # Create the axes for the energy graph
        energy_graph = Axes(
            x_range=[0, 10, 1],
            y_range=[-1, 5, 1],
            x_length=7,
            y_length=4,
            axis_config={"color": WHITE},
            x_axis_config={"numbers_to_include": np.arange(0, 11, 2)},
            y_axis_config={"numbers_to_include": np.arange(0, 6, 1)},
        ).to_edge(RIGHT)

        # Labels for the graph
        graph_labels = energy_graph.get_axis_labels(x_label="t", y_label="Energy")
        self.add(energy_graph, graph_labels)

        # Initialize energy graph lines
        kinetic_energy_line = energy_graph.plot_line_graph(
            x_values=[],
            y_values=[],
            add_vertex_dots=False,
            line_color=GREEN,
            stroke_width=3,
            name="Kinetic Energy",
        )
        potential_energy_line = energy_graph.plot_line_graph(
            x_values=[],
            y_values=[],
            add_vertex_dots=False,
            line_color=RED,
            stroke_width=3,
            name="Potential Energy",
        )
        mechanical_energy_line = energy_graph.plot_line_graph(
            x_values=[],
            y_values=[],
            add_vertex_dots=False,
            line_color=YELLOW,
            stroke_width=3,
            name="Mechanical Energy",
        )

        self.add(kinetic_energy_line, potential_energy_line, mechanical_energy_line)

        # Function to update the pendulum and energies
        def update_pendulum_and_graph(mob, dt):
            t = self.time
            angle = initial_angle * np.cos(np.sqrt(g / length) * t)
            rod.put_start_and_end_on(pivot, pivot + length * np.array([np.sin(angle), -np.cos(angle), 0]))
            bob.move_to(rod.get_end())

            # Energies
            velocity = -initial_angle * np.sqrt(g / length) * np.sin(np.sqrt(g / length) * t)
            kinetic_energy = 0.5 * (velocity ** 2)
            potential_energy = g * (length * (1 - np.cos(angle)))
            mechanical_energy = kinetic_energy + potential_energy

            # Update the graph data
            kinetic_energy_line.add_point_to_plot((t, kinetic_energy))
            potential_energy_line.add_point_to_plot((t, potential_energy))
            mechanical_energy_line.add_point_to_plot((t, mechanical_energy))

        pendulum.add_updater(update_pendulum_and_graph)

        # Slow down the initial motion of the pendulum
        self.wait(1)  # Initial wait
        self.play(UpdateFromAlphaFunc(pendulum, lambda mob, alpha: update_pendulum_and_graph(mob, alpha / 2)), run_time=5)

        # Restore normal speed
        self.remove(pendulum)
        pendulum.remove_updater(update_pendulum_and_graph)
        self.play(UpdateFromAlphaFunc(pendulum, lambda mob, alpha: update_pendulum_and_graph(mob, alpha)), run_time=5)

        self.wait(2)  # Wait to show the final state