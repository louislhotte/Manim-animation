from manim import *
import numpy as np

BLACK = "#000000"
WHITE = "#FFFFFF"
W = config.frame_width
H = config.frame_height

L1 = 1
L2 = 1
m1 = 1
m2 = 1
g = 9.8

# Initial conditions
theta1 = -PI / 2
theta2 = -PI / 2
omega1 = 0
omega2 = 0

def derivs(state, t):
    dtheta1 = state[2]
    dtheta2 = state[3]
    delta = state[1] - state[0]

    den1 = (m1 + m2) * L1 - m2 * L1 * np.cos(delta) * np.cos(delta)
    den2 = (L2 / L1) * den1

    domega1 = ((m2 * L1 * state[2] * state[2] * np.sin(delta) * np.cos(delta)
                + m2 * g * np.sin(state[1]) * np.cos(delta)
                + m2 * L2 * state[3] * state[3] * np.sin(delta)
                - (m1 + m2) * g * np.sin(state[0]))
               / den1)

    domega2 = ((- m2 * L2 * state[3] * state[3] * np.sin(delta) * np.cos(delta)
                + (m1 + m2) * (g * np.sin(state[0]) * np.cos(delta)
                               - L1 * state[2] * state[2] * np.sin(delta)
                               - g * np.sin(state[1])))
               / den2)

    return np.array([dtheta1, dtheta2, domega1, domega2])

# RK4 method for solving ODEs
def rk4_step(state, t, dt):
    k1 = derivs(state, t)
    k2 = derivs(state + 0.5 * k1 * dt, t + 0.5 * dt)
    k3 = derivs(state + 0.5 * k2 * dt, t + 0.5 * dt)
    k4 = derivs(state + k3 * dt, t + dt)
    return state + (k1 + 2 * k2 + 2 * k3 + k4) * dt / 6

