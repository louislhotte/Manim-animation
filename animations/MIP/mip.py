"""Mixed-Integer Programming: how a solver finds the best plan, and proves it.

A film made to be narrated (``tell`` / ``cue``): one short caption per beat, the
picture changes on the narrator's words, ``tools/voiceover.py`` writes the script.

STORYBOARD

    scene      question it answers             hero visual (fills the frame)                    what moves                                         takeaway caption
    1 night    what is the problem?            Paris, tilted, real streets (3D): 104 couriers,   couriers and orders appear; random assignments     Who delivers what, and in which
               [3D]                            403 orders                                        flicker; the camera dives to one courier           sequence?
    2 hour     why not try everything?         Lea's corner of the Marais, her 8 orders, and     a course is ridden on the streets; every           With twenty orders, trying them
                                               the table of fees and delivery windows            sequence is tried; the count explodes with n       all takes 200,000 years.
    3 model    how do you state it?            the same map and the real gurobipy model, line    each line lights its picture: 64 possible rides,   A mixed-integer program. One
               [3D]                            by line; then time as height                      fees, rules; the map tilts, windows rise, the      call solves it.
                                                                                                 course climbs through them as a thread
    4 relax    how can it know without         the 64 rides as dimmable arcs on the map; a       impossible rides vanish (presolve); a switch       Its value is a ceiling: no real
               trying?                         switch that becomes a dimmer; a bound axis        becomes a dimmer; one ride at 0.52, one at 0.76,   course can earn more.
                                                                                                 then the whole fractional plan; half a fee
    5 branch   how does it close in?           the real search tree of Lea's hour, the map of    the tree grows node by node; dead ends, cuts,      Floor and ceiling meet: 24.40
                                               the node being solved, floor and ceiling          real courses; the two bounds close                 euros, proven optimal.
    6 solver   what does Gurobi add, and       Lea's map and the bound axis (a cut, a quick      a derived rule drops the ceiling; guesses raise    Gap closed: proven optimal.
               how do you read it?             guess); Gurobi's real log; then one               the floor; log lines print, columns light up;
                                               arrondissement, its plan and its two bounds       129 nodes become 1; the 3.4 s search replays in
                                               against the clock                                 real time
    7 city     and at city scale?              Paris again (3D): twenty models, the couriers     zones turn green as they are solved; the hour      Describe the plan you want. The
               [3D]                            riding their optimal courses                      is ridden; the plan lifts into threads of time     solver searches, and proves.

Persistent motif: the real map of Paris and the *course* on it (a gold line on real
streets). Colour is a language: gold = a real plan, the best so far (the floor);
blue = the relaxed problem (fractional rides, the ceiling); red = removed or cut;
green = delivered, proven; mint = a time window.

Real data, baked by ``generate_assets.py`` into ``assets/`` (see README.md):
streets, ride times and restaurants from OpenStreetMap; every number on screen
computed by a real run (Gurobi 14, HiGHS, our own branch and bound, brute force)
and asserted. Orders, fees and couriers are invented (seeded).

Scenes render alone (``./render.sh hour --quick --check``) or stitched
(``./render.sh``). Pacing: ``MIP_WPS`` (narrator's words per second), ``MIP_QUICK``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from manimx import *

from kit import *  # noqa: F403
from stage import Guess, Orders, Swarm


class _Common(NarratedMixin):
    """What the flat and the 3D scenes share."""

    pace = Pace.from_env("MIP", read=2.6, delay=1.0, anim_slow=1.0, end_hold=2.0)
    TITLE = "Mixed-Integer Programming"
    SUBTITLE = "How a solver finds the best plan, and proves it"
    TAGLINE = "what happens inside a solver like Gurobi"
    RECAP = "Relax, branch, bound, until the gap is zero."
    TRACE_ENV = "MIP_TRACE"
    WPS = float(os.environ.get("MIP_WPS", 2.3))  # the narrator: 138 words a minute
    VO_PAD = 1.1

    def intro_emblem(self):
        """A courier, an order, a course: the film's motif, at the end of the title rule."""
        a, b, c = (
            np.array([0.0, 0.0, 0]),
            np.array([0.62, 0.3, 0]),
            np.array([1.28, 0.02, 0]),
        )
        path = VMobject().set_points_as_corners(
            [a, [0.3, 0.0, 0], [0.3, 0.3, 0], b, [0.95, 0.3, 0], [0.95, 0.02, 0], c]
        )
        path.set_stroke(PLAN_C, width=3.5)
        g = VGroup(
            path,
            courier_marker(a, r=0.085),
            resto_marker(b, s=0.15),
            home_marker(c, r=0.07),
        )
        g.scale(1.15 / g.width)
        # The card centres this group on the rule's end, and this title's rule ends
        # 0.9 from the frame: the invisible pad keeps the course inside the frame.
        pad = Rectangle(width=0.21, height=0.1, stroke_opacity=0, fill_opacity=0)
        return VGroup(g, pad.next_to(g, RIGHT, buff=0))

    def header(self, label, color=GOLD):
        h = super().header(label, color)
        h.set_z_index(12)  # over the bands that keep it readable on a map
        return h


