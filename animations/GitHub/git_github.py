"""Git & GitHub, Visually — a short, house-style explainer.

A self-explanatory (no voice-over) film that shows, at a high level, what Git &
GitHub are *for* and then walks through the core actions — one scene per action —
using the universal "commit graph" picture: commits are dots, branches are lanes,
and pointers/tags name the tips.

        ●──●──●        commits linked into history (a branch)
              ╲
               ●──●    a branch: a parallel line of work
              ╱
        ●──●─●         …merged back together

Scenes:

    1. Overview    -- what Git & GitHub are for (time machine + shared home)
    2. Commit      -- a commit is a saved snapshot of your project, with a message
    3. Push        -- send your local commits up to GitHub so the team can see them
    4. Branch      -- a branch is a safe, parallel line of work off `main`
    5. Merge       -- bring a finished branch back into `main` (via a Pull Request)
    6. CherryPick  -- copy just ONE commit from another branch, not the whole thing
    7. Collab      -- five people, five branches, all merging back into `main`

Bookended by the channel's intro card and the "Thank you for watching!" outro,
matching animations/BinomialSquare/binomial_square.py.

Everything uses ``Text`` (Pango), never ``Tex`` — so it renders with no LaTeX
toolchain and stays fast to iterate on. Special glyphs use unicode.

Scenes are exposed individually (``Overview``, ``Commit``, ``Push``, ``Branch``,
``Merge``, ``CherryPick``, ``Collab``, ``Intro``, ``Outro``) and as one film
(``GitHubExplained``).

Env knobs:
    GIT_QUICK=1   shorten every hold for a fast sanity render
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` quantises glyph positions badly at small font sizes, so body
# text below ~20 pt comes out with uneven letter/word spacing. Work around it
# once, here: always render glyphs at a large, crisp base size and scale the
# mobject *down* to the requested size. This shadows manim's ``Text`` so every
# call in this module benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("GIT_QUICK") == "1"
# One knob for pacing: every reading "hold" is scaled by this. QUICK collapses
# the holds for a fast iteration; otherwise it sets a calm, readable rhythm
# (tuned so viewers have time to read every panel before it moves on).
DELAY = 0.3 if QUICK else 1.4

# ---- palette (GitHub-dark house style) ------------------------------------ #
BG = "#0D1117"       # GitHub dark background
PANEL = "#161B22"    # panels / terminals / device fills
INK = "#F5F3EF"      # warm white text
MUTED = "#8A93A6"    # secondary text / labels
GRID = "#2A3242"     # faint gridlines
EDGE = "#3B4455"     # commit-graph connectors

MAIN_C = "#58A6FF"   # the default branch `main`            (GitHub blue)
GOLD = "#FFD166"     # highlights / tags / releases
GREEN = "#3DD68C"
AMBER = "#FF9F45"
PURPLE = "#C792EA"
PINK = "#FF6B9D"
TEAL = "#4EC8D4"
BAD = "#FF5C5C"
TERM_C = TEAL        # terminal / command accent

COMMIT_R = 0.26      # default commit-dot radius


# ========================================================================== #
# Small reusable "git graph" building blocks
# ========================================================================== #
def fit(mob, max_w):
    """Scale a mobject down (never up) so it fits within max_w."""
    if mob.width > max_w:
        mob.scale(max_w / mob.width)
    return mob


def commit_dot(color=MAIN_C, r=COMMIT_R):
    """A single commit: a filled dot with a thin ink ring, drawn above edges."""
    d = Circle(radius=r, fill_color=color, fill_opacity=1.0,
               stroke_color=INK, stroke_width=2.0)
    d.set_z_index(2)
    return d


def lane_edge(p0, p1, color=EDGE, sw=3.0):
    """A straight connector between two commit centres (drawn beneath dots)."""
    e = Line(p0, p1, color=color, stroke_width=sw)
    e.set_z_index(0)
    return e


def gcurve(p0, p1, color=EDGE, sw=3.0):
    """A smooth S-curve with horizontal tangents — the fork/merge connector."""
    p0 = np.array(p0, dtype=float)
    p1 = np.array(p1, dtype=float)
    dx = (p1[0] - p0[0]) * 0.5
    h1 = p0 + np.array([dx, 0.0, 0.0])
    h2 = p1 + np.array([-dx, 0.0, 0.0])
    c = CubicBezier(p0, h1, h2, p1)
    c.set_stroke(color=color, width=sw)
    c.set_z_index(0)
    return c


def branch_tag(name, color, fs=22):
    """A rounded 'pointer' pill naming a branch tip."""
    txt = Text(name, font_size=fs, weight="BOLD", color=BG)
    box = RoundedRectangle(corner_radius=0.09,
                           width=txt.width + 0.34, height=txt.height + 0.22,
                           fill_color=color, fill_opacity=1.0, stroke_width=0)
    txt.move_to(box)
    g = VGroup(box, txt)
    g.set_z_index(3)
    return g


def cmd_pill(cmd, accent=TERM_C, fs=26):
    """A little terminal chip: `$ <cmd>` with an accent border."""
    prompt = Text("$", font_size=fs, color=accent, weight="BOLD")
    body = Text(cmd, font_size=fs, color=INK)
    row = VGroup(prompt, body).arrange(RIGHT, buff=0.24)
    box = RoundedRectangle(corner_radius=0.12,
                           width=row.width + 0.55, height=row.height + 0.4,
                           fill_color=PANEL, fill_opacity=1.0,
                           stroke_color=accent, stroke_width=2.2)
    row.move_to(box)
    g = VGroup(box, row)
    g.set_z_index(4)
    return g


def avatar(initial, color, r=0.28, fs=26):
    """A person: an initial on a coloured disc."""
    disc = Circle(radius=r, fill_color=color, fill_opacity=1.0,
                  stroke_color=INK, stroke_width=2.0)
    ini = Text(initial, font_size=fs, color=BG, weight="BOLD").move_to(disc)
    g = VGroup(disc, ini)
    g.set_z_index(3)
    return g


def cloud(color=MUTED, sc=1.0):
    """A simple cloud silhouette (overlapping discs + base), no internal strokes."""
    parts = VGroup(
        Circle(radius=0.42).move_to(LEFT * 0.62),
        Circle(radius=0.60).move_to(UP * 0.10),
        Circle(radius=0.46).move_to(RIGHT * 0.66),
        RoundedRectangle(width=2.5, height=0.66, corner_radius=0.33).move_to(DOWN * 0.30),
    )
    for p in parts:
        p.set_fill(color, opacity=1.0)
        p.set_stroke(width=0)
    parts.scale(sc)
    return parts


# ========================================================================== #
class _Base(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def wipe(self, rt=0.7):
        movers = [m for m in self.mobjects]
        for m in movers:
            m.clear_updaters()
        if movers:
            self.play(*[FadeOut(m) for m in movers], run_time=rt)

    def section_header(self, label, color):
        txt = Text(label, font_size=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(txt, line)

    def caption(self, text, color=MUTED, fs=27, buff=0.6):
        return Text(text, font_size=fs, color=color).to_edge(DOWN, buff=buff)

    # ---- house-style intro / outro cards ---------------------------------- #
    def title_card(self, title1, title2):
        header = Text(title1, font_size=52, color=INK, weight="BOLD")
        fit(header, 11.5)
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=MAIN_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text(title2, font_size=32, color=MUTED)
        fit(sub, 11.5).move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.title_card(
            "Git & GitHub, Visually",
            "commit · push · branch · merge · cherry-pick",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=MAIN_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — Overview: what Git & GitHub are for
    # ====================================================================== #
    def scene_overview(self):
        title = Text("What are Git & GitHub?", font_size=44, color=INK,
                     weight="BOLD").to_edge(UP, buff=0.7)
        self.play(Write(title), run_time=1.1)
        self.beat(0.6)

        # ---- left card: Git (on your computer) ---------------------------- #
        git_card = RoundedRectangle(width=4.4, height=2.7, corner_radius=0.16,
                                    fill_color=PANEL, fill_opacity=1.0,
                                    stroke_color=MAIN_C, stroke_width=2.5)
        git_card.move_to([-3.7, 0.45, 0])
        git_name = Text("Git", font_size=30, color=MAIN_C, weight="BOLD")
        git_name.next_to(git_card.get_top(), DOWN, buff=0.18)
        # a mini commit chain inside
        chain = VGroup()
        pts = [git_card.get_center() + np.array([x, -0.35, 0]) for x in (-1.2, -0.4, 0.4, 1.2)]
        for i, p in enumerate(pts):
            if i > 0:
                chain.add(lane_edge(pts[i - 1], p))
            chain.add(commit_dot(MAIN_C, r=0.17).move_to(p))
        git_sub = Text("saves every change as a commit", font_size=22, color=MUTED)
        git_sub.next_to(git_card, DOWN, buff=0.22)

        self.play(Create(git_card), FadeIn(git_name, shift=DOWN * 0.1), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m) for m in chain], lag_ratio=0.3), run_time=1.0)
        self.play(FadeIn(git_sub, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)

        # ---- right card: GitHub (shared home online) ---------------------- #
        gh_card = RoundedRectangle(width=4.4, height=2.7, corner_radius=0.16,
                                   fill_color=PANEL, fill_opacity=1.0,
                                   stroke_color=GOLD, stroke_width=2.5)
        gh_card.move_to([3.7, 0.45, 0])
        gh_name = Text("GitHub", font_size=30, color=GOLD, weight="BOLD")
        gh_name.next_to(gh_card.get_top(), DOWN, buff=0.18)
        cl = cloud(MUTED, sc=0.5).move_to(gh_card.get_center() + UP * 0.2)
        team = VGroup(avatar("A", GREEN, r=0.20, fs=20),
                      avatar("B", AMBER, r=0.20, fs=20),
                      avatar("C", PINK, r=0.20, fs=20)).arrange(RIGHT, buff=0.3)
        team.move_to(gh_card.get_center() + DOWN * 0.55)
        gh_sub = Text("the shared home for your code online", font_size=22, color=MUTED)
        gh_sub.next_to(gh_card, DOWN, buff=0.22)

        self.play(Create(gh_card), FadeIn(gh_name, shift=DOWN * 0.1), run_time=0.8)
        self.play(FadeIn(cl, shift=DOWN * 0.15), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in team], lag_ratio=0.3),
                  run_time=0.8)
        self.play(FadeIn(gh_sub, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)

        # ---- push / pull arrows between them ------------------------------ #
        push = Arrow(git_card.get_right() + UP * 0.5, gh_card.get_left() + UP * 0.5,
                     buff=0.15, color=GREEN, stroke_width=5,
                     max_tip_length_to_length_ratio=0.14)
        push_l = Text("push", font_size=22, color=GREEN).next_to(push, UP, buff=0.12)
        pull = Arrow(gh_card.get_left() + DOWN * 0.5, git_card.get_right() + DOWN * 0.5,
                     buff=0.15, color=MUTED, stroke_width=5,
                     max_tip_length_to_length_ratio=0.14)
        pull_l = Text("pull", font_size=22, color=MUTED).next_to(pull, DOWN, buff=0.12)
        self.play(GrowArrow(push), FadeIn(push_l), run_time=0.7)
        self.play(GrowArrow(pull), FadeIn(pull_l), run_time=0.7)
        self.beat(1.6)

        payoff = self.caption(
            "Track every change  ·  work in parallel  ·  never lose work",
            color=GOLD, fs=28)
        self.play(FadeIn(payoff, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Commit: a saved snapshot with a message
    # ====================================================================== #
    def scene_commit(self):
        header = self.section_header("Commit — save a snapshot", MAIN_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # ---- the working project (files) on the left ---------------------- #
        proj = RoundedRectangle(width=3.5, height=2.6, corner_radius=0.14,
                                fill_color=PANEL, fill_opacity=1.0,
                                stroke_color=MUTED, stroke_width=2.0)
        proj.move_to([-4.2, 0.55, 0])
        proj_t = Text("your project", font_size=22, color=MUTED)
        proj_t.next_to(proj.get_top(), DOWN, buff=0.16)

        def file_row(name):
            glyph = RoundedRectangle(width=0.26, height=0.32, corner_radius=0.05,
                                     stroke_color=MUTED, stroke_width=2.0, fill_opacity=0)
            nm = Text(name, font_size=22, color=INK)
            return VGroup(glyph, nm).arrange(RIGHT, buff=0.18)

        files = VGroup(file_row("login.py"), file_row("app.py"), file_row("README.md"))
        files.arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to(proj).shift(DOWN * 0.12)
        self.play(Create(proj), FadeIn(proj_t, shift=DOWN * 0.1), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.15) for m in files],
                              lag_ratio=0.25), run_time=0.9)
        self.beat(0.8)

        # the commit lane on the right
        lane_y = -2.2
        lane = lane_edge([-4.6, lane_y, 0], [5.2, lane_y, 0], color=EDGE, sw=2.5)
        self.play(Create(lane), run_time=0.6)

        def edit_and_commit(changed, cmd, msg, h, x, prev):
            # 1. edit some files
            edits = []
            for idx in changed:
                edits.append(files[idx][1].animate.set_color(AMBER))
            badge = Text("● edited", font_size=20, color=AMBER)
            badge.next_to(proj, DOWN, buff=0.2)
            self.play(*edits, FadeIn(badge, shift=UP * 0.1), run_time=0.7)
            self.beat(0.7)
            # 2. run git commit
            pill = cmd_pill(cmd).next_to(header, DOWN, buff=0.35).to_edge(RIGHT, buff=0.7)
            self.play(FadeIn(pill, shift=UP * 0.1), run_time=0.7)
            self.beat(0.8)
            # 3. a commit dot lands on the lane, snapshotting the project
            p = np.array([x, lane_y, 0.0])
            dot = commit_dot(MAIN_C).move_to(p)
            e = lane_edge(prev, p) if prev is not None else None
            mlabel = Text(msg, font_size=22, color=INK).next_to(dot, UP, buff=0.22)
            hlabel = Text(h, font_size=18, color=MUTED).next_to(dot, DOWN, buff=0.18)
            anims = [GrowFromCenter(dot), FadeIn(mlabel, shift=UP * 0.1), FadeIn(hlabel)]
            if e is not None:
                self.play(Create(e), run_time=0.4)
            self.play(*anims, run_time=0.7)
            # reset the file colours for the next round
            self.play(*[files[idx][1].animate.set_color(INK) for idx in changed],
                      FadeOut(badge), FadeOut(pill), run_time=0.5)
            self.beat(0.9)
            return p

        p1 = edit_and_commit([0], 'git commit -m "Add login page"',
                             "Add login page", "a1b2c3d", -3.0, None)
        p2 = edit_and_commit([1, 2], 'git commit -m "Update home & docs"',
                             "Update home & docs", "b2c3d4e", 0.5, p1)

        tag = branch_tag("main", MAIN_C)
        tag.next_to(commit_dot(MAIN_C).move_to(p2), RIGHT, buff=0.3).shift(RIGHT * 0.0)
        tag.move_to([p2[0] + 1.1, lane_y, 0])
        self.play(FadeIn(tag, shift=RIGHT * 0.15), run_time=0.6)
        self.beat(0.8)

        cap = self.caption(
            "Each commit is a snapshot of your whole project — a message, an author, a time.",
            color=INK, fs=26)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.7)
        self.beat(1.6)
        cap2 = self.caption("Commits link up into your history — you can always go back.",
                            color=GOLD, fs=26)
        self.play(FadeTransform(cap, cap2), run_time=0.7)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Push: send local commits up to GitHub
    # ====================================================================== #
    def scene_push(self):
        header = self.section_header("Push — share it on GitHub", GREEN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        xs = [-1.4, 0.0, 1.4]

        # ---- local commits (on your laptop) ------------------------------- #
        local_y = -2.15
        local_lane = lane_edge([-2.4, local_y, 0], [2.4, local_y, 0], sw=2.5)
        local_dots = VGroup()
        prev = None
        for x in xs:
            p = np.array([x, local_y, 0.0])
            if prev is not None:
                local_dots.add(lane_edge(prev, p))
            local_dots.add(commit_dot(MAIN_C).move_to(p))
            prev = p
        laptop = Text("your laptop", font_size=24, color=MUTED)
        laptop.next_to([xs[0], local_y, 0], LEFT, buff=0.5).shift(LEFT * 0.1)
        local_tag = branch_tag("main", MAIN_C).move_to([xs[-1] + 1.0, local_y, 0])

        self.play(Create(local_lane), FadeIn(laptop, shift=RIGHT * 0.1), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(m) for m in local_dots], lag_ratio=0.2), run_time=1.0)
        self.play(FadeIn(local_tag, shift=RIGHT * 0.1), run_time=0.5)
        self.beat(0.8)

        only = Text("These commits only exist on your machine.",
                    font_size=26, color=INK).move_to([0, -3.35, 0])
        self.play(FadeIn(only, shift=UP * 0.1), run_time=0.7)
        self.beat(1.6)

        # ---- the GitHub remote panel at the top --------------------------- #
        panel = RoundedRectangle(width=6.8, height=1.9, corner_radius=0.16,
                                 fill_color=PANEL, fill_opacity=1.0,
                                 stroke_color=GOLD, stroke_width=2.5)
        panel.move_to([0.4, 2.05, 0])
        cl = cloud(MUTED, sc=0.34).move_to(panel.get_corner(UL) + np.array([0.7, -0.42, 0]))
        gh_lbl = Text("GitHub", font_size=24, color=GOLD, weight="BOLD")
        gh_lbl.next_to(cl, RIGHT, buff=0.2)
        origin = Text("origin/main", font_size=20, color=MUTED)
        origin.next_to(gh_lbl, RIGHT, buff=0.35)
        self.play(Create(panel), FadeIn(cl), FadeIn(gh_lbl), FadeIn(origin), run_time=0.9)
        self.beat(0.8)

        # ---- git push: commits travel up into GitHub ---------------------- #
        pill = cmd_pill("git push").move_to([-4.0, 0.1, 0])
        arrow = Arrow([-2.6, -1.5, 0], [-2.6, 1.05, 0], buff=0.1, color=GREEN,
                      stroke_width=6, max_tip_length_to_length_ratio=0.12)
        self.play(FadeIn(pill, shift=UP * 0.1), GrowArrow(arrow), run_time=0.8)
        self.beat(0.7)

        remote_y = 1.75
        remote_pts = [np.array([x + 0.4, remote_y, 0.0]) for x in xs]
        dot_mobs = [m for m in local_dots if isinstance(m, Circle)]
        flyers = VGroup(*[d.copy() for d in dot_mobs])
        self.add(flyers)
        self.play(LaggedStart(*[flyers[i].animate.move_to(remote_pts[i])
                                for i in range(len(remote_pts))],
                              lag_ratio=0.18), run_time=1.5)
        # connect them inside the panel
        redges = VGroup()
        for i in range(1, len(remote_pts)):
            redges.add(lane_edge(remote_pts[i - 1], remote_pts[i]))
        self.play(Create(redges), run_time=0.5)
        self.play(Flash(panel.get_center(), color=GREEN, flash_radius=1.2,
                        line_length=0.3), run_time=0.6)
        self.beat(1.2)

        self.play(FadeOut(only), run_time=0.3)
        cap = self.caption(
            "Now your work is backed up and visible to everyone on the team.",
            color=GOLD, fs=27)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.7)
        self.beat(1.6)
        cap2 = self.caption("`git pull` is the reverse — download the team's latest commits.",
                            color=MUTED, fs=25)
        self.play(FadeTransform(cap, cap2), run_time=0.7)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Branch: a safe, parallel line of work
    # ====================================================================== #
    def scene_branch(self):
        header = self.section_header("Branch — work in parallel", GREEN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        main_y = -0.8
        # main starts with a couple of commits
        mxs = [-5.2, -3.6]
        main_dots = VGroup()
        prev = None
        for x in mxs:
            p = np.array([x, main_y, 0.0])
            if prev is not None:
                main_dots.add(lane_edge(prev, p))
            main_dots.add(commit_dot(MAIN_C).move_to(p))
            prev = p
        main_tag = branch_tag("main", MAIN_C).move_to([mxs[-1], main_y - 0.7, 0])
        self.play(LaggedStart(*[FadeIn(m) for m in main_dots], lag_ratio=0.25), run_time=0.9)
        self.play(FadeIn(main_tag, shift=UP * 0.1), run_time=0.5)
        cap0 = self.caption("`main` is the default branch — your project's source of truth.",
                            color=INK, fs=26)
        self.play(FadeIn(cap0, shift=UP * 0.1), run_time=0.6)
        self.beat(1.6)

        # ---- branch off ---------------------------------------------------- #
        pill = cmd_pill("git checkout -b feature").next_to(header, DOWN, buff=0.4)
        pill.to_edge(RIGHT, buff=0.8)
        self.play(FadeIn(pill, shift=UP * 0.1), run_time=0.7)
        self.beat(0.7)

        fork_from = np.array([mxs[-1], main_y, 0.0])
        feat_y = 1.1
        fxs = [-2.1, -0.7]
        fork = gcurve(fork_from, [fxs[0], feat_y, 0], color=GREEN, sw=3.0)
        feat_dots = VGroup()
        prev = np.array([fxs[0], feat_y, 0.0])
        first = commit_dot(GREEN).move_to(prev)
        feat_dots.add(first)
        for x in fxs[1:]:
            p = np.array([x, feat_y, 0.0])
            feat_dots.add(lane_edge(prev, p, color=GREEN))
            feat_dots.add(commit_dot(GREEN).move_to(p))
            prev = p
        feat_tag = branch_tag("feature", GREEN).move_to([fxs[-1] + 1.1, feat_y, 0])

        self.play(Create(fork), run_time=0.7)
        self.play(GrowFromCenter(first), run_time=0.5)
        self.play(LaggedStart(*[(Create(m) if isinstance(m, Line) else GrowFromCenter(m))
                                for m in feat_dots[1:]], lag_ratio=0.4), run_time=1.1)
        self.play(FadeIn(feat_tag, shift=RIGHT * 0.1), run_time=0.5)
        cap1 = self.caption("A branch is a parallel copy — experiment without touching `main`.",
                            color=GREEN, fs=26)
        self.play(FadeTransform(cap0, cap1), run_time=0.7)
        self.beat(1.8)

        # ---- meanwhile, main keeps moving too ----------------------------- #
        self.play(FadeOut(pill), run_time=0.3)
        meanwhile = Text("meanwhile, `main` keeps moving too",
                         font_size=24, color=MAIN_C).next_to(header, DOWN, buff=0.5)
        meanwhile.to_edge(RIGHT, buff=0.7)
        self.play(FadeIn(meanwhile, shift=DOWN * 0.1), run_time=0.6)
        new_main = np.array([-2.3, main_y, 0.0])
        e = lane_edge(fork_from, new_main)
        d = commit_dot(MAIN_C).move_to(new_main)
        self.play(Create(e), run_time=0.4)
        self.play(GrowFromCenter(d),
                  main_tag.animate.move_to([new_main[0], main_y - 0.7, 0]), run_time=0.6)
        self.beat(1.0)
        cap2 = self.caption("Two independent lines of history — that's the whole point.",
                            color=GOLD, fs=27)
        self.play(FadeTransform(cap1, cap2), run_time=0.7)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Merge: bring a finished branch back into main
    # ====================================================================== #
    def scene_merge(self):
        header = self.section_header("Merge — bring it back together", MAIN_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        main_y = -0.9
        feat_y = 1.2

        # rebuild the diverged picture quickly
        m_pts = [np.array([x, main_y, 0.0]) for x in (-5.2, -3.6, -2.2)]
        main_g = VGroup()
        for i, p in enumerate(m_pts):
            if i > 0:
                main_g.add(lane_edge(m_pts[i - 1], p))
            main_g.add(commit_dot(MAIN_C).move_to(p))
        fork_from = m_pts[1]  # branched from the 2nd commit
        f_pts = [np.array([x, feat_y, 0.0]) for x in (-2.4, -1.0)]
        feat_g = VGroup(gcurve(fork_from, f_pts[0], color=GREEN))
        for i, p in enumerate(f_pts):
            if i > 0:
                feat_g.add(lane_edge(f_pts[i - 1], p, color=GREEN))
            feat_g.add(commit_dot(GREEN).move_to(p))
        main_tag = branch_tag("main", MAIN_C).move_to([m_pts[-1][0] + 0.1, main_y - 0.7, 0])
        feat_tag = branch_tag("feature", GREEN).move_to([f_pts[-1][0] + 1.1, feat_y, 0])

        self.play(FadeIn(main_g), FadeIn(feat_g), FadeIn(main_tag), FadeIn(feat_tag),
                  run_time=1.0)
        self.beat(1.0)

        # ---- the GitHub way: a Pull Request ------------------------------- #
        pr = branch_tag("Pull Request #42", GOLD, fs=22)
        pr.move_to([3.6, 2.05, 0])
        # the explanation lives at the bottom (safe caption lane), not in the graph
        pr_note = self.caption("Open a Pull Request so teammates can review the change first.",
                               color=MUTED, fs=26)
        arrow = Arrow(pr.get_corner(DL), feat_tag.get_right() + UP * 0.05, buff=0.2,
                      color=GOLD, stroke_width=4, max_tip_length_to_length_ratio=0.1)
        self.play(FadeIn(pr, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeIn(pr_note, shift=UP * 0.1), GrowArrow(arrow), run_time=0.7)
        self.beat(1.8)

        # ---- the merge ---------------------------------------------------- #
        self.play(FadeOut(pr_note), FadeOut(arrow), run_time=0.4)
        pill = cmd_pill("git merge feature").move_to([3.0, 0.55, 0])
        self.play(ReplacementTransform(pr, pill), run_time=0.7)
        self.beat(0.7)

        merge_pt = np.array([0.4, main_y, 0.0])
        # merge commit: gold-ringed to mark "the join"
        ring = Circle(radius=COMMIT_R + 0.1, color=GOLD, stroke_width=3).move_to(merge_pt)
        merge_dot = commit_dot(MAIN_C).move_to(merge_pt)
        e_main = lane_edge(m_pts[-1], merge_pt)
        e_feat = gcurve(f_pts[-1], merge_pt, color=GREEN)
        self.play(Create(e_main), Create(e_feat), run_time=0.9)
        self.play(GrowFromCenter(merge_dot), Create(ring),
                  main_tag.animate.move_to([merge_pt[0], main_y - 0.7, 0]), run_time=0.7)
        mlabel = Text("merge commit", font_size=22, color=GOLD).next_to(ring, UP, buff=0.25)
        self.play(FadeIn(mlabel, shift=UP * 0.1),
                  Flash(merge_pt, color=GOLD, flash_radius=0.7), run_time=0.7)
        self.beat(1.4)

        cap = self.caption("`main` now contains the feature's work — two histories, joined.",
                           color=GOLD, fs=27)
        self.play(FadeIn(cap, shift=UP * 0.1),
                  Indicate(VGroup(*[m for m in feat_g if isinstance(m, Circle)]),
                           color=GREEN, scale_factor=1.1), run_time=0.9)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Cherry-pick: copy just one commit
    # ====================================================================== #
    def scene_cherry(self):
        header = self.section_header("Cherry-pick — grab just one commit", AMBER)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        main_y = -1.4
        dev_y = 1.0

        # main branch
        m_pts = [np.array([x, main_y, 0.0]) for x in (-5.0, -3.6)]
        main_g = VGroup()
        for i, p in enumerate(m_pts):
            if i > 0:
                main_g.add(lane_edge(m_pts[i - 1], p))
            main_g.add(commit_dot(MAIN_C).move_to(p))
        main_tag = branch_tag("main", MAIN_C).move_to([m_pts[-1][0], main_y - 0.7, 0])

        # dev branch with three commits — only the middle one is wanted
        d_pts = [np.array([x, dev_y, 0.0]) for x in (-3.4, -1.9, -0.4)]
        dev_g = VGroup(gcurve(m_pts[0], d_pts[0], color=AMBER))
        for i, p in enumerate(d_pts):
            if i > 0:
                dev_g.add(lane_edge(d_pts[i - 1], p, color=AMBER))
            dev_g.add(commit_dot(AMBER).move_to(p))
        dev_tag = branch_tag("dev", AMBER).move_to([d_pts[-1][0] + 0.9, dev_y, 0])
        labels = VGroup(
            Text("WIP", font_size=20, color=MUTED).next_to(d_pts[0], UP, buff=0.22),
            Text("Fix crash", font_size=21, color=INK, weight="BOLD").next_to(d_pts[1], UP, buff=0.22),
            Text("WIP", font_size=20, color=MUTED).next_to(d_pts[2], UP, buff=0.22),
        )

        self.play(FadeIn(main_g), FadeIn(main_tag), run_time=0.7)
        self.play(FadeIn(dev_g), FadeIn(dev_tag), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in labels],
                              lag_ratio=0.25), run_time=0.9)
        self.beat(1.0)

        want = Text("You only want the bug-fix on `main` — not the WIP commits.",
                    font_size=26, color=INK).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(want, shift=UP * 0.1), run_time=0.7)
        # highlight the wanted commit
        want_dot = [m for m in dev_g if isinstance(m, Circle)][1]
        halo = SurroundingRectangle(VGroup(want_dot, labels[1]), color=GOLD,
                                    buff=0.12, corner_radius=0.1)
        self.play(Create(halo), Indicate(want_dot, color=GOLD, scale_factor=1.2), run_time=0.9)
        self.beat(1.6)

        # ---- cherry-pick ---------------------------------------------------- #
        pill = cmd_pill("git cherry-pick b2c3d4e").move_to([3.1, 0.05, 0])
        self.play(FadeIn(pill, shift=UP * 0.1), run_time=0.7)
        self.beat(0.7)

        pick_pt = np.array([-2.1, main_y, 0.0])
        e = lane_edge(m_pts[-1], pick_pt)
        pick_ring = Circle(radius=COMMIT_R + 0.1, color=AMBER, stroke_width=3).move_to(pick_pt)
        pick_dot = commit_dot(MAIN_C).move_to(pick_pt)
        self.play(Create(e), run_time=0.4)
        self.play(TransformFromCopy(want_dot, pick_dot), Create(pick_ring), run_time=0.9)
        pick_lbl = Text("Fix crash (copy)", font_size=21, color=AMBER,
                        weight="BOLD").next_to(pick_pt, DOWN, buff=0.5)
        self.play(FadeIn(pick_lbl, shift=DOWN * 0.1),
                  main_tag.animate.next_to(pick_ring, RIGHT, buff=0.3),
                  Flash(pick_pt, color=AMBER, flash_radius=0.7), run_time=0.8)
        self.beat(1.4)

        self.play(FadeOut(want), FadeOut(halo), run_time=0.4)
        cap = self.caption(
            "cherry-pick copies ONE commit onto your branch — a new commit, the same change.",
            color=GOLD, fs=26)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.7)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 7 — Collaboration: five people, five branches, one `main`
    # ====================================================================== #
    def scene_collab(self):
        title = Text("Many people, one project", font_size=42, color=INK,
                     weight="BOLD").to_edge(UP, buff=0.55)
        self.play(Write(title), run_time=1.0)
        self.beat(0.5)

        main_y = -2.9
        # the trunk: dots at every fork/merge point (they coincide by design)
        trunk_xs = [-6.4, -5.5, -4.0, -2.5, -1.0, 0.5, 2.0, 3.5]
        main_lane = lane_edge([trunk_xs[0] - 0.2, main_y, 0],
                              [trunk_xs[-1] + 0.2, main_y, 0], color=MAIN_C, sw=3.0)
        trunk_dots = {x: commit_dot(MAIN_C, r=0.20).move_to([x, main_y, 0]) for x in trunk_xs}
        main_tag = branch_tag("main", MAIN_C, fs=20).move_to([trunk_xs[0] - 1.0, main_y, 0])
        self.play(Create(main_lane), run_time=0.8)
        self.play(FadeIn(main_tag, shift=RIGHT * 0.1),
                  *[GrowFromCenter(trunk_dots[x]) for x in trunk_xs[:2]], run_time=0.7)
        self.beat(0.6)

        # ---- five people, five branches ----------------------------------- #
        people = [
            ("A", "Ana", "feature/login", GREEN, 2),
            ("B", "Ben", "feature/search", AMBER, 1),
            ("C", "Chen", "fix/checkout", PURPLE, 2),
            ("D", "Dara", "feature/payments", PINK, 1),
            ("E", "Elias", "docs/readme", TEAL, 2),
        ]
        lane_ys = [-1.6, -0.8, 0.0, 0.8, 1.6]
        forks = [-5.5, -4.0, -2.5, -1.0, 0.5]     # each = a trunk dot
        merges = [-2.5, -1.0, 0.5, 2.0, 3.5]      # each = a trunk dot

        branches = []  # (color, lane_y, commit_pts, tip, fork_x, merge_x, avatar_grp)
        intro_anims = []
        for i, (ini, name, task, color, ncommits) in enumerate(people):
            ly = lane_ys[i]
            fx = forks[i]
            cxs = [fx + 0.9 + 1.0 * j for j in range(ncommits)]
            cpts = [np.array([cx, ly, 0.0]) for cx in cxs]
            av = avatar(ini, color, r=0.24, fs=22).move_to([fx - 0.75, ly, 0])
            nm = Text(f"{name} · {task}", font_size=18, color=color)
            nm.next_to(av, UP, buff=0.14)
            if nm.get_left()[0] < -7.0:          # keep the leftmost label on-screen
                nm.shift(RIGHT * (-7.0 - nm.get_left()[0]))
            branches.append(dict(color=color, ly=ly, fx=fx, mx=merges[i],
                                 cpts=cpts, av=VGroup(av, nm)))
            intro_anims.append(FadeIn(VGroup(av, nm), shift=RIGHT * 0.15))

        self.play(LaggedStart(*intro_anims, lag_ratio=0.25), run_time=1.6)
        cap0 = self.caption("Everyone branches off `main` to build their own piece…",
                            color=INK, fs=26, buff=0.35)
        self.play(FadeIn(cap0, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)

        # ---- fork + commit on each branch (a wave = parallel work) -------- #
        fork_anims, first_commit_anims, rest_anims = [], [], []
        for b in branches:
            fork_from = np.array([b["fx"], main_y, 0.0])
            b["fork"] = gcurve(fork_from, b["cpts"][0], color=b["color"])
            fork_anims.append(Create(b["fork"]))
            b["dots"] = [commit_dot(b["color"], r=0.20).move_to(p) for p in b["cpts"]]
            b["edges"] = []
            first_commit_anims.append(GrowFromCenter(b["dots"][0]))
            for j in range(1, len(b["cpts"])):
                e = lane_edge(b["cpts"][j - 1], b["cpts"][j], color=b["color"])
                b["edges"].append(e)
                rest_anims.append(Create(e))
                rest_anims.append(GrowFromCenter(b["dots"][j]))

        # make sure the fork trunk dots exist
        for i, b in enumerate(branches):
            fx = b["fx"]
            if trunk_dots[fx] not in self.mobjects:
                first_commit_anims.append(GrowFromCenter(trunk_dots[fx]))

        self.play(LaggedStart(*fork_anims, lag_ratio=0.12), run_time=1.3)
        self.play(LaggedStart(*first_commit_anims, lag_ratio=0.12), run_time=1.1)
        if rest_anims:
            self.play(LaggedStart(*rest_anims, lag_ratio=0.1), run_time=1.2)
        cap1 = self.caption("…working in parallel, without stepping on each other.",
                            color=GOLD, fs=26, buff=0.35)
        self.play(FadeTransform(cap0, cap1), run_time=0.7)
        self.beat(1.8)

        # ---- merge each branch back into main (left to right) ------------- #
        cap2 = self.caption("Then each merges back into `main` — usually via a Pull Request.",
                            color=INK, fs=26, buff=0.35)
        self.play(FadeTransform(cap1, cap2), run_time=0.7)
        self.beat(0.6)
        for b in branches:
            tip = b["cpts"][-1]
            mx = b["mx"]
            mp = np.array([mx, main_y, 0.0])
            mcurve = gcurve(tip, mp, color=b["color"])
            new = trunk_dots[mx]
            appear = [Create(mcurve)]
            if new not in self.mobjects:
                appear.append(GrowFromCenter(new))
            self.play(*appear, run_time=0.6)
            self.play(main_tag.animate.move_to([mx, main_y, 0]).shift(DOWN * 0.0),
                      Flash(mp, color=b["color"], flash_radius=0.5), run_time=0.45)
        # keep the main tag just under the final trunk dot
        self.play(main_tag.animate.next_to([trunk_xs[-1], main_y, 0], RIGHT, buff=0.3),
                  run_time=0.4)
        self.beat(1.2)

        # ---- release tag on main ------------------------------------------ #
        rel = branch_tag("v1.0 ✔", GOLD, fs=22).move_to([trunk_xs[-1], main_y + 0.75, 0])
        rel_arrow = Arrow(rel.get_bottom(), [trunk_xs[-1], main_y + 0.28, 0], buff=0.05,
                          color=GOLD, stroke_width=4, max_tip_length_to_length_ratio=0.2)
        self.play(FadeIn(rel, shift=DOWN * 0.1), GrowArrow(rel_arrow),
                  Circumscribe(main_lane, color=GOLD, run_time=1.4))
        cap3 = self.caption("One project, many contributors — that's collaboration on GitHub.",
                            color=GOLD, fs=28, buff=0.35)
        self.play(FadeTransform(cap2, cap3), run_time=0.7)
        self.beat(2.4)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_overview()
        self.scene_commit()
        self.scene_push()
        self.scene_branch()
        self.scene_merge()
        self.scene_cherry()
        self.scene_collab()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_Base):
    def construct(self):
        self.play_intro()


class Overview(_Base):
    def construct(self):
        self.scene_overview()


class Commit(_Base):
    def construct(self):
        self.scene_commit()


class Push(_Base):
    def construct(self):
        self.scene_push()


class Branch(_Base):
    def construct(self):
        self.scene_branch()


class Merge(_Base):
    def construct(self):
        self.scene_merge()


class CherryPick(_Base):
    def construct(self):
        self.scene_cherry()


class Collab(_Base):
    def construct(self):
        self.scene_collab()


class Outro(_Base):
    def construct(self):
        self.play_outro()


class GitHubExplained(_Base):
    """The whole film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    GitHubExplained().render()
