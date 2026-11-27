"""The Dunning-Kruger effect: why a little knowledge feels like a lot.

A story, not a study: no percentiles, no error bars. One real game of chess, then
one picture that carries the rest of the film: everything there is to know about a
subject is a dark field, and what you know is the part your light reaches. Made to
be narrated; it also reads without the voice (one short caption per beat).

STORYBOARD (question | hero visual | what moves | takeaway caption)

    1 A great move    what does it feel like?   a chess board seen from black's side,
                      dark except where a beginner looks | the first moves are played;
                      the plan is drawn in gold; the dark lifts and the threat is drawn
                      in red; the queen takes: checkmate; the dark comes back |
                      "The less you know, the harder it is to see how little you know."
    2 A small light   why can't you tell?   the dark field seen from close: a light,
                      22 dots in it, 7 more in sight, a fence | two gauges fill: 22 of
                      29, then the picture pulls back and the fog lifts: 22 of 400 |
                      "To see what is missing, you would need what is missing."
    3 The climb       what happens as you learn?   the field (left) and the same run
                      as a chart (right), one clock for both | the light grows; the
                      fence runs away, the feeling falls; the fence reaches the true
                      edge; both lines climb together | "The bottom is where you start
                      being right about yourself."
    4 The other end   what about those who know?   a row of nine fields, one of them
                      almost fully lit | it imagines its own light on all the others
                      (gold), the real lights appear (blue), the row sorts itself |
                      "Beginners misjudge themselves. Experts misjudge everyone else."
    5 Everyone        so who is this about?   one person, five fields: one lit, four
                      barely | fences close in on the small lights; one of them
                      learns more, with somebody's help, and its fence runs out; then
                      the first field again, pulling back | "Feeling sure is about
                      your light, not about the size of the dark."

Motif: the light in the dark field, with its fence. Gold is always what somebody
believes (the plan on the board, the fence, "you feel you know"); blue is always
what is true (what the light really reaches); red is the danger nobody saw.

What is real: the chess game (the scholar's mate, replayed in ``model.py``), and the
name and date of the effect. What is drawn for the film: the field, the light and
every share on screen, which are read from the toy model in ``model.py``. The chart
of scene 3 is that model, not the study's data; each scene says so in its bottom
line. Where the toy could mislead about the study, it was bent towards it: the
beginner feels far surer than the facts allow, yet never surer than the expert; the
expert's mistake is the smaller one; and what moves the fence is learning more.

Scenes render alone (``./render.sh move --quick --check``) or stitched
(``./render.sh``). Pacing: ``DK_WPS`` (the narrator's words per second), ``DK_QUICK``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from manimx import *

from kit import *  # noqa: F403
import model as M

# One line per scene: what is real, what is drawn for the film.
MOVE_NOTE = "The game is real: the scholar’s mate. The effect: Kruger & Dunning, J. Pers. Soc. Psychol., 1999."
LIGHT_NOTE = "A picture, not a measurement: the field, the light and the numbers come from a toy model."
CLIMB_NOTE = "A toy, not data: the 1999 study has no dip, and its weakest rated themselves below its best."
EXPERT_NOTE = "An illustration with made-up lights. Top performers underrating their rank: Kruger & Dunning, 1999."
EVERYONE_NOTE = "An illustration: the fields, the lights and the bars come from the same toy model."
NOTES = [MOVE_NOTE, LIGHT_NOTE, CLIMB_NOTE, EXPERT_NOTE, EVERYONE_NOTE]
assert all(len(n) <= 100 for n in NOTES), [len(n) for n in NOTES]  # Pango wraps a longer line at 480p


def dashed_arrow(a, b, color, sw=6, buff=0.2, tip=0.2):
    """An arrow with a dashed shaft, between two points: "this attacks that"."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    u = (b - a) / np.linalg.norm(b - a)
    a, b = a + u * buff, b - u * buff
    n = np.array([-u[1], u[0], 0.0])
    shaft = DashedLine(a, b - u * tip * 0.9, dash_length=0.13, dashed_ratio=0.58)
    shaft.set_stroke(color, width=sw)
    head = Polygon(b, b - u * tip + n * tip * 0.55, b - u * tip - n * tip * 0.55)
    head.set_fill(color, 1.0).set_stroke(color, width=1)
    return VGroup(shaft, head)


def callout(text, color, at, to, fs=20):
    """A name beside the picture, and a thin line to the thing it names."""
    at, to = np.array(at, dtype=float), np.array(to, dtype=float)
    t = txt(text, fs=fs, color=color, weight="MEDIUM").move_to(at)
    d = to - at
    side = (RIGHT if d[0] > 0 else LEFT) if abs(d[0]) * t.height > abs(d[1]) * t.width else (UP if d[1] > 0 else DOWN)
    start = t.get_edge_center(side) + side * 0.1
    u = (to - start) / np.linalg.norm(to - start)
    line = Line(start, to - u * 0.14).set_stroke(color, width=2.2, opacity=0.85)
    return VGroup(t, line)


def flow(a, b, color, rt, n=3, z=10.6, r=0.07):
    """Packets that run from ``a`` to ``b`` for ``rt`` seconds: this line is live."""
    path = Line(a, b)
    dots = [glow_dot(color, r=r).set_z_index(z) for _ in range(max(1, int(n * rt / 1.6)))]
    return LaggedStart(*[Travel(d, path, run_time=1.1) for d in dots], lag_ratio=0.45, run_time=rt)