class DoublePendulumScene(Scene):
    def construct(self):
        self.renderer.background_color = BLACK
        self.camera.background_color = BLACK

        intro_group = self.introduction()
        self.play(FadeOut(intro_group))
        self.wait(1)


        # Title and line
        header = Tex("Double pendulum animation")
        header.set_width(8)
        header.to_edge(UP)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)

        self.add(header, line)

        # Setup
        anchor_offset = RIGHT * 2  # Adding offset to the right
        anchor = DashedLine(ORIGIN + anchor_offset + UP * 0.5, ORIGIN + anchor_offset + DOWN * 0.5, color=WHITE)
        rod1 = Line(anchor.get_center(), anchor.get_center() + [L1 * np.sin(theta1), -L1 * np.cos(theta1), 0], color=WHITE)
        rod2 = Line(rod1.get_end(), rod1.get_end() + [L2 * np.sin(theta2), -L2 * np.cos(theta2), 0], color=WHITE)
        mass1 = Circle(radius=0.1, color=DARK_BLUE, fill_opacity=1).move_to(rod1.get_end())
        mass2 = Circle(radius=0.1, color=RED_D, fill_opacity=1).move_to(rod2.get_end())

        self.add(anchor, rod1, rod2, mass1, mass2)

        state = np.array([theta1, theta2, omega1, omega2])
        dt = 0.0025  # Smaller dt to slow down the pendulum

        def update_pendulums(mob, dt):
            nonlocal state
            state = rk4_step(state, 0, dt)
            rod1.put_start_and_end_on(ORIGIN + anchor_offset, ORIGIN + anchor_offset + [L1 * np.sin(state[0]), -L1 * np.cos(state[0]), 0])
            rod2.put_start_and_end_on(rod1.get_end(), rod1.get_end() + [L2 * np.sin(state[1]), -L2 * np.cos(state[1]), 0])
            mass1.move_to(rod1.get_end())
            mass2.move_to(rod2.get_end())

        rod1.add_updater(update_pendulums)
        rod2.add_updater(update_pendulums)
        mass1.add_updater(lambda mob, dt: mass1.move_to(rod1.get_end()))
        mass2.add_updater(lambda mob, dt: mass2.move_to(rod2.get_end()))

        # Trail for the second mass
        trail = TracedPath(mass2.get_center, stroke_color=RED, stroke_width=2, stroke_opacity=0.8, dissipating_time=5)
        self.add(trail)

        # Legend
        legend_text = VGroup(
            Tex(r"$\frac{d\theta_1}{dt} = \omega_1$", color=WHITE),
            Tex(r"$\frac{d\theta_2}{dt} = \omega_2$", color=WHITE), 
            Tex(r"$\frac{d\omega_1}{dt} = \frac{m_2 L_1 \omega_1^2 \sin(\Delta) \cos(\Delta) + m_2 g \sin(\theta_2) \cos(\Delta)}{(m_1 + m_2) L_1 - m_2 L_1 \cos^2(\Delta)}$", color=WHITE),
            Tex(r"$+ \frac{m_2 L_2 \omega_2^2 \sin(\Delta) - (m_1 + m_2) g \sin(\theta_1)}{(m_1 + m_2) L_1 - m_2 L_1 \cos^2(\Delta)}$", color=WHITE),
            Tex(r"$\frac{d\omega_2}{dt} = \frac{-m_2 L_2 \omega_2^2 \sin(\Delta) \cos(\Delta)}{(L_2 / L_1) ((m_1 + m_2) L_1 - m_2 L_1 \cos^2(\Delta))}$", color=WHITE),
            Tex(r"$+ \frac{(m_1 + m_2) (g \sin(\theta_1) \cos(\Delta) - L_1 \omega_1^2 \sin(\Delta) - g \sin(\theta_2))}{(L_2 / L_1) ((m_1 + m_2) L_1 - m_2 L_1 \cos^2(\Delta))}$", color=WHITE)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.6)

        legend = SurroundingRectangle(legend_text, color=WHITE, fill_color=BLACK, fill_opacity=0)
        
        legend_group = VGroup(legend, legend_text).to_edge(LEFT)

        self.add(legend_group)

        # Variable display
        variables_text = Text("", font_size=24, color=WHITE).to_corner(UR)

        def update_variables_text(mob):
            theta1_text = f"θ1 = {state[0]:.2f}"
            theta2_text = f"θ2 = {state[1]:.2f}"
            omega1_text = f"ω1 = {state[2]:.2f}"
            omega2_text = f"ω2 = {state[3]:.2f}"
            mob.text = f"{theta1_text}\n{theta2_text}\n{omega1_text}\n{omega2_text}"

        variables_text.add_updater(update_variables_text)
        self.add(variables_text)

        # Dynamic theta1 and theta2 display
        theta1_display = DecimalNumber(np.degrees(state[0]) % 360, num_decimal_places=2, color=WHITE).next_to(legend_group, RIGHT, buff=6.5)
        theta2_display = DecimalNumber(np.degrees(state[1]) % 360, num_decimal_places=2, color=WHITE).next_to(theta1_display, DOWN, buff=0.5)

        theta1_label = Tex(r"$\theta_1$ = ", color=WHITE).next_to(theta1_display, LEFT, buff=0.2)
        theta2_label = Tex(r"$\theta_2$ = ", color=WHITE).next_to(theta2_display, LEFT, buff=0.2)

        self.add(theta1_label, theta1_display, theta2_label, theta2_display)

        theta1_display.add_updater(lambda d: d.set_value(np.degrees(state[0]) % 360))
        theta2_display.add_updater(lambda d: d.set_value(np.degrees(state[1]) % 360))

        self.wait(140)

    def introduction(self):
        header = Tex("Double Pendulum Animation | Manim CE")
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)
        writer = Tex("Created by Ptolémé")
        writer_pos = [(line.get_left()[0] + line.get_right()[0]) / 2, line.get_bottom()[1] - 1, 0]
        writer.move_to(writer_pos)
        
        self.play(Write(header), Write(line))
        self.wait(0.5)
        self.play(Transform(header, Tex("Chaotic Visualisation")))
        self.play(Write(writer))
        self.wait(1.5)
        
        return VGroup(header, writer, line)

if __name__ == "__main__":
    scene = DoublePendulumScene()
    scene.render()
