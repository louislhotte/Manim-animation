from manim import *

class KochCurve(Scene):
    def construct(self):
        # Starting with an equilateral triangle
        triangle = self.create_equilateral_triangle()
        self.play(Create(triangle))
        self.wait(1)

        # Iterating to create the Koch Curve
        for _ in range(4):
            triangle = self.koch_iteration(triangle)
            self.play(Transform(triangle, triangle.copy()))
            self.wait(1)

    def create_equilateral_triangle(self):
        # Create an equilateral triangle centered at origin
        return Polygon(ORIGIN, RIGHT, np.array([0.5, np.sqrt(3)/2, 0]), color=WHITE)

    def koch_iteration(self, shape):
        # Function to apply one iteration of the Koch snowflake process
        new_points = []
        points = shape.get_points()

        for i in range(len(points)):
            start = points[i]
            end = points[(i + 1) % len(points)]
            vector = end - start

            # Points for the new triangle
            p1 = start + vector / 3
            p2 = start + vector * 2 / 3
            p3 = p1 + np.array([-vector[1], vector[0], 0]) * np.sqrt(3) / 6

            new_points += [start, p1, p3, p2]
        
        new_shape = Polygon(*new_points, color=WHITE)
        return new_shape