class _Common(NarratedMixin):
    pace = Pace.from_env("DK", read=2.6, delay=1.0, anim_slow=1.0, end_hold=2.0)
    TITLE = "The Dunning-Kruger Effect"
    SUBTITLE = "Why a little knowledge feels like a lot"
    TAGLINE = "a story about a small light in a big, dark field"
    RECAP = "Feeling sure is about your light, not about the size of the dark."
    RULE_COLOR = FELT_C
    TRACE_ENV = "DK_TRACE"
    WPS = float(os.environ.get("DK_WPS", 2.6))  # the narrator: 156 words a minute
    VO_PAD = 0.7

    def intro_emblem(self):
        g = face_glyph(0.3)
        pad = Rectangle(width=0.5, height=0.1).set_stroke(opacity=0).set_fill(opacity=0)
        return VGroup(g, pad.next_to(g, RIGHT, buff=0))

    def open_world(self):
        """The scene's clock. From here on every wait is rendered as motion."""
        self.world = World()
        self.ticker = Ticker(self.world)
        self.add(self.ticker)
        return self.world

    def chapter(self, label, color=FELT_C, note=None):
        """The animations that bring in the section header and the bottom line."""
        self.head = self.section_header(label, color).set_z_index(12)
        anims = [FadeIn(self.head, shift=DOWN * 0.2)]
        if note:
            self.foot = self.note(note)
            anims.append(FadeIn(self.foot))
        return anims

    def wipe(self, rt=None):
        if getattr(self, "ticker", None) is not None:
            self.remove(self.ticker)
            self.ticker = None
        super().wipe(rt)


