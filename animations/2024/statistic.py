from manim import *

class StatisticalModel(Scene):
    def construct(self):
        intro_group = self.introduction()
        self.play(FadeOut(intro_group))
        self.statistic_model()
        self.parametric_model()
        

    def introduction(self):
        header = Tex("Handbook of Statistics")
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)
        writer = Tex("Created by Ptolémé")
        writer_pos = [(line.get_left()[0] + line.get_right()[0]) / 2, line.get_bottom()[1] - 1, 0]
        writer.move_to(writer_pos)
        
        self.play(Write(header), Write(line))
        self.wait(1)
        self.play(Transform(header, Tex("Part I: Statistic and Parametric Models")))
        self.play(Write(writer))
        self.wait(2.5)
        
        return VGroup(header, writer, line)

    
    def statistic_model(self):
        # Definition of Statistical Model
        definition_title = Text("Definition (Statistical Model)").to_edge(UP)
        definition_text = Tex(
            r"""
            Consider \(x \in X\) as the data to be processed. We equip \(X\) with a sigma-algebra 
            \( \mathcal{A} \) to make it a measurable space. Then we consider the random variable 
            \(X\) associated with \(x\): \(x\) is a realization of \(X\). Therefore, we need to 
            consider the domain of \(X\): we denote it as \((\Omega, \mathcal{F}, P)\).
            \\
            Here, the probability measure with which we equip the space is important, as we do 
            not know it a priori. Thus, we consider a set \( \mathcal{P} \) of probabilities \(P\) 
            which could potentially correspond to the true probability measure. We denote 
            \(\mathcal{P}_X = \{P_X \mid P \in \mathcal{P}\}\) as the set of possible distributions 
            of \(X\).
            \\
            We recall that the distribution of \(X\) is the probability measure on 
            \((X, \mathcal{A})\) such that \(\forall A \in \mathcal{A}, P_X(A) = P(X^{-1}(A))\).
            \\
            Therefore, we call the statistical model the triplet:
            \[
            M = (X, \mathcal{A}, \mathcal{P}_X)
            \]
            """
        ).scale(0.6).next_to(definition_title, DOWN)

        self.play(Write(definition_title))
        self.wait(1)
        self.play(Write(definition_text))
        self.wait(75)
        self.play(FadeOut(definition_title), FadeOut(definition_text))

        # Explanation of X, A, and PX
        explanation_title = Text("Explanation of the Components of the Statistical Model").to_edge(UP).scale(0.8)
        self.play(Write(explanation_title))
        self.wait(1)

        # Explanation of X
        data_space = Tex(r"$1. \, X : \, \text{The data to be processed}$").scale(0.8).next_to(explanation_title, DOWN, buff=0.5)
        self.play(Write(data_space))
        self.wait(1)
        data_example = Tex(r"$\text{Example: } x_1, x_2, x_3, \ldots, x_n$").scale(0.7).next_to(data_space, DOWN, buff=0.5)
        self.play(Write(data_example))
        self.wait(2)
        colors = [RED, GREEN, BLUE, ORANGE]
        balls = VGroup(*[Dot(color=color).scale(1.5) for color in colors]).arrange(RIGHT, buff=0.5).next_to(data_example, DOWN, buff=0.5)
        
        # Add dots between the third and fourth ball
        dots = Tex(r"$\ldots$").scale(1.5).next_to(balls[2], RIGHT, buff=0.5)
        balls_with_dots = VGroup(balls[0], balls[1], balls[2], dots, balls[3]).arrange(RIGHT, buff=0.5).next_to(data_example, DOWN, buff=0.5)
        
        self.play(FadeIn(balls_with_dots))
        self.wait(2)

        self.play(FadeOut(data_space), FadeOut(data_example), FadeOut(balls_with_dots))

         # Explanation of A
        sigma_algebra = Tex(r"$2. \, \mathcal{A} : \, \text{The sigma-algebra for the measurable space}$").scale(0.6).next_to(explanation_title, DOWN, buff=0.5)
        self.play(Write(sigma_algebra))
        self.wait(2)
        sigma_example = Tex(r"$\{\emptyset, X, \{x_1\}, \{x_2, x_3\}, \ldots \}$").scale(0.7).next_to(sigma_algebra, DOWN, buff=0.5)
        self.play(Write(sigma_example))
        self.wait(2)
        
        # Represent x_1 and {x_2, x_3}
        colors = [RED, GREEN]
        ball_1 = Dot(color=colors[0]).scale(1.5).next_to(sigma_example, DOWN, buff=0.5)
        balls_2_3 = VGroup(Dot(color=colors[1]).scale(1.5), Dot(color=colors[1]).scale(1.5)).arrange(RIGHT, buff=0.2).next_to(ball_1, RIGHT, buff=1.5)
        dots = Tex(r"$\ldots$").scale(1.5).next_to(balls_2_3, RIGHT, buff=0.5)
        ball_4 = Dot(color=ORANGE).scale(1.5).next_to(dots, RIGHT, buff=0.5)

        balls_with_dots = VGroup(ball_1, balls_2_3, dots, ball_4).arrange(RIGHT, buff=0.5).next_to(sigma_example, DOWN, buff=0.5)

        ellipses = VGroup(Ellipse(width=1.2, height=0.8, color=colors[0]).move_to(ball_1),
                          Ellipse(width=1.5, height=1.0, color=colors[1]).move_to(balls_2_3))

        self.play(FadeIn(balls_with_dots))
        self.wait(1)
        self.play(FadeIn(ellipses))
        self.wait(2)

        self.play(FadeOut(sigma_algebra), FadeOut(sigma_example), FadeOut(balls_with_dots), FadeOut(ellipses))

        # Explanation of PX
        prob_space = Tex(r"$3. \, \mathcal{P}_X : \, \text{The set of possible distributions of } X$").scale(0.6).next_to(explanation_title, DOWN, buff=0.5)
        self.play(Write(prob_space))
        self.wait(2)

        # Concrete example of PX with famous distributions
        axes = Axes(
            x_range=[-4, 4], y_range=[0, 1, 0.2], 
            axis_config={"include_numbers": True}
        ).scale(0.8).to_edge(DOWN)

        # Normal distribution curve
        normal_curve = axes.plot(lambda x: np.exp(-x**2 / 2) / np.sqrt(2 * np.pi), color=BLUE, x_range=[-4, 4])

        # Bernoulli distribution points
        bernoulli_points = VGroup(
            Dot(axes.c2p(-2, 0.5), color=RED),
            Dot(axes.c2p(2, 0.5), color=RED)
        )

        # Uniform distribution line
        uniform_line = axes.plot(lambda x: 0.5 if -2 <= x <= 2 else 0, color=GREEN, x_range=[-4, 4])

        # Exponential distribution curve
        exponential_curve = axes.plot(lambda x: np.exp(-x) if x >= 0 else 0, color=ORANGE, x_range=[-4, 4])

        # Play animations
        self.play(Create(axes))
        self.play(Create(normal_curve))
        self.play(FadeIn(bernoulli_points))
        self.play(Create(uniform_line))
        self.play(Create(exponential_curve))
        self.wait(2)
        self.play(FadeOut(prob_space), FadeOut(axes), FadeOut(normal_curve), FadeOut(bernoulli_points), FadeOut(uniform_line), FadeOut(exponential_curve))

        # Conclusion
        conclusion = Tex(r"$\text{A statistical model is the triplet } M = (X, \mathcal{A}, \mathcal{P}_X)$").scale(0.6)
        self.play(Write(conclusion))
        self.wait(2)
        self.play(FadeOut(conclusion), FadeOut(explanation_title))


    def dominated_model(self):
        pass
    
    def parametric_model(self):
        # Title
        title = Text("Definition (Parametric Model)").to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # Definition
        definition_text = Tex(
            r"""
            A parametric model is a family of probability distributions that can be described using 
            a finite number of parameters. Formally, we denote a parametric model as:
            \[
            \mathcal{P}_\theta = \{P_\theta : \theta \in \Theta\}
            \]
            where \(\Theta\) is the parameter space.
            """
        ).scale(0.6).next_to(title, DOWN, buff=0.5)

        self.play(Write(definition_text))
        self.wait(10)
        self.play(FadeOut(definition_text))

        # Explanation of components
        explanation_title = Text("Explanation of the Components of the Parametric Model").to_edge(UP).scale(0.8)
        self.play(Transform(title, explanation_title))
        self.wait(1)

        # Explanation of θ
        theta_exp = Tex(r"$1. \, \theta : \, \text{The parameter that indexes the distributions}$").scale(0.8).next_to(explanation_title, DOWN, buff=0.5)
        self.play(Write(theta_exp))
        self.wait(2)
        theta_example = Tex(r"$\text{Example: } \theta = (\mu, \sigma^2) \text{ for a normal distribution}$").scale(0.7).next_to(theta_exp, DOWN, buff=0.5)
        self.play(Write(theta_example))
        self.wait(2)

        # Explanation of Θ
        theta_space = Tex(r"$2. \, \Theta : \, \text{The parameter space}$").scale(0.8).next_to(theta_example, DOWN, buff=0.5)
        self.play(Write(theta_space))
        self.wait(2)
        theta_space_example = Tex(r"$\text{Example: } \Theta = \mathbb{R} \times \mathbb{R}^+$").scale(0.7).next_to(theta_space, DOWN, buff=0.5)
        self.play(Write(theta_space_example))
        self.wait(2)

        self.play(FadeOut(theta_exp), FadeOut(theta_example), FadeOut(theta_space), FadeOut(theta_space_example))

        # Example of a parametric model: Normal distribution
        example_title = Text("Example of a Parametric Model: Normal Distribution").to_edge(UP).scale(0.8)
        self.play(Transform(title, example_title))
        self.wait(1)

        example_text = Tex(
            r"""
            Consider the normal distribution, parameterized by \(\mu\) (mean) and \(\sigma^2\) (variance):
            \[
            f(x \mid \mu, \sigma^2) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x - \mu)^2}{2\sigma^2}\right)
            \]
            Here, the parameter space is \(\Theta = \mathbb{R} \times \mathbb{R}^+\).
            """
        ).scale(0.6).next_to(example_title, DOWN, buff=0.5)

        self.play(Write(example_text))
        self.wait(10)
        self.play(FadeOut(example_text))

        # Visual representation of the normal distribution
        axes = Axes(
            x_range=[-4, 4], y_range=[0, 0.5, 0.1], 
            axis_config={"include_numbers": True}
        ).scale(0.8).to_edge(DOWN)

        mu_values = [0, 0, 0]
        sigma_values = [1, np.sqrt(2), 2]
        colors = [BLUE, GREEN, RED]

        curves = VGroup()
        for mu, sigma, color in zip(mu_values, sigma_values, colors):
            curve = axes.plot(lambda x: np.exp(-(x - mu)**2 / (2 * sigma**2)) / (np.sqrt(2 * np.pi) * sigma), color=color, x_range=[-4, 4])
            curves.add(curve)

        labels = VGroup(
            Tex(r"$\mu = 0, \sigma^2 = 1$").scale(0.5).next_to(curves[0], UP),
            Tex(r"$\mu = 0, \sigma^2 = 2$").scale(0.5).next_to(curves[1], UP),
            Tex(r"$\mu = 0, \sigma^2 = 4$").scale(0.5).next_to(curves[2], UP)
        )

        self.play(Create(axes))
        for curve, label in zip(curves, labels):
            self.play(Create(curve), Write(label))
            self.wait(2)

        self.play(FadeOut(axes), FadeOut(curves), FadeOut(labels))

        # Conclusion
        conclusion = Tex(r"$\text{A parametric model is the family of distributions } \mathcal{P}_\theta = \{P_\theta : \theta \in \Theta\}$").scale(0.6)
        self.play(Write(conclusion))
        self.wait(2)
        self.play(FadeOut(conclusion), FadeOut(title))
