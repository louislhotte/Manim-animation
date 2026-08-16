"""Fractal leaf — a recursive binary tree rendered upside-down as a leaf.

The whole shape is produced by :func:`fractal_leaf`, whose *star* parameter is
the branching angle ``angle_deg``.  Because the topology only depends on
``depth``, two trees of equal depth share the same submobject structure and can
be smoothly ``Transform``-ed into one another — this is what makes the angle
sweep morph cleanly.

``FractalLeaf`` narrates three phases:

    1. the leaf is *constructed* branch level by branch level,
    2. the branching angle ``theta`` is *explained* on a small tree,
    3. ``theta`` is *swept* from 15 deg to 90 deg (step 5 deg) to show how
       wildly the final shape changes.

Render (low quality, fast):

    manim -pql fractal_leaf.py FractalLeaf

Quick still to eyeball the shape:

    manim -sql fractal_leaf.py LeafStill
"""

from manim import *
import numpy as np

# --------------------------------------------------------------------------- #
# Tunables — everything you'd want to play with lives here.
# --------------------------------------------------------------------------- #
ANGLE_HERO = 23.0        # branching angle (deg) of the "hero" leaf
DEPTH_HERO = 9           # recursion depth of the hero / construction leaf
DEPTH_SWEEP = 8          # depth used while sweeping the angle (kept lighter)
LENGTH_RATIO = 0.72      # each child is this fraction of its parent's length
BACKGROUND = "#000000"   # match the black reference background

TRUNK_BLUE = "#1f3b73"   # deep blue trunk
TIP_BLUE = "#8ad0ff"     # light blue twig tips

# A green -> gold -> red -> violet spread so the leaves are "different colours".
LEAF_PALETTE = [
    "#2e7d32", "#43a047", "#7cb342", "#c0ca33",
    "#fdd835", "#ffb300", "#fb8c00", "#f4511e",
    "#e53935", "#d81b60", "#8e24aa",
]


# --------------------------------------------------------------------------- #
# The fractal itself
# --------------------------------------------------------------------------- #
def fractal_leaf(
    angle_deg=ANGLE_HERO,
    depth=DEPTH_HERO,
    trunk_length=2.0,
    length_ratio=LENGTH_RATIO,
    trunk_color=TRUNK_BLUE,
    tip_color=TIP_BLUE,
    leaf_palette=None,
    leaf_radius=0.045,
    base_stroke=9.0,
    stroke_taper=0.78,
    min_stroke=0.6,
    direction=DOWN,
):
    """Build an upside-down fractal (binary) tree as a :class:`VGroup`.

    Every node splits into two children, each rotated by ``+/- angle_deg`` from
    its parent and shortened by ``length_ratio``.  The trunk starts at the
    origin and grows along ``direction`` (``DOWN`` by default → the canopy hangs
    below, so the whole thing reads as a leaf/frond).

    The returned VGroup carries helper attributes:

        tree.branches -- VGroup of every branch Line (pre-order)
        tree.leaves   -- VGroup of every tip Dot (ordered left -> right)
        tree.levels   -- list[VGroup]; branches grouped by depth level
        tree.root     -- the point the trunk starts from (ORIGIN before placing)
    """
    if leaf_palette is None:
        leaf_palette = LEAF_PALETTE

    angle = angle_deg * DEGREES
    branches = VGroup()
    leaves = VGroup()
    levels = [VGroup() for _ in range(depth + 1)]

    def grow(start, heading, length, level):
        end = start + heading * length
        color = interpolate_color(
            ManimColor(trunk_color),
            ManimColor(tip_color),
            0.0 if depth == 0 else level / depth,
        )
        width = max(base_stroke * (stroke_taper ** level), min_stroke)
        branch = Line(start, end, color=color, stroke_width=width)
        branches.add(branch)
        levels[level].add(branch)

        if level == depth:                       # a twig tip → drop a leaf
            leaves.add(Dot(end, radius=leaf_radius))
            return

        # First child turns one way, second the other; recurse.
        grow(end, rotate_vector(heading, angle), length * length_ratio, level + 1)
        grow(end, rotate_vector(heading, -angle), length * length_ratio, level + 1)

    grow(ORIGIN, np.array(direction, dtype=float), trunk_length, 0)

    # Colour the leaves across the palette (pre-order ≈ left → right).
    colors = color_gradient(leaf_palette, max(len(leaves), 2))
    for dot, col in zip(leaves, colors, strict=False):
        dot.set_color(col)

    tree = VGroup(branches, leaves)
    tree.branches = branches
    tree.leaves = leaves
    tree.levels = levels
    tree.root = ORIGIN
    return tree


def fit_trunk_length(target_height, angle_deg, depth, length_ratio=LENGTH_RATIO):
    """Trunk length (screen units) so a tree of this angle/depth is ~target tall.

    Every coordinate scales linearly with ``trunk_length``, so we measure a
    unit-trunk probe once and rescale.  Using a *fixed* trunk length across the
    sweep keeps the trunk the same size on screen while only the angle changes.
    """
    probe = fractal_leaf(
        angle_deg=angle_deg, depth=depth,
        trunk_length=1.0, length_ratio=length_ratio, leaf_radius=0.0,
    )
    return target_height / max(probe.height, 1e-6)