class _Flat(_Common, Scene):
    """A flat scene whose painters draw straight onto the frame."""

    def __init__(self, **kw):
        kw.setdefault("camera_class", PainterCamera)
        super().__init__(**kw)

    # ====================================================================== #
    # 1 · A great move
    # ====================================================================== #
    def scene_move(self):
        w = self.open_world()
        board = Board((-3.45, 0.02), sq=0.64)
        army = board.setup(M.START)
        at = board.at
        spot = Spot(w, board.rect(), [(*at(s)[:2], r) for s, r in
                                      (("g8", 1.03), ("g6", 1.03), ("f6", 1.05), ("h5", 1.03))])  # fmt: skip
        buddy = Buddy(w, (2.3, -0.6), rad=0.92)
        buddy.look_x = -0.8  # it watches the board

        # the game, written down as it is played
        px0, px1, py0, py1 = 4.0, 6.7, -1.95, 0.75
        sheet = RoundedRectangle(width=px1 - px0, height=py1 - py0, corner_radius=0.16,
                                 stroke_color=FAINT, stroke_width=2.4, fill_color=PANEL, fill_opacity=1.0)  # fmt: skip
        sheet.move_to([(px0 + px1) / 2, (py0 + py1) / 2, 0])
        sheet_name = put(line_txt("the game", fs=20, color=MUTED), px0 + 0.28, py1 - 0.36)
        rows = [py1 - 0.92 - 0.5 * i for i in range(4)]
        nums = VGroup(*[put(line_txt(f"{i + 1}.", fs=21, color=MUTED, font=MONO), px0 + 0.28, y) for i, y in enumerate(rows)])
        plies = [*M.OPENING, M.BLUNDER, M.MATE]
        ink_of = {5: FELT_C, 6: THREAT_C}
        score = [
            put(line_txt(san, fs=21, color=ink_of.get(k, INK), font=MONO), px0 + (0.82 if k % 2 == 0 else 1.72), rows[k // 2])
            for k, (_, _, san) in enumerate(plies)
        ]
        tags = VGroup(
            pill("white", MUTED, fs=18).move_to([at("a1")[0] + 1.1, at("a1")[1] + 0.05, 0]),
            pill("you", FELT_C, fs=18).move_to([at("a8")[0] + 0.98, at("a8")[1] - 0.05, 0]),
        )

        def name(text, sq):  # the name of a piece, on the empty squares beside it
            lab = plate(txt(text, fs=18, color=INK, weight="MEDIUM"), op=0.82)
            return lab.move_to(at(sq) + RIGHT * (lab.width / 2 - 0.26)).set_z_index(13)

        queen_name, bishop_name = name("queen", "g5"), name("bishop", "b4")
        assert bishop_name.get_right()[0] < board.rect()[2]
        plan = arr(at("g8"), at("f6"), color=FELT_C, sw=7, buff=0.2, tip=0.24).set_z_index(12)
        hits = dashed_arrow(at("f6"), at("h5"), FELT_C, sw=6, buff=0.26).set_z_index(12)
        ring = Circle(radius=0.38, stroke_color=FELT_C, stroke_width=5).move_to(at("h5")).set_z_index(12)
        takes = arr(at("h5"), at("f7"), color=THREAT_C, sw=7, buff=0.34, tip=0.24).set_z_index(10.5)
        guards = arr(at("c4"), at("f7"), color=THREAT_C, sw=7, buff=0.34, tip=0.24).set_z_index(10.5)
        dead = board.wash("e8", THREAT_C, 0.62)
        hit_sq = board.wash("f7", THREAT_C, 0.45)
        mate = stamp("CHECKMATE", THREAT_C, fs=38)
        mate[0].set_fill(BG, 0.88)
        mate.move_to([board.c[0], at("a2")[1] + 0.1, 0]).set_z_index(14)
        idea = thought("What a move!", fs=27, toward=DL, hue=FELT_C)
        idea.move_to([4.55, 1.5, 0]).set_z_index(13)
        oh = thought("Oh.", fs=27, toward=DL, hue=MUTED)
        oh.move_to(idea.box.get_left() + RIGHT * oh.box.width / 2 + UP * 0.0).set_z_index(13)
        ring_c, ring_r = at("g6") + UP * 0.1, 1.6
        spot.ring = (ring_c[0], ring_c[1], ring_r)  # the fence around what you could see
        saw = plate(txt("all you could see", fs=20, color=FELT_C, weight="MEDIUM"), op=0.85)
        saw.move_to([at("e3")[0] + 0.1, at("e3")[1] + 0.1, 0]).set_z_index(13)
        assert saw.get_bottom()[1] > ring_c[1] + ring_r + 0.04  # just above the fence
        title = txt("the Dunning-Kruger effect", fs=28, color=FELT_C, weight="BOLD")
        credit = VGroup(
            line_txt("described in 1999 by", fs=20, color=MUTED),
            line_txt("Justin Kruger and David Dunning", fs=20, color=MUTED),
        ).arrange(DOWN, buff=0.02, aligned_edge=LEFT)
        named = VGroup(title, credit).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        named.move_to([4.1, 1.6, 0])
        assert named.get_right()[0] < 6.6 and named.get_left()[0] > 1.6

        # ---- 1.1 the game so far ------------------------------------------------------- #
        self.add(spot)
        self.play(
            self.tell(
                "One of your first games of chess. You play black.",
                "One of your first games of chess. You play black. Three moves in, white "
                "has already brought out its queen and a bishop.",
            ),
            *self.chapter("1 · A great move", FELT_C, MOVE_NOTE),
            FadeIn(board),
            LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in army], lag_ratio=0.02),
            FadeIn(buddy, shift=LEFT * 0.2),
            FadeIn(sheet),
            FadeIn(sheet_name),
            FadeIn(nums[:3]),
            run_time=1.1,
        )
        self.cue("You play black")
        self.play(FadeIn(tags, shift=LEFT * 0.15), run_time=0.5)
        self.cue("Three moves in")
        for k in (0, 1):
            self.play(board.go(*plies[k][:2], rt=0.45), FadeIn(score[k], run_time=0.3))
        self.cue("its queen")
        self.play(board.go("d1", "h5", rt=0.5), FadeIn(score[2], run_time=0.3))
        self.play(
            board.go("b8", "c6", rt=0.45, hop=True),
            FadeIn(score[3], run_time=0.3),
            FadeIn(queen_name, run_time=0.3),
        )
        self.cue("a bishop")
        self.play(board.go("f1", "c4", rt=0.5), FadeIn(score[4], run_time=0.3))
        self.play(FadeIn(bishop_name), run_time=0.3)
        self.hold()

        # ---- 1.2 the plan ---------------------------------------------------------------- #
        self.play(
            self.tell(
                "You spot a great move. You are sure of it.",
                "Then you spot it. Move the knight here, and it attacks the queen. What a "
                "move! You are sure of it.",
            ),
            FadeOut(queen_name),
            FadeOut(bishop_name),
            Tween(spot, dark=0.8, run_time=1.0),
            buddy.feel("sure", 0.6),
        )
        self.cue("Move the knight")
        self.play(GrowArrow(plan), run_time=0.5)
        self.cue("it attacks")
        self.play(Create(hits[0]), FadeIn(hits[1]), Create(ring), run_time=0.55)
        self.cue("What a move")
        self.play(FadeIn(idea, shift=UP * 0.12, run_time=0.4), buddy.feel("proud", 0.45))
        self.hold(ambient=lambda rt: [Throb(ring, rt, amp=0.14)])

        # ---- 1.3 the answer -------------------------------------------------------------- #
        self.play(
            self.tell(
                "One move later: checkmate.",
                "So you play it. And one move later, the queen takes this pawn, with the "
                "bishop guarding her from across the board. Checkmate.",
            ),
            board.go("g8", "f6", rt=0.6, hop=True),
            FadeOut(plan, run_time=0.4),
            FadeIn(score[5], run_time=0.4),
        )
        self.cue("one move later")
        self.play(
            FadeOut(hits, run_time=0.4),
            FadeOut(ring, run_time=0.4),
            FadeOut(idea, run_time=0.4),
            Tween(spot, dark=0.0, run_time=0.9),
            buddy.feel("calm", 0.5),
        )
        self.cue("the queen takes")
        pawn = board.men["f7"]
        self.play(Create(takes), FadeIn(nums[3]), run_time=0.4)
        self.play(
            board.go("h5", "f7", rt=0.5),
            FadeOut(pawn, scale=0.6, run_time=0.5),
            FadeIn(hit_sq, run_time=0.5),
        )
        self.cue("with the bishop")
        self.play(Create(guards), run_time=0.5)
        self.cue("Checkmate")
        self.play(
            FadeIn(mate, scale=1.5, run_time=0.35),
            FadeIn(dead, run_time=0.35),
            FadeIn(score[6], run_time=0.35),
            FadeIn(oh, shift=UP * 0.12, run_time=0.4),
            buddy.feel("shock", 0.3),
        )
        self.hold(ambient=lambda rt: [flow(at("h5"), at("f7"), THREAT_C, rt), flow(at("c4"), at("f7"), THREAT_C, rt)])

        # ---- 1.4 it was there all along --------------------------------------------------- #
        self.play(
            self.tell(
                "The danger was there all along. You could not see it.",
                "The danger sat on the board the whole time. To your eyes, it was not there.",
            ),
            FadeOut(oh, run_time=0.4),
            FadeOut(mate, run_time=0.5),
            buddy.feel("sad", 0.6),
        )
        self.cue(
            "To your eyes",
            ambient=lambda rt: [flow(at("h5"), at("f7"), THREAT_C, rt), flow(at("c4"), at("f7"), THREAT_C, rt)],
        )
        self.play(Tween(spot, dark=0.86, ring_a=1.0, run_time=1.0))
        self.play(FadeIn(saw, shift=UP * 0.1), run_time=0.4)
        self.hold()

        # ---- 1.5 its name ------------------------------------------------------------------ #
        self.play(
            self.tell(
                "The less you know, the harder it is to see how little you know.",
                "The less you know, the harder it is to see how little you know. That is "
                "the idea behind the Dunning-Kruger effect.",
            ),
            buddy.feel("calm", 0.6),
        )
        self.cue("That is")
        self.play(FadeIn(title, shift=UP * 0.12), run_time=0.5)
        self.play(FadeIn(credit), run_time=0.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 2 · A small light
    # ====================================================================== #
    def scene_light(self):
        w = self.open_world()
        win = (-6.72, -2.78, 0.5, 2.52)
        c = np.array([(win[0] + win[2]) / 2, (win[1] + win[3]) / 2, 0.0])
        near, far = 5.6, 2.45  # the field's radius seen from close, then from far
        fm = FogMap(w, c, near, window=win)
        fm.wall = 0.0
        fm.know = M.FIRST  # read the picture once: this is what the gauges will say
        lit, seen, total = fm.counts()
        hollow = [fm.spot_of(i) for i in fm.glimpsed()]
        first_hollow = max(hollow, key=lambda q: float((q - c) @ np.array([0.6, -0.8, 0.0])))  # lower right
        lit_r, fence_r = M.FIRST * near, fm.fence_r()
        aim = c + lit_r * 0.66 * np.array([-0.77, 0.64, 0])
        lit_ones = [fm.spot_of(i) for i in np.flatnonzero(fm.rad < fm.know)]
        a_lit_dot = min(lit_ones, key=lambda q: float(np.linalg.norm(q - aim)))
        fm.know = 0.0
        # the gauges count dots, the chart of scene 3 draws the formulas: they must agree
        assert abs(lit / seen - M.felt(M.FIRST)) < 0.03 and abs(lit / total - M.real(M.FIRST)) < 0.01
        assert 5 <= seen - lit <= 9  # "a few things you have not learned yet"
        assert (percent(lit / seen), percent(lit / total)) == (76, 6)  # what the gauges will show (README)

        buddy = Buddy(w, (3.9, 0.2), rad=1.05)
        buddy.look_x = -0.8  # it looks at its field
        seat = (1.85, 1.5, 0.7)  # where it sits once the gauges are there (x, y, radius)
        idea = thought("Most of it!", fs=26, toward=DL, hue=FELT_C)
        idea.shift([seat[0] + 1.2, seat[1] + 0.72, 0] - idea.box.get_corner(DL)).set_z_index(13)
        g_felt = Gauge("you feel you know", FELT_C, (3.9, -0.3))
        g_real = Gauge("you really know", REAL_C, (3.9, -1.9))
        n_felt = g_felt.detail(f"{lit} of the {seen} things you can see")
        n_real = g_real.detail(f"{lit} of the {total} things there are")
        assert idea.get_right()[0] < 6.76 and idea.get_left()[0] > seat[0] + 0.6

        known_tag = callout("what you know", REAL_C, c + [-2.25, 1.72, 0], a_lit_dot)
        hollow_tag = callout("not learned yet", FELT_C, c + [2.42, -1.5, 0], first_hollow)
        fence_tag = txt("as far as you can tell, the field ends here", fs=20, color=FELT_C, weight="MEDIUM")
        fence_tag.move_to(c + DOWN * (fence_r + 0.4))
        on_fence = c + fence_r * np.array([np.cos(0.6), np.sin(0.6), 0.0])
        fence_name = callout("your fence", FELT_C, c + [2.5, 1.55, 0], on_fence)
        tags = VGroup(known_tag, hollow_tag, fence_tag, fence_name).set_z_index(5)
        for t in (known_tag[0], hollow_tag[0], fence_name[0]):  # each name stands outside the fence
            corners =[t.get_critical_point(d) for d in (UL, UR, DL, DR, LEFT, RIGHT, UP, DOWN)]
            assert min(float(np.linalg.norm(q - c)) for q in corners) > fence_r + 0.12, t
        for t in tags:
            assert win[0] + 0.2 < t.get_left()[0] and t.get_right()[0] < win[2] - 0.2, t
            assert win[1] + 0.2 < t.get_bottom()[1] and t.get_top()[1] < win[3] - 0.2, t

        # ---- 2.1 the field and the light --------------------------------------------------- #
        self.play(
            self.tell(
                "What you know is the part of a dark field your light reaches.",
                "Now picture everything there is to know about a subject as a dark field. What "
                "you have learned so far is the small part your light reaches.",
            ),
            *self.chapter("2 · A small light", FELT_C, LIGHT_NOTE),
            FadeIn(fm),
            FadeIn(buddy, shift=LEFT * 0.2),
            run_time=0.9,
        )
        self.cue("everything there is")
        self.play(Tween(fm, fog=0.5, run_time=1.0))  # it is all there ...
        self.cue("as a dark field")
        self.play(Tween(fm, fog=0.0, run_time=1.2))  # ... and you cannot see it
        self.cue("What you have learned")
        self.play(Tween(fm, know=M.FIRST, run_time=self.span("your light reaches", floor=2.2)))
        self.play(FadeIn(known_tag), run_time=0.4)
        self.hold()

        # ---- 2.2 what is in sight, and the fence --------------------------------------------- #
        self.play(
            self.tell(
                "Just past the light, you can make out a little more.",
                "Just past the light, you can make out a few things you have not learned yet. "
                "And beyond those, as far as you can tell, there is nothing. Call that line your fence.",
            )
        )
        self.cue("you can make out")
        self.play(Tween(fm, sight=1.0, run_time=0.8))
        self.play(FadeIn(hollow_tag), run_time=0.4)
        self.cue("And beyond those")
        self.play(Tween(fm, wall=1.0, run_time=1.0))
        self.play(FadeIn(fence_tag, shift=UP * 0.1), run_time=0.4)
        self.cue("Call that line")
        self.play(FadeIn(fence_name), run_time=0.4)
        self.hold()

        # ---- 2.3 how much it feels like ------------------------------------------------------- #
        self.play(
            self.tell(
                "So you compare the light to what you can see.",
                "So when you ask yourself how much you know, you can only compare the light to "
                f"what you can see. {lit} things out of {seen}. Most of it!",
            ),
            buddy.feel("sure", 0.6),
        )
        self.cue("you can only compare")
        self.play(
            Tween(buddy, px=seat[0], py=seat[1], rad=seat[2], look_x=0.0, run_time=0.8),
            Succession(Wait(0.4), FadeIn(g_felt, shift=UP * 0.1, run_time=0.5)),
        )
        self.cue(f"{lit} things")
        self.play(Tween(g_felt, v=lit / seen, run_time=1.3), FadeIn(n_felt, run_time=0.5))
        self.cue("Most of it")
        self.play(FadeIn(idea, shift=UP * 0.12, run_time=0.4), buddy.feel("proud", 0.45))
        self.hold()

        # ---- 2.4 the fog lifts ----------------------------------------------------------------- #
        self.play(
            self.tell(
                "Now lift the fog. The field was this big all along.",
                "Now let us lift the fog. The field was this big all along. You know "
                f"{lit} things out of {total}.",
            ),
            FadeOut(tags, run_time=0.5),
        )
        self.cue("lift the fog")
        self.play(Tween(fm, R=far, fog=1.0, run_time=self.span("You know", floor=2.6)))
        self.play(FadeIn(g_real, shift=UP * 0.1), run_time=0.5)
        self.play(Tween(g_real, v=lit / total, run_time=1.0), FadeIn(n_real, run_time=0.5))
        self.hold(ambient=lambda rt: [Sweep(fm, rt)])

        # ---- 2.5 why you cannot tell ----------------------------------------------------------- #
        self.play(
            self.tell(
                "To see what is missing, you would need what is missing.",
                "And you cannot count what you cannot see. To notice how much is missing, you "
                "would need the very knowledge that is missing.",
            )
        )
        self.settle(ambient=lambda rt: [Sweep(fm, rt)])
        self.wipe()

    # ====================================================================== #
    # 3 · The climb
    # ====================================================================== #
    def scene_climb(self):
        w = self.open_world()
        win = (-6.72, -2.78, -1.0, 2.52)
        c = np.array([(win[0] + win[2]) / 2, (win[1] + win[3]) / 2, 0.0])
        fm = FogMap(w, c, 2.45, window=win)
        fm.sight = fm.fog = 1.0

        X0, Y0, W, H = 0.45, -2.15, 5.8, 3.5
        chart = ClimbChart(fm, X0, Y0, W, H).set_z_index(3)
        xa = arr([X0, Y0, 0], [X0 + W + 0.38, Y0, 0], color=MUTED, sw=3, buff=0, tip=0.17)
        ya = arr([X0, Y0, 0], [X0, Y0 + H + 0.55, 0], color=MUTED, sw=3, buff=0, tip=0.17)
        top = DashedLine([X0, Y0 + H, 0], [X0 + W, Y0 + H, 0], dash_length=0.1).set_stroke(FAINT, width=2.5)
        ticks = VGroup(*[
            line_txt(name, fs=18, color=MUTED).move_to([X0 - 0.16, yy, 0], aligned_edge=RIGHT)
            for name, yy in (("all", Y0 + H), ("none", Y0))
        ])  # fmt: skip
        y_name = txt("how much of the field", fs=18, color=MUTED).rotate(PI / 2)
        y_name.move_to([X0 - 0.42, Y0 + H / 2, 0])
        x_name = line_txt("time spent learning", fs=18, color=MUTED)
        x_name.move_to([X0 + W - x_name.width / 2, Y0 - 0.3, 0])
        assert ticks.get_left()[0] > win[2] + 0.2

        def key(text, hue, y, sw):
            swatch = Line([1.85, y, 0], [2.45, y, 0]).set_stroke(hue, width=sw)
            return VGroup(swatch, put(line_txt(text, fs=20, color=hue, weight="MEDIUM"), 2.6, y))

        key_felt = key("how much you feel you know", FELT_C, 2.66, 5)
        key_real = key("how much you really know", REAL_C, 2.26, 9)
        assert key_felt.get_right()[0] < 6.76

        hold_mood = {"as": None}

        def mood_at(r):
            if r < 0.04:
                return "calm"
            if r < M.R_PEAK + 0.03:
                return "proud"
            if r < 0.4:
                return "shock"
            if r < M.R_SEEN + 0.01:
                return "sad"
            return "grit" if r < 0.8 else "happy"

        buddy = Buddy(w, (X0, Y0 + 0.4), rad=0.27, bob=0.0).set_z_index(6)

        def ride(m):  # it stands on the tip of the gold line, and feels what the line says
            p = chart.tip()
            m.px, m.py = p[0], p[1] + 0.4
            m.aim = hold_mood["as"] or mood_at(fm.know)

        buddy.add_updater(ride, index=0)

        peak, low = chart.xy(M.R_PEAK, M.felt(M.R_PEAK)), chart.xy(M.R_SEEN, M.felt(M.R_SEEN))
        end = chart.xy(M.EXPERT, M.felt(M.EXPERT))
        peak_tag = txt("“I’ve got this!”", fs=21, color=FELT_C, weight="MEDIUM")
        peak_tag.move_to([peak[0] + 0.56 + peak_tag.width / 2, peak[1] + 0.36, 0])  # beside the face
        low_tag = txt("“So much left to learn.”", fs=21, color=FELT_C, weight="MEDIUM")
        low_tag.move_to([min(low[0] - 0.12, 6.6 - low_tag.width) + low_tag.width / 2, low[1] - 0.56, 0])
        meet = Circle(radius=0.2, stroke_color=INK, stroke_width=4).move_to(low).set_z_index(5)
        end_tag = txt("“Now I really know.”", fs=21, color=FELT_C, weight="MEDIUM")
        end_tag.move_to([end[0] - 0.52 - end_tag.width / 2, Y0 + H + 0.34, 0])  # over the guide, by the face
        VGroup(peak_tag, low_tag, end_tag).set_z_index(5)
        assert peak_tag.get_top()[1] < Y0 + H - 0.12  # under the dashed guide
        assert Y0 + H + 0.12 < end_tag.get_bottom()[1] and end_tag.get_top()[1] < key_real.get_bottom()[1] - 0.15
        assert low_tag.get_bottom()[1] > Y0 + 0.12
        assert max(t.get_right()[0] for t in (peak_tag, low_tag, end_tag)) < 6.76 and end_tag.get_left()[0] > X0 + 0.3
        for tag, slack in ((peak_tag, 0.12), (low_tag, -0.12)):
            # each saying stays on its side of the gold line: above it (slack > 0) or below it
            rs = (np.linspace(tag.get_left()[0], tag.get_right()[0], 30) - X0) / W * M.EXPERT
            ys = Y0 + H * M.felt(np.clip(rs, 1e-6, M.EXPERT))
            assert np.all(tag.get_bottom()[1] > ys + slack) if slack > 0 else np.all(tag.get_top()[1] < ys + slack), tag
        rs = (np.linspace(low_tag.get_left()[0], low_tag.get_right()[0], 30) - X0) / W * M.EXPERT
        assert np.all(low_tag.get_top()[1] < Y0 + H * M.real(np.clip(rs, 0, M.EXPERT)) - 0.1)  # and under the blue one

        # ---- 3.1 two lines ------------------------------------------------------------------------ #
        self.play(
            self.tell(
                "Gold: how much you feel you know. Blue: how much you really know.",
                "Now, the whole journey. Gold is how much of the field you feel you know. Blue "
                "is how much you really know.",
            ),
            *self.chapter("3 · The climb", FELT_C, CLIMB_NOTE),
            FadeIn(fm),
            run_time=0.9,
        )
        self.play(Create(xa), Create(ya), FadeIn(top), FadeIn(ticks), FadeIn(y_name), FadeIn(x_name), run_time=0.9)
        self.play(FadeIn(buddy, scale=0.6), run_time=0.4)
        self.add(chart)
        self.cue("Gold is")
        self.play(FadeIn(key_felt, shift=RIGHT * 0.15), run_time=0.5)
        self.cue("Blue is")
        self.play(FadeIn(key_real, shift=RIGHT * 0.15), run_time=0.5)
        self.hold()

        # ---- 3.2 the peak --------------------------------------------------------------------------- #
        self.play(
            self.tell(
                "At first, the feeling races ahead of the facts.",
                "With the first lessons, the feeling races ahead: a small light, in a field that "
                "looks small. This is the first peak of confidence, and you have barely started.",
            )
        )
        self.cue("the feeling races")
        self.play(Tween(fm, know=M.R_PEAK, run_time=self.span("This is the first peak", floor=2.6)))
        self.play(FadeIn(peak_tag, shift=UP * 0.1), run_time=0.4)
        self.hold()

        # ---- 3.3 the fall --------------------------------------------------------------------------- #
        self.play(
            self.tell(
                "Then every answer shows you three new questions.",
                "Then every answer shows you three new questions. The fence runs away faster "
                "than your light can follow, and your confidence falls.",
            )
        )
        self.play(Tween(fm, know=M.R_SEEN, run_time=self.span(floor=3.5), rate_func=rate_functions.ease_in_out_sine))
        self.play(FadeIn(low_tag, shift=UP * 0.1), run_time=0.4)
        self.hold()

        # ---- 3.4 the bottom ------------------------------------------------------------------------- #
        self.play(
            self.tell(
                "At the bottom, you can finally see the whole field.",
                "But look at the field: the fence has reached the true edge. For the first time, "
                "you can see all of it.",
            )
        )
        self.cue("the fence has reached")
        self.hold(ambient=lambda rt: [Breathe(fm, rt, attr="flash", period=1.3)])

        self.play(
            self.tell(
                "The bottom is where you start being right about yourself.",
                "So the bottom is not where you know least. It is where you start being right "
                "about yourself.",
            ),
        )
        hold_mood["as"] = "grit"
        self.cue("It is where")
        self.play(Create(meet), run_time=0.5)
        self.hold(ambient=lambda rt: [Throb(meet, rt, amp=0.3)])

        # ---- 3.5 the climb -------------------------------------------------------------------------- #
        self.play(
            self.tell(
                "From here, the feeling and the facts climb together.",
                "And from here on, the feeling and the facts climb together. Confidence comes "
                "back. This time, it is earned.",
            ),
            FadeOut(meet, run_time=0.4),
        )
        hold_mood["as"] = None
        self.cue("the feeling and the facts")
        self.play(Tween(fm, know=M.EXPERT, run_time=self.span("This time", floor=3.2), rate_func=rate_functions.ease_in_out_sine))
        self.play(FadeIn(end_tag, shift=UP * 0.1), run_time=0.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 4 · The other end
    # ====================================================================== #
    def scene_expert(self):
        w = self.open_world()
        n, pitch, y_row, r_mini = 9, 1.46, 0.95, 0.62
        slot_x = [(i - (n - 1) / 2) * pitch for i in range(n)]
        lights = [0.12, 0.15, 0.18, 0.21, 0.25, 0.31, 0.40, 0.55]  # made up: most lights are small
        me = 6  # where the expert places itself: above the middle, well short of the top
        free = [i for i in range(n) if i != me]
        order = np.random.default_rng(3).permutation(len(lights))  # the others, in no order
        crowd = []
        for k, slot in zip(order, free, strict=True):
            fm = FogMap(w, (slot_x[slot], y_row), r_mini, n=70, seed=20 + int(k), dot=0.05)
            fm.fog, fm.guess, fm.guess_a = 1.0, 0.9, 1.0
            fm.light = lights[k]  # what it really knows (shown later)
            fm.rank = int(k)  # its place once everyone is lined up
            crowd.append(fm)
        hero = FogMap(w, (-2.7, -0.12), 2.1, n=220, seed=11)
        hero.fog, hero.know = 1.0, 0.3
        hero.calm()
        least = next(fm for fm in crowd if fm.rank == 0)

        buddy = Buddy(w, (3.3, -0.75), rad=1.0, mood="wise")
        buddy.look_x = -0.7  # it looks at its field
        seat = (-5.3, -1.95, 0.7)  # where it sits once the others are there (x, y, radius)
        said = "This is easy. Everyone knows it."
        first = thought(said, fs=25, toward=DL, hue=FELT_C)  # above the big face
        first.shift([buddy.px + 0.5, buddy.py + 1.5, 0] - first.box.get_corner(DL)).set_z_index(13)
        first.shift(LEFT * max(0.0, first.get_right()[0] - 6.6))
        easy = thought(said, fs=25, toward=LEFT + DOWN * 0.35, hue=FELT_C)  # beside the small one
        easy.shift([seat[0] + 1.45, -1.72, 0] - easy.box.get_left()).set_z_index(13)
        assert first.get_left()[0] > hero.cx + hero.R * 1.034 + 0.3 and first.get_right()[0] < 6.76

        y_mark, y_name = -0.12, -0.6
        thinks = Circle(radius=0.12, stroke_color=FELT_C, stroke_width=5).move_to([slot_x[me], y_mark, 0])
        thinks_name = line_txt("where they think they stand", fs=20, color=FELT_C, weight="MEDIUM")
        thinks_name.move_to([slot_x[me] + 0.3 - thinks_name.width / 2, y_name, 0])
        really = Dot(radius=0.13, color=REAL_C).move_to([slot_x[-1], y_mark, 0])
        really_name = line_txt("where they really stand", fs=20, color=REAL_C, weight="MEDIUM")
        really_name.move_to([6.5 - really_name.width / 2, y_name, 0])
        gap = arr(thinks.get_right(), really.get_left(), color=INK, sw=4, buff=0.14, tip=0.2)
        less = txt("knows the least", fs=20, color=MUTED)
        less.move_to([slot_x[0] - r_mini + less.width / 2, y_row + 1.08, 0])
        more = txt("knows the most", fs=20, color=MUTED)
        more.move_to([slot_x[-1] + r_mini - more.width / 2, y_row + 1.08, 0])
        scale = arr(less.get_right() + RIGHT * 0.1, more.get_left() + LEFT * 0.1, color=FAINT, sw=3, buff=0.1, tip=0.16)
        assert thinks_name.get_right()[0] < really_name.get_left()[0] - 0.3
        assert easy.get_right()[0] < 6.76 and easy.get_top()[1] < y_name - 0.25
        assert seat[1] - 1.5 * seat[2] > -3.15  # the small face's halo clears the caption

        # ---- 4.1 someone who knows ------------------------------------------------------------------ #
        self.play(
            self.tell(
                "At the other end: someone who has lit almost the whole field.",
                "At the other end, there is a smaller mistake, and it points the other way. Here is "
                "someone who has lit almost the whole field.",
            ),
            *self.chapter("4 · The other end", REAL_C, EXPERT_NOTE),
            FadeIn(hero),
            FadeIn(buddy, shift=LEFT * 0.2),
            run_time=0.9,
        )
        self.cue("Here is someone")
        self.play(Tween(hero, know=M.EXPERT, run_time=self.span(floor=2.4), rate_func=rate_functions.ease_in_out_sine))
        self.hold()

        # ---- 4.2 how it pictures the others --------------------------------------------------------- #
        self.play(
            self.tell(
                "What is easy for you seems easy for everyone.",
                "When something has become easy for you, you assume it is easy for everyone. So the "
                "expert pictures everybody else with a light as big as their own, and places "
                "themselves above the middle of the pack, but well short of the top.",
            )
        )
        self.cue("you assume")
        self.play(FadeIn(first, shift=UP * 0.12), run_time=0.45)
        self.cue("So the expert")
        self.play(
            FadeOut(first, run_time=0.35),
            Tween(hero, cx=slot_x[me], cy=y_row, R=r_mini, run_time=1.3),
            Tween(buddy, px=seat[0], py=seat[1], rad=seat[2], look_x=0.6, run_time=1.3),
        )
        self.play(
            LaggedStart(*[FadeIn(fm) for fm in crowd], lag_ratio=0.12, run_time=1.6),
            Succession(Wait(0.3), FadeIn(easy, shift=UP * 0.12, run_time=0.45)),
        )
        self.cue("and places themselves")
        self.play(FadeIn(less, run_time=0.5), FadeIn(more, run_time=0.5), Create(scale, run_time=0.9))
        self.play(Tween(hero, mark=1.0, run_time=0.4), Create(thinks, run_time=0.4))
        self.play(FadeIn(thinks_name, shift=UP * 0.1), run_time=0.4)
        self.hold()

        # ---- 4.3 the real lights --------------------------------------------------------------------- #
        self.play(
            self.tell(
                "In truth, most lights are small. The expert stands at the top.",
                "In truth, most lights are small. Line everyone up by what they really know, and the "
                "expert stands at the very top, without knowing it.",
            ),
            *[Tween(fm, guess_a=0.0, run_time=0.7) for fm in crowd],
        )
        self.play(LaggedStart(*[Tween(fm, know=fm.light, run_time=0.9) for fm in crowd], lag_ratio=0.1, run_time=1.5))
        self.cue("Line everyone up")
        self.play(
            *[Hop(fm, slot_x[fm.rank], lift=0.35 + 0.1 * (fm.rank % 3), run_time=1.5) for fm in crowd],
            Hop(hero, slot_x[-1], lift=0.5, run_time=1.5),
        )
        self.cue("at the very top")
        self.play(FadeIn(really, scale=1.6), run_time=0.35)
        self.play(GrowArrow(gap), FadeIn(really_name, shift=UP * 0.1), run_time=0.6)
        self.hold()

        # ---- 4.4 two mistakes ------------------------------------------------------------------------ #
        self.play(
            self.tell(
                "Beginners misjudge themselves. Experts misjudge everyone else.",
                "So beginners misjudge themselves. Experts misjudge everyone else.",
            ),
            Tween(hero, mark=0.0, run_time=0.4),
        )
        self.cue("beginners")
        self.play(Tween(least, mark=1.0, sight=1.0, run_time=0.5))
        self.cue("Experts")
        self.play(Tween(least, mark=0.0, run_time=0.4), Tween(hero, mark=1.0, run_time=0.4))
        self.settle(ambient=lambda rt: [Breathe(fm, rt, attr="guess_a", period=max(1.2, rt / 2)) for fm in crowd])
        self.wipe()

    # ====================================================================== #
    # 5 · Everyone
    # ====================================================================== #
    def scene_everyone(self):
        w = self.open_world()
        names = ["your job", "cooking", "chess", "grammar", "investing"]
        knows = [0.90, 0.21, M.FIRST, 0.26, 0.19]  # one big light, and small ones (made up)
        xs, y, R, bw = [-5.4, -2.7, 0.0, 2.7, 5.4], 1.0, 1.1, 2.0
        fields, labels = [], VGroup()
        for i, x in enumerate(xs):
            fm = FogMap(w, (x, y), R, seed=40 + i, dot=0.03)
            fm.fog = 1.0
            fields.append(fm)
            labels.add(line_txt(names[i], fs=23, color=INK, weight="MEDIUM").move_to([x, y - R - 0.45, 0]))

        def shares(fm, know):
            """(feels, really) for this field at this light, counted from its dots."""
            keep, fm.know = fm.know, know
            lit, seen, total = fm.counts()
            fm.know = keep
            return lit / seen, lit / total

        def bar(x, dy, share, hue):
            b = Rectangle(width=bw * share, height=0.15, stroke_width=0).set_fill(hue, 1.0)
            return b.move_to([x - bw / 2 + b.width / 2, y - R - dy, 0])

        now = [shares(fm, k) for fm, k in zip(fields, knows, strict=True)]
        felt_bars = VGroup(*[bar(x, 0.88, f, FELT_C) for x, (f, _) in zip(xs, now, strict=True)])
        real_bars = VGroup(*[bar(x, 1.13, r, REAL_C) for x, (_, r) in zip(xs, now, strict=True)])
        # what the caption says of the picture: a small light feels almost as complete
        # as the big one, never more; and it is small (under a tenth of its field)
        assert all(0.55 < f < now[0][0] and r < 0.1 for f, r in now[1:]), now
        tracks = VGroup(*[
            Rectangle(width=bw, height=0.15, stroke_width=0).set_fill(FAINT, 0.5).move_to([x, y - R - dy, 0])
            for x in xs for dy in (0.88, 1.13)
        ])  # fmt: skip
        key = VGroup(
            dot_label("how much you feel you know", FELT_C, fs=20),
            dot_label("how much you really know", REAL_C, fs=20),
        ).arrange(RIGHT, buff=0.9)
        key.move_to([0, y - R - 1.72, 0])
        chess = fields[2]
        more, most = 0.32, 0.40  # the chess light after learning more, alone and then with help
        steps = [shares(chess, more), shares(chess, most)]
        assert now[2][0] > steps[0][0] > steps[1][0] and now[2][1] < steps[0][1] < steps[1][1]
        friend = Buddy(w, (xs[2] + 1.15, y + R + 0.9), rad=0.3, mood="happy", hue="#A5EFE3", rim=FRIEND_C)
        friend.look_x, friend.look_y = -0.7, -0.5
        friend.set_z_index(6)

        def learn(to, share, rt):
            """The chess light grows to ``to``; its two bars follow what the dots now say."""
            return [
                Tween(chess, know=to, run_time=rt),
                felt_bars[2].animate(run_time=rt).stretch_to_fit_width(bw * share[0], about_edge=LEFT),
                real_bars[2].animate(run_time=rt).stretch_to_fit_width(bw * share[1], about_edge=LEFT),
            ]

        win = (-6.72, -2.78, 6.72, 2.52)
        last = FogMap(w, (0.0, -0.13), 5.6, window=win, seed=7)
        last.know, last.sight = M.FIRST, 1.0
        last.calm()

        # ---- 5.1 many lights -------------------------------------------------------------------------- #
        self.play(
            self.tell(
                "This is not about foolish people. It is about everyone.",
                "And none of this is about foolish people. Each of us carries many lights: a big "
                "one for what we do every day, and small ones for almost everything else.",
            ),
            *self.chapter("5 · Everyone", FELT_C, EVERYONE_NOTE),
            run_time=0.8,
        )
        rt = self.span("a big one", floor=2.0)
        self.play(
            LaggedStart(
                *[AnimationGroup(FadeIn(fm), FadeIn(lab, shift=UP * 0.1)) for fm, lab in zip(fields, labels, strict=True)],
                lag_ratio=0.6,
                run_time=rt,
            )
        )
        self.play(Tween(fields[0], know=knows[0], run_time=self.span("and small ones", floor=1.6)))
        self.play(
            LaggedStart(*[Tween(fm, know=k, run_time=1.0) for fm, k in zip(fields[1:], knows[1:], strict=True)],
                        lag_ratio=0.25, run_time=1.9)  # fmt: skip
        )
        self.hold()

        # ---- 5.2 from the inside ------------------------------------------------------------------------ #
        self.play(
            self.tell(
                "A small light can feel almost as complete as a big one.",
                "And from the inside, a small light can feel almost as complete as a big one.",
            ),
            *[Tween(fm, sight=1.0, run_time=0.9) for fm in fields],
            FadeIn(tracks, run_time=0.6),
        )
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in felt_bars], lag_ratio=0.12, run_time=1.2))
        self.play(
            LaggedStart(*[GrowFromEdge(b, LEFT) for b in real_bars], lag_ratio=0.12, run_time=1.2),
            FadeIn(key, run_time=0.8),
        )
        self.hold()

        # ---- 5.3 what moves the fence -------------------------------------------------------------------- #
        self.play(
            self.tell(
                "A small light hides where the field ends. Learning more shows it.",
                "A small light cannot show you where the field ends. Learning more does. So keep "
                "learning, and ask people who know more to teach you what you are missing.",
            )
        )
        self.cue("Learning more does")
        self.play(*learn(more, steps[0], self.span("and ask people", floor=2.0)))
        self.play(FadeIn(friend, shift=DOWN * 0.25), run_time=0.4)
        self.play(Tween(friend, py=y + R + 0.3, run_time=0.6), Tween(chess, tint=0.8, run_time=0.6))
        self.play(*learn(most, steps[1], self.span(floor=1.8)))
        self.hold(ambient=lambda rt: [Sweep(chess, rt)])

        # ---- 5.4 the last picture ------------------------------------------------------------------------ #
        row = VGroup(labels, tracks, felt_bars, real_bars, key, friend)
        self.play(
            self.tell(
                "Feeling sure is about your light, not about the size of the dark.",
                "Because feeling sure tells you about your light. On its own, it cannot tell you "
                "the size of the dark.",
            ),
            FadeOut(row, run_time=0.6),
            *[FadeOut(fm, run_time=0.6) for fm in fields],
            Succession(Wait(0.6), FadeIn(last, run_time=0.8)),
        )
        self.cue("On its own")
        self.play(Tween(last, R=2.45, fog=1.0, run_time=self.span(floor=3.0), rate_func=rate_functions.ease_in_out_sine))
        self.settle(ambient=lambda rt: [Sweep(last, rt)])
        self.wipe()


# ---- renderable scenes ---------------------------------------------------------------- #
class Intro(_Flat):
    def construct(self):
        self.over_card(
            "Why is it so hard to tell how little we know?"
        )
        self.play_intro()


class Move(_Flat):
    def construct(self):
        self.scene_move()


class Light(_Flat):
    def construct(self):
        self.scene_light()


class Climb(_Flat):
    def construct(self):
        self.scene_climb()


class Expert(_Flat):
    def construct(self):
        self.scene_expert()


class Everyone(_Flat):
    def construct(self):
        self.scene_everyone()


class Outro(_Flat):
    def construct(self):
        self.play_outro()
