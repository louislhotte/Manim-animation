"""The base scene every explainer inherits: pacing, captions, wipes, bookends.

A film declares only what is specific to it::

    from manimx import *

    class _Base(ExplainerScene):
        pace = Pace.from_env("KV", read=3.0)        # KV_QUICK / KV_DELAY / KV_READ
        TITLE = "The KV Cache"
        SUBTITLE = "Why the 1000th token is almost as cheap as the first"
        RECAP = "Compute the past once. Reuse it forever."
        SCENES = ("waste", "reuse", "cache")         # -> scene_waste(), ...

        def scene_waste(self): ...

    class Intro(_Base):
        def construct(self): self.play_intro()
    class Waste(_Base):
        def construct(self): self.scene_waste()
    class KVCacheFilm(_Base):
        def construct(self): self.play_all()

Every method here is a default: override any of them in the film's base class.
Mixed 2D/3D films put shared methods on a mixin ``class _Common(ExplainerMixin)``
and combine it with ``Scene`` / ``ThreeDScene``.
"""

from __future__ import annotations

from manim import (
    DOWN,
    UL,
    UP,
    Create,
    FadeIn,
    FadeOut,
    Line,
    MovingCameraScene,
    Scene,
    ThreeDScene,
    Transform,
    VGroup,
    Wait,
    Write,
)

from .code import hl_lines
from .layout import CAPTION_W, CAPTION_Y
from .pacing import Pace
from .palette import BG, GOLD, INK, MUTED, SKY
from .text import Text, clamp_width, txt

BYLINE = "Created by Ptolémé"