# --------------------------------------------------------------------------- #
# The narrated scene
# --------------------------------------------------------------------------- #
class FractalLeaf(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND
        self.intro()
        self.phase_construction()
        self.phase_angle()
        self.phase_sweep()
        self.outro()

    # -- intro ------------------------------------------------------------- #
    def intro(self):
        title = Text("The Fractal Leaf", font_size=56, color=TIP_BLUE)
        subtitle = Text(
            "a binary tree grown upside-down", font_size=28, color=GREY_B
        ).next_to(title, DOWN, buff=0.3)
        sig = Text(
            "Created by Ptolémé", font_size=22, color=GREY_C
        ).next_to(subtitle, DOWN, buff=0.7)

        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP * 0.2))
        self.play(FadeIn(sig))
        self.wait(1.2)
        self.play(FadeOut(VGroup(title, subtitle, sig)))

    # -- phase 1: construction -------------------------------------------- #
    def phase_construction(self):
        tree = fractal_leaf(
            angle_deg=ANGLE_HERO, depth=DEPTH_HERO,
            trunk_length=fit_trunk_length(6.0, ANGLE_HERO, DEPTH_HERO),
        ).move_to(UP * 0.35)  # nudge up so the canopy clears the caption

        caption = Text(
            "A leaf grows by splitting every branch in two…",
            font_size=26, color=GREY_B,
        ).to_edge(DOWN)
        self.play(FadeIn(caption))

        # Grow outward, one depth level at a time.
        for i, level in enumerate(tree.levels):
            run_time = 1.0 if i == 0 else max(0.16, 0.9 * (0.8 ** i))
            self.play(Create(level), run_time=run_time)

        # The colourful canopy blooms at the twig tips.
        self.play(FadeIn(tree.leaves, scale=0.4), run_time=1.6)
        self.wait(0.6)
        self.play(FadeOut(caption))
        self.wait(0.6)
        self.play(FadeOut(tree))

    # -- phase 2: the angle ----------------------------------------------- #
    def phase_angle(self):
        tree = fractal_leaf(
            angle_deg=32, depth=3,
            trunk_length=fit_trunk_length(4.6, 32, 3),
        ).move_to(LEFT * 2.2)

        self.play(Create(tree.branches), FadeIn(tree.leaves, scale=0.5))

        trunk = tree.levels[0][0]
        child = tree.levels[1][0]
        node = trunk.get_end()
        trunk_dir = normalize(trunk.get_end() - trunk.get_start())

        # A dashed line continuing "straight ahead" so theta reads as the
        # deviation of a child from its parent's direction.
        cont = DashedLine(node, node + trunk_dir * 1.5, color=GREY_B, stroke_width=3)
        arc = Angle(cont, Line(node, child.get_end()), radius=0.75, color=YELLOW)
        label_pt = arc.point_from_proportion(0.5)
        theta = Text("θ", font_size=42, color=YELLOW).move_to(
            node + (label_pt - node) * 1.55
        )

        self.play(Create(cont))
        self.play(Create(arc), FadeIn(theta))

        caption = VGroup(
            Text("Each branch splits into two.", font_size=27, color=WHITE),
            Text("Every child turns by θ", font_size=25, color=GREY_A),
            Text("and shrinks by a fixed ratio.", font_size=25, color=GREY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28).to_edge(RIGHT, buff=0.8)
        self.play(FadeIn(caption, shift=LEFT * 0.3))
        self.wait(2.6)
        self.play(FadeOut(VGroup(tree, cont, arc, theta, caption)))

    # -- phase 3: sweep 15° → 90° ----------------------------------------- #
    def phase_sweep(self):
        angles = list(range(15, 91, 5))
        # Fix the trunk length to the *tallest* case (15°) so everything fits
        # and the trunk stays put — only the branching angle changes.
        trunk_len = fit_trunk_length(6.2, angles[0], DEPTH_SWEEP)
        root_target = UP * 3.4

        def make(a):
            return fractal_leaf(
                angle_deg=a, depth=DEPTH_SWEEP, trunk_length=trunk_len
            ).shift(root_target)

        def label_for(a):
            return Text(f"θ = {a}°", font_size=44, color=TIP_BLUE).to_corner(UR)

        tree = make(angles[0])
        label = label_for(angles[0])
        caption = Text(
            "Same trunk — a very different leaf", font_size=26, color=GREY_B
        ).to_edge(DOWN)

        self.play(FadeIn(tree), FadeIn(label), FadeIn(caption))
        self.wait(0.8)

        for a in angles[1:]:
            self.play(
                Transform(tree, make(a)),
                Transform(label, label_for(a)),
                run_time=0.55, rate_func=smooth,
            )
            if a in (30, 45, 60, 90):     # linger on the landmark angles
                self.wait(0.5)
        self.wait(1.2)

        # A quick sweep back down, just because it's satisfying.
        for a in reversed(angles[:-1]):
            self.play(
                Transform(tree, make(a)),
                Transform(label, label_for(a)),
                run_time=0.28,
            )
        self.wait(1.0)
        self.play(FadeOut(VGroup(tree, label, caption)))

    # -- outro ------------------------------------------------------------- #
    def outro(self):
        end = VGroup(
            Text("θ shapes everything.", font_size=44, color=TIP_BLUE),
            Text("Created by Ptolémé", font_size=22, color=GREY_C),
        ).arrange(DOWN, buff=0.5)
        self.play(Write(end[0]))
        self.play(FadeIn(end[1]))
        self.wait(2.0)
        self.play(FadeOut(end))


# --------------------------------------------------------------------------- #
# A one-frame still, handy for quickly eyeballing the shape / colours:
#   manim -sql fractal_leaf.py LeafStill
# --------------------------------------------------------------------------- #
class LeafStill(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND
        tree = fractal_leaf(
            angle_deg=ANGLE_HERO, depth=10,
            trunk_length=fit_trunk_length(7.2, ANGLE_HERO, 10),
        ).move_to(ORIGIN)
        self.add(tree)
