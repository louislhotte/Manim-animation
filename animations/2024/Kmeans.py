from manim import *
import numpy as np
from sklearn.datasets import make_blobs

class KMeansClustering:
    def __init__(self, k):
        self.k = k
        self.states = []
    def fit(self, X, num_iter=8):
        if self.k == 3:
            centers = np.array([[0.2, -0.2], [0.3, -0.2], [0.2, -0.3]])
        else:
            indices = np.random.choice(len(X), self.k, replace=False)
            centers = X[indices].copy()
        clusters = np.array([np.argmin(np.linalg.norm(x - centers, axis=1)) for x in X])
        self.states.append({'centers': centers.copy(), 'clusters': clusters.copy(), 'step': "Initial Assignment"})
        for i in range(num_iter):
            new_centers = np.zeros_like(centers)
            for j in range(self.k):
                if np.any(clusters == j):
                    new_centers[j] = np.mean(X[clusters == j], axis=0)
                else:
                    new_centers[j] = centers[j]
            self.states.append({'centers': new_centers.copy(), 'clusters': clusters.copy(), 'step': "Update Centers"})
            centers = new_centers
            clusters = np.array([np.argmin(np.linalg.norm(x - centers, axis=1)) for x in X])
            self.states.append({'centers': centers.copy(), 'clusters': clusters.copy(), 'step': "Reassign Observations"})

class KMeansExplanation(Scene):
    def construct(self):
        bullet_points = VGroup(
            Text("• Initialize k random centers", font_size=24),
            Text("• Assign each point to the nearest center", font_size=24),
            Text("• Update centers as the mean of assigned points", font_size=24),
            Text("• Repeat until convergence", font_size=24)
        )
        bullet_points.arrange(DOWN, aligned_edge=LEFT)
        self.play(Write(bullet_points))
        self.wait(4)
        self.play(FadeOut(bullet_points))

class KMeansLiveAnimation(Scene):
    def construct(self):
        axes = Axes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], x_length=6, y_length=6, tips=True)
        axes.to_edge(DOWN)
        self.play(Create(axes))
        info_text = Text("k = 3, n = 300", font_size=24).to_corner(UL)
        self.play(FadeIn(info_text))
        cluster_colors = [RED, GREEN, BLUE]
        def get_centroid_legend(centers, colors, font_size=24):
            legend_items = VGroup()
            for i, center in enumerate(centers):
                dot = Dot(radius=0.08, color=colors[i])
                label = Text(f"Centroid {i+1}: ({center[0]:.2f}, {center[1]:.2f})", font_size=font_size)
                item = VGroup(dot, label).arrange(RIGHT, buff=0.2)
                legend_items.add(item)
            legend_items.arrange(DOWN, aligned_edge=LEFT)
            legend_items.to_corner(UR)
            return legend_items
        X, _ = make_blobs(n_samples=300, centers=[[0, 0], [0.5, 0], [0, 0.5]], cluster_std=1, random_state=42)
        model = KMeansClustering(k=3)
        model.fit(X, num_iter=4)
        points = VGroup()
        for point in X:
            dot = Dot(axes.c2p(point[0], point[1]), radius=0.05, color=WHITE)
            points.add(dot)
        self.play(FadeIn(points, lag_ratio=0.005))
        init_state = model.states[0]
        colored_points = VGroup()
        for i, point in enumerate(X):
            dot = Dot(axes.c2p(point[0], point[1]), radius=0.05, color=cluster_colors[init_state['clusters'][i]])
            colored_points.add(dot)
        self.play(Transform(points, colored_points), run_time=1)
        centers = VGroup()
        for center in init_state['centers']:
            center_dot = Dot(axes.c2p(center[0], center[1]), radius=0.08, color=WHITE)
            centers.add(center_dot)
        self.play(FadeIn(centers))
        legend = get_centroid_legend(init_state['centers'], cluster_colors, font_size=24)
        self.play(FadeIn(legend))
        step_text = Text(init_state['step'], font_size=28).to_edge(UP)
        self.play(Write(step_text))
        self.wait(1)
        old_points = points
        old_step_text = step_text
        for state in model.states[1:]:
            new_points = VGroup()
            for i, point in enumerate(X):
                dot = Dot(axes.c2p(point[0], point[1]), radius=0.05, color=cluster_colors[state['clusters'][i]])
                new_points.add(dot)
            new_centers = VGroup()
            for center in state['centers']:
                center_dot = Dot(axes.c2p(center[0], center[1]), radius=0.08, color=WHITE)
                new_centers.add(center_dot)
            new_step_text = Text(state['step'], font_size=28).to_edge(UP)
            new_legend = get_centroid_legend(state['centers'], cluster_colors, font_size=24)
            self.play(Transform(legend, new_legend), run_time=1)
            self.play(FadeOut(old_step_text), run_time=0.5)
            self.play(Write(new_step_text), run_time=0.5)
            self.play(ReplacementTransform(centers, new_centers), runtime=2)
            self.play(Transform(old_points, new_points), run_time=2)
            self.wait(1)
            old_points = new_points
            centers = new_centers
            old_step_text = new_step_text
        self.wait(2)

class KMeansIntro(Scene):
    def construct(self):
        intro_group = self.introduction("K-means Visualisation", 
                                        "An iterative algorithm to partition data into clusters")
        self.play(FadeOut(intro_group))
        self.wait(1)
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

class KMeansConclusion(Scene):
    def construct(self):
        conclusion = VGroup(
            Text("K-Means Clustering converged!", font_size=28),
            Text("Thank you for watching!", font_size=28)
        )
        conclusion.arrange(DOWN)
        self.play(Write(conclusion))
        self.wait(3)
        self.play(FadeOut(conclusion))
