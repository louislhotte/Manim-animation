"""Lockfiles — package.json, package-lock.json, and reproducible installs.

A short, house-style explainer on *why* a lockfile is worth committing, and why
the same two-file pattern shows up in every ecosystem.

    1. The manifest  -- package.json: what you *declare*. Direct dependencies,
                        each with a version *range* (^4.18.2).
    2. The catch     -- a range is not a version. Semver + the caret let the
                        resolved version drift, so `npm install` is not
                        deterministic. "Works on my machine."
    3. The lockfile  -- package-lock.json: the exact tree install resolved — every
                        package (direct AND transitive) pinned to one version, with
                        a resolved URL and an integrity hash. `npm ci` replays it.
    4. Reproducible  -- commit the lock and every machine — two devs, CI, prod —
                        gets the identical tree, bit for bit. The heart of the film.
    5. The pattern   -- pyproject.toml + poetry.lock is the same split; so is
                        Cargo, Bundler, Go, Composer. Manifest you write, lockfile
                        the tool computes. Declare loose, lock exact, commit both.

Scenes are exposed individually (``Manifest``, ``Ranges``, ``Lockfile``, ``Repro``,
``Pattern``, ``Recap``, ``Intro``, ``Outro``) and as one continuous film
(``LockfilesFilm``).

Env knobs:
    PL_QUICK=1    shorten every hold for a fast sanity render
    PL_DELAY=..   scale the motion-rhythm pauses
    PL_READ=..    absolute reading hold after a block of text (default 2.4 s)
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Render every glyph at
# a large base size and scale the mobject *down* to the requested size. Shadows
# manim's ``Text`` so every call benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("PL_QUICK") == "1"
# Two pacing knobs: DELAY scales the small motion pauses; READ is the absolute hold
# after a block of text lands. ANIM_SLOW stretches every played animation.
DELAY = float(os.environ.get("PL_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("PL_READ", 0.35 if QUICK else 2.4))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.0

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines / inert strokes
GOLD = "#FFD166"        # accent / the packages you name
GOOD = "#3DD68C"        # match / reproducible / green
BAD = "#FF5C5C"         # drift / mismatch / red
ACCENT = "#FFD166"

ARR_C = "#5B8DEF"       # byline / arrows (blue)

# code-panel colours (Menlo)
PLAIN = INK
COMMENT = MUTED
KEYC = "#82AAFF"        # structural json/toml keys
NAMEC = GOLD            # package names — the stars
STRV = "#C3E88D"        # string / version values
HASHC = MUTED           # urls and integrity hashes (noise)

MONO = "Menlo"
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

CODE_FS = 24

# JSON token → colour. Every key is quote-delimited so matches are precise: the
# quoted token ``"express"`` never bleeds into ``node_modules/express`` or a URL.
CODE_T2C = {
    # structural keys
    '"name"': KEYC, '"version"': KEYC, '"dependencies"': KEYC,
    '"devDependencies"': KEYC, '"lockfileVersion"': KEYC, '"packages"': KEYC,
    '"resolved"': KEYC, '"integrity"': KEYC,
    # package names
    '"express"': NAMEC, '"lodash"': NAMEC, '"jest"': NAMEC,
    '"node_modules/express"': NAMEC, '"node_modules/lodash"': NAMEC,
    # string / version values
    '"checkout-service"': STRV, '"1.4.0"': STRV,
    '"^4.18.2"': STRV, '"^4.17.21"': STRV, '"^29.7.0"': STRV,
    '"4.18.2"': STRV, '"4.17.21"': STRV,
    # noise: urls + hashes
    '"…/express-4.18.2.tgz"': HASHC, '"…/lodash-4.17.21.tgz"': HASHC,
    '"sha512-5/PsL6iGPd…"': HASHC, '"sha512-v2kDEe57lecT…"': HASHC,
}

# TOML token → colour (pyproject.toml / poetry.lock). Section headers coloured as
# keys; values gold/green; the content-hash muted.
TOML_T2C = {
    "[tool.poetry.dependencies]": KEYC, "[[package]]": KEYC, "[metadata]": KEYC,
    '"requests"': NAMEC,
    '"^2.31.0"': STRV, '"2.31.0"': STRV, '"^3.11"': STRV,
    '"sha256:9908…"': HASHC,
}


def _safe_t2c(s, table):
    """Per-line text→colour map, pruned so no key overlaps another present key.

    Manim's ``t2c`` raises on overlapping ranges — even same-colour ones. Keep only
    keys present in the line, then drop any that is a substring of another present
    key (e.g. bare ``requests`` inside quoted ``"requests"``).
    """
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


# ---- small reusable pieces ------------------------------------------------ #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    kw.update(extra)
    return Text(text, **kw)


def mono(text, fs=22, color=INK, **kw):
    return txt(text, fs=fs, color=color, font=MONO, **kw)


def chip(text, color, fs=22, w=None, h=0.6, fill=0.14, tcolor=None, weight="NORMAL",
         radius=0.12, font=None):
    """A rounded, tinted box with a centred auto-fitting label. grp[0] is the box."""
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight, font=font)
    width = (label.width + 0.55) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    return g


def pill(text, color, fs=26):
    """A bold status badge."""
    label = txt(text, fs=fs, color=color, weight="BOLD")
    box = RoundedRectangle(width=label.width + 0.6, height=0.66, corner_radius=0.33,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=0.16)
    label.move_to(box)
    return VGroup(box, label)


def arr(a, b, color=MUTED, sw=4, buff=0.14, tip=0.22):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.4, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.16, -0.16, 0], [0.16, 0.16, 0])
    b = Line([-0.16, 0.16, 0], [0.16, -0.16, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def lock_glyph(color=GOLD, s=1.0, closed=True):
    """A small padlock: rounded body + a shackle arc on top (Arc defaults to RED —
    always pass an explicit stroke_color)."""
    body = RoundedRectangle(width=0.5, height=0.42, corner_radius=0.08,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.12)
    body.move_to([0, -0.06, 0])
    shackle = Arc(radius=0.17, start_angle=0, angle=PI, stroke_color=color,
                  stroke_width=3).move_to([0, 0.19, 0])
    keyhole = Dot(radius=0.045, color=color).move_to([0, -0.04, 0])
    g = VGroup(body, shackle, keyhole)
    return g.scale(s)


def machine_glyph(color=MUTED, s=1.0):
    """A tiny monitor (screen + stand) to mark an environment."""
    screen = RoundedRectangle(width=0.54, height=0.36, corner_radius=0.05,
                              stroke_color=color, stroke_width=2.4, fill_opacity=0)
    screen.move_to([0, 0.12, 0])
    neck = Line([0, -0.06, 0], [0, -0.16, 0]).set_stroke(color, 2.4)
    base = Line([-0.16, -0.16, 0], [0.16, -0.16, 0]).set_stroke(color, 2.4)
    return VGroup(screen, neck, base).scale(s)


# ========================================================================== #
class _PLBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
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
        self._cap = None

    def flash_red(self, opacity=0.20):
        # inset from the frame edge so the transient veil never trips the
        # edge-bleed detector (it reads a full-frame fill as content on every edge)
        veil = Rectangle(width=config.frame_width - 0.5, height=config.frame_height - 0.5,
                         stroke_width=0, fill_color=BAD, fill_opacity=0)
        self.add(veil)
        self.play(veil.animate.set_fill(opacity=opacity), run_time=0.18)
        self.play(veil.animate.set_fill(opacity=0.0), run_time=0.32)
        self.remove(veil)

    def flash_good(self, opacity=0.12):
        veil = Rectangle(width=config.frame_width - 0.5, height=config.frame_height - 0.5,
                         stroke_width=0, fill_color=GOOD, fill_opacity=0)
        self.add(veil)
        self.play(veil.animate.set_fill(opacity=opacity), run_time=0.2)
        self.play(veil.animate.set_fill(opacity=0.0), run_time=0.35)
        self.remove(veil)

    def section_header(self, num, label, color=ACCENT):
        t = txt(f"{num} · {label}", fs=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(t, line)

    def bottomcap(self, s, color=INK, fs=23, buff=0.42, **kw):
        t = txt(s, fs=fs, color=color, **kw)
        if t.width > 12.9:
            t.scale_to_fit_width(12.9)
        t.to_edge(DOWN, buff=buff)
        return t

    def set_cap(self, s, color=INK, fs=23):
        """Replace the running bottom caption (transform if one is present)."""
        new = self.bottomcap(s, color=color, fs=fs)
        if getattr(self, "_cap", None) is not None and self._cap in self.mobjects:
            self.play(Transform(self._cap, new), run_time=0.5)
        else:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.1), run_time=0.5)
        return self._cap

    def clear_cap(self):
        if getattr(self, "_cap", None) is not None and self._cap in self.mobjects:
            self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

    # ---- Menlo code panel -------------------------------------------------- #
    def code_panel(self, spec, title="package.json", fs=CODE_FS, t2c=None,
                   indent_unit=0.5, line_buff=0.18, target_h=5.4, target_w=7.6):
        """spec: list of (indent, text); "" is a blank line. Returns (panel, lines)."""
        table = CODE_T2C if t2c is None else t2c
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.30, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith("#"):
                m = txt(s, fs=fs, color=COMMENT, font=MONO, slant=ITALIC)
            else:
                m = Text(s, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(s, table))
            m._indent = indent
            lines.append(m)
        code = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * indent_unit * m._indent)
        f = min(target_h / code.height, target_w / code.width, 1.0)
        if f < 1:
            code.scale(f)

        bg = RoundedRectangle(width=code.width + 0.9, height=code.height + 1.15,
                              corner_radius=0.16, stroke_color=FAINT, stroke_width=2,
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(code)
        bar = RoundedRectangle(width=bg.width, height=0.5, corner_radius=0.16,
                               stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=15, color=MUTED, font=MONO)
        if ttl.width > bg.width - 1.5:
            ttl.scale_to_fit_width(bg.width - 1.5)
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.2)
        panel = VGroup(bg, bar, dots, ttl, code)
        panel.code = code
        panel.lines = lines
        return panel, lines

    def hl_line(self, panel, line, color=ACCENT, opacity=0.16, pad=0.06, xpad=0.34):
        rect = RoundedRectangle(width=panel[0].width - xpad,
                                height=line.height + 2 * pad,
                                corner_radius=0.08, stroke_width=0,
                                fill_color=color, fill_opacity=opacity)
        rect.move_to([panel[0].get_center()[0], line.get_center()[1], 0])
        return rect

    # ---- house-style intro / outro cards ---------------------------------- #
    def _rule_under(self, header, color=GOLD, pad=1.0, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = txt("Lockfiles", fs=64, color=INK, weight="BOLD")
        header.set(width=min(6.0, header.width))
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=ARR_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = txt("package.json vs package-lock.json", fs=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = txt("one manifest, one lockfile, identical builds", fs=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.3)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = txt("Thank you for watching!", fs=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=ARR_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = txt("Declare loose. Lock exact. Commit both.", fs=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap, shift=UP * 0.1), run_time=0.8)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 1 — the manifest (package.json)
    # ====================================================================== #
    def scene_manifest(self):
        head = self.section_header("1", "The Manifest")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)
        self.set_cap("Every project ships a manifest — a list of what it depends on.")
        self.read(0.6)

        panel, lines = self.code_panel(
            [(0, "{"),
             (1, '"name": "checkout-service",'),
             (1, '"version": "1.4.0",'),
             (1, '"dependencies": {'),
             (2, '"express": "^4.18.2",'),
             (2, '"lodash": "^4.17.21"'),
             (1, "}"),
             (0, "}")],
            title="package.json", target_w=6.4, target_h=4.4)
        panel.move_to(LEFT * 2.9 + UP * 0.05)
        self.play(FadeIn(panel[0]), FadeIn(panel[1]), FadeIn(panel[2]), FadeIn(panel[3]),
                  run_time=0.6)
        self.play(LaggedStart(*[Write(m) for m in lines], lag_ratio=0.18, run_time=1.8))
        self.read(0.8)

        # callout: you write this by hand — direct deps only
        note = VGroup(
            chip("you write this", GOLD, fs=20, weight="BOLD"),
            txt("your direct dependencies,", fs=21, color=INK),
            txt("each with a version range", fs=21, color=INK),
        ).arrange(DOWN, buff=0.28)
        note.next_to(panel, RIGHT, buff=0.9)
        if note.get_right()[0] > config.frame_x_radius - 0.35:
            note.shift(LEFT * (note.get_right()[0] - (config.frame_x_radius - 0.35)))
        # highlight the dependencies block
        hl = self.hl_line(panel, VGroup(lines[3], lines[4], lines[5], lines[6]),
                          color=GOLD, opacity=0.10)
        self.play(FadeIn(hl), FadeIn(note[0], shift=LEFT * 0.2), run_time=0.6)
        self.play(FadeIn(note[1]), FadeIn(note[2]), run_time=0.6)
        self.set_cap("You name a few packages — and pin each to a range, not a version.")
        self.read(1.4)

        # zoom the caret line
        self.play(Indicate(lines[4], color=GOLD, scale_factor=1.12), run_time=0.9)
        self.set_cap("\"^4.18.2\" isn't one version. It's a whole range. Next scene: why that bites.",
                     color=ACCENT)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — the catch: semver ranges drift
    # ====================================================================== #
    def _semver_anatomy(self):
        """Return a VGroup of ^4.18.2 broken into MAJOR.MINOR.PATCH with labels."""
        caret = mono("^", fs=54, color=MUTED)
        n_major = mono("4", fs=54, color=INK)
        d1 = mono(".", fs=54, color=MUTED)
        n_minor = mono("18", fs=54, color=INK)
        d2 = mono(".", fs=54, color=MUTED)
        n_patch = mono("2", fs=54, color=INK)
        row = VGroup(caret, n_major, d1, n_minor, d2, n_patch).arrange(RIGHT, buff=0.10)

        def tag(num, label, color):
            br = Brace(num, DOWN, buff=0.12, color=FAINT)
            lb = txt(label, fs=18, color=color).next_to(br, DOWN, buff=0.10)
            return VGroup(br, lb)

        tags = VGroup(tag(n_major, "MAJOR", BAD),
                      tag(n_minor, "MINOR", GOLD),
                      tag(n_patch, "PATCH", GOOD))
        g = VGroup(row, tags)
        g.row, g.caret = row, caret
        g.nums = (n_major, n_minor, n_patch)
        return g

    def scene_ranges(self):
        head = self.section_header("2", "A Range, Not a Version")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)

        sv = self._semver_anatomy()
        sv.move_to(UP * 1.7)
        self.play(Write(sv.row), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.1) for t in sv[1]],
                              lag_ratio=0.2, run_time=1.0))
        self.set_cap("Versions are MAJOR · MINOR · PATCH — breaking, features, fixes.")
        self.read(1.4)

        # the caret expands to a rule
        rule = mono("^4.18.2   →   >= 4.18.2   and   < 5.0.0", fs=26, color=INK)
        rule.move_to(UP * 0.15)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.7)
        self.set_cap("The caret accepts any newer minor or patch — up to the next major.")
        self.read(1.5)

        # candidate versions: which ones satisfy ^4.18.2?
        cands = [("4.18.2", True, "today"),
                 ("4.18.7", True, "patch fix"),
                 ("4.19.0", True, "new minor"),
                 ("5.0.0", False, "major — excluded")]
        rows = VGroup()
        for ver, ok, why in cands:
            mark = make_tick(scale=0.8) if ok else make_cross(scale=0.8)
            vt = mono(ver, fs=24, color=GOOD if ok else BAD)
            note = txt(why, fs=19, color=MUTED)
            r = VGroup(mark, vt, note).arrange(RIGHT, buff=0.35)
            rows.add(r)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.26).move_to(DOWN * 1.7)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.15) for r in rows],
                              lag_ratio=0.22, run_time=1.6))
        self.read(1.2)

        # punchline — nondeterminism
        self.play(FadeOut(rule), FadeOut(sv), FadeOut(rows), run_time=0.5)
        line1 = mono("npm install", fs=30, color=INK)
        arrow_a = txt("today  →  4.18.2", fs=24, color=GOOD)
        arrow_b = txt("in a month  →  4.19.3", fs=24, color=GOLD)
        stack = VGroup(line1, arrow_a, arrow_b).arrange(DOWN, buff=0.4).move_to(UP * 0.4)
        self.play(FadeIn(line1, scale=0.9), run_time=0.5)
        self.play(FadeIn(arrow_a, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(arrow_b, shift=UP * 0.1), run_time=0.5)
        self.set_cap("Same manifest, different day, different version. The install isn't deterministic.",
                     color=INK)
        self.read(1.4)
        wm = txt("\"...but it works on my machine.\"", fs=30, color=BAD, weight="BOLD")
        wm.next_to(stack, DOWN, buff=0.7)
        self.play(FadeIn(wm, shift=UP * 0.1), run_time=0.6)
        self.flash_red()
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — the lockfile pins the whole resolved tree
    # ====================================================================== #
    def _dep_tree(self):
        """A small resolved tree: your 2 named deps, express dragging in children."""
        root = chip("checkout-service", GOLD, fs=20, weight="BOLD", fill=0.10)
        root.move_to([0, 1.7, 0])
        express = chip("express", NAMEC, fs=20, fill=0.12)
        express.move_to([-2.4, 0.15, 0])
        lodash = chip("lodash", NAMEC, fs=20, fill=0.12)
        lodash.move_to([2.6, 0.15, 0])

        kid_names = ["accepts", "body-parser", "qs"]
        kid_x = [-4.5, -2.85, -1.25]
        kids = VGroup()
        for name, x in zip(kid_names, kid_x):
            kids.add(chip(name, MUTED, fs=16, h=0.5, fill=0.06).move_to([x, -1.5, 0]))
        dots = txt("+ dozens more", fs=17, color=MUTED).move_to([-2.85, -2.28, 0])
        leaf = txt("(0 deps)", fs=17, color=MUTED).move_to([2.6, -1.5, 0])

        def link(a, b):
            return Line(a.get_bottom(), b.get_top(), stroke_color=FAINT, stroke_width=2)

        edges = VGroup(link(root, express), link(root, lodash),
                       *[link(express, k) for k in kids])
        g = VGroup(edges, root, express, lodash, kids, dots, leaf)
        g.root, g.express, g.lodash, g.kids = root, express, lodash, kids
        g.edges, g.dots, g.leaf = edges, dots, leaf
        return g

    def scene_lockfile(self):
        head = self.section_header("3", "The Lockfile")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)

        # first: what install actually resolves — a whole tree
        tree = self._dep_tree()
        self.set_cap("Install doesn't stop at your list — each package pulls in its own.")
        self.play(FadeIn(tree.root, scale=0.9), run_time=0.5)
        self.play(Create(tree.edges[0]), Create(tree.edges[1]),
                  FadeIn(tree.express), FadeIn(tree.lodash), run_time=0.7)
        self.play(LaggedStart(*[AnimationGroup(Create(tree.edges[2 + i]), FadeIn(k))
                                for i, k in enumerate(tree.kids)],
                              lag_ratio=0.15, run_time=1.2),
                  FadeIn(tree.leaf))
        self.play(FadeIn(tree.dots), run_time=0.4)
        self.set_cap("Two names in package.json can resolve to dozens of packages.")
        self.read(1.5)

        # the lock freezes every node of that tree
        self.set_cap("The lockfile records the answer — every node, pinned.", color=ACCENT)
        self.play(FadeOut(tree), run_time=0.6)

        panel, lines = self.code_panel(
            [(0, "{"),
             (1, '"name": "checkout-service",'),
             (1, '"lockfileVersion": 3,'),
             (1, '"packages": {'),
             (2, '"node_modules/express": {'),
             (3, '"version": "4.18.2",'),
             (3, '"resolved": "…/express-4.18.2.tgz",'),
             (3, '"integrity": "sha512-5/PsL6iGPd…"'),
             (2, "}"),
             (1, "}"),
             (0, "}")],
            title="package-lock.json", target_w=7.0, target_h=4.7)
        panel.move_to(LEFT * 2.6 + DOWN * 0.12)
        self.play(FadeIn(panel[0]), FadeIn(panel[1]), FadeIn(panel[2]), FadeIn(panel[3]),
                  run_time=0.6)
        self.play(LaggedStart(*[Write(m) for m in lines], lag_ratio=0.10, run_time=2.0))
        self.read(0.6)

        # three callouts: version / resolved / integrity
        callouts = [
            (5, "exact version", GOOD, "no caret — one pinned version"),
            (6, "resolved", ARR_C, "exactly where it came from"),
            (7, "integrity", GOLD, "a hash to verify the bytes"),
        ]
        col = VGroup(*[chip(name, color, fs=19, weight="BOLD", w=2.7)
                       for _, name, color, _ in callouts]).arrange(DOWN, buff=0.72)
        col.next_to(panel, RIGHT, buff=1.0)
        col.set_y(lines[6].get_center()[1])
        if col.get_right()[0] > config.frame_x_radius - 0.35:
            col.shift(LEFT * (col.get_right()[0] - (config.frame_x_radius - 0.35)))

        for i, (idx, name, color, desc) in enumerate(callouts):
            hl = self.hl_line(panel, lines[idx], color=color, opacity=0.18)
            c = col[i]
            lead = DashedLine([panel[0].get_right()[0] + 0.05, lines[idx].get_center()[1], 0],
                              c.get_left(), dash_length=0.09,
                              stroke_color=color, stroke_width=2)
            self.play(FadeIn(hl), Create(lead), FadeIn(c, shift=LEFT * 0.15), run_time=0.7)
            self.set_cap(desc, color=color)
            self.beat(0.9)
        self.read(0.7)

        # one entry shown — the lock pins the whole tree the same way
        self.set_cap("This is one entry of 57 — every package in the tree is pinned like this.")
        self.read(1.4)
        self.set_cap("`npm ci` installs exactly this tree — no resolving, no surprises.",
                     color=ACCENT)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — reproducibility & collaboration (the payoff)
    # ====================================================================== #
    def _env_box(self, title, install, versions, vcolor=INK):
        """An environment: monitor glyph + title, an install command, 2 version rows."""
        box = RoundedRectangle(width=3.0, height=1.9, corner_radius=0.14,
                               stroke_color=MUTED, stroke_width=2.4,
                               fill_color="#141C29", fill_opacity=0.45)
        glyph = machine_glyph(MUTED, s=0.9)
        ttl = txt(title, fs=21, color=INK, weight="BOLD")
        head = VGroup(glyph, ttl).arrange(RIGHT, buff=0.22)
        cmd = mono(install, fs=16, color=MUTED)
        rows = VGroup()
        for pkg, ver in versions:
            rows.add(VGroup(mono(pkg, fs=17, color=MUTED),
                            mono(ver, fs=17, color=vcolor)).arrange(RIGHT, buff=0.14))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        inner = VGroup(head, cmd, rows).arrange(DOWN, buff=0.16)
        inner.move_to(box)
        g = VGroup(box, inner)
        g.box, g.cmd, g.rows = box, cmd, rows
        return g

    def scene_repro(self):
        head = self.section_header("4", "Same Tree, Everywhere")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)

        # four environments, each running `npm install` and drifting apart
        drift = [
            ("Dev A", [("lodash", "4.17.21"), ("express", "4.18.2")]),
            ("Dev B", [("lodash", "4.17.20"), ("express", "4.18.2")]),
            ("CI", [("lodash", "4.17.21"), ("express", "4.18.1")]),
            ("Prod", [("lodash", "4.17.19"), ("express", "4.18.2")]),
        ]
        boxes = [self._env_box(t, "npm install", vers, vcolor=BAD) for t, vers in drift]
        grid = VGroup(*boxes).arrange_in_grid(rows=2, cols=2, buff=(0.9, 0.65))
        grid.move_to([0, 0.05, 0])
        self.set_cap("Without a lockfile, every environment resolves its own tree.")
        self.play(LaggedStart(*[FadeIn(b.box) for b in boxes], lag_ratio=0.12, run_time=0.9))
        self.play(LaggedStart(*[FadeIn(b[1]) for b in boxes], lag_ratio=0.12, run_time=1.2))
        self.read(1.0)

        drift_tag = pill("trees drifted apart", BAD, fs=22).next_to(grid, DOWN, buff=0.28)
        self.play(FadeIn(drift_tag, shift=UP * 0.1), run_time=0.5)
        self.flash_red()
        self.set_cap("Subtle version drift — and a bug nobody else can reproduce.", color=BAD)
        self.read(1.6)

        # commit the lock → npm ci → everyone converges
        self.play(FadeOut(drift_tag), run_time=0.35)
        self.set_cap("Commit package-lock.json — now every install replays that one tree.",
                     color=ACCENT)
        lock = lock_glyph(GOLD, s=1.1)
        lock_lbl = mono("package-lock.json", fs=20, color=GOLD)
        lock_grp = VGroup(lock, lock_lbl).arrange(RIGHT, buff=0.28)
        lock_grp.next_to(grid, DOWN, buff=0.30)
        self.play(FadeIn(lock_grp, shift=UP * 0.15), run_time=0.6)
        self.read(1.2)

        pinned = [("lodash", "4.17.21"), ("express", "4.18.2")]
        anims = []
        for b in boxes:
            new_rows = VGroup()
            for pkg, ver in pinned:
                new_rows.add(VGroup(mono(pkg, fs=17, color=MUTED),
                                    mono(ver, fs=17, color=GOOD)).arrange(RIGHT, buff=0.14))
            new_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to(b.rows)
            new_cmd = mono("npm ci", fs=16, color=GOOD).move_to(b.cmd, aligned_edge=LEFT)
            new_box = b.box.copy().set_stroke(GOOD, 2.6)
            anims += [Transform(b.rows, new_rows), Transform(b.cmd, new_cmd),
                      Transform(b.box, new_box)]
        self.play(*anims, run_time=1.0)
        self.flash_good()
        self.read(0.8)

        ok_tag = pill("identical, bit for bit", GOOD, fs=22).next_to(grid, DOWN, buff=0.28)
        self.play(FadeOut(lock_grp), FadeIn(ok_tag, shift=UP * 0.1), run_time=0.6)
        self.set_cap("Two devs, CI, prod — the exact same dependency tree. That's reproducibility.",
                     color=GOOD)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — the same pattern everywhere (Poetry, then a fan-out)
    # ====================================================================== #
    def scene_pattern(self):
        head = self.section_header("5", "The Same Pattern")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)
        self.set_cap("This split isn't a JavaScript quirk — it's how every ecosystem works.")

        # two columns: npm vs Poetry
        def col(title, manifest_spec, mtitle, lock_spec, ltitle, t2c):
            head_t = txt(title, fs=24, color=INK, weight="BOLD")
            man, _ = self.code_panel(manifest_spec, title=mtitle, t2c=t2c,
                                     fs=19, target_w=4.4, target_h=1.7)
            lock, _ = self.code_panel(lock_spec, title=ltitle, t2c=t2c,
                                      fs=19, target_w=4.4, target_h=2.1)
            g = VGroup(head_t, man, lock).arrange(DOWN, buff=0.3)
            g.man, g.lock = man, lock
            return g

        npm_col = col(
            "JavaScript · npm",
            [(0, "\"dependencies\": {"),
             (1, "\"express\": \"^4.18.2\""),
             (0, "}")], "package.json",
            [(0, "\"node_modules/express\": {"),
             (1, "\"version\": \"4.18.2\","),
             (1, "\"integrity\": \"sha512-5/PsL6iGPd…\""),
             (0, "}")], "package-lock.json",
            CODE_T2C)
        poetry_col = col(
            "Python · Poetry",
            [(0, "[tool.poetry.dependencies]"),
             (0, "requests = \"^2.31.0\"")], "pyproject.toml",
            [(0, "[[package]]"),
             (0, "name = \"requests\""),
             (0, "version = \"2.31.0\""),
             (0, "content-hash = \"sha256:9908…\"")], "poetry.lock",
            TOML_T2C)

        cols = VGroup(npm_col, poetry_col).arrange(RIGHT, buff=1.0, aligned_edge=UP).move_to(UP * 0.1)
        if cols.height > 5.0:
            cols.scale_to_fit_height(5.0).move_to(UP * 0.1)
        self.play(FadeIn(npm_col[0]), FadeIn(poetry_col[0]), run_time=0.6)
        self.play(FadeIn(npm_col.man), FadeIn(poetry_col.man), run_time=0.7)
        self.set_cap("A manifest you write — package.json, or pyproject.toml — with ranges.")
        self.read(1.4)
        self.play(FadeIn(npm_col.lock, shift=UP * 0.1),
                  FadeIn(poetry_col.lock, shift=UP * 0.1), run_time=0.7)
        self.set_cap("A lockfile the tool computes — exact versions and hashes. `poetry install` replays it.",
                     color=ACCENT)
        self.read(1.7)

        # fan-out: the pattern is universal
        fade = [FadeOut(cols)]
        if getattr(self, "_cap", None) is not None and self._cap in self.mobjects:
            fade.append(FadeOut(self._cap))
        self._cap = None
        self.play(*fade, run_time=0.5)
        title = txt("Manifest + lockfile is universal", fs=30, color=INK, weight="BOLD")
        title.move_to(UP * 2.2)
        self.play(FadeIn(title, shift=UP * 0.1), run_time=0.6)
        eco = [
            ("Rust · Cargo", "Cargo.toml", "Cargo.lock"),
            ("Ruby · Bundler", "Gemfile", "Gemfile.lock"),
            ("Go", "go.mod", "go.sum"),
            ("PHP · Composer", "composer.json", "composer.lock"),
        ]
        # fixed column widths so the arrows line up across rows
        names = [txt(name, fs=20, color=MUTED) for name, _, _ in eco]
        lead = max(n.width for n in names) + 0.25
        rows = VGroup()
        for (name, man, lock), nm in zip(eco, names):
            spacer = Rectangle(width=lead, height=0.5, stroke_opacity=0, fill_opacity=0)
            nm.move_to(spacer, aligned_edge=LEFT)
            namecell = VGroup(spacer, nm)
            m = chip(man, KEYC, fs=17, h=0.5, fill=0.10, w=2.35)
            ar = txt("→", fs=22, color=FAINT)
            lk = chip(lock, GOOD, fs=17, h=0.5, fill=0.10, w=2.5)
            rows.add(VGroup(namecell, m, ar, lk).arrange(RIGHT, buff=0.32))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(DOWN * 0.55)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.12) for r in rows],
                              lag_ratio=0.18, run_time=1.6))
        self.set_cap("Declare loose. Lock exact. Commit both — in any language.", color=ACCENT)
        self.read(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Closing takeaway
    # ====================================================================== #
    def scene_recap(self):
        lines = VGroup(
            txt("Lockfiles, in one breath:", fs=30, color=MUTED),
            txt("package.json says what you want.", fs=32, color=INK, weight="BOLD"),
            txt("package-lock.json pins what you got —", fs=32, color=INK, weight="BOLD"),
            txt("so every machine builds the same thing.", fs=30, color=INK),
            txt("Commit the lockfile.", fs=27, color=ACCENT, weight="BOLD"),
        ).arrange(DOWN, buff=0.34)
        self.play(FadeIn(lines[0]), run_time=0.6)
        self.read(0.5)
        self.play(Write(lines[1]), run_time=0.9)
        self.play(Write(lines[2]), run_time=0.9)
        self.play(FadeIn(lines[3], shift=UP * 0.1), run_time=0.7)
        self.read(1.0)
        self.play(FadeIn(lines[4], shift=UP * 0.12), run_time=0.8)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_manifest()
        self.scene_ranges()
        self.scene_lockfile()
        self.scene_repro()
        self.scene_pattern()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_PLBase):
    def construct(self):
        self.play_intro()


class Manifest(_PLBase):
    def construct(self):
        self.scene_manifest()


class Ranges(_PLBase):
    def construct(self):
        self.scene_ranges()


class Lockfile(_PLBase):
    def construct(self):
        self.scene_lockfile()


class Repro(_PLBase):
    def construct(self):
        self.scene_repro()


class Pattern(_PLBase):
    def construct(self):
        self.scene_pattern()


class Recap(_PLBase):
    def construct(self):
        self.scene_recap()


class Outro(_PLBase):
    def construct(self):
        self.play_outro()


class LockfilesFilm(_PLBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    LockfilesFilm().render()