class _Flat(_Common, Scene):
    """A flat scene. The map, when there is one, is painted by the GPU."""

    def __init__(self, **kw):
        kw.setdefault("camera_class", PainterCamera)
        super().__init__(**kw)

    def desk(self):
        """Lea's corner of Paris, full frame, with the bands and the HUD column."""
        self.DESK = Desk()
        plane = self.DESK.plane()
        col = hud_column().set_z_index(8)
        bands = VGroup(band(-4.1, -2.5), band(2.3, 4.1, top=True, x1=0.2)).set_z_index(
            -20
        )
        self.add(plane, bands, col)
        self.add(
            self.note(
                "Map data © OpenStreetMap contributors. Orders, fees and couriers are invented."
            )
        )
        return plane

    # ====================================================================== #
    # 2 · One courier, one hour
    # ====================================================================== #
    def scene_hour(self):
        plane = self.desk()
        stops = Stops(plane).set_z_index(4)
        stops.labels.set_z_index(6)
        table = OrderTable().set_z_index(10)
        table.move_to([Desk.COL_MID + 0.12, 0.56, 0])
        col_x = table.get_left()[0]
        self.header("2 · One courier, one hour", GOLD)

        # ---- 2.1 the cast ------------------------------------------------------ #
        vo = (
            "This is Léa. She has one hour left, and eight orders around her. Each "
            "pays a fee, and each can only be delivered inside its own window: after "
            "the meal is ready, before the customer's deadline."
        )
        self.play(
            self.tell("Léa has one hour, and eight orders around her.", vo),
            FadeIn(stops.lea, scale=0.4),
            FadeIn(stops.who, shift=UP * 0.1),
            run_time=0.9,
        )
        self.cue("eight orders")
        self.play(
            FadeIn(table.heads[0]),
            LaggedStart(
                *[
                    AnimationGroup(
                        FadeIn(stops.of[j], scale=0.8),
                        FadeIn(stops.dish[j]),
                        FadeIn(table.label[j], shift=RIGHT * 0.15),
                        FadeIn(table.lane[j]),
                    )
                    for j in NAMES
                ],
                lag_ratio=0.45,
            ),
            run_time=2.6,
        )
        self.cue("pays a fee")
        self.play(
            FadeIn(table.heads[1]),
            LaggedStart(
                *[
                    AnimationGroup(
                        FadeIn(stops.fee[j], scale=1.25),
                        FadeIn(table.fee[j], scale=1.25),
                    )
                    for j in NAMES
                ],
                lag_ratio=0.12,
            ),
            run_time=1.3,
        )
        self.cue("its own window")
        self.play(
            FadeIn(table.heads[2]),
            FadeIn(table.axis),
            LaggedStart(
                *[GrowFromEdge(table.bar[j], LEFT) for j in NAMES], lag_ratio=0.12
            ),
            run_time=1.4,
        )

        def ends(side):
            g = VGroup()
            for j in NAMES:
                b = table.bar[j]
                x = b.get_left()[0] if side == "L" else b.get_right()[0]
                y = b.get_center()[1]
                g.add(
                    Line([x, y - 0.19, 0], [x, y + 0.19, 0]).set_stroke(INK, width=3.5)
                )
            return g.set_z_index(11)

        for phrase, side in (("after the meal", "L"), ("before the customer", "R")):
            self.cue(phrase)
            marks = ends(side)
            self.play(FadeIn(marks, run_time=0.25))
            self.play(FadeOut(marks, run_time=0.7))
        self.hold()

        # ---- 2.2 a course; what instinct gets ------------------------------------ #
        vo = (
            "She cannot deliver them all. A course is a choice: which orders, in which "
            "sequence. Her instinct: take the best-paid order that still fits, then "
            "the next. That course earns eleven euros ninety."
        )
        trial = ["kebab", "pasta", "pad thai"]
        assert any(c["seq"] == trial for c in HERO["brute"]["sample"])
        greedy = HERO["greedy"]["pay"]
        assert greedy["seq"] == ["pad thai", "noodles"] and greedy["obj"] == 11.9
        self.play(self.tell("A course: some of the orders, in a sequence.", vo))
        self.cue("A course is")
        c1 = course_mob(plane, trial, color=TRY_C, width=3.6, glow=False).set_z_index(2)
        b1 = table.badges(trial, TRY_C).set_z_index(11)
        self.play(
            Create(c1.core, rate_func=linear),
            *table.focus(trial),
            LaggedStart(*[FadeIn(b, scale=0.5) for b in b1], lag_ratio=0.4),
            run_time=1.8,
        )
        self.cue("Her instinct")
        c2 = course_mob(plane, greedy["seq"], color=MEH_C, width=4.6).set_z_index(2)
        b2 = table.badges(greedy["seq"], MEH_C).set_z_index(11)
        self.play(FadeOut(c1), FadeOut(b1), *table.focus(None), run_time=0.45)
        self.cue("best-paid")
        top = max(NAMES, key=lambda j: ORDERS[j]["pay"])
        assert top == greedy["seq"][0]
        ring = SurroundingRectangle(
            table.fee[top].body, color=MEH_C, buff=0.07, corner_radius=0.07
        )
        ring.set_stroke(width=2.5).set_z_index(11)
        self.play(Create(ring), run_time=0.5)
        self.play(
            FadeOut(ring),
            FadeIn(c2[0]),
            Create(c2.core, rate_func=linear),
            *table.focus(greedy["seq"]),
            LaggedStart(*[FadeIn(b, scale=0.5) for b in b2], lag_ratio=0.5),
            run_time=1.8,
        )
        ride2 = rider(c2.core, period=5.0, color=MEH_C).set_z_index(3)
        self.add(ride2)
        self.cue("That course earns")
        r_inst = Readout(
            "instinct", euro(greedy["obj"]), color=MEH_C, at=(col_x, -2.38)
        ).set_z_index(10)
        self.play(FadeIn(r_inst, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ---- 2.3 try them all ------------------------------------------------------ #
        vo = (
            "Is there better? With eight orders, a computer can try every sequence: "
            "one hundred and nine thousand six hundred of them. The best one earns "
            "twenty-four euros forty. Twice as much."
        )
        total = HERO["brute"]["sequences"]
        assert total == 109_600 and HERO["brute"]["obj"] == 24.4
        assert 2 * greedy["obj"] <= HERO["brute"]["obj"]
        self.play(
            self.tell("Trying every sequence finds the best course: 24.40 euros.", vo),
            FadeOut(c2),
            FadeOut(ride2),
            FadeOut(b2),
            *table.focus(None),
            run_time=0.6,
        )
        self.cue("try every sequence")
        sample = HERO["brute"]["sample"]
        k, n = ValueTracker(0), ValueTracker(0)
        flick = always_redraw(
            lambda: course_mob(
                plane, sample[min(int(k.get_value()), len(sample) - 1)]["seq"],
                color=TRY_C, width=3.0, glow=False,
            ).set_z_index(2)
        )  # fmt: skip
        r_try = Readout(
            "sequences tried", f"{total:,}", at=(col_x + 2.05, -2.38)
        ).set_z_index(10)
        count = always_redraw(
            lambda: r_try.fresh(f"{n.get_value():,.0f}").set_z_index(10)
        )
        self.play(FadeIn(r_try.lab), run_time=0.3)
        self.add(flick, count)
        self.play(
            k.animate.set_value(len(sample) - 0.01),
            n.animate.set_value(total),
            run_time=3.6,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.remove(flick)
        self.cue("The best one")
        best = course_mob(plane, BEST).set_z_index(2)
        bb = table.badges(BEST).set_z_index(11)
        self.play(
            FadeIn(best[0]),
            Create(best.core, rate_func=linear),
            *table.focus(BEST),
            LaggedStart(*[FadeIn(b, scale=0.5) for b in bb], lag_ratio=0.5),
            run_time=2.4,
        )
        self.add(rider(best.core, period=9.0, color=INK).set_z_index(3))
        r_best = Readout(
            "best course",
            euro(HERO["brute"]["obj"]),
            color=PLAN_C,
            at=(col_x + 4.55, -2.38),
        )
        r_best.set_z_index(10)
        self.play(FadeIn(r_best, shift=UP * 0.1), run_time=0.5)
        self.cue("Twice")
        self.play(
            Indicate(r_best.val, color=PLAN_C, scale_factor=1.12),
            Indicate(r_inst.val, color=MEH_C, scale_factor=1.12),
            run_time=0.9,
        )
        self.hold()

        # ---- 2.4 it does not scale -------------------------------------------------- #
        vo = (
            "But this does not scale. With twenty orders, there are six billion "
            "billion sequences: at a million per second, two hundred thousand years."
        )
        per_s = 1e6
        years = sequences(20) / per_s / (365.25 * 86400)
        assert 6e18 < sequences(20) < 7e18 and 200_000 < years < 220_000
        self.play(
            self.tell("With twenty orders, trying them all takes 200,000 years.", vo),
            FadeOut(table),
            FadeOut(bb),
            FadeOut(count),
            FadeOut(r_try.lab),
            FadeOut(r_inst),
            FadeOut(r_best),
            run_time=0.6,
        )
        t = ValueTracker(8)

        def n_now():
            return int(round(t.get_value()))

        cx = Desk.COL_MID
        lab_n = txt("orders", fs=18, color=MUTED).move_to([cx, 1.95, 0]).set_z_index(10)
        lab_s = (
            txt("sequences to try", fs=18, color=MUTED)
            .move_to([cx, 0.25, 0])
            .set_z_index(10)
        )
        lab_t = (
            txt("at a million per second", fs=18, color=MUTED)
            .move_to([cx, -1.25, 0])
            .set_z_index(10)
        )
        num_n = always_redraw(
            lambda: (
                txt(str(n_now()), fs=64, color=INK, weight="BOLD")
                .move_to([cx, 1.25, 0])
                .set_z_index(10)
            )
        )
        num_s = always_redraw(
            lambda: clamp_width(
                txt(f"{sequences(n_now()):,}", fs=30, color=INK, font=MONO, weight="BOLD"), 6.2
            ).move_to([cx, -0.3, 0]).set_z_index(10)
        )  # fmt: skip
        num_t = always_redraw(
            lambda: (
                txt(
                    how_long(sequences(n_now()) / per_s),
                    fs=34,
                    color=MEH_C,
                    weight="BOLD",
                )
                .move_to([cx, -1.85, 0])
                .set_z_index(10)
            )
        )
        self.play(FadeIn(lab_n), FadeIn(lab_s), FadeIn(lab_t), run_time=0.4)
        self.add(num_n, num_s, num_t)
        self.cue("twenty orders")
        self.play(t.animate.set_value(20), run_time=3.4, rate_func=linear)
        self.cue("at a million")
        self.play(ripple(num_t, color=MEH_C, buff=0.16), run_time=0.9)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 4 · Allow fractions
    # ====================================================================== #
    def scene_relax(self):
        plane = self.desk()
        stops = Stops(plane).set_z_index(4)
        # the dishes and Léa, not the fees: this scene is about rides and their
        # values, and the map has to leave room for them
        names = VGroup(stops.who, *stops.dish.values()).set_z_index(6)
        rides = RideSet(plane).set_z_index(1)
        rides.hot = ManimColor(WHITE)  # here, "hot" is the one ride being talked about
        self.add(rides, stops, names)
        self.header("4 · Allow fractions", SKY)
        cx = Desk.COL_MID  # the middle of the HUD column
        root = TREE[0]
        x_root = {tuple(k.split("|")): v for k, v in root["x"].items()}
        removed = [r for r in RIDES if r not in KEPT]
        assert (len(RIDES), len(removed), len(KEPT)) == (64, 28, 36)

        # ---- 4.1 presolve -------------------------------------------------------- #
        vo = (
            "How can a solver be sure, without trying every sequence? It starts by "
            "simplifying. Of the sixty-four possible rides, twenty-eight can never fit "
            "the clock. Remove them: thirty-six switches remain."
        )
        n = ValueTracker(64)
        lab = (
            txt("possible rides", fs=18, color=MUTED)
            .move_to([cx, 2.2, 0])
            .set_z_index(10)
        )
        num = live_number(
            n, fmt="{:.0f}", fs=60, color=INK, weight="BOLD",
            anchor=lambda m: m.move_to([cx, 1.5, 0]),
        ).set_z_index(10)  # fmt: skip
        known = course_mob(plane, BEST).set_z_index(2)
        k_ride = rider(known.core, period=9.0, color=INK).set_z_index(3)
        self.play(
            self.tell("First, simplify: rides that can never fit the clock go.", vo),
            FadeIn(known),
            run_time=0.8,
        )
        self.add(k_ride)
        self.cue("It starts by simplifying")
        self.play(FadeOut(known), FadeOut(k_ride), run_time=0.6)
        self.cue("sixty-four possible rides")
        first = (
            txt("64", fs=60, color=INK, weight="BOLD")
            .move_to([cx, 1.5, 0])
            .set_z_index(10)
        )
        self.play(
            Dim(rides, rest=0.3, run_time=1.2), FadeIn(lab), FadeIn(first), run_time=1.2
        )
        self.remove(first)
        self.add(num)
        self.cue("twenty-eight")
        # one of them, and why: noodles cannot be delivered before ramen is due
        ex = ("noodles", "ramen")
        assert ex in removed and ORDERS["noodles"]["early"] > ORDERS["ramen"]["late"]
        why = VGroup(
            line_txt("noodles, then ramen?", fs=20, color=INK, weight="BOLD"),
            line_txt(
                f"noodles cannot be delivered before {clock(ORDERS['noodles']['early'])}",
                fs=17,
                color=MUTED,
            ),
            line_txt(
                f"ramen must be delivered by {clock(ORDERS['ramen']['late'])}",
                fs=17,
                color=MUTED,
            ),
            line_txt("this ride can never happen", fs=17, color=CUT_C, weight="BOLD"),
        ).arrange(DOWN, buff=0.02, aligned_edge=LEFT)
        why.move_to([cx, -0.25, 0]).set_z_index(10)
        self.play(
            Dim(rides, gone={r: 0.5 for r in removed}, val={ex: 1.0}, run_time=0.8),
            FadeIn(why[:3], shift=UP * 0.1),
            run_time=0.8,
        )
        self.play(FadeIn(why[3]), run_time=0.4)
        self.cue("Remove them")
        self.play(
            Dim(rides, gone={r: 1.0 for r in removed}, rest=0.55, run_time=1.0),
            n.animate.set_value(36),
            run_time=1.0,
        )
        self.hold()

        # ---- 4.2 relax -------------------------------------------------------------- #
        vo = (
            "Then it cheats. Let every switch become a dimmer, anywhere between zero "
            "and one: half of this ride, three quarters of that one. With no yes-or-no "
            "left, the problem is easy: a linear program, solved in half a "
            "millisecond."
        )
        half, three_q = ("pasta", "pad thai"), ("kebab", "pasta")
        assert abs(x_root[half] - 0.52) < 0.01 and abs(x_root[three_q] - 0.76) < 0.01
        assert 0.35 < HERO["tree"]["lp_ms"] < 0.7  # one relaxation, measured (HiGHS)
        dim = Dimmer().move_to([cx, 0.1, 0]).set_z_index(10)
        dim_lab = (
            txt("one switch", fs=18, color=MUTED)
            .next_to(dim, DOWN, buff=0.3)
            .set_z_index(10)
        )
        self.play(
            self.tell("Then relax: every switch may take any value from 0 to 1.", vo),
            FadeOut(why),
            FadeOut(lab),
            FadeOut(num),
            run_time=0.6,
        )
        self.play(FadeIn(dim), FadeIn(dim_lab), run_time=0.4)
        for v in (1.0, 0.0, 1.0):  # a switch has two positions
            self.play(Tween(dim, v=v, run_time=0.16))
            self.wait(0.22)
        self.cue("a dimmer")
        new_lab = (
            txt("one dimmer", fs=18, color=RELAX_C, weight="BOLD")
            .move_to(dim_lab)
            .set_z_index(10)
        )
        dim.hue = ManimColor(RELAX_C)
        self.play(  # the old label leaves, then the new one arrives: never both
            Tween(dim, v=0.3, run_time=0.9),
            FadeOut(dim_lab, run_time=0.3),
            self.then(FadeIn(new_lab, run_time=0.5), 0.3),
        )
        self.cue("half of this ride")

        def value_badge(r, q, off):
            """The value of ride r, pinned at proportion q of its arc (``off`` to its
            side when the arc itself is taken)."""
            arc = rides.arc[r]
            a, b = (
                arc.point_from_proportion(q - 0.01),
                arc.point_from_proportion(q + 0.01),
            )
            t_ = (b - a) / np.linalg.norm(b - a)
            m = badge(f"{x_root[r]:.2f}", rides.hue)
            m.move_to(arc.point_from_proportion(q) - off * np.array([-t_[1], t_[0], 0]))
            assert stops.is_clear(m, 0.06, fees=False)
            return m.set_z_index(7)

        t_half, t_q = value_badge(half, 0.2, 0.0), value_badge(three_q, 0.2, 0.26)
        self.play(  # this ride, alone and lit: half on
            Dim(
                rides,
                val={half: x_root[half]},
                tint={half: 1.0},
                rest=0.0,
                run_time=0.9,
            ),
            Tween(dim, v=x_root[half], run_time=0.9),
            FadeIn(t_half, scale=1.3, run_time=0.9),
        )
        self.cue("three quarters")
        self.play(  # that one: three quarters on
            Dim(
                rides,
                val={three_q: x_root[three_q]},
                tint={half: 0.0, three_q: 1.0},
                run_time=0.8,
            ),
            Tween(dim, v=x_root[three_q], run_time=0.8),
            FadeIn(t_q, scale=1.3, run_time=0.8),
        )
        self.cue("With no yes-or-no")
        self.play(  # and every other switch: the whole relaxed plan
            Dim(
                rides, val=x_root, tint={three_q: 0.0}, rest=0.0, legs=1.0, run_time=1.4
            )
        )
        self.hold(
            ambient=lambda rt: [Breathe(dim, rt, attr="v", lo=0.2, hi=0.9, period=2.4)]
        )

        # ---- 4.3 a ceiling ------------------------------------------------------------ #
        vo = (
            "The relaxed plan claims thirty-three euros ninety. It is not a real "
            "course: half a ride earns half its fee, and only half obeys the clock. "
            "But every real course is still allowed in the relaxed problem, so no "
            "real course can earn more. That number is a ceiling."
        )
        best = HERO["brute"]["obj"]
        assert abs(root["bound"] - 33.9) < 1e-6 and best < root["bound"]
        bar = GapBar(w=5.7).set_z_index(10)
        bar.shift(A([cx - 5.7 / 2, -1.55, 0]) - bar.axis.get_start())
        bar.ceil, bar.known = 35.0, [root["bound"]]
        claim = Readout(
            "the relaxed plan earns",
            euro(root["bound"]),
            color=RELAX_C,
            at=(cx, 2.0),
            align=ORIGIN,
        )
        claim.set_z_index(10)
        self.play(
            self.tell("Its value is a ceiling: no real course can earn more.", vo),
            dim.animate.shift(UP * 0.6),  # room for the bound axis and its labels
            new_lab.animate.shift(UP * 0.6),
            run_time=0.6,
        )
        self.play(Tween(dim, v=x_root[half], run_time=0.5))

        def shimmer(rt):  # the plan under discussion breathes
            return [Breathe(rides, rt, attr="gain", lo=0.62, hi=1.0, period=2.2)]

        self.cue("thirty-three euros ninety")
        self.play(FadeIn(claim, shift=UP * 0.1), run_time=0.5)
        # what a fraction is worth: the half ride to pad thai, and half its fee
        fee = ORDERS[half[1]]["pay"]
        part = x_root[half] * fee
        assert (half[1], fee) == ("pad thai", 7.0)
        assert (f"{x_root[half]:.2f}", f"{part:.2f}") == ("0.52", "3.64")
        half_lab = (
            Text(
                f"half a ride earns 0.52 × {euro(fee)} = {euro(part)}",
                font_size=17,
                color=INK,
                weight="MEDIUM",
                t2c={"0.52": RELAX_C, euro(part): RELAX_C},
            )
            .move_to(new_lab)
            .set_z_index(10)
        )
        self.cue("half a ride earns", ambient=shimmer)
        self.play(  # the dimmer's label leaves, then the sum arrives; its ride lights up
            Dim(rides, tint={half: 1.0}, run_time=0.6),
            FadeOut(new_lab, run_time=0.25),
            self.then(FadeIn(half_lab, run_time=0.4), 0.25),
        )
        self.cue("every real course", ambient=shimmer)
        self.play(FadeIn(bar), Dim(rides, tint={half: 0.0}, run_time=0.5), run_time=0.5)
        self.cue("no real course can earn more", ambient=shimmer)
        self.play(Tween(bar, a_ceil=1.0, ceil=root["bound"], run_time=1.0))
        ghost = VGroup(
            DashedLine([0, -0.3, 0], [0, 0.3, 0], dash_length=0.06).set_stroke(
                PLAN_C, width=2.5
            ),
            txt("the best course", fs=16, color=PLAN_C),
            txt(euro(best), fs=18, color=PLAN_C, font=MONO, weight="BOLD"),
        )
        gx = bar.axis.get_start() + RIGHT * bar.x_of(best)
        ghost[0].move_to(gx)
        ghost[1].move_to(gx + DOWN * 0.52)
        ghost[2].move_to(gx + DOWN * 0.84)
        ghost.set_z_index(10)
        bar.a_avoid = 0.0
        bar.avoid.append(best)  # the tick label under the mark steps aside
        self.cue("a ceiling")
        self.play(
            FadeIn(ghost, shift=UP * 0.1),
            Tween(bar, a_avoid=1.0, run_time=0.6),
            run_time=0.6,
        )
        self.settle(ambient=shimmer)
        self.wipe()

    # ====================================================================== #
    # 5 · Branch and bound
    # ====================================================================== #
    def scene_branch(self):
        self.header("5 · Branch and bound", LILAC)
        self.add(
            self.note(
                "Our own branch and bound on Léa's hour: every node is a linear program, solved for real."
            )
        )
        desk = Desk()
        win = MapWindow(desk.mid, 2450.0, 4.2, 3.05, at=(-4.75, 0.72))
        mini = MiniStops(win).set_z_index(4)
        rides = RideSet(win, w0=1.2, w1=4.2).set_z_index(1)
        rides.legs = 1.0
        bar = GapBar(w=3.7).set_z_index(5)
        bar.shift(A([-4.75 - 3.7 / 2, -1.85, 0]) - bar.axis.get_start())
        tree = SearchTree(TREE, w=8.7, h=4.75).fit(-2.0, 6.8, 2.28)
        lps = [0]
        for nd in TREE:
            lps.append(lps[-1] + int(nd["lp"]))
        assert lps[-1] == HERO["tree"]["lps"] == 116 and len(TREE) == 129
        plans = [nd for nd in TREE if nd.get("incumbent")]
        assert [round(nd["bound"], 1) for nd in plans] == [17.5, 22.4, 23.7, 24.4]
        assert plans[-1]["seq"] == BEST

        solved = Readout(
            "relaxations solved", "0", at=(6.85, 3.22), align=RIGHT, fs=26
        ).set_z_index(5)
        count = VGroup(solved.val.copy())
        # ``floor``: the floor marker waits until the narrator says the word;
        # ``cut``: a branch has been cut by the bound (its legend entry may appear)
        state = {"plan": None, "floor": False, "cut": False}
        first_cut = next(nd["id"] for nd in TREE if nd["kind"] == "pruned")
        course = VGroup().set_z_index(2)
        course.add_updater(lambda m: None)  # redrawn on every frame (see kit._alive)
        runner = VGroup(
            Circle(radius=0.11, stroke_width=0).set_fill(INK, opacity=0.25),
            Circle(radius=0.055, stroke_width=0).set_fill(INK, opacity=1.0),
        ).set_z_index(3)
        runner.clock = 0.0

        def run(m, dt):  # a dot rides the best course found so far, round and round
            m.clock += dt
            if len(course) == 0:
                m.set_opacity(0.0)
                return
            m[0].set_fill(opacity=0.25)
            m[1].set_fill(opacity=1.0)
            m.move_to(course[-1].point_from_proportion((m.clock / 7.0) % 1.0))

        runner.add_updater(run)

        def step(i):
            nd = TREE[i]
            bar.ceil = nd["ceiling"] if nd["ceiling"] is not None else bar.ceil
            bar.a_ceil = 1.0
            if nd["floor"] is not None:
                bar.floor = nd["floor"]
                bar.a_floor = 1.0 if state["floor"] else 0.0
            state["cut"] = state["cut"] or i >= first_cut
            if nd["lp"] and nd["x"]:
                x = {tuple(k.split("|")): v for k, v in nd["x"].items()}
                for r in rides.val:
                    rides.val[r] = x.get(r, 0.0)
                    rides.tint[r] = 1.0 if nd["kind"] == "plan" else 0.0
                rides.refresh()
            best = max(
                (p for p in plans if p["id"] <= i), key=lambda p: p["id"], default=None
            )
            if best is not None and best["id"] != state["plan"]:
                state["plan"] = best["id"]
                course.become(course_mob(win, best["seq"], width=3.4).set_z_index(2))
            count.become(VGroup(solved.fresh(str(lps[i + 1]))))

        self.play(FadeIn(win), FadeIn(mini), run_time=0.6)
        self.add(rides, course, runner)

        # ---- 5.1 branch ------------------------------------------------------------ #
        vo = (
            "Now pick one fractional ride, and split the problem in two. In one "
            "branch, she must take that ride. In the other, she must leave it. Each "
            "branch is relaxed again, and gets a ceiling of its own."
        )
        root, first = TREE[0], TREE[1]
        var = tuple(root["var"].split("|"))
        other = next(nd for nd in TREE if nd["parent"] == 0 and nd["take"] == 0)
        assert var == ("pasta", "pad thai") and first["take"] == 1 and other["id"] == 24
        self.play(
            self.tell("Branch: take one fractional ride, or leave it.", vo),
            FadeIn(bar),
            FadeIn(solved.lab),
            run_time=0.6,
        )
        self.add(tree, count)
        tree.on_step = step
        self.play(Tween(tree, k=0.99, run_time=0.6))
        t_root = tag(
            euro(root["bound"]), fs=16, color=RELAX_C, font=MONO, weight="BOLD"
        )
        t_root.next_to(tree.point(0), UR, buff=0.08)
        self.play(FadeIn(t_root, shift=LEFT * 0.1), run_time=0.4)
        self.cue("one fractional ride")
        ask = tag("pasta, then pad thai?  0.52", fs=16, color=INK).next_to(
            tree.point(0), UL, buff=0.08
        )
        self.play(
            Dim(rides, tint={var: 1.0}, val={var: 1.0}, run_time=0.5),
            FadeIn(ask, shift=DOWN * 0.1),
            run_time=0.5,
        )

        # each branch is a smaller problem of the same kind: show both, with their own relaxed plan
        def branch(nd, x, title):
            w2 = MapWindow(desk.mid, 2450.0, 3.75, 2.72, at=(x, -0.42))
            rs = RideSet(w2, w0=1.0, w1=3.6).set_z_index(1)
            rs.legs = 1.0
            for r, v in nd["x"].items():
                rs.val[tuple(r.split("|"))] = v
            extra = VGroup().set_z_index(5)
            if nd["take"]:
                rs.tint[var] = 1.0
            else:  # the ride she may not take: struck out
                arc = rs.arc[var].copy().set_stroke(CUT_C, width=2.6, opacity=0.95)
                extra.add(
                    arc,
                    make_cross(CUT_C, sw=4, scale=0.45).move_to(
                        arc.point_from_proportion(0.5)
                    ),
                )
            rs.refresh()
            body = Group(w2, rs, MiniStops(w2, k=0.5).set_z_index(4), extra)
            edge = Line(tree.point(0), [x, w2.rim.get_top()[1] + 0.34, 0]).set_stroke(
                MUTED, width=1.6, opacity=0.7
            )
            name = tag(title, fs=17, color=INK, weight="BOLD").move_to(
                [x, w2.rim.get_top()[1] + 0.2, 0]
            )
            value = tag(
                f"ceiling {euro(nd['bound'])}", fs=17, color=RELAX_C, weight="BOLD"
            )
            value.move_to([x, w2.rim.get_bottom()[1] - 0.24, 0])
            return body, edge, name, value

        kid_a = branch(first, 0.35, "she must take it")
        kid_b = branch(other, 4.6, "she must leave it")
        assert (
            abs(first["bound"] - 33.9) < 1e-6 and abs(other["bound"] - 33.7143) < 1e-3
        )
        self.cue("she must take")
        self.play(Create(kid_a[1]), FadeIn(kid_a[0]), FadeIn(kid_a[2]), run_time=0.8)
        self.cue("she must leave")
        self.play(Create(kid_b[1]), FadeIn(kid_b[0]), FadeIn(kid_b[2]), run_time=0.8)
        self.cue("relaxed again")
        self.play(
            FadeIn(kid_a[3], shift=UP * 0.1),
            FadeIn(kid_b[3], shift=UP * 0.1),
            run_time=0.6,
        )
        self.hold()

        # ---- 5.2 dive to a first real course ------------------------------------------ #
        vo = (
            "Keep splitting, diving down one side. Some branches are dead ends: no "
            "plan fits. Then a relaxed plan comes out whole, only zeros and ones: a "
            "real course, worth seventeen euros fifty. That is a floor: the best "
            "course so far."
        )
        p0 = plans[0]
        assert p0["id"] == 23

        def key(glyph, text):
            return VGroup(glyph, line_txt(text, fs=16, color=MUTED)).arrange(
                RIGHT, buff=0.14
            )

        cross = VGroup(
            Line([-0.05, -0.05, 0], [0.05, 0.05, 0]),
            Line([-0.05, 0.05, 0], [0.05, -0.05, 0]),
        )
        legend = (
            VGroup(
                key(
                    Circle(radius=0.055, stroke_width=0).set_fill(RELAX_C, 1.0),
                    "a relaxation, split",
                ),
                key(cross.copy().set_stroke(MUTED, width=2.6), "a dead end"),
                key(
                    Circle(radius=0.085, stroke_width=0).set_fill(PLAN_C, 1.0),
                    "a real course",
                ),
                key(cross.copy().set_stroke(CUT_C, width=2.6), "cut by the bound"),
            )
            .arrange(RIGHT, buff=0.45)
            .move_to([2.4, -2.86, 0])
        )
        assert legend.get_right()[0] < 6.75 and legend.get_left()[0] > -2.0

        def with_first_cross(
            m, dt
        ):  # "cut by the bound" arrives with the first red cross
            if state["cut"] and m.a < 1.0:
                m.a = min(1.0, m.a + dt / 0.4)
                m.set_opacity(m.a)

        legend[3].a = 0.0
        legend[3].set_opacity(0.0).add_updater(with_first_cross)
        self.play(
            self.tell("Dive until a plan comes out whole: a real course, a floor.", vo),
            *[FadeOut(m) for kid in (kid_a, kid_b) for m in kid],
            FadeOut(ask),
            run_time=0.6,
        )
        self.play(Tween(tree, k=1.99, run_time=0.6), FadeIn(legend[0]), run_time=0.6)
        first_dead = next(nd["id"] for nd in TREE if nd["kind"] == "infeasible")
        self.cue(
            "dead ends",
            lead=0.2,
            ambient=lambda rt: [
                Tween(tree, k=first_dead + 1.99, run_time=rt, rate_func=linear)
            ],
        )
        self.play(
            Tween(tree, k=first_dead + 2.5, run_time=0.4),
            FadeIn(legend[1]),
            run_time=0.4,
        )
        self.cue(
            "comes out whole",
            lead=0.2,
            ambient=lambda rt: [
                Tween(tree, k=p0["id"] - 0.01, run_time=rt, rate_func=linear)
            ],
        )
        self.play(
            Tween(tree, k=p0["id"] + 0.99, run_time=0.5),
            FadeIn(legend[2]),
            run_time=0.5,
        )
        t_plan = tag(euro(p0["bound"]), fs=16, color=PLAN_C, font=MONO, weight="BOLD")
        t_plan.next_to(tree.point(p0["id"]), DOWN, buff=0.16)
        self.cue("seventeen euros fifty")
        self.play(FadeIn(t_plan, shift=UP * 0.1), run_time=0.4)
        self.cue("That is a floor")  # the marker lands on the bar with its name
        state["floor"] = True
        self.play(Tween(bar, a_floor=1.0, run_time=0.5))
        self.play(ripple(bar.v_floor, color=PLAN_C, buff=0.1), run_time=0.7)
        self.hold()

        # ---- 5.3 bound --------------------------------------------------------------- #
        vo = (
            "From here, always open the branch with the highest ceiling. Better "
            "courses appear, and the floor rises: twenty-two forty, twenty-three "
            "seventy, twenty-four forty. And a branch whose ceiling is under the "
            "floor cannot hide anything better: cut it, without looking inside."
        )
        self.add(legend[3])  # (invisible until the first red cross: see above)
        self.play(
            self.tell("Bound: a branch whose ceiling is under the floor is cut.", vo),
            FadeOut(t_plan),
            FadeOut(t_root),
            run_time=0.5,
        )
        for phrase, p in zip(
            ("twenty-two forty", "twenty-three seventy", "twenty-four forty"),
            plans[1:],
            strict=True,
        ):
            self.cue(
                phrase,
                lead=0.25,
                ambient=lambda rt, p=p: [
                    Tween(tree, k=p["id"] - 0.01, run_time=rt, rate_func=linear)
                ],
            )
            self.play(Tween(tree, k=p["id"] + 0.99, run_time=0.35))
            self.play(ripple(bar.v_floor, color=PLAN_C, buff=0.1), run_time=0.5)
        meet = next(
            nd["id"]
            for nd in TREE
            if nd["floor"] is not None and nd["ceiling"] - nd["floor"] < 1e-6
        )
        assert meet == 115 and not any(nd["lp"] for nd in TREE[meet + 1 :])
        # the very next branch is worth less than the course she already has
        gone = TREE[plans[-1]["id"] + 1]
        assert (gone["id"], gone["kind"], gone["lp"]) == (107, "pruned", True)
        assert round(gone["bound"], 2) == 21.7 < gone["floor"]
        assert abs(gone["floor"] - plans[-1]["bound"]) < 1e-6
        verdict = Text(
            f"ceiling {euro(gone['bound'])} < floor {euro(gone['floor'])}: cut",
            font_size=22,
            color=CUT_C,
            weight="BOLD",
            t2c={
                f"ceiling {euro(gone['bound'])}": RELAX_C,
                f"floor {euro(gone['floor'])}": PLAN_C,
            },
        ).move_to([1.2, 3.22, 0])
        self.cue("a branch whose ceiling", lead=0.2)
        self.play(Tween(tree, k=gone["id"] + 0.99, run_time=0.5))
        self.play(
            FadeIn(verdict, shift=UP * 0.1),
            ripple(tree.dot[gone["id"]], color=CUT_C, buff=0.1),
            run_time=0.8,
        )
        self.cue("cut it", lead=0.2)
        self.play(Tween(tree, k=meet - 2.01, run_time=2.4, rate_func=linear))
        self.hold()

        # ---- 5.4 proof ---------------------------------------------------------------- #
        vo = (
            "The ceiling comes down, the floor comes up. When they meet, the search "
            "is over: twenty-four euros forty is proven optimal. One hundred and "
            "sixteen small problems, and no branch is left that could hide a better "
            "course."
        )
        self.play(
            self.tell("Floor and ceiling meet: 24.40 euros, proven optimal.", vo),
            FadeOut(verdict),
            run_time=0.5,
        )
        self.cue("When they meet")
        self.play(Tween(tree, k=len(TREE) - 0.01, run_time=1.6, rate_func=linear))
        assert abs(TREE[-1]["ceiling"] - TREE[-1]["floor"]) < 1e-6
        tree.cursor.set_stroke(opacity=0)
        t_opt = txt(
            f"{euro(HERO['brute']['obj'])} is proven optimal",
            fs=24,
            color=DONE_C,
            weight="BOLD",
        )
        t_opt.move_to([1.2, 3.22, 0])
        self.cue("proven optimal")
        self.play(
            FadeIn(t_opt, shift=UP * 0.1),
            ripple(tree.dot[plans[-1]["id"]], color=DONE_C, buff=0.1),
            Dim(
                rides, rest=0.0, run_time=0.9
            ),  # only the proven course stays on the map
            run_time=0.9,
        )
        self.cue("One hundred and sixteen")
        self.play(Indicate(count, color=PLAN_C, scale_factor=1.25), run_time=0.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 6 · Inside a real solver
    # ====================================================================== #
    def scene_solver(self):
        self.header("6 · Inside a real solver", AMBER)
        desk = Desk()
        note = self.note(
            "Map data © OpenStreetMap contributors. Léa's hour: the rule and both bounds are computed."
        )
        self.add(note)

        # ---- 6.1 a cutting plane, on our own example ------------------------------------ #
        vo = (
            "A real solver adds two accelerators. First, cutting planes. Our relaxed "
            "plan claimed six orders. But six deliveries take more than sixty "
            "minutes, and the last deadline is at fifty-nine: no real course fits "
            "more than five. Add that rule, at most five, and the ceiling drops from "
            "thirty-three ninety to twenty-nine twenty, without a single branch. A "
            "solver finds such rules by itself."
        )
        cut, root = HERO["cut"], TREE[0]
        assert (
            cut["max_orders"],
            cut["relaxed_orders"],
            cut["before"],
            cut["bound"],
        ) == (5, 6.0, 33.9, 29.2)
        # the rule is derived from the model's data (the six quickest rides into an
        # order add up to more than the last deadline), not looked up by brute force
        assert cut["need"] > 60 > cut["deadline"] and clock(cut["deadline"]) == "20:59"
        assert (
            max(len(c["seq"]) for c in HERO["brute"]["sample"]) <= 5 and len(BEST) == 5
        )
        ww, wh = 6.3, 4.65
        win = MapWindow(desk.mid, 2650.0, ww, wh, at=(-3.62, -0.12))
        box = (
            win.at[0] - ww / 2 + 0.1,
            win.at[1] - wh / 2 + 0.1,
            win.at[0] + ww / 2 - 0.1,
            win.at[1] + wh / 2 - 0.1,
        )
        stops = Stops(win, region=box).set_z_index(4)
        stops.labels.set_z_index(6)
        rides = RideSet(win).set_z_index(1)
        rides.legs = 1.0
        x_root = {tuple(k.split("|")): v for k, v in root["x"].items()}
        x_cut = {tuple(k.split("|")): v for k, v in cut["x"].items()}
        for r, v in x_root.items():
            rides.val[r] = v
        rides.refresh()
        cx = 3.55
        bar = GapBar(w=5.6).set_z_index(5)
        bar.shift(A([cx - 2.8, -1.75, 0]) - bar.axis.get_start())
        bar.ceil, bar.a_ceil = root["bound"], 1.0
        bar.known = [root["bound"], cut["bound"]]  # the label shows nothing in between
        n = ValueTracker(cut["relaxed_orders"])
        r_n = Readout(
            "orders the relaxed plan claims",
            "6",
            at=(cx, 2.35),
            align=ORIGIN,
            fs=44,
            color=RELAX_C,
        )
        count = always_redraw(lambda: r_n.fresh(f"{n.get_value():.0f}"))
        rule = (
            VGroup(
                line_txt(
                    "Six deliveries take more than 60 min.",
                    fs=18,
                    color=MUTED,
                ),
                line_txt(
                    f"The last deadline is {clock(cut['deadline'])}.",
                    fs=18,
                    color=MUTED,
                ),
                line_txt(
                    "No real course delivers more than 5.",
                    fs=22,
                    color=INK,
                    weight="BOLD",
                ),
            )
            .arrange(DOWN, buff=0.03)
            .move_to([cx, 0.5, 0])
        )
        self.play(
            self.tell("A cut: a rule every real course obeys, and the relaxed plan breaks.", vo),
            FadeIn(win), FadeIn(stops), FadeIn(stops.labels), FadeIn(rides), FadeIn(bar),
            run_time=0.9,
        )  # fmt: skip

        def shimmer(rt):
            return [Breathe(rides, rt, attr="gain", lo=0.62, hi=1.0, period=2.2)]

        self.cue("claimed six orders", ambient=shimmer)
        self.play(FadeIn(r_n.lab), FadeIn(r_n.val, scale=1.3), run_time=0.5)
        self.remove(r_n.val)
        self.add(count)
        self.cue("six deliveries take", ambient=shimmer)
        self.play(FadeIn(rule[0], shift=UP * 0.1), run_time=0.5)
        self.cue("the last deadline", ambient=shimmer)
        self.play(FadeIn(rule[1], shift=UP * 0.1), run_time=0.5)
        self.cue("no real course fits", ambient=shimmer)
        self.play(FadeIn(rule[2], shift=UP * 0.1), run_time=0.5)
        self.cue("Add that rule", ambient=shimmer)
        self.play(
            Dim(rides, val=x_cut, rest=0.0, run_time=1.2),
            n.animate.set_value(cut["max_orders"]),
            run_time=1.2,
        )
        self.cue("the ceiling drops")
        self.play(Tween(bar, ceil=cut["bound"], run_time=3.0))  # lands on its number
        under = Line(
            rule[2].body.get_corner(DL) + DOWN * 0.1,
            rule[2].body.get_corner(DR) + DOWN * 0.1,
        ).set_stroke(CUT_C, width=3)
        cut_name = line_txt("a cutting plane", fs=16, color=CUT_C, weight="BOLD")
        cut_name.next_to(under, DOWN, buff=0.04)
        self.cue("A solver finds such rules", ambient=shimmer)
        self.play(Create(under), FadeIn(cut_name, shift=UP * 0.08), run_time=0.7)
        self.hold(ambient=shimmer)

        # ---- 6.2 a heuristic ------------------------------------------------------------- #
        vo = (
            "Second, heuristics: quick guesses at real courses, to raise the floor "
            "early. Even a simple rule, always the order that can be delivered "
            "soonest, gives a floor of seventeen euros ten before the search begins."
        )
        quick = HERO["greedy"]["soon"]
        assert quick["obj"] == 17.1 and quick["seq"] == [
            "ramen",
            "kebab",
            "pizza",
            "noodles",
        ]
        guess = course_mob(win, quick["seq"], width=4.6).set_z_index(2)
        picks = HERO["brute"]["sample"][::2]  # real courses, of every shape
        assert len(picks) == 7 and quick["seq"] not in [c["seq"] for c in picks]
        self.play(
            self.tell("A heuristic: a quick real course, an early floor.", vo),
            Dim(rides, rest=0.0, legs=0.0),
            FadeOut(rule), FadeOut(under), FadeOut(cut_name),
            FadeOut(r_n.lab), FadeOut(count),
            run_time=0.6,
        )  # fmt: skip
        self.cue("quick guesses")
        k = ValueTracker(0)
        flick = always_redraw(
            lambda: course_mob(
                win, picks[min(int(k.get_value()), len(picks) - 1)]["seq"],
                color=TRY_C, width=3.2, glow=False,
            ).set_z_index(2)
        )  # fmt: skip
        self.add(flick)
        self.play(
            k.animate.set_value(len(picks) - 0.01), run_time=3.4, rate_func=linear
        )
        self.remove(flick)
        self.cue("Even a simple rule")
        self.play(FadeIn(guess[0]), Create(guess.core, rate_func=linear), run_time=2.4)
        g_ride = rider(guess.core, period=7.0, color=INK).set_z_index(3)
        self.add(g_ride)
        bar.floor = bar.lo
        bar.known.append(quick["obj"])
        r_q = Readout(  # where the cut's count stood: same place, same size
            "the quick guess, soonest first, earns",
            euro(quick["obj"]),
            at=(cx, 2.35),
            align=ORIGIN,
            fs=44,
            color=PLAN_C,
        )
        self.cue("a floor of seventeen")
        self.play(
            FadeIn(r_q, shift=UP * 0.1),
            Tween(bar, floor=quick["obj"], a_floor=1.0, run_time=1.0),
            run_time=1.0,
        )
        self.hold()

        # ---- 6.3 the same story, in Gurobi's log ------------------------------------------ #
        vo = (
            "Gurobi does all this, and narrates it in its log. Presolve removes "
            "forty-four of the seventy-three columns, its word for variables. The "
            "root relaxation gives a first ceiling, already lower than ours: "
            "thirty-two seventy-nine. Lines marked H are heuristic floors. Then "
            "cutting planes take the ceiling down to twenty-seven."
        )
        L = read_log("course")
        a, b, c = (
            L.index(log_line(L, " Expl Unexpl")),
            L.index("Cutting planes:"),
            L.index(log_line(L, "Explored")),
        )
        lines = [
            log_line(L, "Optimize a model"), "…",
            log_line(L, "Presolve removed"), "…",
            *wrap(log_line(L, "Root relaxation"), 80), "",
            L[a - 1], L[a], *L[a + 1 : b], *L[b:c],
            log_line(L, "Explored"), "…",
            log_line(L, "Optimal solution"), log_line(L, "Best objective"),
        ]  # fmt: skip
        assert all(len(x) <= 80 for x in lines) and len(lines) == 27
        g = HERO["gurobi"]
        assert g["nodes"] == 1 and g["obj"] == 24.4 and "44 columns" in lines[2]
        assert "3.278638e+01" in lines[4] and "Explored 1 nodes" in lines[23]
        # 73 columns = 64 switches + 9 delivery minutes; Gurobi's own first ceiling
        # (32.79) is under the one of our plain relaxation (33.90)
        assert "73 columns" in lines[0] and g["vars"] == 73 == g["binaries"] + 9
        assert 32.78638 < TREE[0]["bound"]
        panel = LogPanel(lines, cols=80, rows=15, title="gurobi.log").place(0, -0.2)
        row = {
            k: next(i for i, x in enumerate(lines) if x.startswith(k))
            for k in (
                "Presolve",
                "Root",
                " Expl",
                "Cutting",
                "Explored",
                "Best objective",
            )
        }
        table = [i for i in range(row[" Expl"] + 1, row["Cutting"]) if lines[i].strip()]
        heur = [i for i in table if lines[i].startswith("H")]
        plain = [i for i in table if not lines[i].startswith("H")]
        assert len(heur) == 3 and len(plain) == 2

        def mark(i, text, color, nth=0, **kw):
            return panel.mark(i, *panel.find(i, text, nth), color, **kw)

        m_pre = mark(row["Presolve"], "44 columns", PLAN_C)
        m_all = mark(0, "73 columns", PLAN_C)
        m_root = mark(row["Root"], "3.278638e+01", RELAX_C)
        m_h = [mark(i, lines[i].split()[3], PLAN_C) for i in heur] + [
            panel.mark(i, 0, 1, PLAN_C) for i in heur
        ]
        b0, b1 = lines[plain[0]].split()[6], lines[plain[1]].split()[6]
        assert (b0, b1) == ("32.78638", "27.11528")
        m_b = [mark(plain[0], b0, RELAX_C, nth=1), mark(plain[1], b1, RELAX_C, nth=1)]
        m_cut = panel.mark(row["Cutting"], 0, len("Cutting planes:"), RELAX_C)
        log_note = self.note(
            "Gurobi Optimizer 14.0, the log of Léa's hour (excerpt, long lines wrapped)."
        )
        self.play(
            self.tell("Gurobi's log tells the same story.", vo),
            *[
                FadeOut(m)
                for m in (
                    win,
                    stops,
                    stops.labels,
                    rides,
                    guess,
                    g_ride,
                    bar,
                    r_q,
                    note,
                )
            ],
            run_time=0.6,
        )
        self.play(FadeIn(panel), FadeIn(log_note), run_time=0.6)
        self.play(Tween(panel, shown=1.0, run_time=0.3))
        self.cue("Presolve removes")
        self.play(
            Tween(panel, shown=3.0, run_time=0.5),
            Tween(m_pre, a=1.0, run_time=0.5),
            Tween(m_all, a=1.0, run_time=0.5),
        )
        self.cue("The root relaxation")
        self.play(
            Tween(panel, shown=6.0, run_time=0.6), Tween(m_root, a=1.0, run_time=0.6)
        )
        ours = line_txt(
            f"our own relaxation: {TREE[0]['bound']:.2f}",
            fs=16,
            color=RELAX_C,
            weight="BOLD",
        )
        ours.add_updater(  # under Gurobi's number, on the wrapped line; follows the log
            lambda m: m.move_to(
                [panel.x_col(30), panel.y_row(row["Root"] + 1), 0], aligned_edge=LEFT
            )
        )
        self.cue("already lower than ours")
        self.play(FadeIn(ours), run_time=0.4)
        self.cue("Lines marked H", lead=1.3)
        self.play(
            Tween(panel, shown=float(table[-1] + 1), run_time=1.3, rate_func=linear),
            Tween(m_pre, a=0.0),
            Tween(m_all, a=0.0),
        )
        self.play(
            LaggedStart(*[Tween(m, a=1.0, run_time=0.4) for m in m_h], lag_ratio=0.25),
            run_time=1.0,
        )
        self.cue("cutting planes take")
        self.play(FadeOut(ours), Tween(m_root, a=0.0, run_time=0.3), run_time=0.3)
        self.play(
            Tween(panel, scroll=7.0, shown=22.0, run_time=1.2),
            Tween(m_cut, a=1.0, run_time=1.2),
        )
        self.play(Tween(m_b[0], a=1.0, run_time=0.4))
        self.cue("down to twenty-seven")
        self.play(Tween(m_b[1], a=1.0, run_time=0.4))
        self.hold()

        # ---- 6.4 three columns ------------------------------------------------------------- #
        vo = (
            "Three columns tell the story. Incumbent is the floor. Best bound is the "
            "ceiling. Gap is the distance between them, as a share of the floor. Here "
            "it closes at the very first node, without a single branch: our one "
            "hundred and twenty-nine nodes became one."
        )
        first = lines[plain[0]].split()
        assert first[5:8] == [
            "16.60000",
            "32.78638",
            "97.5%",
        ]  # (32.79 - 16.60) / 16.60
        assert abs((32.78638 - 16.6) / 16.6 - 0.975) < 5e-4
        hdr = row[" Expl"]
        cols = {k: panel.find(hdr, k) for k in ("Incumbent", "BestBd", "Gap")}
        m_cols = {
            "Incumbent": [
                panel.mark(
                    i,
                    cols["Incumbent"][0] - 1,
                    cols["Incumbent"][1] + 1,
                    PLAN_C,
                    op=0.2,
                )
                for i in (hdr, *table)
            ],
            "BestBd": [
                panel.mark(i, cols["BestBd"][0] - 2, cols["BestBd"][1], RELAX_C, op=0.2)
                for i in (hdr, *table)
            ],
            "Gap": [
                panel.mark(i, cols["Gap"][0] - 2, cols["Gap"][1] + 1, LILAC, op=0.22)
                for i in (hdr, *table)
            ],
        }
        blank = table[-1] + 1
        calls = {}
        for k, word, color in (
            ("Incumbent", "floor", PLAN_C),
            ("BestBd", "ceiling", RELAX_C),
            ("Gap", "distance", LILAC),
        ):
            t = line_txt(word, fs=17, color=color, weight="BOLD")
            x = (panel.x_col(cols[k][0]) + panel.x_col(cols[k][1])) / 2
            t.add_updater(lambda m, x=x: m.move_to([x, panel.y_row(blank), 0]))
            calls[k] = t
        self.play(
            self.tell("Incumbent, best bound, gap: floor, ceiling, distance.", vo),
            *[Tween(m, a=0.0) for m in (*m_h, *m_b, m_cut)],
            run_time=0.5,
        )
        for k, phrase in (
            ("Incumbent", "Incumbent is"),
            ("BestBd", "Best bound is"),
            ("Gap", "Gap is"),
        ):
            self.cue(phrase)
            self.play(
                *[Tween(m, a=1.0, run_time=0.5) for m in m_cols[k]],
                FadeIn(calls[k]),
                run_time=0.5,
            )
        # the gap, spelled out with the numbers of the table's first row
        share = [
            line_txt(
                "gap = (ceiling − floor) / floor",
                fs=17,
                color=INK,
                weight="BOLD",
                t2c={"gap": LILAC, "ceiling": RELAX_C, "floor": PLAN_C},
            ),
            line_txt(
                f"{first[7][:-1]} % = ({float(first[6]):.2f} − {float(first[5]):.2f}) / {float(first[5]):.2f}",
                fs=16,
                color=INK,
                font=MONO,
                t2c={f"{first[7][:-1]} %": LILAC},
            ),
        ]
        for q, t in enumerate(share):
            t.add_updater(
                lambda m, q=q: m.move_to(
                    [panel.x_col(33), panel.y_row(blank + 2 + q), 0], aligned_edge=LEFT
                )
            )
        self.cue("the distance between them")
        self.play(FadeIn(share[0]), run_time=0.4)
        self.cue("as a share of the floor")
        self.play(FadeIn(share[1]), run_time=0.4)
        self.cue("Here it closes")
        m_one = mark(row["Explored"], "1 nodes", PLAN_C)
        m_gap = mark(row["Best objective"], "gap 0.0000%", DONE_C)
        self.play(
            *[FadeOut(t) for t in (*calls.values(), *share)],
            *[Tween(m, a=0.0, run_time=0.4) for ms in m_cols.values() for m in ms],
            Tween(panel, scroll=12.0, shown=27.0, run_time=1.2),
            run_time=1.2,
        )
        self.play(Tween(m_gap, a=1.0, run_time=0.5))
        self.cue("the very first node")
        self.play(Tween(m_one, a=1.0, run_time=0.5))
        # our tree against Gurobi's: the count of scene 5 runs down to the log's "1"
        r_one = Readout(
            "nodes explored",
            str(len(TREE)),
            at=(2.9, panel.y_row(row["Cutting"] + 2.5)),
            align=ORIGIN,
            fs=40,
        )
        n_one = ValueTracker(len(TREE))
        count_one = always_redraw(lambda: r_one.fresh(f"{n_one.get_value():.0f}"))
        self.cue("our one hundred")
        self.play(FadeIn(r_one, shift=UP * 0.1), run_time=0.5)
        self.remove(r_one.val)
        self.add(count_one)
        self.cue("became one", lead=0.7)
        self.play(n_one.animate.set_value(1), run_time=1.2)
        self.play(ripple(m_one, color=PLAN_C, buff=0.07), run_time=0.7)
        self.hold()

        # ---- 6.5 a whole district -------------------------------------------------------- #
        vo = (
            "Now a whole district, the eleventh arrondissement: eight couriers, "
            "thirty-two orders, one thousand two hundred and forty-eight switches. "
            "Same model, same call. Here is the search, in real time."
        )
        Z = DEEP
        assert (Z["arr"], len(Z["couriers"]), len(Z["orders"]), Z["binaries"]) == (
            11,
            8,
            32,
            1248,
        )
        assert Z["optimal"] and Z["nodes"] == 31577 and 3.3 < Z["runtime"] < 3.6
        pts = np.array(
            [c["start"] for c in Z["couriers"]]
            + [o["R"] for o in Z["orders"]]
            + [o["C"] for o in Z["orders"]]
        )
        mid, span = (
            (pts.min(axis=0) + pts.max(axis=0)) / 2,
            pts.max(axis=0) - pts.min(axis=0),
        )
        ww, wh = 4.9, 5.05
        win = MapWindow(
            mid, max(span[0] / ww, span[1] / wh) * ww * 1.07, ww, wh, at=(-4.35, -0.12)
        )
        import city

        ring = VMobject().set_points_as_corners(
            win.w(city.geometry().arrondissement(11)[0])
        )
        ring.set_stroke(INK, width=1.8, opacity=0.75).set_z_index(3)
        dist = District(win, Z).set_z_index(4)
        dist.show({c["name"]: [] for c in Z["couriers"]})
        t_end = Z["recorded_runtime"]
        chart = GapChart(Z["plans"], Z["trace"], t_end, w=6.3, h=3.1)
        chart.shift(A([0.45, -1.72, 0]) - chart.axes[0][0].get_start())
        legend = (
            VGroup(
                line_txt(
                    "best bound: the ceiling", fs=17, color=RELAX_C, weight="BOLD"
                ),
                line_txt("incumbent: the floor", fs=17, color=PLAN_C, weight="BOLD"),
            )
            .arrange(RIGHT, buff=0.6)
            .move_to([3.6, 1.72, 0])
        )
        r_gap = Readout("gap", "none yet", at=(0.45, 2.62), fs=28)
        r_nodes = Readout("nodes explored", "0", at=(2.95, 2.62), fs=28)
        r_time = Readout("solver clock", "0.0 s", at=(5.2, 2.62), fs=28)
        live = {
            k: VGroup(r.val.copy())
            for k, r in (("gap", r_gap), ("nodes", r_nodes), ("time", r_time))
        }
        shown = {"plan": -1}

        def sync(m):
            t = chart.t
            k = max((i for i, p in enumerate(Z["plans"]) if p["time"] <= t), default=-1)
            if k != shown["plan"] and k >= 0:
                shown["plan"] = k
                dist.show(Z["plans"][k]["courses"])
            gap = chart.gap_at(t)
            nodes = Z["nodes"] if t >= t_end - 1e-6 else (chart.at(chart.nodes, t) or 0)
            for key, text, r in (
                ("gap", "none yet" if gap is None else f"{100 * gap:.1f} %", r_gap),
                ("nodes", f"{nodes:,.0f}", r_nodes),
                ("time", f"{t:.1f} s", r_time),
            ):
                if getattr(live[key], "text", None) != text:
                    live[key].text = text
                    live[key].become(VGroup(r.fresh(text)))

        driver = Mobject()
        driver.add_updater(sync)
        new_note = self.note(
            "Gurobi Optimizer 14.0 on the 11th arrondissement: bounds and plans recorded during the run."
        )
        self.play(
            self.tell("A whole district: 8 couriers, 32 orders, 1,248 switches.", vo),
            FadeOut(panel),
            FadeOut(log_note),
            FadeOut(r_one.lab),
            FadeOut(count_one),
            run_time=0.6,
        )
        self.play(FadeIn(win), FadeIn(new_note), run_time=0.6)
        self.play(Create(ring), run_time=0.8)
        self.cue("eight couriers")
        self.play(
            LaggedStart(*[FadeIn(m, scale=0.4) for m in dist.couriers], lag_ratio=0.15),
            run_time=0.9,
        )
        self.cue("thirty-two orders")
        self.play(
            LaggedStart(*[FadeIn(m) for m in dist.orders], lag_ratio=0.05), run_time=1.2
        )
        self.add(dist)
        web = dist.web(mix(RELAX_C, WHITE, 0.22)).set_z_index(2)
        assert len(Z["mins"]) == Z["binaries"]
        self.cue("one thousand two hundred")
        self.play(FadeIn(web), run_time=1.2)
        self.cue("Same model")
        self.play(
            FadeOut(web),
            FadeIn(chart.axes),
            FadeIn(legend),
            *[FadeIn(r.lab) for r in (r_gap, r_nodes, r_time)],
            run_time=0.8,
        )
        self.add(chart, driver, *live.values())
        self.cue("Here is the search")
        self.play(Tween(chart, t=t_end, run_time=t_end, rate_func=linear))  # real time
        self.hold()

        # ---- 6.6 the gap ------------------------------------------------------------------ #
        vo = (
            "More than thirty-one thousand nodes in three point four seconds, for a problem "
            "with three thousand billion billion billion ways to hand out its orders. "
            "The gap is closed: this plan is proven optimal. Stop a solver earlier, "
            "and the gap still tells you how far from the best you can possibly be."
        )
        assert chart.gap_at(t_end) < 1e-9 and Z["plans"][-1]["obj"] == Z["obj"] == 166.8
        # each of the 32 orders goes to one of the 8 couriers, or to nobody
        ways = (len(Z["couriers"]) + 1) ** len(Z["orders"])
        assert (
            3.0e30 < ways < 4.0e30 and f"{t_end:.1f}" == f"{Z['runtime']:.1f}" == "3.4"
        )
        proven = txt(
            f"{euro(Z['obj'])}  proven optimal", fs=22, color=DONE_C, weight="BOLD"
        )
        proven.move_to(chart.d_inc.get_center() + LEFT * 2.0 + DOWN * 0.55)
        self.play(
            self.tell(
                "Gap closed: proven optimal. Stopped early, a solver still reports its gap.",
                vo,
            )
        )
        dist.ride(60 / 23.5)  # the proven plan, ridden: its hour lasts the whole beat
        self.play(
            ripple(live["nodes"], color=PLAN_C),
            ripple(live["time"], color=PLAN_C),
            run_time=0.8,
        )
        ways_lab = mtext(
            [
                (f"ways to hand out its orders: {ways / 1e30:.1f} × 10", "b", INK),
                ("30", "^", INK),
            ],
            base_fs=20,
        ).move_to(legend)
        self.cue("for a problem with")
        self.play(  # the legend leaves, then the number takes its place
            FadeOut(legend, run_time=0.25),
            self.then(FadeIn(ways_lab, run_time=0.5), 0.25),
        )
        self.cue("The gap is closed")
        self.play(
            FadeIn(proven, shift=UP * 0.1),
            ripple(live["gap"], color=DONE_C),
            run_time=0.9,
        )
        self.cue("Stop a solver earlier")
        # go back to where the search stood after one second: a plan, and its guarantee
        t1 = 1.0
        g1 = chart.gap_at(t1)
        stop = DashedLine(
            chart.axes[0][0].get_start() + RIGHT * 6.3 * t1 / t_end,
            chart.axes[0][0].get_start() + RIGHT * 6.3 * t1 / t_end + UP * 3.1,
            dash_length=0.08,
        ).set_stroke(INK, width=2)
        s_lab = tag(
            f"stopped after 1 s: the best plan is at most {100 * g1:.1f} % better",
            fs=16,
        )
        s_lab.next_to(stop, UP, buff=0.06).align_to(stop, LEFT).shift(LEFT * 0.2)
        keep_inside(s_lab)
        self.play(  # that line leaves before the label that takes its place
            FadeOut(ways_lab, run_time=0.25),
            self.then(Create(stop, run_time=0.5), 0.25),
            self.then(FadeIn(s_lab, run_time=0.5), 0.25),
        )
        self.settle()
        self.wipe()


def _at(p):
    """A function that always returns the point ``p`` (a billboard's fixed anchor)."""
    p = np.array(p, dtype=float)
    return lambda: p


class _Shift:
    """The camera's screen shift as two plain attributes (for ``Tween``)."""

    def __init__(self, cam):
        self.cam, self.x, self.y = (
            cam,
            float(cam.screen_shift[0]),
            float(cam.screen_shift[1]),
        )

    def refresh(self):
        self.cam.screen_shift = np.array([self.x, self.y, 0.0])


class _Stage(_Common, ExplainerStageScene):
    """A scene on the 3D map of Paris, with a HUD."""

    ZT = 0.085  # world units per minute, when time is drawn as height

    def aim(self, points, zone, phi, theta, amp=0.0, centre=None):
        """The zoom and screen shift that keep ``points`` (world) inside ``zone``
        (x0, x1, y0, y1 on the screen) for a camera at ``phi`` / ``theta`` (degrees,
        swaying by ``amp``) looking at ``centre`` (default: where it looks now).
        The camera itself is left as it was."""
        cam = self.camera
        keep = (cam.get_phi(), cam.get_theta(), cam.get_zoom(), cam.screen_shift.copy())
        look = np.array(cam.frame_center, dtype=float)
        if centre is not None:
            cam._frame_center.move_to(centre)
        cam.set_phi(phi * DEGREES)
        cam.set_zoom(1.0)
        cam.screen_shift = np.zeros(3)
        lo, hi = np.full(2, np.inf), np.full(2, -np.inf)
        for th in np.linspace(theta - amp, theta + amp, 7 if amp else 1):
            cam.set_theta(th * DEGREES)
            cam.reset_rotation_matrix()
            q = cam.project_points(np.array(points, dtype=float))[:, :2]
            lo, hi = np.minimum(lo, q.min(axis=0)), np.maximum(hi, q.max(axis=0))
        cam.set_phi(keep[0])
        cam.set_theta(keep[1])
        cam.set_zoom(keep[2])
        cam.screen_shift = keep[3]
        cam._frame_center.move_to(look)
        cam.reset_rotation_matrix()
        x0, x1, y0, y1 = zone
        zoom = float(min((x1 - x0) / (hi[0] - lo[0]), (y1 - y0) / (hi[1] - lo[1])))
        mid = (lo + hi) / 2 * zoom
        return zoom, ((x0 + x1) / 2 - mid[0], (y0 + y1) / 2 - mid[1])

    def screen_at(self, points, phi, theta, zoom, shift):
        """Where world ``points`` land on the screen for a camera we are not at yet."""
        cam = self.camera
        keep = (cam.get_phi(), cam.get_theta(), cam.get_zoom(), cam.screen_shift.copy())
        cam.set_phi(phi * DEGREES)
        cam.set_theta(theta * DEGREES)
        cam.set_zoom(zoom)
        cam.screen_shift = np.array([shift[0], shift[1], 0.0])
        cam.reset_rotation_matrix()
        out = cam.project_points(np.array(points, dtype=float))[:, :2]
        cam.set_phi(keep[0])
        cam.set_theta(keep[1])
        cam.set_zoom(keep[2])
        cam.screen_shift = keep[3]
        cam.reset_rotation_matrix()
        return out

    def stage_desk(self):
        """The desk of the flat scenes as a 3D stage: same picture, seen from above."""
        desk = Desk()
        plane = desk.plane(wide=True)
        c = np.array([desk.at[0], desk.at[1], 0.0])
        self.set_camera_orientation(
            phi=0, theta=-90 * DEGREES, zoom=1.0, frame_center=c
        )
        self.camera.screen_shift = c.copy()
        col = self.hud(hud_column().set_z_index(8))
        bands = self.hud(
            VGroup(band(-4.1, -2.5), band(2.3, 4.1, top=True, x1=0.2)).set_z_index(7)
        )
        self.add(plane, bands, col)
        self.add(
            self.note(
                "Map data © OpenStreetMap contributors. Orders, fees and couriers are invented."
            )
        )
        return desk, plane

    def labels(self, stops):
        """The stops' labels as billboards: they face the camera wherever it goes."""
        for m in stops.labels:
            self.billboard(m, _at(m.get_center()), z=6)
        return stops.labels

    # ====================================================================== #
    # 3 · Say what you want
    # ====================================================================== #
    def scene_model(self):
        desk, plane = self.stage_desk()
        stops = Stops(plane).set_z_index(4)
        rides = RideSet(plane).set_z_index(1)
        self.add(rides, stops, self.labels(stops))
        self.header("3 · Say what you want", MINT)
        lines = model_lines()
        X, T, OBJ, START, ONCE, FLOW, TIME, RUN = (
            [0],
            [1],
            [2, 3, 4],
            [5, 6],
            [7, 8],
            [9, 10, 11],
            [12, 13, 14, 15],
            [16],
        )
        assert (
            "vtype=GRB.BINARY" in lines[0]
            and "lb=early" in lines[1]
            and "MAXIMIZE" in lines[4]
        )
        assert (
            "couriers" in lines[6] and "orders" in lines[8] and "x.sum(j" in lines[10]
        )
        assert (
            ">>" in lines[13]
            and "t[j] >= t[i] + mins[i, j]" in lines[14]
            and lines[16] == "m.optimize()"
        )
        panel = CodePanel(lines).hide_all()
        panel.shift(A([Desk.COL_MID, 3.5 - panel.h0 / 2, 0]) - panel.bg.get_center())
        self.hud_root(panel)
        hl = self.pin(breathing(panel.bar(X).set_z_index(11)))
        for m in panel.line:
            m.set_z_index(12)
        chain = [("lea", BEST[0]), (BEST[0], BEST[1]), (BEST[1], BEST[2])]
        assert chain == [("lea", "ramen"), ("ramen", "burger"), ("burger", "pasta")]

        def to(idxs):
            return [Transform(hl, panel.bar(idxs)), *panel.focus(idxs)]

        # ---- 3.1 decisions --------------------------------------------------------- #
        vo = (
            "So we stop searching by hand, and describe the problem instead. First, "
            "the decisions. For every possible ride, from one stop to an order, a "
            "variable that is zero or one: skip it, or ride it. Sixty-four switches."
        )
        self.play(
            self.tell("Decisions: one switch per possible ride, 0 or 1.", vo),
            FadeIn(panel),
            run_time=0.7,
        )
        self.cue("First, the decisions")
        self.play(FadeIn(hl), *panel.focus(X), run_time=0.5)
        self.cue("every possible ride")
        self.play(Dim(rides, rest=0.3, run_time=1.4))
        r1 = ("lea", "crêpes")  # a long ride, with free map under its far end
        on = tag("x[lea, crêpes] = 1", fs=16, color=PLAN_C, font=MONO, weight="BOLD")
        on.next_to(
            VGroup(stops.of["crêpes"][1], stops.dish["crêpes"]),
            DOWN,
            buff=0.16,
            aligned_edge=LEFT,
        )  # (the middle of the ride is crowded: a label there touches three others)
        assert stops.is_clear(on)
        off = tag(
            "x[lea, crêpes] = 0", fs=16, color=MUTED, font=MONO, weight="BOLD"
        ).move_to(on)
        for m in (on, off):
            self.billboard(m, _at(on.get_center()), z=7)
        self.cue("zero or one")
        self.play(
            Dim(rides, val={r1: 1.0}, tint={r1: 1.0}, run_time=0.4),
            FadeIn(on, scale=1.2),
            run_time=0.4,
        )
        self.cue("skip it")
        self.play(
            Dim(rides, val={r1: 0.3}, tint={r1: 0.0}, run_time=0.3),
            FadeOut(on),
            FadeIn(off),
            run_time=0.3,
        )
        self.cue("or ride it")
        self.play(
            Dim(rides, val={r1: 1.0}, tint={r1: 1.0}, run_time=0.3),
            FadeOut(off),
            FadeIn(on),
            run_time=0.3,
        )
        self.cue("Sixty-four")
        under = (Desk.COL_MID, -2.6)  # the strip between the code and the caption
        r_n = self.pin(
            figure_line(
                str(len(RIDES)), "switches, one per possible ride", at=under
            ).set_z_index(10)
        )
        assert len(RIDES) == 64
        self.play(FadeIn(r_n, shift=UP * 0.1), run_time=0.5)
        self.hold()

        # ---- 3.2 the goal ----------------------------------------------------------- #
        vo = (
            "Second, the goal: add up the fee of every order she rides to, and make "
            "that sum as large as possible."
        )
        self.play(
            self.tell(
                "The goal: the fees of the rides she takes, as high as possible.", vo
            ),
            *to(OBJ),
            FadeOut(r_n),
            FadeOut(on),
            Dim(rides, val={r1: 0.3}, tint={r1: 0.0}),
            run_time=0.6,
        )
        self.cue("the fee of every order")
        self.play(
            LaggedStart(
                *[
                    Indicate(stops.fee[j], color=PLAN_C, scale_factor=1.35)
                    for j in NAMES
                ],
                lag_ratio=0.12,
            ),
            run_time=1.8,
        )
        # what "that sum" is: two courses, and what each one collects
        tries = [
            c
            for c in HERO["brute"]["sample"]
            if c["seq"]
            in (
                ["kebab", "pasta", "pad thai"],
                ["ramen", "kebab", "burger", "pad thai"],
            )
        ]
        assert [c["pay"] for c in tries] == [17.5, 22.4]
        self.cue("make that sum")
        r_sum = None
        for c in tries:
            legs_ = list(zip(["lea", *c["seq"][:-1]], c["seq"], strict=True))
            val = {r: 0.07 for r in RIDES}
            val.update({r: 1.0 for r in legs_})
            new = self.pin(
                figure_line(
                    euro(c["pay"]),
                    "the sum of the fees on this course",
                    color=PLAN_C,
                    at=under,
                ).set_z_index(10)
            )
            self.play(
                Dim(
                    rides,
                    val=val,
                    tint={r: (1.0 if r in legs_ else 0.0) for r in RIDES},
                    run_time=0.6,
                ),
                *([FadeOut(r_sum, run_time=0.25)] if r_sum is not None else []),
                Succession(Wait(0.25), FadeIn(new, run_time=0.35)),
            )
            r_sum = new
            self.wait(0.15 if self.pace.quick else 1.3)
        self.hold()

        # ---- 3.3 the rules ---------------------------------------------------------- #
        vo = (
            "Third, the rules. A courier starts one course at most. An order is "
            "delivered at most once. And she can only leave a stop she has reached."
        )
        self.play(
            self.tell(
                "The rules: one start, each order once, no ride from nowhere.", vo
            ),
            FadeOut(r_sum),
            Dim(rides, rest=0.3, tint={r: 0.0 for r in RIDES}),
            run_time=0.5,
        )
        picked = {}
        for phrase, idxs, cand, pick in (
            ("A courier starts", START, [r for r in RIDES if r[0] == "lea"], chain[0]),
            (
                "An order is delivered",
                ONCE,
                [r for r in RIDES if r[1] == chain[1][1]],
                chain[1],
            ),
            (
                "she can only leave",
                FLOW,
                [r for r in RIDES if r[0] == chain[2][0]],
                chain[2],
            ),
        ):
            self.cue(phrase)
            val = {r: 0.07 for r in RIDES}
            val.update({r: 0.62 for r in cand})
            val.update(picked)
            self.play(*to(idxs), Dim(rides, val=val, run_time=0.6), run_time=0.6)
            self.wait(0.15 if self.pace.quick else 0.7)
            picked[pick] = 1.0
            val.update({r: 0.07 for r in cand})
            val.update(picked)
            self.play(Dim(rides, val=val, tint={pick: 1.0}, run_time=0.5))
        self.hold()

        # ---- 3.4 time, as height ------------------------------------------------------ #
        vo = (
            "The last rule is about time. Every order gets one more variable: the "
            "minute it is delivered. Draw time as height: each order's window becomes "
            "a bar."
        )
        zt = self.ZT
        top = META["shift"] * zt

        def up(xy, minute):
            return plane.w(A(xy), z=minute * zt)

        ground = np.array(
            [plane.w(stop_xy(i, e)) for i in ["lea", *NAMES] for e in ("R", "C")]
        )
        (x0, y0), (x1, y1) = (
            ground[:, :2].min(axis=0) - 0.35,
            ground[:, :2].max(axis=0) + 0.35,
        )
        floor_pts = [[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0]]
        box = floor_pts + [[x, y, top] for x, y, _ in floor_pts]
        roof = Polygon(*[[x, y, top] for x, y, _ in floor_pts]).set_stroke(
            INK, width=1.6, opacity=0.55
        )
        roof.set_fill(INK, opacity=0.05).set_z_index(3)
        # the time axis stands on the near left corner, clear of the windows
        axis = VGroup(
            Line([x0, y0, 0], [x0, y0, top]).set_stroke(MUTED, width=2)
        ).set_z_index(3)
        ticks = []
        for minute in (0, 30, 60):
            z = minute * zt
            axis.add(Line([x0, y0, z], [x0 + 0.14, y0, z]).set_stroke(MUTED, width=2))
            lab = tag(clock(minute), fs=16, color=INK, font=MONO)
            ticks.append(
                self.billboard(lab, lambda z=z: np.array([x0 - 0.42, y0 - 0.1, z]), z=6)
            )
        bars, posts = {}, VGroup().set_z_index(3)
        for j in NAMES:
            o = ORDERS[j]
            posts.add(
                Line(up(o["C"], 0), up(o["C"], o["early"])).set_stroke(
                    WINDOW_C, width=1.3, opacity=0.5
                )
            )
            b = Line(up(o["C"], o["early"]), up(o["C"], o["late"])).set_stroke(
                WINDOW_C, width=7.5, opacity=0.95
            )
            bars[j] = b.set_z_index(5)
        verts = np.array(HERO["timeline"]["v"])
        t_of = {j: t for kind, j, t in HERO["timeline"]["events"] if kind == "deliver"}
        cut = t_of[chain[2][1]]

        def thread(sel):
            v = verts[sel]
            core = VMobject().set_points_as_corners([up(q[1:], q[0]) for q in v])
            core.set_stroke(PLAN_C, width=4.6).set_z_index(6)
            core.joint_type = LineJointType.ROUND
            return core

        th_a, th_b = (
            thread(verts[:, 0] <= cut + 1e-9),
            thread(verts[:, 0] >= cut - 1e-9),
        )
        shadow = course_mob(plane, BEST, width=3.0, glow=False).set_z_index(2)
        shadow.core.set_stroke(opacity=0.38)
        beads = {
            j: Circle(radius=0.085)
            .set_stroke(BG, width=1.5)
            .set_fill(PLAN_C, 1.0)
            .move_to(up(ORDERS[j]["C"], t_of[j]))
            .set_z_index(7)
            for j in BEST
        }
        phi, theta, amp = 64, -77, 5
        # the right limit leaves room for the label that hangs right of the last
        # delivery: it must end before the HUD column (x = -0.55)
        zoom, shift = self.aim(box, (-6.1, -1.8, -2.45, 2.3), phi, theta, amp)
        shifter = _Shift(self.camera)

        def when(j, side=RIGHT):
            """The delivery of order j, labelled beside its bead: dish and minute."""
            lab = tag(f"{j}  {clock(t_of[j])}", fs=16, color=INK, weight="BOLD")
            pad = Rectangle(
                width=lab.width + 0.36, height=0.1, stroke_width=0, fill_opacity=0
            )
            g = VGroup(pad, lab).arrange(
                side, buff=0.0
            )  # its centre is the bead: the text hangs beside it
            return self.billboard(g, _at(up(ORDERS[j]["C"], t_of[j])), z=8)

        # (pizza and pasta are delivered a block apart: their labels hang on opposite sides)
        whens = {j: when(j, LEFT if j == "pizza" else RIGHT) for j in BEST}
        self.play(
            self.tell("And time: each order gets the minute it is delivered.", vo),
            *to(T),
            run_time=0.5,
        )
        self.move_camera(
            phi=phi * DEGREES, theta=theta * DEGREES, zoom=zoom,
            added_anims=[
                Tween(shifter, x=shift[0], y=shift[1], run_time=2.6),
                Dim(rides, rest=0.0, run_time=1.2),
                *[FadeOut(m, run_time=0.8) for j in NAMES for m in (stops.fee[j], stops.dish[j])],
                FadeIn(shadow, run_time=2.0),
            ],
            run_time=2.6,
        )  # fmt: skip
        self.sway(theta, amp=amp, period=17)
        self.cue("Every order gets")  # one variable per order: where each is delivered
        self.play(
            LaggedStart(
                *[ripple(stops.of[j][2], color=WINDOW_C, buff=0.06) for j in NAMES],
                lag_ratio=0.12,
            ),
            run_time=1.6,
        )
        self.cue("Draw time as height")
        self.play(Create(axis), *[FadeIn(m) for m in ticks], run_time=1.0)
        self.cue("each order's window")
        self.play(
            FadeIn(posts),
            LaggedStart(*[Create(bars[j]) for j in NAMES], lag_ratio=0.1),
            run_time=1.6,
        )
        self.hold()

        # ---- 3.4b the rule that links two delivery minutes -------------------------------- #
        vo = (
            "If she rides from one order to the next, the second minute comes at "
            "least one ride later. And every delivery must fall inside its window, "
            "before the hour ends."
        )
        self.play(
            self.tell(
                "Each delivery comes one ride after the last, inside its window.", vo
            ),
            *to(TIME),
            run_time=0.5,
        )
        self.cue("If she rides")
        self.play(Create(th_a, rate_func=linear), run_time=2.4)
        self.play(
            LaggedStart(
                *[
                    AnimationGroup(FadeIn(beads[j], scale=2.0), FadeIn(whens[j]))
                    for j in BEST[:3]
                ],
                lag_ratio=0.3,
            ),
            run_time=0.9,
        )
        self.cue("at least one ride later")
        i, j = chain[2]
        gap_min = HERO["mins"][f"{i}|{j}"]
        assert (
            abs((t_of[j] - t_of[i]) - gap_min) < 0.01
        )  # she does not wait on this ride
        # ... and the label agrees with the two clocks shown beside it
        assert int(t_of[j]) - int(t_of[i]) == round(gap_min) == 13
        rise = (
            Line(up(ORDERS[j]["C"], t_of[i]), up(ORDERS[j]["C"], t_of[j]))
            .set_stroke(INK, width=2.5)
            .set_z_index(6)
        )
        level = (
            DashedLine(
                up(ORDERS[i]["C"], t_of[i]),
                up(ORDERS[j]["C"], t_of[i]),
                dash_length=0.08,
            )
            .set_stroke(INK, width=1.6, opacity=0.8)
            .set_z_index(6)
        )
        r_tag = tag(f"{gap_min:.0f} min later", fs=16, color=PLAN_C, weight="BOLD")
        r_pad = Rectangle(
            width=r_tag.width + 0.3, height=0.1, stroke_width=0, fill_opacity=0
        )
        r_lab = VGroup(r_pad, r_tag).arrange(RIGHT, buff=0.0)
        self.billboard(r_lab, lambda: up(ORDERS[j]["C"], (t_of[i] + t_of[j]) / 2), z=8)
        self.play(Create(level), Create(rise), FadeIn(r_lab), run_time=0.9)
        self.cue("inside its window")
        self.play(*[bars[q].animate.set_stroke(DONE_C) for q in BEST[:3]], run_time=0.5)
        self.cue("before the hour ends")
        self.play(FadeIn(roof), run_time=0.8)
        self.hold()

        # ---- 3.5 solve ---------------------------------------------------------------- #
        vo = (
            "Whole-number decisions, continuous times, rules that can be written as "
            "linear inequalities: a mixed-integer program. One call, optimize, and the "
            "solver answers: twenty-four euros forty. The same course as trying "
            "everything, in two hundredths of a second."
        )
        g = HERO["gurobi"]
        assert g["obj"] == HERO["brute"]["obj"] == 24.4 and 0.012 < g["runtime"] < 0.03
        self.play(
            self.tell("A mixed-integer program. One call solves it.", vo),
            FadeOut(level),
            FadeOut(rise),
            FadeOut(r_lab),
            run_time=0.5,
        )
        self.cue("optimize")
        self.play(*to(RUN), run_time=0.4)
        self.play(Create(th_b, rate_func=linear), run_time=2.0)
        self.play(
            LaggedStart(
                *[
                    AnimationGroup(FadeIn(beads[q], scale=2.0), FadeIn(whens[q]))
                    for q in BEST[3:]
                ],
                lag_ratio=0.3,
            ),
            *[bars[q].animate.set_stroke(DONE_C) for q in BEST[3:]],
            run_time=0.7,
        )
        res = VGroup(
            line_txt(euro(g["obj"]), fs=32, color=PLAN_C, weight="BOLD", font=MONO),
            line_txt("proven optimal", fs=20, color=DONE_C, weight="BOLD"),
            line_txt(f"{g['runtime']:.2f} s", fs=20, color=MUTED, font=MONO),
        ).arrange(RIGHT, buff=0.4)
        align_baselines(*res)  # a big number, then small words: one baseline
        res.move_to([Desk.COL_MID, -2.6, 0]).set_z_index(10)
        self.pin(res)
        self.cue("twenty-four euros")
        self.play(FadeIn(res[0], shift=UP * 0.1), run_time=0.5)
        self.cue("The same course")
        self.play(FadeIn(res[1:], shift=UP * 0.1), run_time=0.5)
        self.settle()
        self.wipe()

    # ---- the whole city ------------------------------------------------------------ #
    CITY_VIEW = dict(phi=43, theta=-84, amp=6, zone=(-6.8, 6.8, -2.5, 2.75))

    def stage_city(self):
        """All of Paris under a tilted camera. World units: kilometres from the
        middle of the city. Returns the plane and the arrondissement outlines."""
        import city

        geo = city.geometry()
        rings = [geo.arrondissement(a)[0] for a in range(1, 21)]
        pts = np.vstack(rings)
        mid = (pts.min(axis=0) + pts.max(axis=0)) / 2
        plane = MapPlane(mid, 0.001)
        plane.add_layer(
            *BIG_VIEW[:3], 8192, aspect=BIG_VIEW[3], detail=False, feather=0.05
        )
        plane.add_layer(
            *Desk().mid, 6400.0, 4096, feather=0.12
        )  # sharp where the camera dives
        v = self.CITY_VIEW
        self.paris = plane.w(pts[:: max(1, len(pts) // 400)])
        zoom, shift = self.aim(
            self.paris, v["zone"], v["phi"], v["theta"], v["amp"], centre=ORIGIN
        )
        self.set_camera_orientation(
            phi=v["phi"] * DEGREES,
            theta=v["theta"] * DEGREES,
            zoom=zoom,
            frame_center=ORIGIN,
        )
        self.camera.screen_shift = np.array([shift[0], shift[1], 0.0])
        bands = self.hud(
            VGroup(band(-4.1, -2.45), band(2.4, 4.1, top=True)).set_z_index(7)
        )
        self.add(plane, bands)
        self.add(
            self.note(
                "Map data © OpenStreetMap contributors. Orders, fees and couriers are invented. Solver: Gurobi 14.0."
            )
        )
        self.sway(v["theta"], amp=v["amp"], period=19)
        return plane, rings

    # ====================================================================== #
    # 1 · Friday, 8 p.m.
    # ====================================================================== #
    def scene_night(self):
        plane, rings = self.stage_city()
        plane.opacity = 0.0
        swarm = Swarm(
            plane, [c["v"] for z in ZONES for c in z["couriers"]], color=PLAN_C
        )
        orders = Orders(
            plane, [o for z in ZONES for o in z["orders"]], color=LINK_C, done=DONE_C
        )
        guess = Guess(plane, ZONES, color=RELAX_C)
        swarm.pop, swarm.trail, orders.show = 0.0, 0.0, 0.0
        self.add(orders, guess, swarm)
        n_c, n_o = TOTALS["couriers"], TOTALS["orders"]
        assert (n_c, n_o) == (104, 403) and len(swarm.T) == n_c and len(orders.t) == n_o

        # ---- 1.1 the night ---------------------------------------------------------- #
        vo = (
            "Friday, eight p.m., in Paris. One hundred and four couriers are on their "
            "bikes, and four hundred and three meals are waiting in restaurant "
            "kitchens."
        )
        r_c = self.pin(
            Readout(
                "couriers", str(n_c), color=PLAN_C, at=(4.1, 3.2), fs=34
            ).set_z_index(10)
        )
        r_o = self.pin(
            Readout("orders", str(n_o), color=INK, at=(5.6, 3.2), fs=34).set_z_index(10)
        )
        self.play(
            self.tell("Friday, 8 p.m. in Paris: 104 couriers, 403 orders.", vo),
            Tween(plane, opacity=1.0, run_time=1.6),
            run_time=1.6,
        )
        self.header("1 · Friday, 8 p.m.", GOLD)
        self.cue("One hundred and four")
        self.play(
            Tween(swarm, pop=1.0, run_time=2.2, rate_func=linear),
            FadeIn(r_c, shift=DOWN * 0.1),
            run_time=2.2,
        )
        self.cue("four hundred and three")
        self.play(
            Tween(orders, show=1.0, run_time=2.6, rate_func=linear),
            FadeIn(r_o, shift=DOWN * 0.1),
            run_time=2.6,
        )
        self.hold()

        # ---- 1.2 the question -------------------------------------------------------- #
        vo = (
            "Who should deliver what, and in which sequence, so that the couriers "
            "earn the most in the next hour? Just handing out the orders can be done "
            "in more ways than there are atoms in the universe."
        )
        ways = TOTALS["log10_assignments"]
        assert ways > 80  # atoms in the observable universe: about 10^80
        self.play(
            self.tell("Who delivers what, and in which sequence?", vo),
            Tween(guess, alpha=1.0, run_time=0.5),
            run_time=0.5,
        )
        big = VGroup(
            txt("ways to hand out the orders", fs=18, color=MUTED),
            mtext([("10", "b"), (f"{ways:.0f}", "^")], base_fs=46),
            txt("atoms in the universe: about", fs=18, color=MUTED),
            mtext([("10", "b"), ("80", "^")], base_fs=30),
        )
        big[0].move_to([-4.6, -1.05, 0], aligned_edge=LEFT)
        big[1].next_to(big[0], DOWN, buff=0.16, aligned_edge=LEFT)
        big[2].next_to(big[1], DOWN, buff=0.3, aligned_edge=LEFT)
        big[3].next_to(big[2], RIGHT, buff=0.16, aligned_edge=DOWN)
        back = RoundedRectangle(
            width=big.width + 0.6,
            height=big.height + 0.5,
            corner_radius=0.14,
            stroke_width=0,
        )
        back.set_fill(BG, opacity=0.82).move_to(big)
        card = self.pin(VGroup(back, big).set_z_index(10))
        self.cue(
            "more ways than",
            lead=0.2,
            ambient=lambda rt: [
                Tween(guess, k=guess.k + rt * 2.2, run_time=rt, rate_func=linear)
            ],
        )
        self.play(
            FadeIn(card[0]),
            FadeIn(big[:2], shift=UP * 0.1),
            Tween(guess, k=guess.k + 1.5, run_time=0.7, rate_func=linear),
            run_time=0.7,
        )
        self.cue(
            "atoms in the universe",
            lead=0.2,
            ambient=lambda rt: [
                Tween(guess, k=guess.k + rt * 2.2, run_time=rt, rate_func=linear)
            ],
        )
        self.play(
            FadeIn(big[2:], shift=UP * 0.1),
            Tween(guess, k=guess.k + 1.5, run_time=0.7, rate_func=linear),
            run_time=0.7,
        )
        self.hold(
            ambient=lambda rt: [
                Tween(guess, k=guess.k + rt * 2.2, run_time=rt, rate_func=linear)
            ]
        )

        # ---- 1.3 follow one courier ---------------------------------------------------- #
        vo = (
            "A solver such as Gurobi finds the best plan, district by district, in "
            "under a minute, and proves that nothing better exists. To see how, "
            "follow one courier: Léa."
        )
        assert TOTALS["runtime"] < 60 and TOTALS["all_optimal"]
        # her marker faces the camera like the swarm's dots, at the size it has in
        # the next scene (a billboard keeps its size on screen: the zoom does not scale it)
        lea = courier_marker(ORIGIN, alive=True)
        self.billboard(lea, _at(plane.w(LEA)), z=6)
        name = tag("Léa", color=PLAN_C, weight="BOLD", fs=20)
        pad = Rectangle(
            width=name.width + 0.72, height=0.1, stroke_width=0, fill_opacity=0
        )
        who = VGroup(pad, name).arrange(RIGHT, buff=0.0)
        self.billboard(who, _at(plane.w(LEA)), z=8)
        self.play(
            self.tell(
                "A solver finds the best plan, and proves it. Follow one courier.", vo
            ),
            Tween(guess, alpha=0.0, run_time=0.6),
            FadeOut(card),
            run_time=0.6,
        )
        self.cue("To see how")
        self.sway(0, amp=0)
        desk = Desk()
        pts = plane.w(
            np.array(
                [
                    LEA,
                    *[o["R"] for o in ORDERS.values()],
                    *[o["C"] for o in ORDERS.values()],
                ]
            )
        )
        lo, hi = pts.min(axis=0) - 0.25, pts.max(axis=0) + 0.25
        box = [
            [lo[0], lo[1], 0],
            [hi[0], lo[1], 0],
            [hi[0], hi[1], 0],
            [lo[0], hi[1], 0],
        ]
        look = plane.w(desk.mid)
        phi, theta = 38, -90
        zoom, shift = self.aim(box, (-6.3, 6.3, -2.3, 2.5), phi, theta, centre=look)
        shifter = _Shift(self.camera)
        self.move_camera(
            phi=phi * DEGREES, theta=theta * DEGREES, zoom=zoom, frame_center=look,
            added_anims=[
                Tween(shifter, x=shift[0], y=shift[1], run_time=3.6),
                Tween(swarm, r=swarm.r * 1.0, run_time=3.6),
                FadeIn(lea, run_time=3.0),
                FadeOut(r_c, run_time=1.0),
                FadeOut(r_o, run_time=1.0),
            ],
            run_time=3.6,
        )  # fmt: skip
        self.cue("Léa")
        self.play(
            FadeIn(who, shift=UP * 0.1),
            ripple(lea, color=PLAN_C, buff=0.08),
            run_time=0.9,
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 7 · The whole city
    # ====================================================================== #
    def scene_city(self):
        plane, rings = self.stage_city()
        swarm = Swarm(
            plane, [c["v"] for z in ZONES for c in z["couriers"]], color=PLAN_C, zt=0.05
        )
        orders = Orders(
            plane, [o for z in ZONES for o in z["orders"]], color=LINK_C, done=DONE_C
        )
        swarm.trail = 0.0
        self.add(orders, swarm)
        self.header("7 · The whole city", GOOD)
        T = TOTALS
        assert T["all_optimal"] and len(ZONES) == 20 and 10_000 < T["binaries"] < 11_000
        assert 55 < T["runtime"] < 56 and (T["delivered"], T["greedy_delivered"]) == (
            378,
            332,
        )

        # the twenty zones: outlines on the ground, a board in the HUD
        outline = {}
        for z, ring in zip(ZONES, rings, strict=True):
            m = VMobject().set_points_as_corners(plane.w(ring))
            m.set_stroke(INK, width=1.6, opacity=0.0).set_fill(
                DONE_C, opacity=0.0
            ).set_z_index(2)
            outline[z["arr"]] = m
        cells, cw = {}, 0.56
        for k, z in enumerate(ZONES):
            box = RoundedRectangle(width=cw - 0.08, height=0.4, corner_radius=0.07)
            box.set_stroke(FAINT, width=1.5).set_fill(PANEL, opacity=0.9)
            box.move_to([1.42 + (k % 10) * cw, 3.42 - (k // 10) * 0.47, 0])
            num = txt(str(z["arr"]), fs=16, color=MUTED, font=MONO).move_to(box)
            cells[z["arr"]] = VGroup(box, num)
        board = VGroup(*cells.values()).set_z_index(10)
        clock_at = [0.84, 2.95, 0]  # the board's second row; the text grows leftwards

        def clock_text(text):
            return line_txt(text, fs=24, color=INK, font=MONO, weight="BOLD").move_to(
                clock_at, aligned_edge=RIGHT
            )

        clock_lab = (
            line_txt("solver time", fs=16, color=MUTED)
            .move_to([clock_at[0], 3.42, 0], aligned_edge=RIGHT)
            .set_z_index(10)
        )
        clock_val = VGroup(clock_text("0.0 s")).set_z_index(10)
        hud = VGroup(board, clock_lab, clock_val)
        self.hud_root(hud)
        done_at = np.cumsum([z["runtime"] for z in ZONES])

        class Solve:
            k = 0.0  # how many zones are solved (a float: the next one is on its way)

            @staticmethod
            def refresh():
                n = int(np.floor(Solve.k + 1e-9))
                for i, z in enumerate(ZONES):
                    a = float(np.clip(Solve.k - i, 0, 1))
                    flash = float(np.clip(1 - abs(Solve.k - i - 0.6) / 0.6, 0, 1))
                    outline[z["arr"]].set_fill(DONE_C, opacity=0.07 * a + 0.3 * flash)
                    outline[z["arr"]].set_stroke(
                        mix(INK, DONE_C, a), opacity=0.55 + 0.4 * a
                    )
                    box, num = cells[z["arr"]]
                    box.set_fill(mix(PANEL, DONE_C, 0.75 * a), opacity=0.9).set_stroke(
                        mix(FAINT, DONE_C, a)
                    )
                    num.set_color(mix(MUTED, BG, a))
                secs = 0.0 if n == 0 else float(done_at[n - 1])
                text = f"{secs:.1f} s"
                if getattr(clock_val, "text", None) != text:
                    clock_val.text = text
                    clock_val.become(VGroup(clock_text(text)))

        # ---- 7.1 twenty models ------------------------------------------------------ #
        vo = (
            "Back to Friday night. Each courier serves one arrondissement, so the "
            "same model runs once per arrondissement: twenty models, more than ten "
            "thousand switches in all. Gurobi solves them one after the other in "
            "fifty-five seconds, and every one is proven optimal."
        )
        self.play(
            self.tell(
                "Twenty arrondissements, twenty models, all solved to proven optimality.",
                vo,
            )
        )
        self.cue("once per arrondissement")
        self.add(*outline.values())
        self.play(
            LaggedStart(
                *[m.animate.set_stroke(opacity=0.55) for m in outline.values()],
                lag_ratio=0.08,
            ),
            FadeIn(hud),
            run_time=2.0,
        )
        self.cue("Gurobi solves them")
        self.play(Tween(Solve, k=20.0, run_time=5.0, rate_func=linear))
        self.hold()

        # ---- 7.2 the hour -------------------------------------------------------------- #
        vo = (
            "And the couriers ride. One hour later: three hundred and seventy-eight "
            "of the four hundred and three meals delivered, two thousand one hundred "
            "and sixty euros earned."
        )
        times = np.sort(orders.t[np.isfinite(orders.t)])
        pays = np.array([o["pay"] for z in ZONES for o in z["orders"]])[
            np.argsort(orders.t)
        ][: len(times)]
        earned = np.cumsum(pays)
        assert len(times) == T["delivered"] and abs(earned[-1] - T["obj"]) < 0.05
        r_clock = Readout("Friday", "20:00", at=(0.3, 3.25), fs=32)
        r_meals = Readout(
            f"meals delivered, of {T['orders']}",
            "0",
            at=(2.15, 3.25),
            fs=32,
            color=DONE_C,
        )
        r_euro = Readout(
            "couriers' earnings", "€0", at=(4.95, 3.25), fs=32, color=PLAN_C
        )
        row = (
            r_clock,
            r_meals,
            r_euro,
        )  # three readouts side by side: 0.4 apart at least
        assert (
            all(
                a.get_right()[0] + 0.4 < b.get_left()[0]
                for a, b in zip(row, row[1:], strict=False)
            )
            and r_euro.fresh(f"€{T['obj']:,.0f}").get_right()[0]
            < config.frame_width / 2 - SAFE
        )
        live = {
            "clock": VGroup(r_clock.val.copy()),
            "meals": VGroup(r_meals.val.copy()),
            "euro": VGroup(r_euro.val.copy()),
        }
        ride_hud = VGroup(
            r_clock.lab, r_meals.lab, r_euro.lab, *live.values()
        ).set_z_index(10)
        self.hud_root(ride_hud)

        class Ride:
            now = 0.0

            @staticmethod
            def refresh():
                swarm.now = orders.now = Ride.now
                k = int(np.searchsorted(times, Ride.now, side="right"))
                for key, text, r in (
                    ("clock", clock(min(Ride.now, 60)), r_clock),
                    ("meals", str(k), r_meals),
                    ("euro", f"€{(earned[k - 1] if k else 0):,.0f}", r_euro),
                ):
                    if getattr(live[key], "text", None) != text:
                        live[key].text = text
                        live[key].become(VGroup(r.fresh(text)))

        Ride.refresh()
        self.play(
            self.tell("20:00 to 21:00: the couriers ride the plan.", vo),
            FadeOut(hud),
            *[
                m.animate.set_fill(opacity=0.0).set_stroke(INK, opacity=0.3)
                for m in outline.values()
            ],
            run_time=0.6,
        )
        self.play(FadeIn(ride_hud), Tween(swarm, trail=1.0, run_time=0.5), run_time=0.5)
        self.play(Tween(Ride, now=60.0, run_time=12.0, rate_func=linear))
        self.hold()

        # ---- 7.3 against the obvious rule ------------------------------------------------ #
        vo = (
            "The obvious rule, always sending the order that can be delivered "
            "soonest, would have delivered forty-six meals fewer, and earned the "
            "couriers fifteen percent less."
        )
        less = 1 - T["greedy"] / T["obj"]
        assert T["delivered"] - T["greedy_delivered"] == 46 and 0.145 < less < 0.155
        unit = 5.2 / T["obj"]
        rows = VGroup()
        for label, euros, meals, color in (
            ("soonest first", T["greedy"], T["greedy_delivered"], MEH_C),
            ("solved to optimality", T["obj"], T["delivered"], PLAN_C),
        ):
            bar = Rectangle(width=euros * unit, height=0.34, stroke_width=0).set_fill(
                color, opacity=0.95
            )
            name = line_txt(label, fs=18, color=INK, weight="MEDIUM")
            val = line_txt(
                f"€{euros:,.2f}   {meals} meals",
                fs=18,
                color=color,
                font=MONO,
                weight="BOLD",
            )
            rows.add(VGroup(name, bar, val))
        for k, row in enumerate(rows):
            name, bar, val = row
            y = -0.9 - k * 0.62
            bar.move_to([-3.2 + bar.width / 2, y, 0])
            name.next_to(bar, LEFT, buff=0.2)
            val.next_to(bar, RIGHT, buff=0.2)
        back = RoundedRectangle(
            width=rows.width + 0.7,
            height=rows.height + 0.55,
            corner_radius=0.14,
            stroke_width=0,
        )
        back.set_fill(BG, opacity=0.86).move_to(rows)
        versus = self.pin(VGroup(back, rows).set_z_index(10))
        fit_in_frame(versus)
        self.play(
            self.tell(
                "Same couriers, same hour: 46 more meals than the obvious rule.", vo
            ),
            FadeIn(back),
            run_time=0.6,
        )
        self.cue("The obvious rule")
        self.play(FadeIn(rows[0][0]), GrowFromEdge(rows[0][1], LEFT), run_time=0.9)
        self.play(FadeIn(rows[0][2]), run_time=0.3)
        self.cue("forty-six meals fewer")
        self.play(FadeIn(rows[1][0]), GrowFromEdge(rows[1][1], LEFT), run_time=0.9)
        self.play(FadeIn(rows[1][2]), run_time=0.3)
        self.hold()

        # ---- 7.4 the hour as threads; takeaway ------------------------------------------- #
        vo = (
            "That is mixed-integer programming. You describe the plan you want: "
            "decisions, a goal, rules. The solver relaxes, branches and bounds, until "
            "it can prove its answer."
        )
        v = self.CITY_VIEW
        top = [[x, y, 60 * swarm.zt] for x, y, _ in self.paris[::8]]
        zoom, shift = self.aim(
            [*self.paris, *top], (-6.6, 6.6, -2.3, 2.6), 60, v["theta"], v["amp"]
        )
        shifter = _Shift(self.camera)
        k1 = txt("Describe the plan you want.", fs=36, color=INK, weight="BOLD")
        k2 = txt("The solver searches, and proves.", fs=27, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.3).move_to([0, -1.55, 0])
        plate2 = RoundedRectangle(
            width=max(k1.width, k2.width) + 1.0,
            height=1.75,
            corner_radius=0.16,
            stroke_width=0,
        )
        plate2.set_fill(BG, opacity=0.84).move_to(VGroup(k1, k2))
        self.pin(VGroup(plate2, k1, k2).set_z_index(10))
        self.play(self.tell("", vo), FadeOut(versus), FadeOut(ride_hud), run_time=0.6)
        self.move_camera(
            phi=60 * DEGREES, zoom=zoom,
            added_anims=[
                Tween(shifter, x=shift[0], y=shift[1], run_time=3.2),
                Tween(swarm, lift=1.0, run_time=3.2),
                Tween(orders, alpha=0.35, run_time=2.0),
            ],
            run_time=3.2,
        )  # fmt: skip
        self.cue("You describe")
        self.play(FadeIn(plate2), FadeIn(k1, shift=UP * 0.1), run_time=0.7)
        self.cue("The solver relaxes")
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()


class Intro(_Flat):
    def construct(self):
        self.over_card(
            "Mixed-integer programming: how a solver finds the best plan among "
            "billions, and proves it. Our example: delivering meals in Paris, on a "
            "Friday night."
        )
        self.play_intro()


class Outro(_Flat):
    def construct(self):
        self.play_outro()


class Hour(_Flat):
    def construct(self):
        self.scene_hour()


class City(_Stage):
    def construct(self):
        self.scene_city()


class Night(_Stage):
    def construct(self):
        self.scene_night()


class Model(_Stage):
    def construct(self):
        self.scene_model()


class Solver(_Flat):
    def construct(self):
        self.scene_solver()


class Branch(_Flat):
    def construct(self):
        self.scene_branch()


class Relax(_Flat):
    def construct(self):
        self.scene_relax()
