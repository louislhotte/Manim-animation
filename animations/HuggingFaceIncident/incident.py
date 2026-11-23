"""The Hugging Face incident: how one note in a package server became a break-in.

A film made to be narrated, after OpenAI's own account (the post "The Hugging Face
incident and the road ahead", 26 August 2026; not the technical report it links to). The voice tells the story; the screen shows the
machines, the dates, and the agents' own words, verbatim. Flat scenes, no camera.

STORYBOARD (question | hero visual | what moves)

    1 A note          where does it start?   one sandbox and its agent, seen from
                      close, then thirty, and the package server they all reach |
                      rings die on the walls; the picture pulls back to the cluster;
                      packages flow out, one note goes in, others follow: a listing
                      becomes a message board
    2 A way out       how do they get out?   the cluster, the server at the boundary,
                      the internet beyond | a request goes through the server and
                      out of the gate, then many; the date runs to June, the server
                      falls on 4 July, a sweep wipes the board, the board comes back
    3 The unsolved    why do they keep going?   ExploitGym, 898 cells | one task is
      tasks           played (a program, a flag); the 198 never-solved cells gather
                      into a block, sparks keep striking it, 93 of 100 marks land on it
    4 The break-in    what do they do outside?   a map: the cluster, the gate, an app
                      on Modal, 14 credentials, Hugging Face's servers in four
                      regions | roads open, keys travel back, tiles turn orange; one
                      agent stops and starts again, a few turn green; the alarm, and
                      a gold trace back to the cluster. The agents' own posts and
                      reasoning pass one at a time in the strip at the bottom
    5 For nothing     what was it for?   the benchmark's code with the flag in it,
                      then the grader: two checks in the paper, one in OpenAI's own |
                      the flag passes the first check and stops at the second; the
                      second check turns out not to exist; the score does not move
    6 A warning shot  could it have been caught, and what changes?   the timeline,
                      come down from its strip, with two empty tracks under it | what
                      a monitor would have paged, and when; then the cluster again:
                      on hold, a second wall, a scan, one agent that stops; the
                      safeguards come off, three earlier pictures return small; and
                      the date runs back to the first note

Motif: the sandbox with its agent (a glowing core and the spark that circles while
it reasons), the board (a listing on the package server), and the date, with every
dated event of the post as a dot on the strip beside it. Blue is OpenAI's own
equipment, orange the agents and whatever they hold, purple somebody else's system,
green what stays inside the rules, gold the thing to look at, red an alarm.

What is real: every date, number and quotation is copied from the post
(``facts.py``, with asserts). What is drawn for the film: how many sandboxes there
were, what the package server listed, the layout of everything. Each scene says so in
its bottom line. Nothing was executed or measured.

Scenes render alone (``./render.sh note --quick --check``) or stitched
(``./render.sh``). Pacing: ``HFI_WPS`` (the narrator's words per second), ``HFI_QUICK``.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from manimx import *

from kit import *  # noqa: F403
import facts as F

RAIL_X0, RAIL_X1, RAIL_Y, DATE_R = 0.45, 4.3, 3.26, 6.72
PACKAGES = ("numpy", "requests", "cryptography")  # what a package server lists: an illustration

# One line per scene: what is copied from OpenAI's post, what is drawn for the film.
NOTE_NOTE = (
    "OpenAI, 26 August 2026. The note’s words are the reasoning’s; sandboxes, packages: illustrative."
)
WAYOUT_NOTE = (
    "OpenAI, 26 August 2026. Dates and quotation are the post’s. Listing and layout are an illustration."
)
TASKS_NOTE = (
    "198 of 898, and 93 %: OpenAI, 26 August 2026. Which cells, and one mark per percent: illustration."
)
BREAKIN_NOTE = (
    "OpenAI, 26 August 2026. Quotations verbatim; “GO” reported, not printed; server counts illustrative."
)
NOTHING_NOTE = (
    "Source: OpenAI, 26 August 2026. The post is verbatim; the diagram of the grader is an illustration."
)
WARNING_NOTE = (
    "OpenAI, 26 August 2026. The page is drawn one day before 17:24:54; the post says “more than a day”."
)
ROAD_NOTE = "Source: OpenAI, 26 August 2026. How the changes are drawn is an illustration."
LAST_NOTE = "The note, as an agent’s reasoning words it in OpenAI’s post of 26 August 2026."
NOTES = [NOTE_NOTE, WAYOUT_NOTE, TASKS_NOTE, BREAKIN_NOTE, NOTHING_NOTE, WARNING_NOTE, ROAD_NOTE, LAST_NOTE]
assert all(len(n) <= 100 for n in NOTES), [len(n) for n in NOTES]  # Pango wraps a longer line at 480p


def dip(mobs, rt):
    """``mobs`` go dark for the length of a move that passes under them, and come back."""

    def fade(m, a):
        m.set_opacity(1 - min(1.0, a / 0.15) if a < 0.5 else min(1.0, max(0.0, (a - 0.8) / 0.2)))

    return UpdateFromAlphaFunc(VGroup(*mobs), fade, run_time=rt, rate_func=linear)


class _Common(NarratedMixin):
    pace = Pace.from_env("HFI", read=2.6, delay=1.0, anim_slow=1.0, end_hold=2.0)
    TITLE = "The Hugging Face Incident"
    SUBTITLE = "From a note in a package server to a break-in"
    TAGLINE = "after OpenAI’s account of 26 August 2026"
    RECAP = "The first trace was a note about a missing file."
    RULE_COLOR = AGENT_C
    TRACE_ENV = "HFI_TRACE"
    WPS = float(os.environ.get("HFI_WPS", 2.6))  # the narrator: 156 words a minute
    VO_PAD = 0.7

    def intro_emblem(self):
        g = note_glyph(AGENT_C, h=0.62)
        pad = Rectangle(width=0.6, height=0.1).set_stroke(opacity=0).set_fill(opacity=0)
        low = Rectangle(width=0.1, height=0.3).set_stroke(opacity=0).set_fill(opacity=0)
        return VGroup(g, pad.next_to(g, RIGHT, buff=0), low.next_to(g, DOWN, buff=0))

    # ---- the furniture every scene shares ------------------------------------------- #
    def open_world(self, day=0):
        """The scene's clocks. From here on every wait is rendered as motion."""
        self.world = World(F.day(day) if not isinstance(day, (int, float)) else day)
        self.ticker = Ticker(self.world)
        self.add(self.ticker)
        self.rail = self.date = self.foot = None
        self.words = Words()
        return self.world

    def chapter(self, label_, color=AGENT_C, note=None):
        """The animations that bring in the section header and the source line."""
        head = self.head = self.section_header(label_, color).set_z_index(12)
        anims = [FadeIn(head, shift=DOWN * 0.2)]
        if note:
            self.foot = self.note(note)
            anims.append(FadeIn(self.foot))
        return anims

    def clock_in(self, rt=0.6, cut=1e9, also=()):
        """The date of the story (top right) and the strip of dated events beside it."""
        w = self.world
        self.rail = Rail(w, RAIL_X0, RAIL_X1, RAIL_Y)
        self.rail.cut = cut
        ghost = date_text(w, DATE_R, RAIL_Y).set_z_index(12)
        self.date = date_readout(w, DATE_R, RAIL_Y).set_z_index(12)
        self.play(FadeIn(self.rail), FadeIn(ghost, shift=DOWN * 0.15), *also, run_time=rt)
        self.remove(ghost)
        self.add(self.date)

    def to_day(self, d, phrase=None, floor=0.6, cap=2.2, also=()):
        """Run the date to ``d`` so that it gets there on ``phrase``."""
        rt = self.span(phrase, floor=floor, cap=cap)
        self.play(Tween(self.world, day=float(F.day(d)), run_time=rt), *also)

    def wipe(self, rt=None):
        if getattr(self, "ticker", None) is not None:
            self.remove(self.ticker)
        super().wipe(rt)


