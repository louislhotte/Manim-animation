"""Role-Based Access Control — a short, house-style explainer.

Authentication answers *who are you?* (see the SSO / JWT films). Authorization
answers the next question: *what are you allowed to do?* RBAC is the pattern that
runs almost every real system's answer.

The idea in one line: **don't grant permissions to people — grant them to roles,
then hand people a role.** It collapses an N×M tangle of direct grants into a
tidy N + M, and turns "who can do what" into something you can actually manage.

We build it in four beats:

    1. The tangle  -- wire each person straight to each permission → chaos, and
                      the stale grant nobody remembered to revoke
    2. The fix     -- put a Role in the middle: Users → Roles → Permissions
    3. The check   -- a request arrives; resolve roles → permissions → allow/deny
    4. The rules   -- role hierarchy, least privilege, and where ABAC picks up

Everything is drawn with Manim ``Text`` (Pango), never ``Tex`` — no LaTeX
toolchain. Scenes render individually (``Tangle``, ``Roles``, ``Check``,
``Recap``, ``Intro``, ``Outro``) or as one film (``HowRBACWorks``).

Env knobs:
    RBAC_QUICK=1   collapse every hold for a fast sanity render
    RBAC_DELAY=..  reading-rhythm multiplier for small inter-step pauses
    RBAC_READ=..   absolute hold after a subtitle lands (seconds) — reading time
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text (shared house fix) ----------------------------------------- #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Render every glyph
# at a large base size and scale the mobject *down* — spacing stays crisp.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("RBAC_QUICK") == "1"
DELAY = float(os.environ.get("RBAC_DELAY", 0.28 if QUICK else 1.05))
READ = float(os.environ.get("RBAC_READ", 0.35 if QUICK else 2.7))
ANIM_SLOW = 1.0 if QUICK else 1.3
END_HOLD = 0.2 if QUICK else 2.3  # settle held on a finished scene before it wipes

# ---- palette (dark house style, shared across the series) ----------------- #
BG = "#0E1117"          # dark slate background
PANEL = "#151A23"       # panel fill
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#2A3140"       # gridlines / faint wires
GOLD = "#FFD166"        # accent / rules

USER_C = "#5B8DEF"      # people (blue)
ROLE_C = "#C792EA"      # roles (violet — the hero indirection)
PERM_C = "#2EC4B6"      # ordinary permissions (teal)
DANGER = "#FF8C42"      # high-privilege permissions: delete / manage (orange)
GOOD = "#3DD68C"        # allowed / granted (green)
BAD = "#FF5C5C"         # denied / stale grant (red)
ACCENT = GOLD

MONO = "Menlo"          # code / permission names
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    return Text(text, **kw)


def mono(text, fs=18, color=INK):
    return Text(text, font_size=fs, color=color, font=MONO)


def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, tcolor=None, weight="NORMAL", radius=0.12):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    g.label = label
    return g


def pill(text, color, fs=22, fill=0.16, weight="BOLD"):
    t = txt(text, fs=fs, color=color, weight=weight)
    box = RoundedRectangle(width=t.width + 0.44, height=t.height + 0.26,
                           corner_radius=0.13, stroke_color=color, stroke_width=2,
                           fill_color=color, fill_opacity=fill)
    box.move_to(t)
    return VGroup(box, t)


def plate(mob, pad_x=0.14, pad_y=0.09, op=0.72):
    """A translucent dark plate behind a label so it reads over anything."""
    bg = RoundedRectangle(width=mob.width + 2 * pad_x, height=mob.height + 2 * pad_y,
                          corner_radius=0.08, stroke_width=0,
                          fill_color=BG, fill_opacity=op).move_to(mob)
    return VGroup(bg, mob)


def arr(a, b, color=MUTED, sw=4, buff=0.12, tip=0.2):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.35, tip_length=tip)


def wire(a, b, color=USER_C, sw=2.0, op=0.85):
    """A thin connecting line that sits behind the glyphs."""
    ln = Line(a, b, stroke_color=color, stroke_width=sw, stroke_opacity=op)
    ln.set_z_index(-1)
    return ln


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


# ---- glyphs (all hand-drawn Manim mobjects, no assets) -------------------- #
def person(color=USER_C, s=1.0):
    """A simple 'user' silhouette: head + body."""
    body = RoundedRectangle(width=0.5 * s, height=0.56 * s, corner_radius=0.14 * s,
                            color=color, fill_opacity=1, stroke_width=0)
    head = Circle(radius=0.18 * s, color=color, fill_opacity=1, stroke_width=0)
    head.next_to(body, UP, buff=0.04 * s)
    g = VGroup(body, head)
    g.body = body
    return g


def user_unit(name, color=USER_C, s=0.62, fs=20):
    """A person glyph with a bold name to its right — one row of the Users column."""
    p = person(color, s=s)
    lbl = txt(name, fs=fs, color=INK, weight="BOLD")
    g = VGroup(p, lbl).arrange(RIGHT, buff=0.16)
    g.person = p
    g.label = lbl
    return g


def role_badge(name, color, w=2.15, h=0.76, fs=21):
    """A role, drawn as an access badge: a rounded card with a keyhole emblem."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.13,
                            stroke_color=color, stroke_width=2.8,
                            fill_color=color, fill_opacity=0.18)
    tag = RoundedRectangle(width=0.28, height=0.4, corner_radius=0.06,
                           stroke_color=color, stroke_width=2.2,
                           fill_color=color, fill_opacity=0.55)
    hole = VGroup(
        Dot(radius=0.05, color=BG),
        Rectangle(width=0.05, height=0.1, fill_color=BG, fill_opacity=1, stroke_width=0),
    ).arrange(DOWN, buff=0.0)
    hole.move_to(tag)
    emblem = VGroup(tag, hole).move_to(body.get_left() + RIGHT * 0.3)
    name_t = txt(name, fs=fs, color=INK, weight="BOLD")
    if name_t.width > w - 0.85:
        name_t.scale((w - 0.85) / name_t.width)
    name_t.move_to(body).shift(RIGHT * 0.2)
    g = VGroup(body, emblem, name_t)
    g.body = body
    g.name = name_t
    return g


