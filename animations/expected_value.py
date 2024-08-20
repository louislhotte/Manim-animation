from manim import *

class ExpectedValueDice(Scene):
    def construct(self):
        # intro_group = self.introduction("Expected Value Animation", 
        #                                 "Handbook of Statistics - Part IV")
        # self.play(FadeOut(intro_group))
        # self.wait(1)
        # self.dice_scene()
        self.explanations()
        # Define a rounded square to represent the dice faces
        

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


    def explanations(self):
        text = Text("On a single throw, we can get any value between 1 and 6").scale(0.5)
        self.play(FadeIn(text))
        self.wait(1)
        self.play(Transform(text, Text("The following simulation gives us the result of 100 throws").scale(0.5)))
        self.wait(2)
        self.play(FadeOut(text))
        self.boxes()
    

    def boxes(self):
        num_boxes = 100
        grid = VGroup()
        num_columns = 10
        spacing = 0.6
        for i in range(num_boxes):
            roll_result = np.random.randint(1, 7)
            box = Square(side_length=1, fill_color=BLUE, fill_opacity=0.6, stroke_color=WHITE).scale(0.5)
            label = Text(str(roll_result), font_size=24).move_to(box.get_center()).scale(0.3)  # Move the label inside the box
            box_group = VGroup(box, label)
            row = i // num_columns
            col = i % num_columns
            box_group.move_to(np.array([col * spacing, -row * spacing, 0]))
            grid.add(box_group)

        grid.move_to(ORIGIN)  # Center the entire grid on the screen
        self.play(FadeIn(grid, lag_ratio=0.1))
        self.wait(5)
        self.play(FadeOut(grid))


    def dice_scene(self):
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

        text = Text("Let's take a dice.").scale(0.5)
        self.play(FadeIn(text))
        self.wait(1)
        self.play(Transform(text, Text("Each simulation gives us an outcome value between 1 and 6").scale(0.5)))
        self.wait(2)
        self.play(FadeOut(text))

        faces = VGroup(*[create_dice_face(positions) for positions in dot_positions])
        dice =  RoundedRectangle(corner_radius=0.3, width=3.5, height=3.5, fill_color=DARK_BLUE, fill_opacity=0.8, stroke_color=WHITE, stroke_width=1)
        dice_face = faces[0].move_to(dice)

        outcome_text = Text("Outcome").next_to(dice, UP, buff=1)
        self.add(dice_face)
        self.add(dice)
        self.add(outcome_text)

        def display_outcome(face_number):
            new_face = faces[face_number - 1]
            self.play(Transform(outcome_text, (Text(f"Outcome = {face_number}").next_to(dice, UP, buff=1))), run_time=0.25)
            self.play(Transform(dice_face, new_face), Rotate(dice, angle=PI/2), run_time=1)
            self.wait(0.5)
            return dice_face

        def roll_dice_batch(batch_size, num_batches):
            for batch in range(num_batches):
                for i in range(batch_size):
                    outcome = np.random.randint(1, 7)
                    display_outcome(outcome)
                    
        roll_dice_batch(batch_size=6, num_batches=1)
        self.play(FadeOut(dice_face, dice, outcome_text))

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