def rule_under(header, color=GOLD, pad=1.0, drop=0.45):
    """The house title rule: runs ``pad`` past both ends of ``header``."""
    return Line(
        [header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
        [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0],
    ).set_stroke(width=3, color=color)


class ExplainerMixin:
    """House plumbing shared by 2D and 3D explainer scenes (see module docstring)."""

    pace: Pace = Pace.from_env()
    background: str = BG
    WIPE_RT: float = 0.7  # default fade-out time of wipe()
    WIPE_STRETCH: bool = True  # False: the wipe fade ignores pace.anim_slow
    WIPE_SETTLES: bool = False  # True: wipe() holds settle() before fading

    # canonical bookend cards (play_intro / play_outro) and film order (play_all)
    TITLE: str = ""
    SUBTITLE: str = ""
    TAGLINE: str = ""
    RECAP: str = ""
    RULE_COLOR: str = GOLD
    BYLINE_COLOR: str = SKY
    SCENES: tuple[str, ...] = ()

    def setup(self):
        super().setup()
        self.camera.background_color = self.background
        self._cap = None  # the running bottom caption
        self.hlrect = None  # the moving code-line highlight

    # ---- timing ----------------------------------------------------------- #
    def play(self, *anims, **kwargs):
        """``Scene.play`` with every animation stretched by ``pace.anim_slow``.

        Bare ``Wait``s are never stretched: reading holds are owned by
        ``beat``/``read``/``settle``.
        """
        p = self.pace
        if p.stretch == "given":
            if not (len(anims) == 1 and isinstance(anims[0], Wait)):
                rt = kwargs.get("run_time")
                if rt is not None:
                    kwargs["run_time"] = rt * p.anim_slow
        elif p.stretch == "infer":
            is_wait = any(type(a).__name__ == "Wait" for a in anims)
            if not p.quick and anims and not is_wait:
                rt = kwargs.get("run_time")
                if rt is None:
                    rts = [r for r in (getattr(a, "run_time", None) for a in anims) if r]
                    rt = max(rts) if rts else 1.0
                kwargs["run_time"] = rt * p.anim_slow
        return super().play(*anims, **kwargs)

    def play_unstretched(self, *anims, **kwargs):
        """``Scene.play`` with the exact ``run_time`` (no ``anim_slow`` stretch)."""
        return super().play(*anims, **kwargs)

    def beat(self, t=1.0):
        """A rhythm pause between animation steps: ``t * pace.delay`` seconds."""
        self.wait(t * self.pace.delay)

    def read(self, k=1.0):
        """A reading hold after text lands: ``k * pace.read`` seconds (~3 s)."""
        self.wait(k * self.pace.read)

    def card_wait(self, t=1.0):
        quick, normal = self.pace.card
        self.wait(t * (quick if self.pace.quick else normal))

    def settle(self):
        """Hold the finished scene before it wipes."""
        self.wait(self.pace.end_hold)

    def wipe(self, rt=None):
        """Clear every updater, then fade everything out."""
        if self.WIPE_SETTLES:
            self.settle()
        rt = self.WIPE_RT if rt is None else rt
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            fades = [FadeOut(m) for m in self.mobjects]
            if self.WIPE_STRETCH:
                self.play(*fades, run_time=rt)
            else:
                self.play_unstretched(*fades, run_time=rt)
        self._cap = None
        self.hlrect = None

    # ---- text furniture ---------------------------------------------------- #
    def section_header(self, label, color=GOLD):
        """Top-left section title with a coloured underline. Keep content below y~2.6."""
        t = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=23, y=CAPTION_Y, weight="NORMAL"):
        """A bottom caption mobject (not played), clamped to the frame width."""
        m = txt(text, fs=fs, color=color, weight=weight)
        clamp_width(m, CAPTION_W)
        m.move_to([0, y, 0])
        return m

    def caption(self, text, hold=1.0, rt=0.5, **kw):
        """Replace the running bottom caption, then hold ``read(hold)``."""
        new = self.say(text, **kw)
        if self._cap is not None and self._cap in self.mobjects:
            self.play(FadeOut(self._cap, shift=UP * 0.1), FadeIn(new, shift=UP * 0.1), run_time=rt)
        else:
            self.play(FadeIn(new, shift=UP * 0.1), run_time=rt)
        self._cap = new
        if hold:
            self.read(hold)
        return new

    def clear_cap(self, rt=0.4):
        if self._cap is not None and self._cap in self.mobjects:
            self.play(FadeOut(self._cap), run_time=rt)
        self._cap = None

    def swap_cap(self, old, new_text, **kw):
        """Transform caption ``old`` (or nothing) into a new one; returns it."""
        new = self.say(new_text, **kw)
        if old is None:
            self.play(FadeIn(new), run_time=0.5)
        else:
            from manim import ReplacementTransform

            self.play(ReplacementTransform(old, new), run_time=0.5)
        return new

    def cite(self, s):
        """A small source line on the bottom edge: papers, datasets, benchmarks."""
        from manim import ITALIC

        return Text(s, font_size=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)

    def takeaway(self, line1, line2, c2=GOLD):
        """A full-screen two-line takeaway. Use sparingly: one per film, at the end."""
        k1 = Text(line1, font_size=36, color=INK, weight="BOLD")
        k2 = Text(line2, font_size=27, color=c2, weight="BOLD")
        clamp_width(k1, 12.8)
        clamp_width(k2, 12.8)
        VGroup(k1, k2).arrange(DOWN, buff=0.36).move_to([0, 0, 0])
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.read(1.4)

    # ---- code panels -------------------------------------------------------- #
    def hl_lines(self, panel, lines, idxs, color=GOLD, opacity=0.16, pad=0.05, xpad=0.34):
        return hl_lines(panel, lines, idxs, color=color, opacity=opacity, pad=pad, xpad=xpad)

    def focus(self, panel, lines, idxs, color=GOLD, rt=0.4):
        """Move the single code-line highlight to ``lines[idxs]``."""
        new = self.hl_lines(panel, lines, idxs, color)
        if self.hlrect is None:
            self.hlrect = new
            self.play(FadeIn(new), run_time=rt)
        else:
            self.play(Transform(self.hlrect, new), run_time=rt)
        return self.hlrect

    # ---- bookends ------------------------------------------------------------ #
    def intro_emblem(self):
        """Optional small mobject shown at the right end of the intro rule."""
        return None

    def play_intro(self):
        """Title + rule, title morphs into the subtitle, byline, tagline."""
        header = Text(self.TITLE, font_size=56, color=INK, weight="BOLD")
        clamp_width(header, 10.5)
        line = rule_under(header, color=self.RULE_COLOR)
        byline = Text(BYLINE, font_size=28, color=self.BYLINE_COLOR)
        byline.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        emblem = self.intro_emblem()

        self.play(Write(header), Create(line), run_time=1.6)
        if emblem is not None:
            emblem.move_to(line.get_right() + UP * 0.3)
            self.play(FadeIn(emblem, shift=DOWN * 0.15), run_time=0.6)
        self.read(0.7)
        if self.SUBTITLE:
            sub = Text(self.SUBTITLE, font_size=32, color=MUTED)
            clamp_width(sub, 11.5)
            sub.move_to(header)
            fades = [FadeOut(emblem)] if emblem is not None else []
            self.play(Transform(header, sub), *fades, run_time=1.0)
            self.read(0.9)
        self.play(FadeIn(byline, shift=UP * 0.3), run_time=0.9)
        card = VGroup(header, line, byline)
        if self.TAGLINE:
            tag = Text(self.TAGLINE, font_size=22, color=MUTED).next_to(byline, DOWN, buff=0.4)
            self.play(FadeIn(tag), run_time=0.8)
            card.add(tag)
        self.read(1.4)
        self.play(FadeOut(card), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        """"Thank you for watching!" + rule, byline, optional one-line recap."""
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = rule_under(header, color=self.RULE_COLOR)
        byline = Text(BYLINE, font_size=28, color=self.BYLINE_COLOR)
        byline.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        card = VGroup(header, line, byline)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(byline, shift=UP * 0.3), run_time=1.0)
        if self.RECAP:
            recap = Text(self.RECAP, font_size=26, color=GOLD)
            clamp_width(recap, 12.0)
            recap.next_to(byline, DOWN, buff=0.5)
            self.play(FadeIn(recap), run_time=0.8)
            card.add(recap)
        self.read(1.6)
        self.play(FadeOut(card), run_time=1.3)
        self.card_wait(0.5)

    def play_all(self):
        """The whole film: intro, every ``scene_<name>`` in ``SCENES``, outro."""
        self.play_intro()
        for name in self.SCENES:
            getattr(self, f"scene_{name}")()
        self.play_outro()


class ExplainerScene(ExplainerMixin, Scene):
    """A 2D explainer scene."""


class Explainer3DScene(ExplainerMixin, ThreeDScene):
    """A 3D explainer scene. Pin HUD text with ``self.hud(...)``.

    Cairo 3D is unlit: shade faces by hand. Camera moves belong only here,
    never in 2D scenes.
    """

    def hud(self, *mobs):
        """Pin mobjects to the screen (captions, headers, legends) and return them."""
        self.add_fixed_in_frame_mobjects(*mobs)
        return mobs[0] if len(mobs) == 1 else VGroup(*mobs)


class ExplainerCameraScene(ExplainerMixin, MovingCameraScene):
    """A 2D explainer scene whose camera frame can pan and zoom."""