def perm_chip(name, danger=False, w=None, h=0.56, fs=18):
    """A single permission, in monospace, tagged teal (ordinary) or orange (high)."""
    c = DANGER if danger else PERM_C
    dot = Dot(radius=0.05, color=c)
    lbl = mono(name, fs=fs, color=INK)
    inner = VGroup(dot, lbl).arrange(RIGHT, buff=0.13)
    width = (inner.width + 0.42) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.1,
                           stroke_color=c, stroke_width=2.4,
                           fill_color=c, fill_opacity=0.12)
    inner.move_to(box)
    g = VGroup(box, inner)
    g.box = box
    g.label = lbl
    g.perm_color = c
    return g


def padlock(color=ROLE_C, s=1.0, closed=True):
    """A padlock: body, shackle (an Arc — defaults RED, so pass color), keyhole."""
    body = RoundedRectangle(width=0.52 * s, height=0.44 * s, corner_radius=0.08 * s,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.18)
    shackle = Arc(radius=0.16 * s, start_angle=0, angle=PI, color=color, stroke_width=3.2)
    kh = VGroup(
        Dot(radius=0.035 * s, color=color),
        Line([0, 0, 0], [0, -0.1 * s, 0], color=color, stroke_width=2.4),
    ).arrange(DOWN, buff=0.0).move_to(body)
    if closed:
        shackle.next_to(body, UP, buff=-0.03 * s)
    else:
        shackle.next_to(body, UP, buff=-0.03 * s).shift(UP * 0.09 * s + LEFT * 0.08 * s)
        shackle.rotate(-0.5, about_point=shackle.get_bottom() + RIGHT * 0.16 * s)
    g = VGroup(body, shackle, kh)
    g.body = body
    g.shackle = shackle
    return g