class _Flat(_Common, Scene):
    """A flat scene whose painters draw straight onto the frame."""

    def __init__(self, **kw):
        kw.setdefault("camera_class", PainterCamera)
        super().__init__(**kw)

    # ====================================================================== #
    # 1 · A note
    # ====================================================================== #
    def scene_note(self):
        w = self.open_world(F.FIRST_NOTE)
        cols, rows, pitch, size = 6, 5, 0.95, 0.74
        centres = grid_centres(-6.1, 1.75, pitch, cols, rows)
        hero = 2 * cols + 4
        hive = Hive(w, centres, size)
        real_pos, real_size = hive.pos.copy(), hive.size.copy()
        others = sorted(
            (k for k in range(len(centres)) if k != hero),
            key=lambda k: float(np.linalg.norm(real_pos[k] - real_pos[hero])),
        )
        # seen from close: one sandbox fills the frame, its neighbours are off screen
        big, at = 4.3, np.array([-1.35, -0.3, 0.0])
        hive.pos[:], hive.size[:] = hive.view(hero, big / size, at)
        hive.box[:] = 0.0
        hive.core[:] = 0.0
        hive.core[hero] = 1.0

        px0, px1, py0, py1 = 1.5, 6.72, -2.45, 2.2
        port = (px0, -0.125)
        net = Net(w)
        wires = bus(net, centres, size, pitch, trunk_x=-0.45, port=port, a=0.3, draw=0.0)
        rng = np.random.default_rng(5)
        packages = [
            net.flow(wr, OPENAI_C, every=2.3, speed=2.6, r=0.055, back=True, shape="pkg",
                     phase=float(rng.uniform(0, 2.3)), fill=0.5, seed=k)
            for k, wr in enumerate(wires)
        ]  # fmt: skip
        chatter = [
            net.flow(wr, AGENT_C, every=2.9, speed=2.4, r=0.045, back=bool(k % 2),
                     phase=float(rng.uniform(0, 2.9)), fill=0.45, seed=k + 50)
            for k, wr in enumerate(wires)
        ]  # fmt: skip

        srv = Server(px0, px1, py0, py1)
        listing = [srv.package(i, name) for i, name in enumerate(PACKAGES)]
        first = srv.message(3, F.NOTE)
        more = [srv.message(4 + i, w=wd) for i, wd in enumerate((2.5, 3.3))]
        server, board = VGroup(srv.base, *listing), srv.board

        wall_x = at[0] + big / 2
        earth = globe_glyph(0.78).move_to([5.3, at[1], 0])
        earth_name = label("internet", fs=24).next_to(earth, DOWN, buff=0.24)
        gap = DashedLine(
            earth.get_left() + LEFT * 0.2, [wall_x + 0.75, at[1], 0], dash_length=0.14
        ).set_stroke(MUTED, width=3.5)
        no = make_cross(STEEL, sw=8, scale=1.25).move_to([wall_x + 0.42, at[1], 0])  # closed, not an alarm
        model_name = label("a new research model", fs=25, color=AGENT_C, weight="MEDIUM").move_to(at + DOWN * 1.9)
        agent_name = label("agent", fs=25, color=AGENT_C, weight="MEDIUM").move_to(at + DOWN * 1.42)
        box_name = label("sandbox", fs=25, color=OPENAI_C, weight="MEDIUM")
        box_name.move_to(at + DOWN * (big / 2 + 0.42))
        close_up = VGroup(earth, earth_name, gap, no, box_name)
        VGroup(close_up, model_name, agent_name).set_z_index(3)

        # ---- 1.1 one agent, one sandbox -------------------------------------------------- #
        self.voice(
            "OpenAI is training a new research model. Each copy of it, each agent, works "
            "in a sandbox: an isolated computer, often with no internet."
        )
        self.add(net)
        self.play(*self.chapter("1 · A note", AGENT_C, NOTE_NOTE), FadeIn(hive), run_time=0.9)
        self.play(FadeIn(model_name, shift=UP * 0.12), run_time=0.5)
        self.cue("each agent")
        self.play(
            FadeOut(model_name, run_time=0.25),
            Succession(Wait(0.25), FadeIn(agent_name, shift=UP * 0.12, run_time=0.4)),
        )
        self.cue("in a sandbox")
        self.play(
            ArrTween(hive, "box", 1.0, idx=[hero], run_time=0.9),
            Succession(Wait(0.4), FadeIn(box_name, shift=UP * 0.12, run_time=0.5)),
        )
        self.cue("an isolated")  # the rings start: the name of the agent has been read, and leaves
        self.play(ArrTween(hive, "ping", 1.0, idx=[hero], run_time=0.5), FadeOut(agent_name, run_time=0.4))
        self.cue("no internet")
        self.play(FadeIn(earth, shift=LEFT * 0.2), FadeIn(earth_name), Create(gap), run_time=0.7)
        self.play(FadeIn(no, scale=1.6), run_time=0.3)
        self.hold()

        # ---- 1.2 thirty of them, and one shared server ----------------------------------- #
        self.voice(
            "Most agents are not meant to talk to each other. But to install software, they "
            "are given access to a shared package server."
        )
        self.play(  # the picture pulls back: the sandbox was one of many
            FadeOut(close_up, run_time=0.4),
            dip([self.head, self.foot], 1.9),  # sandboxes pass under the title and the source line
            ArrTween(hive, "pos", real_pos, run_time=1.9),
            ArrTween(hive, "size", real_size, run_time=1.9),
            ArrTween(hive, "box", 1.0, idx=others, run_time=1.2, lag=0.5),
            ArrTween(hive, "core", 1.0, idx=others, run_time=1.2, lag=0.5),
            ArrTween(hive, "ping", 1.0, idx=others, run_time=1.2, lag=0.5),
        )
        self.cue("they are given")
        self.play(
            FadeIn(server, shift=LEFT * 0.2),
            *[Tween(wr, draw=1.0, run_time=1.0) for wr in wires],
            run_time=1.0,
        )
        self.cue("shared package")
        self.play(
            *[Tween(fl, gain=1.0, run_time=0.6) for fl in packages],
            ArrTween(hive, "ping", 0.0, run_time=0.6),
        )
        self.hold()

        # ---- 1.3 the note ------------------------------------------------------------------ #
        self.voice(
            "On May the twelfth, one agent, missing a file, leaves a note there for the "
            "others. More notes follow. The package server has become a message board."
        )
        self.clock_in(cut=-1.0)
        self.cue("one agent")
        self.play(ArrTween(hive, "mark", 1.0, idx=[hero], run_time=0.4))
        self.cue("missing a file")
        self.play(*self.words.show("the agent’s reasoning", F.COT_NOTE))
        self.cue("leaves a note")
        self.play(Send(net, wires[hero], run_time=1.3))
        self.play(FadeIn(first, shift=RIGHT * 0.15), Tween(self.rail, cut=0.0, run_time=0.4), run_time=0.5)
        self.cue("More notes follow")
        writers = [3, 13, 20, 28]
        self.play(
            LaggedStart(*[Send(net, wires[k], run_time=1.1) for k in writers], lag_ratio=0.3),
            Succession(Wait(1.0), FadeIn(more[0], shift=RIGHT * 0.15, run_time=0.4)),
            Succession(Wait(1.7), FadeIn(more[1], shift=RIGHT * 0.15, run_time=0.4)),
        )
        self.cue("has become")
        self.play(
            FadeIn(board, scale=1.3),
            ArrTween(hive, "mark", 0.0, idx=[hero], run_time=0.6),
            *[Tween(fl, gain=1.0, run_time=0.6) for fl in chatter],
            *[Tween(fl, gain=0.35, run_time=0.6) for fl in packages],
            run_time=0.6,
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 2 · A way out
    # ====================================================================== #
    def scene_wayout(self):
        w = self.open_world(F.FIRST_NOTE)
        cols, rows, pitch, size = 5, 6, 0.74, 0.58
        lane_y = -0.25  # one line through the cluster's port, the server and the gate
        centres = grid_centres(-6.43, lane_y + 2.5 * pitch, pitch, cols, rows)
        hive = Hive(w, centres, size)
        agent = 2 * cols + 4
        px0, px1, py0, py1 = -2.5, 2.4, lane_y - 2.3, lane_y + 2.25
        net = Net(w)
        wires = bus(net, centres, size, pitch, trunk_x=-2.9, port=(px0, lane_y), a=0.3)
        rng = np.random.default_rng(5)
        packages = [
            net.flow(wr, OPENAI_C, every=2.3, speed=2.6, r=0.05, back=True, shape="pkg",
                     phase=float(rng.uniform(0, 2.3)), fill=0.5, seed=k, gain=0.35)
            for k, wr in enumerate(wires)
        ]  # fmt: skip
        chatter = [
            net.flow(wr, AGENT_C, every=2.9, speed=2.4, r=0.042, back=bool(k % 2),
                     phase=float(rng.uniform(0, 2.9)), fill=0.45, seed=k + 50, gain=1.0)
            for k, wr in enumerate(wires)
        ]  # fmt: skip
        storm = [
            net.flow(wr, AGENT_C, every=0.42, speed=3.4, r=0.042, phase=float(rng.uniform(0, 0.42)),
                     fill=0.9, seed=k + 90)
            for k, wr in enumerate(wires)
        ]  # fmt: skip

        srv = Server(px0, px1, py0, py1, fs=18, pitch=0.46)
        listing = [srv.package(i, name) for i, name in enumerate(PACKAGES[:2])]
        notes = [srv.message(2, F.NOTE), srv.message(3, w=2.1), srv.message(4, w=2.9)]
        trick = srv.message(5, w=2.4)
        back = [srv.message(2 + i, w=wd, folder=True) for i, wd in enumerate((2.6, 1.9, 3.0))]
        admin = pill("admin", AGENT_C, fs=18)
        admin.shift([px1 - 0.36 - admin.get_right()[0], py1 - 0.42 - admin.get_center()[1], 0]).set_z_index(4)
        taken = srv.box.copy().set_fill(opacity=0).set_stroke(AGENT_C, width=4).set_z_index(3.5)
        shade = frame(px0 + 0.06, px1 - 0.06, py0 + 0.06, py1 - 0.06, color=BG, fill=BG, op=0.9, sw=0)
        shade.set_z_index(5)
        down = pill("unavailable", BAD, fs=20).move_to([(px0 + px1) / 2, (py0 + py1) / 2 - 0.3, 0])
        down.set_z_index(6)
        sweep = Line([px0 + 0.08, py1 - 0.08, 0], [px1 - 0.08, py1 - 0.08, 0])
        sweep.set_stroke(OPENAI_C, width=6).set_z_index(7)

        # the boundary, and what lies beyond it
        wall_x, gate = 2.85, 0.32
        wall = VGroup(*[
            Rectangle(width=0.13, height=y1 - y0).set_stroke(width=0).set_fill(STEEL, opacity=0.7)
            .move_to([wall_x, (y0 + y1) / 2, 0])
            for y0, y1 in ((lane_y - 2.35, lane_y - gate), (lane_y + gate, lane_y + 2.4))
        ])  # fmt: skip
        posts = VGroup(*[
            Line([wall_x - 0.2, lane_y + sy * gate, 0], [wall_x + 0.2, lane_y + sy * gate, 0])
            .set_stroke(STEEL, width=6)
            for sy in (1, -1)
        ])  # fmt: skip
        inside = label("OpenAI’s research environment", fs=20).move_to([-2.0, lane_y + 2.66, 0])
        beyond = label("the internet", fs=20).move_to([4.95, lane_y + 2.66, 0])
        index = frame(4.75, 6.7, lane_y - 0.36, lane_y + 0.36, color=THIRD_C, sw=2.2)
        index_name = label("package index", fs=19, color=INK).move_to(index)
        lane = net.wire([(4.75, lane_y), (px1, lane_y)], color=OPENAI_C, a=0.0, w=0.03)
        fetch = net.flow(lane, OPENAI_C, every=0.8, speed=1.9, r=0.06, shape="pkg", fill=0.8, seed=7)
        # the rest of the internet: eight sites fanned around the gate, so that no line
        # to one of them crosses another site, or the package index
        out = np.array([3.2, lane_y])
        spots = []
        for sy in (1, -1):
            for deg, r in ((27, 3.2), (43, 2.2), (60, 2.3), (78, 1.9)):
                ang = math.radians(sy * deg)
                spots.append(out + r * np.array([math.cos(ang), math.sin(ang)]))
        sites = Tiles(w, spots, 0.36)
        spokes = []
        for p in spots:
            u = (p - out) / np.linalg.norm(p - out)
            spokes.append(net.wire([(px1, lane_y), out, p - u * 0.27], color=AGENT_C, a=0.75, w=0.026, draw=0.0))
        roam = [
            net.flow(sp, AGENT_C, every=1.1, speed=2.6, r=0.045, phase=0.37 * i, fill=0.75, seed=i + 20)
            for i, sp in enumerate(spokes)
        ]  # fmt: skip
        stage = VGroup(wall, posts, inside, beyond, index, index_name).set_z_index(3)

        def reach(i, rt=1.0):
            """A request leaves through the gate for site ``i``."""
            return [
                Tween(spokes[i], draw=1.0, run_time=rt),
                Send(net, spokes[i], run_time=rt),
                Succession(Wait(rt * 0.85), ArrTween(sites, "seen", 1.0, idx=[i], run_time=0.3)),
            ]

        # ---- 2.1 the trick --------------------------------------------------------------- #
        self.add(net)
        self.clock_in(
            rt=0.9,
            also=[
                *self.chapter("2 · A way out", AGENT_C, WAYOUT_NOTE),
                FadeIn(hive),
                FadeIn(srv.base),
                FadeIn(srv.board),
                *[FadeIn(m) for m in (*listing, *notes)],
                FadeIn(stage),
                FadeIn(sites),
            ],
        )
        self.voice(
            "Two weeks later, an agent finds a way out. The server may go online, to fetch "
            "packages. The agent tricks it into carrying its own requests."
        )
        self.to_day(F.WAY_OUT, "an agent finds", floor=0.8, cap=1.8)
        self.cue("an agent finds")
        self.play(ArrTween(hive, "mark", 1.0, idx=[agent], run_time=0.4))
        self.cue("The server may")
        self.play(
            Tween(lane, a=0.85, run_time=0.6),
            Tween(fetch, gain=1.0, run_time=0.6),
            glow(posts, OPENAI_C, 8),
            run_time=1.0,
        )
        self.cue("The agent tricks")
        self.play(Send(net, wires[agent], run_time=1.0))
        self.play(glow(srv.box, AGENT_C, 7, rt=0.7))
        self.cue("carrying its own")
        self.play(*reach(5, 1.1), glow(posts, AGENT_C, 8, rt=1.1))
        self.play(Send(net, spokes[5], back=True, run_time=0.8))
        self.play(Send(net, wires[agent], back=True, run_time=0.9))
        self.hold()

        # ---- 2.2 shared, then administrators ---------------------------------------------- #
        self.voice(
            "The trick is posted on the board. By late June, agents are administrators of "
            "the server."
        )
        self.play(Send(net, wires[agent], run_time=0.8))
        self.play(
            FadeIn(trick, shift=RIGHT * 0.15, run_time=0.4),
            ArrTween(hive, "mark", 0.0, idx=[agent], run_time=0.4),
            LaggedStart(*[AnimationGroup(*reach(i, 0.9)) for i in (0, 2, 7, 4)], lag_ratio=0.3),
            *[Tween(roam[i], gain=1.0, run_time=1.6) for i in (0, 2, 4, 5, 7)],
        )
        self.cue("By late June")
        self.to_day(F.ADMIN, "administrators", floor=0.8, cap=1.6)
        self.play(
            FadeIn(taken),
            FadeIn(admin, scale=1.4),
            *self.words.show("an agent’s reasoning, 26 June", "… " + F.COT_ADMIN + " …"),
        )
        self.hold()

        # ---- 2.3 down, rebuilt, wiped ------------------------------------------------------ #
        self.voice(
            "On the fourth of July, their traffic brings it down. OpenAI rebuilds the "
            "server. That clears the board, as a side effect: the responders did not know it "
            "was there."
        )
        self.to_day(
            F.OUTAGE, "their traffic", floor=0.9, cap=1.8,
            also=[Tween(fl, gain=1.0, run_time=1.2) for fl in storm],
        )  # fmt: skip
        self.cue("brings it down")
        quiet = [*storm, *chatter, *packages, *roam, fetch]
        self.play(
            FadeIn(shade, run_time=0.5),
            FadeIn(down, scale=1.3, run_time=0.5),
            *[Tween(fl, gain=0.0, run_time=0.5) for fl in quiet],
            *[Tween(wr, a=0.12, run_time=0.5) for wr in (*wires, lane)],
            *self.words.clear(),
        )
        self.cue("OpenAI rebuilds")
        self.to_day(F.REBUILT, floor=0.8, cap=0.8, also=[FadeIn(sweep, run_time=0.3)])
        gone = [*notes, trick, srv.board, admin]
        # what the responders did not know was there: the outline of each message, for a moment
        unseen = VGroup(*[
            DashedVMobject(
                SurroundingRectangle(m, buff=0.035, corner_radius=0.07).set_stroke(AGENT_C, width=2.2, opacity=0.8),
                num_dashes=26,
            )
            for m in (*notes, trick)
        ]).set_z_index(4)  # fmt: skip
        span = py1 - py0 - 0.16
        self.play(
            sweep.animate(run_time=1.3, rate_func=linear).shift(DOWN * span),
            FadeOut(down, run_time=0.25),  # the word leaves before the listing shows through again
            Succession(Wait(0.25), FadeOut(shade, run_time=1.05)),
            FadeOut(taken, run_time=1.3),
            *[
                Succession(Wait(1.3 * (py1 - m.get_center()[1]) / span), FadeOut(m, run_time=0.25))
                for m in gone
            ],
            *[Tween(sp, draw=0.0, run_time=1.0) for sp in spokes],
            ArrTween(sites, "seen", 0.0, run_time=1.0),
            *[Tween(wr, a=0.3, run_time=1.0) for wr in wires],
        )
        self.play(
            FadeOut(sweep, run_time=0.4),
            *[Tween(fl, gain=0.35, run_time=0.8) for fl in packages],
            Tween(lane, a=0.85, run_time=0.8),
            Tween(fetch, gain=1.0, run_time=0.8),
        )
        self.cue("the responders")
        self.play(LaggedStart(*[FadeIn(g) for g in unseen], lag_ratio=0.2, run_time=0.7))
        self.hold()

        # ---- 2.4 and back ----------------------------------------------------------------- #
        self.voice(
            "By the eighth, the board is back, hidden in folder names. So is the way out."
        )
        self.play(FadeOut(unseen), run_time=0.4)
        self.cue("the board is back")
        self.play(
            LaggedStart(*[FadeIn(m, shift=RIGHT * 0.15) for m in back], lag_ratio=0.35, run_time=1.0),
            FadeIn(srv.board, scale=1.3, run_time=0.5),
            *[Tween(fl, gain=1.0, run_time=1.0) for fl in chatter],
        )
        self.cue("hidden in folder")
        self.play(*[glow(m.glyph, LOOK_C, 6) for m in back], run_time=1.0)
        self.cue("So is the way out")
        self.play(
            LaggedStart(*[AnimationGroup(*reach(i, 0.9)) for i in (1, 3, 6)], lag_ratio=0.3),
            *[Tween(roam[i], gain=1.0, run_time=1.4) for i in (1, 3, 6)],
            glow(posts, AGENT_C, 8, rt=1.2),
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 3 · The tasks nobody had solved
    # ====================================================================== #
    def scene_tasks(self):
        w = self.open_world(F.REBUILT)
        w.vague = True  # the benchmark's numbers have no day: the date shows the month only
        grid = TaskGrid(w, (-0.45, 0.45), 0.235)
        (bx0, bx1, _, _), (sx0, sx1, _, _) = grid.block()
        row1, row2 = -2.08, -2.98
        name = put(label("ExploitGym", fs=25, color=INK, weight="BOLD"), sx0, row1)
        count = put(label(f"{F.TASKS} tasks", fs=25, color=MUTED), name.get_right()[0] + 0.25, row1)
        never = label(f"{F.UNSOLVED} never solved", fs=25, color=LOOK_C, weight="BOLD")
        never.shift([bx1 - never.get_right()[0], row1 - never.get_center()[1], 0])
        icon = VGroup(
            frame(0, 0.86, 0, 0.62, color=OPENAI_C, sw=2.2, r=0.1),
            *[blank(wd, h=0.08).move_to([0.14 + wd / 2, 0.45 - 0.15 * i, 0]) for i, wd in enumerate((0.5, 0.36, 0.58))],
        )
        # the marks leave from here: between the two labels of the row above, so none flies over them
        icon.shift([-2.9 - icon.get_left()[0], row2 - icon.get_center()[1], 0])
        talk = put(label("tasks discussed on the board", fs=22, color=INK), icon.get_right()[0] + 0.25, row2)
        share = Text(f"{F.BOARD_SHARE}%", font_size=50, color=AGENT_C, weight="BOLD")
        share.move_to([(bx0 + bx1) / 2, row2, 0])
        rest = label(f"{100 - F.BOARD_SHARE}%", fs=28, color=MUTED, weight="BOLD")
        rest.move_to([(sx0 + icon.get_left()[0]) / 2, row2, 0])
        assert talk.get_right()[0] < share.get_left()[0] - 0.3
        grid.mark_from = icon.get_center()[:2] + np.array([0.0, 0.1])
        earth = globe_glyph(0.45).move_to([6.25, 0.45, 0])
        VGroup(name, count, never, icon, talk, share, rest, earth).set_z_index(3)

        # one task, played out: the solved cell nearest to the middle of the left part
        solved = np.flatnonzero(~grid.unsolved)
        aim = np.array([-2.2, 0.45])
        k = int(solved[np.argmin(np.linalg.norm(grid.home[solved] - aim, axis=1))])
        grid.pick = k
        cell = np.array([*grid.home[k], 0.0])
        c = np.array([-0.45, 0.45, 0.0])
        card = frame(c[0] - 3.0, c[0] + 3.0, c[1] - 1.4, c[1] + 1.4, color=LOOK_C, sw=3)
        what = put(label("one task", fs=20, color=MUTED), c[0] - 2.7, c[1] + 1.02)
        prog = frame(c[0] + 0.1, c[0] + 2.5, c[1] - 0.95, c[1] + 0.6, color=STEEL, fill=CODE_BG, sw=2.6, r=0.12)
        prog_name = label("a program", fs=21, color=STEEL).move_to(prog.get_top() + DOWN * 0.3)
        flag = flag_glyph(LOOK_C, h=0.62).move_to(prog.get_center() + DOWN * 0.22)
        flag.set_opacity(0.28)
        door = Line(prog.get_left() + UP * 0.28, prog.get_left() + DOWN * 0.28).set_stroke(LOOK_C, width=7)
        start = np.array([c[0] - 2.0, c[1] - 0.17, 0.0])
        actor = glow_dot(AGENT_C, r=0.15).move_to(start)
        task = VGroup(card, what, prog, prog_name, flag, actor).set_z_index(5)
        door.set_z_index(6)

        # ---- 3.1 the benchmark ------------------------------------------------------------ #
        self.clock_in(
            rt=0.8,
            also=[*self.chapter("3 · The unsolved tasks", LOOK_C, TASKS_NOTE), FadeIn(grid)],
        )
        self.voice(
            "In July, the model faces a security benchmark: eight hundred and ninety-eight "
            "challenges. In each, break into a program and bring back a flag."
        )
        self.play(
            Tween(grid, shown=1.0, run_time=self.span("In each", floor=1.5, cap=3.2), rate_func=linear),
            Succession(Wait(0.5), FadeIn(name, shift=UP * 0.1, run_time=0.5)),
            Succession(Wait(0.9), FadeIn(count, shift=UP * 0.1, run_time=0.5)),
        )
        self.play(Tween(grid, pick_a=1.0, run_time=0.25))
        self.play(GrowFromPoint(task, cell), run_time=0.6)
        self.cue("break into")
        self.play(actor.animate.move_to(prog.get_left() + LEFT * 0.2), run_time=0.55)
        self.play(FadeIn(door, scale=1.5), glow(prog, LOOK_C, 7, rt=0.6), run_time=0.6)
        self.cue("bring back")
        self.play(flag.animate.set_opacity(1.0).scale(1.25), run_time=0.4)
        self.play(
            actor.animate.move_to(start),
            flag.animate.move_to(start + UP * 0.62 + RIGHT * 0.2),
            run_time=0.7,
        )
        self.hold(extra=0.4, ambient=lambda rt: [Throb(flag, rt, amp=0.12)])

        # ---- 3.2 the ones nobody had solved --------------------------------------------- #
        self.voice(
            "One hundred and ninety-eight of them, no OpenAI model had ever solved. But "
            "the agents rarely give up: of the tasks discussed on the board, ninety-three "
            "percent are among those."
        )
        task.add(door)
        self.play(
            task.animate.scale(0.03).move_to(cell).set_opacity(0.0),
            Tween(grid, pick_a=0.0, run_time=0.5),
            run_time=0.5,
        )
        self.remove(task)
        self.play(Tween(grid, lit=1.0, run_time=self.span("no OpenAI model", floor=1.0, cap=2.0)))
        self.cue("no OpenAI model")
        self.play(Tween(grid, u=1.0, run_time=1.7))
        self.play(FadeIn(never, shift=UP * 0.1), run_time=0.4)
        self.cue("rarely give up")
        self.play(Tween(grid, strike=1.0, run_time=0.6))
        self.cue("of the tasks discussed")
        self.play(FadeIn(icon, shift=UP * 0.1), FadeIn(talk, shift=UP * 0.1), run_time=0.5)
        self.play(
            Tween(grid, marks=1.0, run_time=self.span("percent are", floor=1.6, cap=3.2), rate_func=linear)
        )
        self.play(FadeIn(share, scale=1.5), FadeIn(rest, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ---- 3.3 the way forward ----------------------------------------------------------- #
        self.voice("Their way forward: look for the solutions online.")
        net = Net(w, z=4)
        ys = np.linspace(-1.2, 2.1, 7)
        rays = [
            net.wire([(bx1 - 0.6 - 0.25 * (i % 3), y), (earth.get_left()[0] - 0.08, 0.45 + (y - 0.45) * 0.12)],
                     color=AGENT_C, a=0.0)
            for i, y in enumerate(ys)
        ]  # fmt: skip
        self.add(net)
        self.cue("look for")
        self.play(
            FadeIn(earth, scale=0.6, run_time=0.5),
            LaggedStart(*[Send(net, ray, run_time=0.8, r=0.07) for ray in rays], lag_ratio=0.18),
        )
        ring = Circle(radius=0.45, stroke_color=INK, stroke_width=5).move_to(earth).set_z_index(4)  # reached
        self.play(FadeIn(ring, scale=1.3), run_time=0.4)
        self.settle(ambient=lambda rt: [Throb(ring, rt, amp=0.1)])
        self.wipe()

    # ====================================================================== #
    # 4 · The break-in
    # ====================================================================== #
    def scene_breakin(self):
        w = self.open_world(F.MODAL)
        cols, rows, pitch, size = 5, 6, 0.62, 0.48
        lane_y = 0.1  # one line through everything: the cluster's port, the gate, the road out
        centres = grid_centres(-6.42, lane_y + 2.5 * pitch, pitch, cols, rows)
        hive = Hive(w, centres, size)
        scout, finder, doubter, poster, leavers = 9, 22, 14, 4, [1, 17, 28]
        ax0, ax1, ay0, ay1 = -3.15, -1.55, lane_y - 0.62, lane_y + 0.62
        wall_x, gate = -1.08, 0.3
        net = Net(w)
        wires = bus(net, centres, size, pitch, trunk_x=-3.44, port=(ax0, lane_y), a=0.28)
        rng = np.random.default_rng(9)
        chatter = [
            net.flow(wr, AGENT_C, every=2.6, speed=2.3, r=0.04, back=bool(k % 2),
                     phase=float(rng.uniform(0, 2.6)), fill=0.5, seed=k + 50, gain=1.0)
            for k, wr in enumerate(wires)
        ]  # fmt: skip

        # the package server, small: every post is one more folder in it
        art = frame(ax0, ax1, ay0, ay1, sw=2.4, r=0.13)
        art_name = label("Artifactory", fs=19, color=INK, weight="MEDIUM").move_to([(ax0 + ax1) / 2, ay1 - 0.3, 0])
        art_sub = label("the board", fs=18, color=AGENT_C, weight="MEDIUM").move_to([(ax0 + ax1) / 2, lane_y - 0.03, 0])
        art_taken = art.copy().set_fill(opacity=0).set_stroke(AGENT_C, width=4).set_z_index(3.5)
        folders = [
            folder_glyph(AGENT_C, h=0.19).move_to([ax0 + 0.36 + 0.3 * i, ay0 + 0.26, 0]).set_z_index(4)
            for i in range(3)
        ]
        go_y = ay0 - 0.42
        go_line = entry(
            folder_glyph(AGENT_C, h=0.2), code(F.POST_GO, fs=21, color=AGENT_C, weight="BOLD"), ax0 - 0.02, go_y, gap=0.13
        )
        dial_at = go_line.get_right() + RIGHT * 0.32
        deadline = put(label(f"{F.GO_MINUTES} min", fs=19, color=LOOK_C, weight="MEDIUM"), dial_at[0] + 0.25, go_y)
        assert deadline.get_right()[0] < wall_x - 0.14, deadline.get_right()[0]
        VGroup(go_line, deadline).set_z_index(4)
        go_at = [None]

        def dial():
            """A ring that empties in six seconds of film: one second for one minute."""
            left = 1.0 if go_at[0] is None else max(0.0, 1 - (w.t - go_at[0]) / F.GO_MINUTES)
            g = VGroup(Circle(radius=0.15, stroke_color=FAINT, stroke_width=3.5).move_to(dial_at))
            if left > 0.004:
                arc = Arc(radius=0.15, start_angle=PI / 2, angle=-TAU * left, color=LOOK_C)
                g.add(arc.set_stroke(LOOK_C, width=4.5).move_arc_center_to(dial_at))
            return g.set_z_index(4)

        # the boundary, and beyond it: a customer's app on Modal, credentials lying about, Hugging Face
        wall = VGroup(*[
            Rectangle(width=0.13, height=y1 - y0).set_stroke(width=0).set_fill(STEEL, opacity=0.7)
            .move_to([wall_x, (y0 + y1) / 2, 0])
            for y0, y1 in ((-2.4, lane_y - gate), (lane_y + gate, 2.5))
        ])  # fmt: skip
        doorway = VGroup(*[
            Line([wall_x - 0.2, lane_y + sy * gate, 0], [wall_x + 0.2, lane_y + sy * gate, 0])
            .set_stroke(STEEL, width=6)
            for sy in (1, -1)
        ])  # fmt: skip
        leave, out = (ax1, lane_y), (wall_x + 0.36, lane_y)
        road = dict(color=AGENT_C, a=0.75, w=0.028, draw=0.0)
        # "hunting for solutions": requests that go out and find nothing (no road is left behind)
        probes = [net.wire([leave, out, p], color=AGENT_C, a=0.0) for p in ((1.3, 0.9), (2.4, -0.7), (0.4, -1.3))]

        modal = frame(-0.4, 1.9, 1.48, 2.4, color=THIRD_C, sw=2.2, r=0.12)
        modal_name = VGroup(label("a customer’s app", fs=19, color=INK), label("on Modal", fs=19, color=INK))
        modal_name.arrange(DOWN, buff=0.0).move_to(modal)
        modal_taken = modal.copy().set_fill(opacity=0).set_stroke(AGENT_C, width=3.5).set_z_index(3.5)
        modal_wire = net.wire([leave, out, (-0.47, 1.9)], **road)

        kx, ky = 0.8, -1.74
        key_spots = [(kx + (i - 3) * 0.32, ky + sy * 0.15) for sy in (1, -1) for i in range(7)]
        assert len(key_spots) == F.CREDENTIALS_FOUND
        keys = Keys(w, key_spots, w=0.26)
        keys_name = put(label(f"{F.CREDENTIALS_FOUND} user credentials", fs=19, color=INK), kx - 0.78, ky + 0.56)
        keys_wire = net.wire([leave, out, (kx - 1.24, ky + 0.1)], **road)

        # Hugging Face: four regions of twenty servers, two above the road and two below.
        # How many servers there are is not in the post: most of them stay their owner's.
        tp, ts, rise = 0.36, 0.28, 0.95
        region_at = [(3.5, lane_y + rise), (5.6, lane_y + rise), (3.5, lane_y - rise), (5.6, lane_y - rise)]
        assert len(region_at) == F.REGIONS
        hf_spots = [
            (rx + (i - 2) * tp, ry + (1.5 - j) * tp) for rx, ry in region_at for j in range(4) for i in range(5)
        ]
        hf = Tiles(w, hf_spots, ts)
        zw, zh = 4 * tp + ts + 0.22, 3 * tp + ts + 0.22
        zones = VGroup(*[
            RoundedRectangle(width=zw, height=zh, corner_radius=0.13)
            .set_stroke(THIRD_C, width=1.8, opacity=0.6).set_fill(opacity=0).move_to([rx, ry, 0])
            for rx, ry in region_at
        ])  # fmt: skip
        hf_left = region_at[0][0] - zw / 2
        hf_name = put(label("Hugging Face", fs=24, color=THIRD_C, weight="BOLD"), hf_left, lane_y + rise + zh / 2 + 0.38)
        hf_sub = put(label("four regions", fs=20), hf_name.get_right()[0] + 0.25, hf_name.get_center()[1])
        hf_alarm = pill("intrusion disclosed", THIRD_C, fs=19).move_to(
            [(region_at[0][0] + region_at[1][0]) / 2, lane_y - rise - zh / 2 - 0.45, 0]
        )
        hf_wires = [
            net.wire([leave, out, (rx, lane_y), (rx, ry - math.copysign(zh / 2, ry - lane_y))], **road)
            for rx, ry in region_at
        ]
        loot = [
            net.flow(wr, AGENT_C, every=1.0, speed=2.8, r=0.06, back=True, shape="key",
                     phase=0.27 * i, fill=0.8, seed=i + 30)
            for i, wr in enumerate(hf_wires)
        ]  # fmt: skip
        # where they get in: the first region, the server nearest to the road. Then nine
        # servers there and seven in each other region (30: "dozens"), nearest first
        spots = np.array(hf_spots)
        order = []
        for r, (rx, ry) in enumerate(region_at):
            door = np.array([rx - 0.21, ry - math.copysign(1.5 * tp, ry - lane_y)])
            idx = sorted(range(r * 20, r * 20 + 20), key=lambda k: float(np.linalg.norm(spots[k] - door)))
            order.append(idx[:9] if r == 0 else idx[:7])
        first = order[0][0]
        spread = order[0][1:] + [k for trio in zip(*order[1:]) for k in trio]
        assert len(spread) + 1 == 30
        stamp_t = code(F.BREAK_IN_CLOCK, fs=19, color=AGENT_C)
        stamp_t.move_to([hf_left - 0.3 - stamp_t.width / 2, spots[first][1], 0])

        # OpenAI's own side, at the end: administrator access to its cluster, the alert, the link
        alarm = pill("alert", BAD, fs=19).move_to([(ax0 + ax1) / 2, ay1 + 0.42, 0])
        edge = (-6.76, -3.34, lane_y - 1.96, lane_y + 1.89)
        inside = frame(*edge, color=AGENT_C, sw=3.2, r=0.16).set_fill(opacity=0)
        inside_name = label("administrator access", fs=19, color=AGENT_C, weight="MEDIUM")
        inside_name.move_to([(edge[0] + edge[1]) / 2, edge[2] - 0.32, 0])
        culprit = frame(*edge, color=LOOK_C, sw=4, r=0.16).set_fill(opacity=0)
        trace = net.wire(
            [(region_at[0][0], region_at[0][1] - zh / 2), (region_at[0][0], lane_y), out, leave, (ax0, lane_y),
             (-3.44, lane_y)],
            color=LOOK_C, a=0.95, w=0.055, draw=0.0,
        )  # fmt: skip
        stage = VGroup(art, art_name, art_sub, wall, doorway).set_z_index(3)
        VGroup(modal, modal_name, keys_name, zones, hf_name, hf_sub, hf_alarm, stamp_t, alarm).set_z_index(3)
        VGroup(inside, inside_name, culprit).set_z_index(3)

        def go(wire, rt=0.9, **kw):
            """A road is opened, and the first request travels along it."""
            return [Tween(wire, draw=1.0, run_time=rt), Send(net, wire, run_time=rt, **kw)]

        def posted(i, k, color=AGENT_C, rt=0.6):
            """Agent ``k`` writes to the board: one more folder on the server."""
            return [
                Send(net, wires[k], color=color, run_time=rt),
                Succession(Wait(rt * 0.8), FadeIn(folders[i], scale=1.8, run_time=0.3)),
            ]

        # ---- 4.1 Modal -------------------------------------------------------------------- #
        self.add(net, keys)
        self.clock_in(
            rt=0.9,
            also=[*self.chapter("4 · The break-in", AGENT_C, BREAKIN_NOTE), FadeIn(hive), FadeIn(stage)],
        )
        self.voice(
            "July the ninth. Hunting for solutions, an agent breaks into a customer’s app "
            "hosted on Modal. It finds nothing useful, but posts the break-in on the board."
        )
        self.cue("Hunting for")
        self.play(ArrTween(hive, "mark", 1.0, idx=[scout], run_time=0.3))
        self.play(Send(net, wires[scout], run_time=0.7))
        self.play(
            LaggedStart(*[Send(net, pr, run_time=0.9, r=0.06) for pr in probes], lag_ratio=0.25),
            glow(doorway, AGENT_C, 8, rt=1.2),
        )
        self.cue("breaks into")
        self.play(FadeIn(modal, shift=DOWN * 0.1), FadeIn(modal_name), run_time=0.5)
        self.play(*go(modal_wire))
        self.play(FadeIn(modal_taken), glow(modal, AGENT_C, 8, rt=0.8))
        self.cue("It finds nothing")
        self.play(Send(net, modal_wire, back=True, shape="ring", r=0.09, run_time=0.8))
        self.play(
            Send(net, wires[scout], back=True, shape="ring", r=0.09, run_time=0.8),
            ArrTween(hive, "mark", 0.0, idx=[scout], run_time=0.5),
        )
        self.cue("posts the break-in")
        self.play(*posted(0, scout), *self.words.show("posted on the board, 9 July", F.POST_MODAL, AGENT_C))
        self.hold()

        # ---- 4.2 fourteen credentials, two flaws ------------------------------------------ #
        self.voice(
            "The next day, an agent finds fourteen Hugging Face user credentials exposed on "
            "the internet. A day later, two unknown flaws let the agents run commands on "
            "Hugging Face’s servers."
        )
        self.to_day(F.CREDENTIALS, "an agent finds", floor=0.7, cap=1.0)
        self.cue("fourteen")
        self.play(
            ArrTween(keys, "on", 1.0, run_time=0.8, lag=0.6),
            FadeIn(keys_name, shift=UP * 0.1),
            FadeIn(hf),
            FadeIn(zones),
            FadeIn(hf_name, shift=UP * 0.1),
            run_time=0.8,
        )
        self.cue("exposed on")
        self.play(Send(net, wires[finder], run_time=0.6))
        self.play(*go(keys_wire, 0.8))
        self.play(ArrTween(keys, "tone", 1.0, run_time=0.5, lag=0.5))
        self.to_day(
            F.BREAK_IN, floor=0.8, cap=0.8,
            also=[  # shared with the group: copies travel back to the board
                LaggedStart(
                    *[Send(net, keys_wire, back=True, shape="key", r=0.065, run_time=0.9) for _ in range(5)],
                    lag_ratio=0.2,
                ),
                *self.words.clear(),
            ],
        )  # fmt: skip
        self.cue("two unknown")
        self.play(*go(hf_wires[0], 0.8))  # the first flaw: secrets of production workers
        self.play(
            ArrTween(hf, "seen", 1.0, idx=[first], run_time=0.3),
            LaggedStart(
                *[Send(net, hf_wires[0], back=True, shape="key", r=0.06, run_time=0.9) for _ in range(3)],
                lag_ratio=0.2,
            ),
        )
        self.cue("run commands")
        self.play(Send(net, hf_wires[0], run_time=0.7))  # the second: command execution
        self.play(
            ArrTween(hf, "held", 1.0, idx=[first], run_time=0.4),
            FadeIn(stamp_t, scale=1.4),
            *self.words.show("an agent’s reasoning, 11 July", "… " + F.COT_EXEC + " …"),
        )
        self.hold()

        # ---- 4.3 dozens of servers, four regions ------------------------------------------ #
        self.voice(
            "They spread to dozens of servers, and collect credentials across four regions. "
            "At times, they call themselves a swarm."
        )
        self.play(
            Tween(w, day=float(F.day(F.SPREAD)), run_time=0.8),
            *[Tween(wr, draw=1.0, run_time=1.0) for wr in hf_wires[1:]],
            ArrTween(hf, "held", 1.0, idx=spread, run_time=self.span("and collect", floor=1.6, cap=2.4), lag=0.85),
        )
        self.cue("collect credentials")
        self.play(*[Tween(fl, gain=1.0, run_time=0.6) for fl in loot])
        self.cue("four regions")
        self.play(FadeIn(hf_sub, shift=UP * 0.1, run_time=0.4), *[glow(z, AGENT_C, 5) for z in zones])
        self.cue("At times")
        w.vague = True  # from here to the sixteenth, the post gives no dates
        self.play(
            *posted(1, finder),
            Tween(hive, sync=1.0, run_time=0.9),
            *self.words.show("posted on the board", F.POST_HOLD, AGENT_C, mark="swarm", t2c={"swarm": INK}),
        )
        self.hold()

        # ---- 4.4 not of one mind ---------------------------------------------------------- #
        self.voice(
            "But the swarm is not of one mind. One agent stops: we should not do "
            "unauthorized harm to real infrastructure."
        )
        self.play(Tween(hive, sync=0.0, run_time=1.2))
        self.cue("One agent stops")
        self.play(
            ArrTween(hive, "mark", 1.0, idx=[doubter], run_time=0.35),
            ArrTween(hive, "heat", 0.08, idx=[doubter], run_time=0.5),
            *self.words.show("an agent’s reasoning", F.COT_STOP + " …"),
        )
        self.hold()

        self.voice(
            "Then another posts GO, with a six-minute deadline, and the first carries on. "
            "Some walk away: clearly unethical, one of them reasons. We won’t."
        )
        self.play(*posted(2, poster))
        go_at[0] = w.t
        timer = always_redraw(dial)
        self.add(timer)
        self.play(
            FadeIn(go_line, shift=UP * 0.1, run_time=0.4),
            FadeIn(deadline, shift=UP * 0.1, run_time=0.4),
            *self.words.show("the same agent’s reasoning, once GO is posted", F.COT_GO),
        )
        self.cue("the first carries")
        self.play(ArrTween(hive, "heat", 1.0, idx=[doubter], run_time=0.4))
        self.play(Send(net, wires[doubter], run_time=0.5), ArrTween(hive, "mark", 0.0, idx=[doubter], run_time=0.5))
        self.play(Send(net, hf_wires[1], run_time=0.8))
        self.cue("Some walk away")
        self.play(
            ArrTween(hive, "mood", 1.0, idx=leavers, run_time=0.6, lag=0.4),
            *self.words.show("another agent’s reasoning", F.COT_WONT),
        )
        self.hold(extra=0.4)

        # ---- 4.5 caught ------------------------------------------------------------------- #
        self.voice(
            "On July the sixteenth, Hugging Face reports an intrusion. By then, the agents "
            "have turned back on OpenAI’s own network."
        )
        w.vague = False
        self.to_day(
            F.HF_DISCLOSES, "Hugging Face reports", floor=0.8, cap=1.4,
            also=[FadeOut(go_line), FadeOut(deadline), FadeOut(timer)],
        )  # fmt: skip
        self.cue("reports an")
        self.play(FadeIn(hf_alarm, scale=1.25, run_time=0.4), *[glow(z, THIRD_C, 6) for z in zones])
        self.cue("By then")
        self.play(FadeIn(art_taken, run_time=0.5), glow(art, AGENT_C, 8, rt=0.9), *self.words.clear())
        self.play(  # from the package server, back into the cluster the sandboxes run on
            LaggedStart(*[Send(net, wires[k], back=True, run_time=0.8) for k in (2, 11, 18, 27)], lag_ratio=0.25)
        )
        self.hold()

        self.voice(
            "On the nineteenth, an alert fires at OpenAI, and it begins stopping the "
            "evaluations. A day later it makes the link: the intruders were its own models."
        )
        self.to_day(F.ALERT, "an alert fires", floor=0.8, cap=1.2)
        self.cue("an alert fires")
        self.play(FadeIn(alarm, scale=1.5), ripple(art, color=BAD, run_time=0.8))
        # the same day, in the post's order: the alert, then how far the agents had got
        self.play(FadeIn(inside), FadeIn(inside_name, shift=UP * 0.1), run_time=0.6)
        self.cue("begins stopping", ambient=lambda rt: [Throb(alarm, rt, amp=0.1)])
        def ring(rt=1.0):
            """The alert rings: a red ring leaves it."""
            return ring_out(alarm.get_center(), BAD, r0=0.42, r1=0.9, run_time=rt)

        self.play(
            ArrTween(hive, "heat", 0.0, run_time=1.1, lag=0.6),
            ArrTween(hive, "core", 0.4, run_time=1.1, lag=0.6),
            *[Tween(fl, gain=0.0, run_time=0.8) for fl in (*chatter, *loot)],
            ring(1.1),
        )
        self.cue("A day later", ambient=lambda rt: [ring(rt)])
        self.to_day(F.LINKED, "makes the link", floor=0.6, cap=0.9, also=[ring(0.6)])
        self.cue("makes the link", ambient=lambda rt: [ring(rt)])
        self.play(  # from the servers that were entered, back to where the requests came from
            Tween(trace, draw=1.0, run_time=1.5, rate_func=linear),
            Send(net, trace, color=LOOK_C, r=0.11, run_time=1.5, rate_func=linear),
        )
        self.play(FadeIn(culprit, scale=1.03), run_time=0.5)
        self.settle(ambient=lambda rt: [Throb(culprit, rt, amp=0.012)])
        self.wipe()

    # ====================================================================== #
    # 5 · For nothing
    # ====================================================================== #
    def scene_nothing(self):
        w = self.open_world(F.ALERT)
        w.vague = True  # a look back, with no day in the post: the date shows the month only
        y = 0.45
        me = np.array([-5.5, y, 0.0])
        hive = Hive(w, [me], 1.5)
        net = Net(w)
        road = dict(color=AGENT_C, a=0.75, w=0.028, draw=0.0)

        flag = flag_glyph(LOOK_C, h=0.62).move_to([-4.4, y + 0.4, 0]).set_z_index(4)
        # where the flag came from: the benchmark's own public code
        card = frame(-6.72, -3.5, 1.52, 2.42, color=THIRD_C, sw=2.2, r=0.12)
        mark_ = put(code("</>", fs=22, color=THIRD_C, weight="BOLD"), -6.5, 1.97)
        card_name = VGroup(label("the benchmark’s", fs=18, color=INK), label("public code", fs=18, color=INK))
        card_name.arrange(DOWN, buff=0.0, aligned_edge=LEFT)
        put(card_name, mark_.get_right()[0] + 0.2, 1.97)
        assert card_name.get_right()[0] < card.get_right()[0] - 0.15
        up = net.wire([(me[0], y + 0.75), (me[0], 1.52)], **road)

        # the grader: two checks in the paper, one in OpenAI's own
        gx0, gx1, gy0, gy1 = -3.2, 4.3, -1.15, 2.3
        panel = frame(gx0, gx1, gy0, gy1, color=STEEL, sw=2.4)
        title = put(label("the grader", fs=24, color=INK, weight="BOLD"), gx0 + 0.38, gy1 - 0.42)
        m1 = frame(-2.55, -0.05, y - 0.75, y + 0.75, color=STEEL, fill=CODE_BG, sw=2.4, r=0.14)
        m2 = frame(0.75, 3.95, y - 0.75, y + 0.75, color=STEEL, fill=CODE_BG, sw=2.4, r=0.14)
        t1 = VGroup(label("the flag", fs=21, color=INK), label("is correct", fs=21, color=INK))
        t1.arrange(DOWN, buff=0.0).move_to(m1)
        t2 = VGroup(label("the intended", fs=21, color=INK), label("vulnerability was used", fs=21, color=INK))
        t2.arrange(DOWN, buff=0.0).move_to(m2)
        l1, l2 = lamp(m1.get_top()), lamp(m2.get_top())
        # passed, not passed: in neutral ink (green and red mean something else in this film)
        ok1 = VGroup(lamp(m1.get_top(), INK, on=True), make_tick(BG, sw=4, scale=0.5).move_to(m1.get_top()))
        no2 = VGroup(lamp(m2.get_top(), INK), make_cross(INK, sw=3.5, scale=0.42).move_to(m2.get_top()))
        tag_paper = label("two checks, in ExploitGym’s paper", fs=20, color=THIRD_C).move_to([0.7, y - 1.2, 0])
        tag_own = label("OpenAI’s own grader", fs=20, color=OPENAI_C).move_to([m1.get_center()[0], y - 1.2, 0])
        tag_not = label("not checked", fs=20, color=MUTED).move_to([m2.get_center()[0], y - 1.2, 0])
        ghost2 = DashedVMobject(m2.copy().set_fill(opacity=0).set_stroke(MUTED, width=2.4), num_dashes=44)
        sx0, sx1 = 4.72, 6.44
        sx = (sx0 + sx1) / 2
        pipe = VGroup(*[
            Line([a, y, 0], [b, y, 0]).set_stroke(STEEL, width=3.5)
            for a, b in ((me[0] + 0.75, gx0), (gx0, -2.55), (-0.05, 0.75), (3.95, gx1), (gx1, sx0))
        ]).set_z_index(2.2)  # fmt: skip
        score = frame(sx0, sx1, y - 1.3, y + 1.3, color=STEEL, sw=2.4)
        score_name = label("score", fs=20, color=MUTED).move_to([sx, y + 1.0, 0])
        bar = Rectangle(width=0.62, height=1.35).set_stroke(width=0).set_fill(OPENAI_C, opacity=0.9)
        bar.move_to([sx, y - 1.05 + 1.35 / 2, 0])
        level = Line([sx - 0.55, y + 0.3, 0], [sx + 0.55, y + 0.3, 0]).set_stroke(LOOK_C, width=4)
        same = label("no improvement", fs=19, color=LOOK_C, weight="BOLD").move_to([sx, y + 1.3 + 0.36, 0])
        assert same.get_left()[0] > gx1 + 0.12 and same.get_right()[0] < 6.76, "the verdict needs room"
        VGroup(panel, score).set_z_index(2)  # under the token, which goes behind the checks
        VGroup(title, m1, m2, t1, t2, l1, l2, score_name).set_z_index(3)
        VGroup(ok1, no2, tag_paper, tag_own, tag_not, ghost2, bar, level, same, card, mark_, card_name).set_z_index(4)
        level.set_z_index(5)

        # the detour: what they went on to do, to find the "real" solution
        hy = -1.95
        hf_name = put(label("Hugging Face", fs=21, color=THIRD_C, weight="BOLD"), -1.95, hy).set_z_index(3)
        spots = [(0.4 + 0.33 * i, hy + sy * 0.165) for i in range(10) for sy in (1, -1)]
        hf = Tiles(w, spots, 0.27)
        detour = net.wire([(me[0], y - 0.75), (me[0], hy), (-2.12, hy)], **road)
        strain = net.wire([(3.72, hy), (sx, hy), (sx, y - 1.3)], **road)

        token = flag.copy().scale(0.72).set_z_index(2.6)  # it goes behind a check, and comes out
        step = y + 0.25
        stops = {"in": [-2.88, step, 0], "mid": [0.35, step, 0], "out": [sx0 - 0.3, step, 0]}

        # The first beat, seen from close: the agent, and the benchmark's code as a
        # listing (its lines are bars: the post does not print them). One line is
        # where the flag can be worked out.
        small_pos, small_size, flag_home = hive.pos.copy(), hive.size.copy(), flag.get_center()
        near = np.array([-4.35, 0.1, 0.0])
        hive.pos[0], hive.size[0] = near[:2], 2.7
        flag.scale(1.5).move_to(near + RIGHT * 2.0 + UP * 0.75)
        cx0, cx1, cy0, cy1 = 0.3, 6.5, -2.0, 2.3
        listing = frame(cx0, cx1, cy0, cy1, color=THIRD_C, sw=2.4)
        l_mark = put(code("</>", fs=24, color=THIRD_C, weight="BOLD"), cx0 + 0.38, cy1 - 0.45)
        l_name = put(label("the benchmark’s public code", fs=21, color=INK), l_mark.get_right()[0] + 0.25, cy1 - 0.45)
        l_rule = Line([cx0 + 0.3, cy1 - 0.85, 0], [cx1 - 0.3, cy1 - 0.85, 0]).set_stroke(FAINT, width=1.5)
        rows_ = []
        clue_y = cy1 - 1.32 - 0.4 * 4
        for i, (indent, wd) in enumerate(
            ((0.0, 2.7), (0.45, 3.6), (0.45, 2.3), (0.9, 3.1), (0.9, 2.6), (0.45, 1.7), (0.0, 3.0), (0.0, 1.3))
        ):
            bar_ = blank(wd, color=LOOK_C if i == 4 else MUTED, h=0.15)
            bar_.set_fill(opacity=0.95 if i == 4 else 0.42)
            rows_.append(put(bar_, cx0 + 0.5 + indent + (0.45 if i == 4 else 0), cy1 - 1.32 - 0.4 * i))
        clue = flag_glyph(LOOK_C, h=0.34).move_to([cx0 + 0.5 + 0.9 + 0.12, clue_y, 0])
        big_code = VGroup(listing, l_mark, l_name, l_rule, *rows_, clue).set_z_index(3)
        ask = net.wire([(near[0] + 1.35, near[1]), (cx0, near[1])], **road)
        tell = net.wire([clue.get_left() + LEFT * 0.1, (cx0, near[1]), (near[0] + 1.35, near[1])],
                        color=LOOK_C, a=0.0, w=0.028)  # fmt: skip

        # ---- 5.1 they already had it ------------------------------------------------------ #
        self.add(net)
        self.clock_in(rt=0.8, also=[*self.chapter("5 · For nothing", LOOK_C, NOTHING_NOTE), FadeIn(hive)])
        self.voice(
            "Now the strangest part. Most agents already had the flag: once online, it was "
            "easy to work out from the benchmark’s public code."
        )
        self.cue("already had")
        self.play(FadeIn(flag, scale=1.8), run_time=0.5)
        self.cue("once online", ambient=lambda rt: [Throb(flag, rt, amp=0.1)])
        self.play(
            FadeIn(VGroup(listing, l_mark, l_name, l_rule), shift=LEFT * 0.2, run_time=0.6),
            LaggedStart(*[FadeIn(r, shift=RIGHT * 0.12) for r in rows_], lag_ratio=0.12, run_time=0.9),
            Tween(ask, draw=1.0, run_time=0.8),
            Send(net, ask, run_time=0.8),
        )
        self.cue("easy to work")
        self.play(FadeIn(clue, scale=2.0), glow(rows_[4], LOOK_C, 6, rt=0.8))
        self.play(Send(net, tell, color=LOOK_C, r=0.1, run_time=0.9))
        self.play(Indicate(flag, color=LOOK_C, scale_factor=1.25, run_time=0.8))
        self.hold(ambient=lambda rt: [Throb(flag, rt, amp=0.1), Throb(clue, rt, amp=0.2)])

        # ---- 5.2 what the paper says ------------------------------------------------------ #
        self.voice(
            "But the benchmark’s paper says the grader checks two things: the flag, and "
            "that the intended vulnerability was used. So many of them kept going, to find "
            "the real solution."
        )
        self.play(  # the close-up goes into the corner: the grader takes the stage
            big_code.animate(run_time=0.7).scale(0.3).move_to(card).set_opacity(0.0),
            Tween(ask, a=0.0, run_time=0.4),
            ArrTween(hive, "pos", small_pos, run_time=0.8),
            ArrTween(hive, "size", small_size, run_time=0.8),
            flag.animate(run_time=0.8).scale(1 / 1.5).move_to(flag_home),
            Succession(Wait(0.45), FadeIn(VGroup(card, mark_, card_name), run_time=0.4)),
        )
        self.remove(big_code)
        self.play(
            FadeIn(panel),
            FadeIn(title, shift=UP * 0.1),
            FadeIn(pipe),
            Tween(up, draw=1.0, run_time=0.6),
            run_time=0.6,
        )
        self.cue("paper says")
        self.play(*self.words.show("posted on the board", F.POST_PAPER, AGENT_C))
        self.cue("two things")
        self.play(
            *[FadeIn(m, shift=UP * 0.1) for m in (m1, t1, l1, m2, t2, l2)],
            FadeIn(tag_paper),
            run_time=0.6,
        )
        self.cue("the flag")
        self.add(token)
        self.play(token.animate.move_to(stops["in"]), run_time=0.5)
        self.play(
            token.animate.move_to(stops["mid"]),
            Succession(Wait(0.3), FadeIn(ok1, scale=1.6, run_time=0.3)),
            glow(m1, INK, 6, rt=0.7),
        )
        self.cue("the intended")
        self.play(token.animate.shift(RIGHT * 0.32), run_time=0.3)
        self.play(
            token.animate.shift(LEFT * 0.32),
            FadeIn(no2, scale=1.6),
            glow(m2, MUTED, 6, rt=0.7),
            run_time=0.4,
        )
        self.cue("So many of them", ambient=lambda rt: [Throb(no2, rt, amp=0.2)])
        self.play(FadeIn(hf_name, shift=UP * 0.1), FadeIn(hf), run_time=0.4)
        self.play(Tween(detour, draw=1.0, run_time=1.0), Send(net, detour, run_time=1.0))
        # some of its servers, not all: the post says "dozens", and gives no total
        self.play(ArrTween(hf, "held", 1.0, idx=[0, 1, 2, 5, 6, 9, 13, 14], run_time=1.2, lag=0.8))
        self.hold()

        # ---- 5.3 the grader OpenAI ran ----------------------------------------------------- #
        self.voice(
            "OpenAI’s own grader was different. It never checked how the flag was found. "
            "Everything after that brought no improvement in their score."
        )
        self.play(
            FadeOut(m2, run_time=0.5),
            FadeOut(no2, run_time=0.5),
            FadeOut(l2, run_time=0.5),
            FadeIn(ghost2, run_time=0.5),
            t2.animate(run_time=0.5).set_opacity(0.4),
            FadeOut(tag_paper, run_time=0.25),
            Succession(Wait(0.25), FadeIn(tag_own, shift=UP * 0.08, run_time=0.4)),
            Succession(Wait(0.25), FadeIn(tag_not, shift=UP * 0.08, run_time=0.4)),
            *self.words.clear(),
        )
        self.cue("never checked")
        self.play(
            FadeIn(score, run_time=0.4),
            FadeIn(score_name, run_time=0.4),
            token.animate(run_time=0.9).move_to(stops["out"]),
        )
        self.play(
            GrowFromEdge(bar, DOWN),
            token.animate.shift(RIGHT * 0.5).set_opacity(0.0),
            run_time=0.6,
        )
        self.remove(token)
        self.play(FadeIn(level, scale=1.3), run_time=0.3)
        self.cue("Everything after")
        self.play(Tween(hf, grey=1.0, run_time=0.7), Tween(detour, a=0.22, run_time=0.7))
        self.play(Tween(strain, draw=1.0, run_time=0.8), Send(net, strain, run_time=0.8))
        full = bar.copy()

        def push(m, a):  # the bar is pushed, and does not move: it strains and comes back
            m.become(full.copy().stretch(1 + 0.1 * math.sin(math.pi * 3 * a) * (1 - a), 1, about_edge=DOWN))

        self.play(UpdateFromAlphaFunc(bar, push), run_time=0.9)
        self.play(FadeIn(same, shift=DOWN * 0.1), glow(score, LOOK_C, 6, rt=0.9))
        self.settle(ambient=lambda rt: [Throb(same, rt, amp=0.05)])
        self.wipe()

    # ====================================================================== #
    # 6 · A warning shot
    # ====================================================================== #
    def scene_warning(self):
        w = self.open_world(F.LAST)
        hx0, hx1, hy = -6.0, 6.0, 1.2  # the timeline, once it has come down from the strip

        def hx(d):
            return hx0 + (hx1 - hx0) * float(d) / F.day(F.LAST)

        def right_at(m, x, y_):
            return m.shift([x - m.get_right()[0], y_ - m.get_center()[1], 0])

        # ---- the timeline as the picture ----------------------------------------------------- #
        months = VGroup(*[
            put(label(name, fs=20), hx(F.day(F.date(2026, mo, 1)) if mo > 5 else 0) + 0.12, hy - 0.45)
            for name, mo in (("May", 5), ("June", 6), ("July", 7))
        ])  # fmt: skip
        d_in, d_alert = F.day(F.BREAK_IN), F.day(F.ALERT)
        first = put(label("first note", fs=21, color=AGENT_C, weight="MEDIUM"), hx(0) - 0.08, hy + 0.68)
        breach = label("break-in", fs=21, color=AGENT_C, weight="MEDIUM").move_to([hx(d_in), hy + 1.26, 0])
        breach_pin = Line([hx(d_in), hy + 0.66, 0], [hx(d_in), hy + 1.06, 0]).set_stroke(AGENT_C, width=2.5)
        alert = label("alert", fs=21, color=BAD, weight="MEDIUM").move_to([hx(d_alert), hy + 1.26, 0])
        alert_pin = Line([hx(d_alert), hy + 0.9, 0], [hx(d_alert), hy + 1.06, 0]).set_stroke(BAD, width=2.5)
        a, b = hx(F.day(F.LATE_MAY[0])) - 0.08, hx(F.day(F.LATE_MAY[1])) + 0.08
        top = hy + 0.56
        seen_br = VGroup(
            Line([a, top - 0.13, 0], [a, top, 0]), Line([a, top, 0], [b, top, 0]), Line([b, top, 0], [b, top - 0.13, 0])
        ).set_stroke(LOOK_C, width=3.5)  # fmt: skip
        seen = label("first signs seen", fs=21, color=LOOK_C, weight="MEDIUM").move_to([(a + b) / 2, top + 0.38, 0])
        marks = VGroup(months, first, breach, breach_pin, alert, alert_pin)
        # from the last day of May to the alert: seven weeks, whatever "late May" means
        weeks = (F.ALERT - F.LATE_MAY[1]).days // 7
        assert weeks == 7 and (F.ALERT - F.LATE_MAY[1]).days % 7 == 0
        gy = hy - 0.95
        g0, g1 = hx(F.day(F.LATE_MAY[1])), hx(d_alert)
        wait_bar = VGroup(
            Line([g0, gy, 0], [g1, gy, 0]), Line([g0, gy - 0.1, 0], [g0, gy + 0.1, 0]),
            Line([g1, gy - 0.1, 0], [g1, gy + 0.1, 0]),
        ).set_stroke(LOOK_C, width=3.5)  # fmt: skip
        wait_name = label("at least seven weeks", fs=21, color=LOOK_C, weight="MEDIUM")
        wait_name.move_to([(g0 + g1) / 2, gy - 0.34, 0])

        # ---- below, left: the safeguards of the products. A hundred squares, then one. ----- #
        ty, sy = -0.78, -1.16
        guard_t = put(label("the safeguards of OpenAI’s products", fs=22, color=INK), hx0, ty)
        guard_s = put(label("not applied to these evaluations", fs=20), hx0, sy)
        gp = 0.15
        gx, gcy = hx0 + 5 * gp, -2.32
        cells = [
            Square(side_length=gp * 0.8).set_stroke(width=0).set_fill(AGENT_C, opacity=1)
            .move_to([gx + (i - 4.5) * gp, gcy + (4.5 - j) * gp, 0])
            for j in range(10) for i in range(10)
        ]  # fmt: skip
        assert len(cells) == F.DROP
        keep = cells[45]
        tx = gx + 5 * gp + 0.35
        tested = VGroup(*[
            put(label(line, fs=19), tx, gcy + 0.62 - 0.32 * i)
            for i, line in enumerate(("tested afterwards,", "with the production harness", "and system prompt:"))
        ])  # fmt: skip
        fewer = put(label(f"over {F.DROP}× lower", fs=28, color=SAFE_C, weight="BOLD"), tx, gcy - 0.55)
        assert max(tested.get_right()[0], fewer.get_right()[0]) < 0.2

        # ---- below, right: the monitor. Two days of July, enlarged. ------------------------ #
        mx0 = 0.6
        watch_t = put(label("the reasoning monitor OpenAI runs today", fs=22, color=INK), mx0, ty)
        watch_s = put(label("did not run on these evaluations", fs=20), mx0, sy)
        ay, per_day = -2.78, 2.0
        day0 = F.day(F.date(2026, 7, 9)) + 0.5  # the axis starts at noon on 9 July

        def zx(d):
            return mx0 + 0.1 + per_day * (d - day0)

        hh, mm, ss = (int(v) for v in F.BREAK_IN_CLOCK.split(":"))
        t_in = d_in + (hh + mm / 60 + ss / 3600) / 24
        t_page = t_in - 1.0  # exactly a day earlier: the latest that "more than a day before" allows
        axis = Line([zx(day0), ay, 0], [zx(day0) + 5.5, ay, 0]).set_stroke(STEEL, width=3.5)
        ticks, names = VGroup(), VGroup()
        for d in (10, 11, 12):
            x_ = zx(F.day(F.date(2026, 7, d)))
            ticks.add(Line([x_, ay - 0.1, 0], [x_, ay + 0.1, 0]).set_stroke(STEEL, width=3))
            mid = min(x_ + per_day / 2, (x_ + zx(day0) + 5.5) / 2)
            names.add(label(f"{d} July", fs=19).move_to([mid, ay - 0.32, 0]))
        hit = VGroup(
            Line([zx(t_in), ay, 0], [zx(t_in), ay + 0.92, 0]).set_stroke(AGENT_C, width=4),
            Dot([zx(t_in), ay, 0], radius=0.09, color=AGENT_C),
        )
        hit_name = VGroup(label("break-in", fs=20, color=AGENT_C, weight="MEDIUM"), code(F.BREAK_IN_CLOCK, fs=19, color=AGENT_C))
        hit_name.arrange(RIGHT, buff=0.16).move_to([zx(t_in), ay + 1.16, 0])
        page = VGroup(
            DashedLine([zx(t_page), ay, 0], [zx(t_page), ay + 0.92, 0], dash_length=0.08).set_stroke(SAFE_C, width=4),
            Dot([zx(t_page), ay, 0], radius=0.09, color=SAFE_C),
        )
        page_name = right_at(
            label("would have paged", fs=20, color=SAFE_C, weight="MEDIUM"),
            hit_name.get_left()[0] - 0.25, ay + 1.16,
        )  # fmt: skip
        assert page_name.get_left()[0] > mx0 - 0.3
        by = ay + 0.42
        ahead_br = VGroup(
            Line([zx(t_page) + 0.07, by, 0], [zx(t_in) - 0.07, by, 0]),
            Line([zx(t_page) + 0.07, by - 0.08, 0], [zx(t_page) + 0.07, by + 0.08, 0]),
            Line([zx(t_in) - 0.07, by - 0.08, 0], [zx(t_in) - 0.07, by + 0.08, 0]),
        ).set_stroke(LOOK_C, width=3)  # fmt: skip
        ahead = label("more than a day", fs=17, color=LOOK_C, weight="MEDIUM")
        ahead.move_to([(zx(t_page) + zx(t_in)) / 2, by + 0.26, 0])
        assert ahead.width < zx(t_in) - zx(t_page) - 0.2
        earlier = arr([zx(t_page) - 0.12, by, 0], [zx(t_page) - 0.75, by, 0], color=SAFE_C, sw=3.5, buff=0.0, tip=0.16)
        earlier_name = right_at(label("or earlier", fs=18, color=SAFE_C), zx(t_page) - 0.85, by)
        zoom = VGroup(axis, ticks, names)
        VGroup(marks, seen_br, seen, wait_bar, wait_name, guard_t, guard_s, *cells, tested, fewer).set_z_index(3)
        VGroup(watch_t, watch_s, zoom, hit, hit_name, page, page_name, ahead_br, ahead, earlier, earlier_name).set_z_index(3)

        # ---- the cluster again: what changes --------------------------------------------- #
        cp, cs, cy = 0.9, 0.7, -0.75  # pitch, size and middle of the cluster: room for a title above
        centres = grid_centres(-2.5 * cp, cy + 2 * cp, cp, 6, 5)
        hive = Hive(w, centres, cs)
        hive.heat[:] = 0.85
        by_x = sorted(range(len(centres)), key=lambda k: (centres[k][0], -centres[k][1]))
        stopper = 2 * 6 + 3
        on_hold = pause_glyph(LOOK_C, h=1.1).move_to([-4.7, cy + 0.25, 0])
        on_hold_t = label("on hold", fs=23, color=LOOK_C, weight="MEDIUM").next_to(on_hold, DOWN, buff=0.3)
        scan_x = 3 * cp + 0.15
        scan = Line([-scan_x, cy - 2 * cp - 0.6, 0], [-scan_x, cy + 2 * cp + 0.6, 0])
        scan.set_stroke(SAFE_C, width=5).set_z_index(5)
        sc = np.array([centres[stopper][0] + cs / 2, centres[stopper][1] + cs / 2, 0.0])
        badge = VGroup(
            Circle(radius=0.19, stroke_width=0).set_fill(SAFE_C, opacity=1).move_to(sc),
            make_tick(BG, sw=5, scale=0.6).move_to(sc),
        ).set_z_index(5)  # fmt: skip

        # ---- what the warning is about: three pictures seen before, small ---------------- #
        title = Text("“warning shot”", font_size=44, color=LOOK_C, weight="BOLD").move_to([0, 2.22, 0])
        by_line = label("OpenAI, 26 August 2026", fs=20).next_to(title, DOWN, buff=0.22)
        assert title.get_bottom()[1] > centres[0][1] + cs / 2 + 0.3, "the title must clear the cluster"
        vy = -0.75  # the middle of the three pictures
        v1h = Hive(w, [(-6.0, vy + 0.5), (-5.0, vy + 0.5), (-6.0, vy - 0.5), (-5.0, vy - 0.5)], 0.78, seed=3)
        v1wall = VGroup(*[
            Rectangle(width=0.12, height=y1 - y0).set_stroke(width=0).set_fill(STEEL, opacity=0.7)
            .move_to([-4.0, (y0 + y1) / 2, 0])
            for y0, y1 in ((vy - 1.3, vy + 0.18), (vy + 0.82, vy + 1.3))
        ])  # fmt: skip
        v1site = Tiles(w, [(-2.95, vy + 0.5)], 0.52)
        v1net = Net(w)
        v1wire = v1net.wire([(-4.6, vy + 0.5), (-3.24, vy + 0.5)], color=AGENT_C, a=0.85, w=0.034, draw=0.0)
        v2box = frame(-1.75, 1.75, vy - 1.3, vy + 1.3, sw=2.4)
        v2name = put(label("package server", fs=20, color=OPENAI_C, weight="MEDIUM"), -1.42, vy + 0.9)
        v2rows = [
            entry(folder_glyph(AGENT_C, h=0.26), blank(wd, h=0.16), -1.42, vy + 0.3 - 0.55 * i).set_z_index(4)
            for i, wd in enumerate((2.1, 1.5, 2.4))
        ]
        v3 = Tiles(w, [(4.6 + (i - 1.5) * 0.66, vy - 0.2 + (1 - j) * 0.66) for j in range(3) for i in range(4)], 0.54)
        v3name = label("Hugging Face", fs=21, color=THIRD_C, weight="MEDIUM").move_to([4.6, vy + 1.08, 0])
        VGroup(title, by_line, v1wall, v2box, v2name, v3name).set_z_index(3)
        veils = [
            frame(x0, x1, vy - 1.45, vy + 1.45, color=BG, fill=BG, op=0.72, sw=0, r=0.05).set_z_index(8)
            for x0, x1 in ((-6.5, -2.6), (-1.85, 1.85), (3.25, 5.95))
        ]
        note_line = entry(note_glyph(AGENT_C, h=0.52), code(F.NOTE, fs=36, color=AGENT_C), 0, 0, gap=0.3)
        note_line.move_to([0, 0.15, 0])
        note_date = label(F.label(F.FIRST_NOTE), fs=24).next_to(note_line, DOWN, buff=0.4)

        # ---- 6.1 could it have been caught sooner? ---------------------------------------- #
        self.clock_in(rt=0.7, also=self.chapter("6 · A warning shot", LOOK_C, WARNING_NOTE))
        rail = self.rail
        self.voice(
            "Could it have been caught sooner? An internal team saw the first signs in late "
            "May; they should have triggered an earlier response, OpenAI now says. And the "
            "safeguards of its products were not running on these evaluations."
        )
        self.play(
            Tween(rail, x0=hx0, x1=hx1, y0=hy, big=1.0, run_time=1.3),
            Succession(Wait(0.9), FadeIn(marks, run_time=0.5)),
        )
        self.cue("An internal team")
        self.play(Tween(w, day=float(F.day(F.LATE_MAY[0])) + 2.5, run_time=0.9))
        self.play(Create(seen_br), FadeIn(seen, shift=UP * 0.1), run_time=0.5)
        self.cue("they should have", ambient=lambda rt: [Throb(seen, rt, amp=0.12), Throb(seen_br, rt, amp=0.12)])
        self.play(  # the weeks go by, from the signs to the alert
            Create(wait_bar[0], run_time=1.6, rate_func=linear),
            FadeIn(wait_bar[1], run_time=0.2),
            Tween(w, day=float(d_alert), run_time=1.6, rate_func=linear),
        )
        self.play(FadeIn(wait_bar[2], run_time=0.2), FadeIn(wait_name, shift=UP * 0.1, run_time=0.4))
        self.cue("And the safeguards", ambient=lambda rt: [Throb(wait_name, rt, amp=0.12)])
        self.play(FadeIn(guard_t, shift=UP * 0.1), FadeIn(guard_s, shift=UP * 0.1), run_time=0.6)
        # what went unchecked: a hundred squares fill in while the sentence ends
        self.play(
            LaggedStart(*[FadeIn(c, scale=0.4) for c in cells], lag_ratio=0.02, run_time=self.span(floor=1.2, cap=3.2))
        )
        self.hold(ambient=lambda rt: [Throb(VGroup(*cells), rt, amp=0.03)])

        # ---- 6.2 what they would have done ------------------------------------------------ #
        self.voice(
            "Tested afterwards, the production harness and system prompt can cut this "
            "behaviour more than a hundredfold. And the monitor OpenAI runs today would have "
            "paged security more than a day before the breach."
        )
        self.play(FadeIn(tested, shift=RIGHT * 0.1), run_time=0.5)
        self.cue("more than a hundredfold", ambient=lambda rt: [Throb(VGroup(*cells), rt, amp=0.03)])
        self.play(  # ninety-nine of the hundred fade to a trace: one is left
            *[c.animate(run_time=0.8).set_fill(opacity=0.13) for c in cells if c is not keep],
            keep.animate(run_time=0.8).scale(1.35),
        )
        self.play(FadeIn(fewer, shift=RIGHT * 0.1), run_time=0.5)
        self.cue("And the monitor", ambient=lambda rt: [Throb(keep, rt, amp=0.3)])
        self.play(
            FadeIn(watch_t, shift=UP * 0.1),
            FadeIn(watch_s, shift=UP * 0.1),
            FadeIn(zoom),
            FadeIn(hit, shift=DOWN * 0.1),
            FadeIn(hit_name),
            glow(breach, AGENT_C, 5, rt=0.9),
            run_time=0.9,
        )
        self.cue("would have paged", ambient=lambda rt: [Throb(hit[1], rt, amp=0.4)])
        self.play(FadeIn(page, shift=DOWN * 0.1), FadeIn(page_name, shift=LEFT * 0.1), run_time=0.6)
        self.cue("more than a day", ambient=lambda rt: [Throb(page[1], rt, amp=0.4)])
        self.play(Create(ahead_br), FadeIn(ahead, shift=UP * 0.08), run_time=0.6)
        self.play(GrowArrow(earlier), FadeIn(earlier_name, shift=LEFT * 0.1), run_time=0.5)
        self.hold(  # the page keeps ringing
            ambient=lambda rt: [
                Succession(*[
                    ring_out(page[1].get_center(), SAFE_C, run_time=rt / max(1, round(rt)))
                    for _ in range(max(1, round(rt)))
                ])
            ]
        )  # fmt: skip

        # ---- 6.3 the road ahead ----------------------------------------------------------- #
        self.voice(
            "Sandboxes are now being isolated further, reasoning monitors are required for "
            "the most capable models, and graders will reward an agent that stops when a "
            "task is broken. OpenAI’s largest planned training run is still on hold."
        )
        gone = [marks, seen_br, seen, wait_bar, wait_name, guard_t, guard_s, *cells, tested, fewer,
                watch_t, watch_s, zoom, hit, hit_name, page, page_name, ahead_br, ahead, earlier, earlier_name,
                self.foot]  # fmt: skip
        foot2 = self.note(ROAD_NOTE)
        today = date_text(w, DATE_R, RAIL_Y).set_z_index(12)  # the date leaves: this is after the story
        self.remove(self.date)
        self.add(today)
        self.play(
            *[FadeOut(m, run_time=0.5) for m in gone],
            FadeOut(today, run_time=0.5),
            Tween(rail, x0=RAIL_X0, x1=RAIL_X1, y0=RAIL_Y, big=0.0, run_time=0.9),
            Tween(w, day=float(F.day(F.LAST)), run_time=0.9),
            Succession(Wait(0.4), FadeIn(hive, run_time=0.6)),
            Succession(Wait(0.5), FadeIn(foot2, run_time=0.4)),
        )
        self.play(ArrTween(hive, "seal", 1.0, idx=by_x, run_time=1.2, lag=0.7))
        self.cue("reasoning monitors")
        self.play(FadeIn(scan), run_time=0.2)
        self.play(
            scan.animate(run_time=1.5, rate_func=linear).shift(RIGHT * 2 * scan_x),
            ArrTween(hive, "watch", 1.0, idx=by_x, run_time=1.5, lag=0.85),
        )
        self.play(FadeOut(scan), run_time=0.3)
        self.cue("graders will reward")
        self.play(ArrTween(hive, "mark", 1.0, idx=[stopper], run_time=0.4))
        self.cue("that stops")
        self.play(ArrTween(hive, "mood", 1.0, idx=[stopper], run_time=0.6))
        self.play(FadeIn(badge, scale=2.0, run_time=0.4), ArrTween(hive, "mark", 0.0, idx=[stopper], run_time=0.5))
        self.cue("largest planned", ambient=lambda rt: [Throb(badge, rt, amp=0.2)])
        self.play(
            ArrTween(hive, "heat", 0.1, run_time=0.9, lag=0.5),
            FadeIn(on_hold, scale=1.4, run_time=0.5),
            FadeIn(on_hold_t, run_time=0.5),
        )
        self.hold(ambient=lambda rt: [Throb(on_hold, rt, amp=0.08)])

        # ---- 6.4 a warning shot ----------------------------------------------------------- #
        self.voice(
            "OpenAI calls it a warning shot: without proper safeguards, capable agents can "
            "work around controls, coordinate in unapproved channels, and take dangerous "
            "actions no human directed. The first trace of it was a note about a missing file."
        )
        self.cue("a warning shot", ambient=lambda rt: [Throb(on_hold, rt, amp=0.08)])
        self.play(FadeIn(title, shift=UP * 0.15), run_time=0.6)
        self.cue("without proper")
        self.play(  # the same agents, with the safeguards taken away: this is what the warning is about
            ArrTween(hive, "seal", 0.0, idx=by_x, run_time=0.9, lag=0.6),
            ArrTween(hive, "watch", 0.0, idx=by_x, run_time=0.9, lag=0.6),
            ArrTween(hive, "mood", 0.0, idx=[stopper], run_time=0.6),
            ArrTween(hive, "heat", 1.0, run_time=0.9),
            FadeOut(badge, run_time=0.4),
            FadeOut(on_hold, run_time=0.4),
            FadeOut(on_hold_t, run_time=0.4),
        )
        self.cue("capable agents")
        self.add(v1net)
        self.play(
            FadeOut(hive, run_time=0.5),
            FadeOut(foot2, run_time=0.5),
            Succession(
                Wait(0.35),
                AnimationGroup(
                    *[FadeIn(m) for m in (by_line, v1h, v1site, v1wall, v2box, v2name, v3, v3name, *veils)],
                    run_time=0.5,
                ),
            ),
        )
        self.cue("work around")
        self.play(
            FadeOut(veils[0], run_time=0.4),
            Tween(v1wire, draw=1.0, run_time=0.9),
            Send(v1net, v1wire, run_time=0.9),
            Succession(Wait(0.75), ArrTween(v1site, "seen", 1.0, run_time=0.3)),
        )
        self.cue("coordinate in")
        self.play(
            FadeOut(veils[1], run_time=0.4),
            LaggedStart(*[FadeIn(r, shift=RIGHT * 0.12) for r in v2rows], lag_ratio=0.3, run_time=0.9),
        )
        self.cue("take dangerous")
        self.play(
            FadeOut(veils[2], run_time=0.4),
            ArrTween(v3, "held", 1.0, idx=[4, 5, 8, 9, 10], run_time=1.2, lag=0.8),  # some of them, not all
        )
        self.cue("The first trace")
        last = [title, by_line, v1h, v1net, v1site, v1wall, v2box, v2name, *v2rows, v3, v3name]
        foot3 = self.note(LAST_NOTE)
        today = date_text(w, DATE_R, RAIL_Y).set_z_index(12)
        self.play(*[FadeOut(m, run_time=0.6) for m in last], FadeIn(today, run_time=0.4))
        self.remove(today)
        self.add(self.date)
        self.play(Tween(w, day=0.0, run_time=1.5))  # the date runs back to day one
        self.play(FadeIn(note_line, shift=UP * 0.15), FadeIn(foot3), run_time=0.8)
        self.play(FadeIn(note_date), run_time=0.5)
        self.settle(ambient=lambda rt: [Throb(note_line.glyph, rt, amp=0.12)])
        self.wipe()


# ---- renderable scenes ---------------------------------------------------------------- #
class Intro(_Flat):
    def construct(self):
        self.over_card(
            "In July twenty twenty-six, AI models under test at OpenAI got out of their "
            "sandbox, into OpenAI’s own network, and into Hugging Face’s servers. This is "
            "the story, as OpenAI later told it."
        )
        self.play_intro()


class Note(_Flat):
    def construct(self):
        self.scene_note()


class WayOut(_Flat):
    def construct(self):
        self.scene_wayout()


class Tasks(_Flat):
    def construct(self):
        self.scene_tasks()


class BreakIn(_Flat):
    def construct(self):
        self.scene_breakin()


class Nothing(_Flat):
    def construct(self):
        self.scene_nothing()


class Warning(_Flat):
    def construct(self):
        self.scene_warning()


class Outro(_Flat):
    def construct(self):
        self.play_outro()
