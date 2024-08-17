from manim import *

class ExpectedValueDice(Scene):
    def construct(self):
        # intro_group = self.introduction("Expected Value Animation", 
        #                                 "Handbook of Statistics - Part IV")
        # self.play(FadeOut(intro_group))
        # self.wait(1)
        
        # Define a rounded square to represent the dice faces
        def create_dice_face(dots):
            dots_group = VGroup(*[Dot(radius=0.2).move_to(pos) for pos in dots])
            return VGroup(dots_group)

        # Positions for dots on each face (1 through 6)
        dot_positions = [
            [ORIGIN],  # Face 1
            [LEFT, RIGHT],  # Face 2
            [UL, ORIGIN, DR],  # Face 3
            [UL, UR, DL, DR],  # Face 4
            [UL, UR, DL, DR, ORIGIN],  # Face 5
            [UL, UR, DL, DR, LEFT + ORIGIN, RIGHT + ORIGIN]  # Face 6
        ]
        
        # Create faces for the dice
        faces = VGroup(*[create_dice_face(positions) for positions in dot_positions])
        # Create the dice and set the initial face to 1
        dice =  RoundedRectangle(corner_radius=0.3, width=2.5, height=2.5, fill_color=DARK_BLUE, fill_opacity=0.8, stroke_color=WHITE, stroke_width=1)
        dice_face = faces[0].move_to(dice)

        self.add(dice_face,)
        self.add(dice)

        def display_outcome(face_number):
            new_face = faces[face_number - 1]
            self.play(Transform(dice_face, new_face), Rotate(dice, angle=PI/2), run_time=0.5)
            return dice_face

        def roll_dice_batch(batch_size, num_batches):
            for batch in range(num_batches):
                for i in range(batch_size):
                    outcome = np.random.randint(1, 7)
                    display_outcome(outcome)

        # Roll the dice 100 times in batches of 10
        roll_dice_batch(batch_size=6, num_batches=3)

        # # Display the formula for Expected Value
        # formula = MathTex(
        #     r"E[X] = \sum_{i=1}^{6} x_i f(x_i) = \sum_{i=1}^{6} x_i \times \frac{1}{6}"
        # ).to_edge(UP)
        # self.play(Write(formula))
        
        # # Show the calculated Expected Value
        # expected_value_text = Text("Expected Value: 3.5").to_edge(DOWN)
        # self.play(FadeIn(expected_value_text))

        # # Animate Convergence
        # avg_value = sum(np.random.randint(1, 7, 1000)) / 1000
        # convergence_text = Text(f"Average of Rolls: {avg_value:.2f}").next_to(expected_value_text, DOWN)
        # self.play(FadeIn(convergence_text))
        
        # # Show the convergence
        # self.play(convergence_text.animate.to_edge(RIGHT))

        # # Final summary
        # summary = Text("As the number of rolls increases, \nthe average converges to the expected value: 3.5").to_edge(DOWN)
        # self.play(Write(summary))

        # self.wait(3)

    def introduction(self, title1, title2):
        header = Tex(title1)
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)
        writer = Tex("Created by Ptolémé")
        writer_pos = [(line.get_left()[0] + line.get_right()[0]) / 2, line.get_bottom()[1] - 1, 0]
        writer.move_to(writer_pos)
        
        self.play(Write(header), Write(line))
        self.wait(0.5)
        self.play(Transform(header, Tex(title2)))
        self.play(Write(writer))
        self.wait(4)
        
        return VGroup(header, writer, line)