def stamp(text, color):
    """A rotated rubber-stamp verdict (ALLOWED / DENIED)."""
    t = txt(text, fs=44, color=color, weight="BOLD")
    box = RoundedRectangle(width=t.width + 0.6, height=t.height + 0.42, corner_radius=0.14,
                           stroke_color=color, stroke_width=6, fill_opacity=0)
    t.move_to(box)
    g = VGroup(box, t).rotate(-0.2)
    return g


# ========================================================================== #
class _RBACBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
        # stretch real animations so transitions aren't abrupt, but never scale a
        # bare Wait (a reading hold, handled by read()/beat()).
        if not (len(anims) == 1 and isinstance(anims[0], Wait)):
            rt = kwargs.get("run_time")
            if rt is not None:
                kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def read(self, k=1.0):
        self.wait(k * READ)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.7):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- text helpers ----------------------------------------------------- #
    def section_header(self, label, color):
        t = txt(label, fs=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=23, y=-3.42, weight="NORMAL"):
        """A bottom caption, width-clamped so it never runs off-screen."""
        m = txt(text, fs=fs, color=color, weight=weight)
        if m.width > 12.7:
            m.scale_to_fit_width(12.7)
        m.move_to([0, y, 0])
        return m

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("Role-Based Access Control", font_size=56, color=INK, weight="BOLD")
        header.set(width=min(9.6, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        lock = padlock(GOLD, s=0.95, closed=True).move_to(line.get_right() + RIGHT * 0.08 + UP * 0.3)
        writer = Text("Created by Ptolémé", font_size=28, color=USER_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.play(FadeIn(lock, shift=DOWN * 0.15), run_time=0.6)
        self.read(0.7)
        sub = Text("Who can do what — without losing your mind.",
                   font_size=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), FadeOut(lock), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("the authorization layer · System Design",
                   font_size=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.4)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=USER_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Who you are ≠ what you can do.",
                     font_size=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ---- shared column builders ------------------------------------------- #
    def build_users(self, names, x, ys):
        col = VGroup(*[user_unit(n) for n in names])
        for u, y in zip(col, ys):
            u.move_to([x, y, 0])
        rx = max(u.get_right()[0] for u in col)
        for u in col:
            u.align_to([rx, 0, 0], RIGHT)  # tidy right edges for line origins
        return col

    def build_perms(self, specs, x, ys):
        col = VGroup(*[perm_chip(n, danger=d) for n, d in specs])
        for p, y in zip(col, ys):
            p.move_to([x, y, 0])
        lx = min(p.get_left()[0] for p in col)
        for p in col:
            p.align_to([lx, 0, 0], LEFT)  # tidy left edges for line targets
        return col

    # ====================================================================== #
    # Scene 1 — The tangle: grant permissions straight to people
    # ====================================================================== #
    def scene_tangle(self):
        # opening bridge: authentication -> authorization
        title = Text("Authorization", font_size=54, color=INK, weight="BOLD")
        sub = txt("Authentication proved who you are.   Now — what are you allowed to do?",
                  fs=25, color=MUTED)
        sub.next_to(title, DOWN, buff=0.32)
        self.play(Write(title), run_time=1.2)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.7)
        self.read(1.4)
        self.play(FadeOut(sub), FadeOut(title), run_time=0.6)

        header = self.section_header("The naïve way: grant to people", BAD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        names = ["Alice", "Bob", "Carol", "Dan"]
        col_ys = [1.95, 0.7, -0.55, -1.8]
        users = self.build_users(names, -4.7, col_ys)
        perms = self.build_perms(
            [("read", False), ("write", False), ("delete", True), ("manage", True)],
            4.95, col_ys)

        u_head = pill("Users", USER_C, fs=18).move_to([users.get_center()[0], 2.72, 0])
        p_head = pill("Permissions", PERM_C, fs=18).move_to([perms.get_center()[0], 2.72, 0])

        self.play(FadeIn(u_head), LaggedStart(*[FadeIn(u, shift=RIGHT * 0.12) for u in users],
                                              lag_ratio=0.12, run_time=1.0))
        self.play(FadeIn(p_head), LaggedStart(*[FadeIn(p, shift=LEFT * 0.12) for p in perms],
                                              lag_ratio=0.12, run_time=1.0))
        cap = self.say("Wire each person straight to each permission they need.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.2)

        # the tangle of direct grants
        grants = {0: [0, 1, 2, 3], 1: [0, 1], 2: [0], 3: [0, 1, 2]}
        wires = {}
        for ui, pis in grants.items():
            for pi in pis:
                w = wire(users[ui].get_right() + RIGHT * 0.08,
                         perms[pi].get_left() + LEFT * 0.08,
                         color=USER_C, sw=1.8, op=0.5)
                wires[(ui, pi)] = w
        self.play(LaggedStart(*[Create(w) for w in wires.values()],
                              lag_ratio=0.04, run_time=1.7))
        nm = plate(txt("N users  ×  M permissions", fs=20, color=INK, weight="BOLD"))
        nm.move_to([0, 2.72, 0])
        self.play(FadeIn(nm, shift=DOWN * 0.1), run_time=0.5)
        cap2 = self.say("Every grant is its own thread. It only grows.")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.3)

        # the stale grant: Dan moved to read-only, but delete was never revoked
        stale = wires[(3, 2)]
        self.play(stale.animate.set_stroke(BAD, 3.4, opacity=1.0),
                  perms[2].box.animate.set_stroke(BAD, 3.0),
                  run_time=0.5)
        self.play(Flash(users[3], color=BAD, flash_radius=0.9), run_time=0.6)
        cap3 = self.say("Dan moved to a read-only job — but this grant was never revoked.",
                        color=BAD, weight="BOLD")
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(1.5)

        # takeaway card
        self.play(FadeOut(Group(users, perms, u_head, p_head, nm, header,
                                *wires.values(), cap3)), run_time=0.6)
        k1 = Text("Grant permissions to people, one by one…", font_size=36, color=INK, weight="BOLD")
        k2 = Text("…and every hire, quit, or transfer means untangling the mess.",
                  font_size=27, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.36).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.read(1.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The fix: a Role in the middle
    # ====================================================================== #
    def scene_roles(self):
        header = self.section_header("The fix: a role in the middle", ROLE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        col_ys = [1.95, 0.7, -0.55, -1.8]
        users = self.build_users(["Alice", "Bob", "Carol", "Dan"], -5.05, col_ys)
        perms = self.build_perms(
            [("read", False), ("write", False), ("delete", True), ("manage", True)],
            5.15, col_ys)
        roles = VGroup(
            role_badge("Viewer", PERM_C),
            role_badge("Editor", ROLE_C),
            role_badge("Admin", DANGER),
        )
        for r, y in zip(roles, [1.5, 0.0, -1.5]):
            r.move_to([0, y, 0])

        u_head = pill("Users", USER_C, fs=17).move_to([users.get_center()[0], 2.72, 0])
        r_head = pill("Roles", ROLE_C, fs=17).move_to([0, 2.72, 0])
        p_head = pill("Permissions", PERM_C, fs=17).move_to([perms.get_center()[0], 2.72, 0])

        self.play(FadeIn(u_head), FadeIn(p_head),
                  LaggedStart(*[FadeIn(u) for u in users], lag_ratio=0.08, run_time=0.7),
                  LaggedStart(*[FadeIn(p) for p in perms], lag_ratio=0.08, run_time=0.7))
        cap = self.say("Instead of wiring people straight to permissions…")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        self.play(FadeIn(r_head),
                  LaggedStart(*[FadeIn(r, scale=0.7) for r in roles], lag_ratio=0.15, run_time=1.0))
        cap2 = self.say("…put a Role in the middle. Each role bundles the permissions for a job.")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.2)

        # role -> permission grants
        role_perms = {0: [0], 1: [0, 1], 2: [0, 1, 2, 3]}
        rp_wires = VGroup()
        for ri, pis in role_perms.items():
            for pi in pis:
                col = perms[pi].perm_color
                rp_wires.add(wire(roles[ri].get_right() + RIGHT * 0.08,
                                  perms[pi].get_left() + LEFT * 0.08,
                                  color=col, sw=2.0, op=0.7))
        self.play(LaggedStart(*[Create(w) for w in rp_wires], lag_ratio=0.05, run_time=1.3))
        self.read(0.8)

        # user -> role assignments (Alice→Admin, Bob→Editor, Carol→Viewer, Dan→Editor)
        assign = {0: 2, 1: 1, 2: 0, 3: 1}
        ur_wires = {}
        for ui, ri in assign.items():
            ur_wires[ui] = wire(users[ui].get_right() + RIGHT * 0.08,
                                 roles[ri].get_left() + LEFT * 0.08,
                                 color=USER_C, sw=2.2, op=0.8)
        self.play(LaggedStart(*[Create(w) for w in ur_wires.values()],
                              lag_ratio=0.1, run_time=1.1))
        cap3 = self.say("Assign people a role — not a pile of permissions.", color=ACCENT)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(1.4)

        # maintenance win #1 — promote Carol: Viewer -> Editor, one edge moves
        new_c = wire(users[2].get_right() + RIGHT * 0.08,
                     roles[1].get_left() + LEFT * 0.08, color=USER_C, sw=2.2, op=0.85)
        self.play(Transform(ur_wires[2], new_c), run_time=0.8)
        self.play(Indicate(roles[1], color=GOOD, scale_factor=1.08),
                  Flash(perms[1], color=GOOD, flash_radius=0.7), run_time=0.7)
        cap4 = self.say("Promote Carol? Point her at Editor — she gains write instantly.", color=GOOD)
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.3)

        # maintenance win #2 — offboard Dan: cut one assignment, all access gone
        self.play(users[3].animate.set_opacity(0.3),
                  FadeOut(ur_wires[3]), run_time=0.7)
        cap5 = self.say("Dan leaves? Delete one assignment — every permission goes with it.", color=BAD)
        self.play(ReplacementTransform(cap4, cap5), run_time=0.5)
        self.read(1.4)

        # takeaway card
        self.play(FadeOut(Group(users, perms, roles, u_head, r_head, p_head,
                                rp_wires, *ur_wires.values(), header, cap5)), run_time=0.6)
        k1 = Text("Users get Roles.   Roles hold Permissions.", font_size=36, color=INK, weight="BOLD")
        k2 = Text("N + M relationships to manage — not N × M.",
                  font_size=28, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.36).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.read(1.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The check: a request arrives, allow or deny
    # ====================================================================== #
    def _make_request(self, user_name, ucolor):
        who = chip(user_name, ucolor, fs=19, weight="BOLD")
        act = chip("DELETE", DANGER, fs=18, weight="BOLD")
        res = mono("/reports/Q3", fs=19, color=INK)
        row = VGroup(who, act, res).arrange(RIGHT, buff=0.24)
        box = RoundedRectangle(width=row.width + 0.6, height=row.height + 0.42, corner_radius=0.12,
                               stroke_color=MUTED, stroke_width=2, fill_color=PANEL, fill_opacity=0.55)
        row.move_to(box)
        g = VGroup(box, row)
        g.who = who
        return g

    def _check_pass(self, user_name, ucolor, role_name, role_color, perm_specs, allowed):
        """Run one authorization check; return the created mobjects to fade later."""
        LX = -6.3          # left edge for row labels
        created = VGroup()

        def row(label_text, y, target_builder):
            lab = txt(label_text, fs=22, color=MUTED)
            lab.move_to([LX + lab.width / 2, y, 0])
            a = arr(lab.get_right() + RIGHT * 0.1, lab.get_right() + RIGHT * 0.9,
                    color=MUTED, sw=3, buff=0.05)
            tgt = target_builder()
            tgt.next_to(a, RIGHT, buff=0.22)
            grp = VGroup(lab, a, tgt)
            grp.target = tgt
            return grp

        # row 1 — resolve the user's role
        r1 = row(f"who is {user_name}?", 1.25, lambda: role_badge(role_name, role_color))
        self.play(FadeIn(r1[0]), GrowArrow(r1[1]), run_time=0.5)
        self.play(FadeIn(r1.target, scale=0.8), run_time=0.5)
        created.add(r1)
        self.read(0.8)

        # row 2 — expand that role to its permissions
        def perms_group():
            g = VGroup(*[perm_chip(n, danger=d, fs=15, h=0.48) for n, d in perm_specs])
            g.arrange(RIGHT, buff=0.15)
            return g
        r2 = row(f"{role_name} can:", 0.05, perms_group)
        self.play(FadeIn(r2[0]), GrowArrow(r2[1]), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.08) for c in r2.target],
                              lag_ratio=0.12, run_time=0.7))
        created.add(r2)
        self.read(0.9)

        # row 3 — does that set include the required permission?
        lab3 = txt('needs  "delete"  →', fs=22, color=INK)
        lab3.move_to([LX + lab3.width / 2, -1.15, 0])
        created.add(lab3)
        self.play(FadeIn(lab3), run_time=0.5)

        # scan the permission set for "delete"
        has_delete = any(n == "delete" for n, _ in perm_specs)
        if has_delete:
            target_chip = [c for (n, _), c in zip(perm_specs, r2.target) if n == "delete"][0]
            mark = make_tick(GOOD, sw=7, scale=1.1).next_to(lab3, RIGHT, buff=0.3)
            self.play(Indicate(target_chip, color=GOOD, scale_factor=1.15), run_time=0.6)
            self.play(Create(mark), run_time=0.4)
        else:
            ghost = perm_chip("delete", danger=True, fs=15, h=0.48).next_to(lab3, RIGHT, buff=0.3)
            ghost.set_opacity(0.35)
            cx = make_cross(BAD, sw=6, scale=0.9).move_to(ghost)
            self.play(FadeIn(ghost), run_time=0.4)
            self.play(Create(cx), run_time=0.4)
            mark = VGroup(ghost, cx)
        created.add(mark)
        self.read(0.7)

        # the verdict — slammed into the open lower-right, clear of the rows
        vcolor = GOOD if allowed else BAD
        vtext = "ALLOWED" if allowed else "DENIED"
        vst = stamp(vtext, vcolor).move_to([3.55, -1.05, 0])
        self.play(FadeIn(vst, scale=0.6), Flash(vst, color=vcolor, flash_radius=1.15),
                  run_time=0.5)
        created.add(vst)
        return created

    def scene_check(self):
        header = self.section_header("The access check", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        req = self._make_request("Bob", USER_C).move_to([0, 2.55, 0])
        self.play(FadeIn(req, shift=DOWN * 0.1), run_time=0.6)
        cap = self.say("A request arrives. RBAC answers it in three lookups.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.2)

        # Bob is an Editor — no delete → DENIED
        made = self._check_pass("Bob", USER_C, "Editor", ROLE_C,
                                [("read", False), ("write", False)], allowed=False)
        cap2 = self.say("Bob is an Editor. Editors can't delete → request denied.", color=BAD, weight="BOLD")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.6)

        # swap the request to Alice, re-run
        self.play(FadeOut(made), run_time=0.5)
        req2 = self._make_request("Alice", USER_C).move_to([0, 2.55, 0])
        self.play(ReplacementTransform(req, req2), run_time=0.5)
        cap3 = self.say("Same file, same action — a different role.")
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(1.0)

        made2 = self._check_pass("Alice", USER_C, "Admin", DANGER,
                                 [("read", False), ("write", False),
                                  ("delete", True), ("manage", True)], allowed=True)
        cap4 = self.say("Alice is an Admin. Admins may delete → allowed.", color=GOOD, weight="BOLD")
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.5)

        # takeaway
        self.play(FadeOut(Group(made2, req2, header, cap4)), run_time=0.6)
        k1 = Text("The check never looks at the person.", font_size=36, color=INK, weight="BOLD")
        k2 = Text("It asks: does any of their roles grant this permission?",
                  font_size=27, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.36).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.read(1.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — The rules: hierarchy, least privilege, and ABAC
    # ====================================================================== #
    def scene_recap(self):
        header = self.section_header("The rules that make it work", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        # cumulative stacks: Viewer ⊂ Editor ⊂ Admin — the same chips pile up
        role_defs = [
            ("Viewer", PERM_C, [("read", False)]),
            ("Editor", ROLE_C, [("read", False), ("write", False)]),
            ("Admin", DANGER, [("read", False), ("write", False),
                               ("delete", True), ("manage", True)]),
        ]
        base_y = -2.05
        cols = VGroup()
        xs = [-3.9, 0.0, 3.9]
        for (rname, rcolor, specs), x in zip(role_defs, xs):
            chips = VGroup(*[perm_chip(n, danger=d, w=2.0, fs=17) for n, d in specs])
            chips.arrange(UP, buff=0.16)
            chips.move_to([x, base_y + chips.height / 2, 0])
            lab = pill(rname, rcolor, fs=18)
            lab.move_to([x, chips.get_top()[1] + 0.42, 0])
            col = VGroup(lab, chips)
            col.chips = chips
            col.lab = lab
            cols.add(col)

        self.play(FadeIn(cols[0].lab), FadeIn(cols[0].chips[0]), run_time=0.6)
        cap = self.say("A Viewer can read.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(0.9)

        # Editor = Viewer's chips + write
        self.play(FadeIn(cols[1].lab), run_time=0.4)
        self.play(TransformFromCopy(cols[0].chips[0], cols[1].chips[0]), run_time=0.6)
        self.play(FadeIn(cols[1].chips[1], shift=UP * 0.1), run_time=0.5)
        cap2 = self.say("An Editor inherits read — and adds write.")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.0)

        # Admin = Editor's chips + delete + manage
        self.play(FadeIn(cols[2].lab), run_time=0.4)
        self.play(TransformFromCopy(cols[1].chips[:2], cols[2].chips[:2]), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(cols[2].chips[i], shift=UP * 0.1) for i in (2, 3)],
                              lag_ratio=0.2, run_time=0.7))
        cap3 = self.say("An Admin inherits both — and adds the dangerous powers.")
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(1.2)

        # the principle
        hier = plate(txt("Viewer  ⊂  Editor  ⊂  Admin", fs=24, color=INK, weight="BOLD"))
        hier.move_to([0, 2.5, 0])
        self.play(FadeIn(hier, shift=DOWN * 0.1), run_time=0.5)
        cap4 = self.say("Senior roles inherit junior permissions — so grant the smallest role that works.",
                        color=ACCENT)
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.6)

        # least privilege + ABAC nod, then the final takeaway
        self.play(FadeOut(Group(cols, hier, header, cap4)), run_time=0.6)
        lp = Text("Least privilege, by default.", font_size=40, color=INK, weight="BOLD")
        note = txt("Need finer control — time, location, ownership? That's ABAC, the next layer.",
                   fs=24, color=MUTED)
        note.next_to(lp, DOWN, buff=0.5)
        self.play(FadeIn(lp, shift=UP * 0.1), run_time=0.7)
        self.read(1.0)
        self.play(FadeIn(note), run_time=0.7)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_tangle()
        self.scene_roles()
        self.scene_check()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_RBACBase):
    def construct(self):
        self.play_intro()


class Tangle(_RBACBase):
    def construct(self):
        self.scene_tangle()


class Roles(_RBACBase):
    def construct(self):
        self.scene_roles()


class Check(_RBACBase):
    def construct(self):
        self.scene_check()


class Recap(_RBACBase):
    def construct(self):
        self.scene_recap()


class Outro(_RBACBase):
    def construct(self):
        self.play_outro()


class HowRBACWorks(_RBACBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    HowRBACWorks().render()
