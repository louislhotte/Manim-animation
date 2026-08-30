"""Precision, Recall & F1 — a short, house-style explainer.

A self-explanatory (no voice-over) film that builds the confusion matrix from a
concrete example and then shows precision, recall, F1 — and, crucially, *when to
maximise each*:

    1. Matrix     -- 20 items, 8 truly relevant; the model flags 10. Sort them
                     into the 2x2 confusion matrix: TP / FP / FN / TN.
    2. Precision  -- of everything you FLAGGED, how much was right? (the column)
                     maximise it when a false alarm is costly (spam, recs).
    3. Recall     -- of everything that MATTERED, how much did you catch? (the row)
                     maximise it when a miss is costly (retrieval/RAG, medical,
                     fraud, e-discovery) — you'd rather over-include than miss the
                     one that matters.
    4. Trade-off  -- one model, a moving decision threshold: push recall up and
                     precision falls, and vice-versa. F1 = the harmonic mean that
                     is only high when BOTH are high.
    5. Recap      -- a one-card summary: maximise recall vs precision vs F1.

Bookended by the channel's intro card and the "Thank you for watching!" outro,
matching animations/BiasVariance/bias_variance.py.

Everything uses ``Text`` (Pango), never ``Tex`` — so it renders with no LaTeX
toolchain and stays fast to iterate on. Every precision / recall / F1 number on
screen is computed from the counts actually shown (TP=6, FP=4, FN=2, TN=8; and
the 20-item ordering in the trade-off scene), not faked.

Scenes are exposed individually (``Matrix``, ``Precision``, ``Recall``,
``Tradeoff``, ``Recap``, ``Intro``, ``Outro``) and as one film
(``PrecisionRecallF1``).

Env knobs:
    PRF_QUICK=1   shorten every hold for a fast sanity render
    PRF_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("PRF_QUICK") == "1"
# One knob for pacing: every reading "hold" is scaled by this. QUICK collapses
# the holds for fast iteration; otherwise it sets a comfortable reading rhythm
# (give the eye time to finish the text before anything moves on).
DELAY = float(os.environ.get("PRF_DELAY", "0.3" if QUICK else "1.7"))
# Extra hold on each scene's final frame, before it wipes to the next scene —
# so the reader can finish the last line before the transition.
END_HOLD = 0.2 if QUICK else 1.6

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
GRID = "#232A38"        # faint gridlines / panel fills

REL_C = "#FFD166"       # truly relevant / positive item (gold)
NEG_C = "#4A5568"       # not relevant / negative item (slate)

TP_C = "#3DD68C"        # true positive  — caught it            (green)
FP_C = "#FF8C42"        # false positive — false alarm          (amber)
FN_C = "#FF5C5C"        # false negative — the miss             (red)
TN_C = "#6B7280"        # true negative  — correctly skipped    (grey)

PREC_C = "#5B8DEF"      # the precision metric (blue)
REC_C = "#C77DFF"       # the recall metric    (violet)
F1_C = "#FFD166"        # the F1 metric        (gold)

# ---- the running example (all downstream numbers derive from these) ------- #
TP, FP, FN, TN = 6, 4, 2, 8
N_FLAGGED = TP + FP          # 10  (the "flagged" / predicted-positive column)
N_RELEVANT = TP + FN         # 8   (the "truly relevant" / actual-positive row)
PRECISION = TP / N_FLAGGED   # 0.60
RECALL = TP / N_RELEVANT     # 0.75
F1 = 2 * PRECISION * RECALL / (PRECISION + RECALL)   # 0.667


# ---- crisp text: render big, scale down (Pango mangles small sizes) ------- #
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


def pct(x):
    return f"{round(100 * x)}%"


# ========================================================================== #
# Small reusable pieces
# ========================================================================== #
def bullet(text, color=INK, fs=25, dot=REL_C, dot_r=0.06):
    d = Dot(radius=dot_r, color=dot)
    t = Text(text, font_size=fs, color=color)
    t.next_to(d, RIGHT, buff=0.22)
    d.align_to(t, UP).shift(DOWN * 0.11)
    return VGroup(d, t)


def hrow(*mobs, buff=0.12):
    return VGroup(*mobs).arrange(RIGHT, buff=buff, aligned_edge=DOWN)


def fraction(num_pieces, den_pieces, fs=30, bar_color=INK):
    """A real stacked fraction built from coloured Text pieces (no LaTeX).

    num_pieces / den_pieces are lists of (string, color) tuples.
    """
    num = hrow(*[Text(s, font_size=fs, color=c, weight="BOLD") for s, c in num_pieces])
    den = hrow(*[Text(s, font_size=fs, color=c, weight="BOLD") for s, c in den_pieces])
    w = max(num.width, den.width) + 0.28
    bar = Line(LEFT * w / 2, RIGHT * w / 2).set_stroke(bar_color, 3)
    num.next_to(bar, UP, buff=0.14)
    den.next_to(bar, DOWN, buff=0.14)
    return VGroup(num, bar, den)


# ========================================================================== #
class _PRBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.25))

    def wipe(self, rt=0.7):
        # hold the finished scene a beat longer so the last line can be read,
        # then clear updaters and fade everything out.
        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(txt, line)

    def say(self, text, color=INK, fs=26, y=-3.35, weight=NORMAL):
        """A running bottom caption, clamped to the safe width."""
        cap = Text(text, font_size=fs, color=color, weight=weight)
        if cap.width > 12.6:
            cap.scale_to_fit_width(12.6)
        cap.move_to([0, y, 0])
        return cap

    def clamp_w(self, mob, w=6.6):
        if mob.width > w:
            mob.scale_to_fit_width(w)
        return mob

    def place_card(self, card, center, max_w=6.3, max_h=3.15):
        """Scale a side-card down so it never bleeds past the safe frame edges."""
        s = min(1.0, max_w / card.width, max_h / card.height)
        if s < 1.0:
            card.scale(s)
        card.move_to(center)
        return card

    # ---- house-style intro / outro cards ---------------------------------- #
    def introduction(self, title1, title2):
        header = Text(title1, font_size=52, color=INK, weight="BOLD")
        header.set(width=min(10.5, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=F1_C)
        writer = Text("Created by Ptolémé", font_size=28, color=PREC_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text(title2, font_size=34, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "Precision, Recall & F1",
            "What a classifier gets right — and what it misses",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=F1_C)
        writer = Text("Created by Ptolémé", font_size=28, color=PREC_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # The reusable confusion matrix
    # ====================================================================== #
    CELL_W, CELL_H, GAP = 2.35, 1.5, 0.16

    def _cell_center(self, key):
        dx = (self.CELL_W + self.GAP) / 2
        dy = (self.CELL_H + self.GAP) / 2
        return {
            "TP": np.array([-dx, dy, 0.0]),
            "FN": np.array([dx, dy, 0.0]),
            "FP": np.array([-dx, -dy, 0.0]),
            "TN": np.array([dx, -dy, 0.0]),
        }[key]

    def make_cm(self, center=ORIGIN, scale=1.0):
        """Build the 2x2 confusion matrix. Returns a VGroup with attributes:

        .cell[k]  cell background   .tag[k]  the TP/FP/FN/TN pill
        .count[k] the big count     .word[k] the plain-language word
        .col_head / .row_head       header labels
        .col_hi   (left col overlay, precision)   .row_hi (top row overlay, recall)

        Every piece (counts included) is parented to the group, so a single
        .scale()/.move_to() keeps them all aligned. The highlight overlays are
        built *after* the transform and left out of the group, so scenes reveal
        them on demand.
        """
        spec = {
            "TP": (TP, TP_C, "TP", "caught"),
            "FN": (FN, FN_C, "FN", "missed"),
            "FP": (FP, FP_C, "FP", "false alarm"),
            "TN": (TN, TN_C, "TN", "skipped"),
        }
        cm = VGroup()
        cm.cell, cm.tag, cm.count, cm.word = {}, {}, {}, {}
        for k, (n, col, name, word) in spec.items():
            c = self._cell_center(k)
            box = RoundedRectangle(width=self.CELL_W, height=self.CELL_H, corner_radius=0.12,
                                   stroke_color=col, stroke_width=2.5,
                                   fill_color=col, fill_opacity=0.10).move_to(c)
            tag = Text(name, font_size=20, color=col, weight="BOLD")
            tag.next_to(box.get_corner(UL), DR, buff=0.14)
            num = Text(str(n), font_size=46, color=INK, weight="BOLD")
            num.move_to(box.get_center()).shift(DOWN * 0.04)
            wrd = Text(word, font_size=18, color=col)
            wrd.next_to(box.get_bottom(), UP, buff=0.12)
            cm.cell[k], cm.tag[k], cm.count[k], cm.word[k] = box, tag, num, wrd
            cm.add(box, tag, wrd, num)

        # column headers (the model's decision)
        colL = Text("Model\nflags it", font_size=20, color=INK, line_spacing=0.7)
        colR = Text("Model\nskips it", font_size=20, color=INK, line_spacing=0.7)
        top_edge = cm.cell["TP"].get_top()[1]
        colL.move_to([self._cell_center("TP")[0], top_edge + 0.42, 0])
        colR.move_to([self._cell_center("FN")[0], top_edge + 0.42, 0])
        # row headers (the truth)
        rowT = Text("Truly\nrelevant", font_size=20, color=REL_C, line_spacing=0.7)
        rowB = Text("Not\nrelevant", font_size=20, color=NEG_C, line_spacing=0.7)
        left_edge = cm.cell["TP"].get_left()[0]
        rowT.move_to([left_edge - 0.72, self._cell_center("TP")[1], 0])
        rowB.move_to([left_edge - 0.72, self._cell_center("FP")[1], 0])
        cm.col_head = VGroup(colL, colR)
        cm.row_head = VGroup(rowT, rowB)
        cm.add(cm.col_head, cm.row_head)

        cm.scale(scale).move_to(center)

        # highlight overlays — built after the transform so they hug the *final*
        # cells; deliberately not added to cm (scenes reveal them on demand).
        left_cells = VGroup(cm.cell["TP"], cm.cell["FP"])
        top_cells = VGroup(cm.cell["TP"], cm.cell["FN"])
        cm.col_hi = SurroundingRectangle(left_cells, color=PREC_C, buff=0.10,
                                         corner_radius=0.14).set_stroke(width=5)
        cm.row_hi = SurroundingRectangle(top_cells, color=REC_C, buff=0.10,
                                         corner_radius=0.14).set_stroke(width=5)
        return cm

    # ====================================================================== #
    # Scene 1 — Build the confusion matrix from 20 concrete items
    # ====================================================================== #
    def scene_matrix(self):
        header = self.section_header("The confusion matrix", INK)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # 20 items in a 5x4 grid. Truth: 8 relevant (gold), 12 not (slate).
        # relevant indices chosen so a later "flag 10" gives TP6/FP4/FN2/TN8.
        rel = [True, True, True, True, False, True, False, True, False, False,
               False, True, False, False, False, True, False, False, False, False]
        flagged = [True, True, True, True, True, True, False, True, False, True,
                   False, False, True, False, False, False, True, False, False, False]
        # sanity (kept honest): counts must match the running example
        tp = sum(r and f for r, f in zip(rel, flagged))
        fp = sum((not r) and f for r, f in zip(rel, flagged))
        fn = sum(r and (not f) for r, f in zip(rel, flagged))
        assert (tp, fp, fn) == (TP, FP, FN), (tp, fp, fn)

        cols, rows = 5, 4
        x0, y0, sx, sy = -2.9, 1.55, 1.45, 1.05
        dots = VGroup()
        for i in range(20):
            r, c = divmod(i, cols)
            p = [x0 + c * sx, y0 - r * sy, 0]
            d = Dot(p, radius=0.16, color=REL_C if rel[i] else NEG_C)
            d.set_stroke(INK, width=1.2, opacity=0.5)
            dots.add(d)
        cap = self.say("20 items — 8 are truly relevant (gold).", color=MUTED)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.05),
                  run_time=1.6)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.5)
        self.beat(1.4)

        # the model flags 10 of them (a ring around each flagged item)
        rings = VGroup()
        for i in range(20):
            if flagged[i]:
                rings.add(Circle(radius=0.26, color=PREC_C, stroke_width=4)
                          .move_to(dots[i]))
        cap2 = self.say("The model flags 10 as relevant (blue rings).", color=PREC_C)
        self.play(ReplacementTransform(cap, cap2),
                  LaggedStart(*[Create(r) for r in rings], lag_ratio=0.06),
                  run_time=1.6)
        self.beat(1.6)

        # sort every item into its confusion-matrix cell
        cm = self.make_cm(center=[0.15, -0.35, 0], scale=0.92)
        # pre-compute slot positions inside each cell
        slot_iter = {k: iter(self._cell_slots(cm, k)) for k in ("TP", "FP", "FN", "TN")}

        def category(i):
            if rel[i] and flagged[i]:
                return "TP"
            if (not rel[i]) and flagged[i]:
                return "FP"
            if rel[i] and (not flagged[i]):
                return "FN"
            return "TN"

        cat_color = {"TP": TP_C, "FP": FP_C, "FN": FN_C, "TN": TN_C}
        cap3 = self.say("Sort each item by (truth × decision) → four outcomes.",
                        color=INK)
        self.play(FadeOut(rings), ReplacementTransform(cap2, cap3),
                  FadeIn(cm.cell["TP"], cm.cell["FN"], cm.cell["FP"], cm.cell["TN"]),
                  FadeIn(cm.col_head, cm.row_head),
                  run_time=1.1)
        moves = []
        for i in range(20):
            k = category(i)
            target = next(slot_iter[k])
            moves.append(dots[i].animate.move_to(target).set_color(cat_color[k])
                         .scale(0.62))
        self.play(LaggedStart(*moves, lag_ratio=0.05), run_time=2.2)
        self.beat(1.0)

        # label the cells and collapse each cluster into its count
        reveal = []
        for k in ("TP", "FN", "FP", "TN"):
            reveal += [FadeIn(cm.tag[k]), FadeIn(cm.word[k]),
                       FadeIn(cm.count[k], scale=1.3)]
        cap4 = self.say("Every metric is just a ratio of these four numbers.",
                        color=INK, weight=BOLD)
        self.play(*reveal, ReplacementTransform(cap3, cap4),
                  dots.animate.set_opacity(0.0), run_time=1.0)
        self.remove(dots)
        self.beat(2.0)
        self.wipe()

    def _cell_slots(self, cm, key):
        """Grid of positions inside a cell to lay the item-dots out neatly."""
        n = {"TP": TP, "FP": FP, "FN": FN, "TN": TN}[key]
        box = cm.cell[key]
        c = box.get_center() + LEFT * 0.42   # dots sit on the left, count on right
        cols = 2
        rows = int(np.ceil(n / cols))
        sx, sy = 0.34, 0.34
        slots = []
        for j in range(n):
            rr, cc = divmod(j, cols)
            slots.append(c + np.array([(cc - (cols - 1) / 2) * sx,
                                       ((rows - 1) / 2 - rr) * sy, 0]))
        return slots

    # ====================================================================== #
    # Scene 2 — Precision
    # ====================================================================== #
    def scene_precision(self):
        header = self.section_header("Precision", PREC_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        cm = self.make_cm(center=[-3.55, -0.15, 0], scale=0.78)
        self.play(FadeIn(cm), run_time=0.8)
        self.beat(0.4)

        q = Text("Of everything you flagged,\nhow much was right?",
                 font_size=28, color=INK, line_spacing=0.8)
        self.clamp_w(q, 6.5).move_to([3.0, 2.25, 0])
        self.play(FadeIn(q, shift=UP * 0.15), run_time=0.7)
        self.beat(1.0)

        # highlight the flagged column
        self.play(Create(cm.col_hi), run_time=0.8)
        colcap = Text("the flagged column", font_size=20, color=PREC_C)
        colcap.next_to(cm.col_hi, DOWN, buff=0.16)
        self.play(FadeIn(colcap, shift=UP * 0.1), run_time=0.5)
        self.beat(1.0)

        frac = fraction([("TP", TP_C)],
                        [("TP", TP_C), ("+", INK), ("FP", FP_C)], fs=30)
        eq = Text("=", font_size=34, color=INK)
        val = Text(f"{TP} / {N_FLAGGED}  =  {pct(PRECISION)}", font_size=32,
                   color=PREC_C, weight="BOLD")
        formula = VGroup(frac, eq, val).arrange(RIGHT, buff=0.3)
        formula.move_to([3.0, 1.05, 0])
        self.play(FadeIn(frac, shift=UP * 0.1), run_time=0.7)
        self.beat(0.5)
        self.play(FadeIn(eq), FadeIn(val, shift=RIGHT * 0.1), run_time=0.7)
        self.beat(1.4)

        mean = Text("Precision = how much you can trust a “yes.”",
                    font_size=24, color=INK)
        self.clamp_w(mean, 6.6).move_to([3.0, 0.0, 0])
        self.play(FadeIn(mean, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)

        # when to maximise precision
        card = self._use_card(
            "Maximise precision when a false alarm is costly",
            ["Spam filter — don't trash a real email",
             "Recommendations — a bad pick erodes trust",
             "Flagging for costly human review"],
            PREC_C, punch="Be sure before you flag.")
        self.place_card(card, [3.0, -2.05, 0])
        self.play(FadeIn(card, shift=UP * 0.15), run_time=0.8)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Recall  (the headline: maximise recall in retrieval)
    # ====================================================================== #
    def scene_recall(self):
        header = self.section_header("Recall", REC_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        cm = self.make_cm(center=[-3.55, -0.15, 0], scale=0.78)
        self.play(FadeIn(cm), run_time=0.8)
        self.beat(0.4)

        q = Text("Of everything that mattered,\nhow much did you catch?",
                 font_size=28, color=INK, line_spacing=0.8)
        self.clamp_w(q, 6.5).move_to([3.0, 2.25, 0])
        self.play(FadeIn(q, shift=UP * 0.15), run_time=0.7)
        self.beat(1.0)

        # highlight the truly-relevant row + flash the missed cell
        self.play(Create(cm.row_hi), run_time=0.8)
        rowcap = Text("the relevant row", font_size=19, color=REC_C)
        rowcap.next_to(cm.cell["FN"], RIGHT, buff=0.22)
        self.play(FadeIn(rowcap, shift=DOWN * 0.1), run_time=0.5)
        self.play(Indicate(VGroup(cm.count["FN"], cm.tag["FN"]), color=FN_C,
                           scale_factor=1.25), run_time=0.9)
        self.beat(1.0)

        frac = fraction([("TP", TP_C)],
                        [("TP", TP_C), ("+", INK), ("FN", FN_C)], fs=30)
        eq = Text("=", font_size=34, color=INK)
        val = Text(f"{TP} / {N_RELEVANT}  =  {pct(RECALL)}", font_size=32,
                   color=REC_C, weight="BOLD")
        formula = VGroup(frac, eq, val).arrange(RIGHT, buff=0.3)
        formula.move_to([3.0, 1.05, 0])
        self.play(FadeIn(frac, shift=UP * 0.1), run_time=0.7)
        self.beat(0.5)
        self.play(FadeIn(eq), FadeIn(val, shift=RIGHT * 0.1), run_time=0.7)
        self.beat(1.4)

        mean = Text("Recall = how little slips past you.",
                    font_size=24, color=INK)
        self.clamp_w(mean, 6.6).move_to([3.0, 0.0, 0])
        self.play(FadeIn(mean, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)

        card = self._use_card(
            "Maximise recall when a miss is costly",
            ["Retrieval / RAG — keep the key passage",
             "Medical screening — never miss a case",
             "Fraud, security & legal e-discovery"],
            REC_C, punch="Rather over-include than miss it.")
        self.place_card(card, [3.0, -2.05, 0])
        self.play(FadeIn(card, shift=UP * 0.15), run_time=0.8)
        self.beat(2.4)
        self.wipe()

    def _use_card(self, title, items, color, punch=None):
        head = Text(title, font_size=22, color=color, weight="BOLD")
        rows = VGroup(*[bullet(t, fs=20, dot=color, dot_r=0.05) for t in items])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        body = VGroup(head, rows).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        if punch:
            pl = Text(punch, font_size=21, color=INK, weight="BOLD", slant=ITALIC)
            body.add(pl)
            pl.next_to(rows, DOWN, aligned_edge=LEFT, buff=0.22)
        box = RoundedRectangle(width=body.width + 0.6, height=body.height + 0.5,
                               corner_radius=0.16, stroke_color=color, stroke_width=2.5,
                               fill_color=color, fill_opacity=0.08)
        box.move_to(body)
        return VGroup(box, body)

    # ====================================================================== #
    # Scene 4 — The trade-off & F1
    # ====================================================================== #
    def scene_tradeoff(self):
        header = self.section_header("The trade-off", F1_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # 20 items sorted left->right by the model's confidence score.
        rel = [True, True, True, True, False, True, False, True, False, False,
               False, True, False, False, False, True, False, False, False, False]
        n = len(rel)
        x0, x1, y = -5.7, 5.7, 1.5
        xs = np.linspace(x0, x1, n)
        dots = VGroup()
        for i in range(n):
            d = Dot([xs[i], y, 0], radius=0.13, color=REL_C if rel[i] else NEG_C)
            d.set_stroke(INK, width=1.1, opacity=0.5)
            dots.add(d)
        axcap = Text("20 items, sorted by the model's confidence  →",
                     font_size=21, color=MUTED)
        axcap.move_to([0, y + 1.3, 0])
        self.play(FadeIn(axcap, shift=DOWN * 0.1),
                  LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.04),
                  run_time=1.4)
        # legend
        leg = VGroup(bullet("relevant", fs=18, dot=REL_C, dot_r=0.06),
                     bullet("not", fs=18, dot=NEG_C, dot_r=0.06)).arrange(RIGHT, buff=0.5)
        leg.move_to([0, y - 1.0, 0])
        self.play(FadeIn(leg), run_time=0.4)
        self.beat(1.0)

        # a movable decision threshold; flag everything to its left
        def thr_x(k):   # boundary after the k-th dot
            return (xs[k - 1] + xs[k]) / 2 if 0 < k < n else (x0 - 0.4 if k == 0 else x1 + 0.4)

        def counts(k):
            tp = sum(rel[:k])
            fp = k - tp
            fn = sum(rel) - tp
            p = tp / k if k else 0.0
            r = tp / sum(rel)
            f = 2 * p * r / (p + r) if (p + r) else 0.0
            return p, r, f

        k0 = 10
        line = DashedLine([thr_x(k0), y + 0.5, 0], [thr_x(k0), y - 0.5, 0],
                          color=INK, stroke_width=5)
        tlab = Text("threshold", font_size=18, color=INK).next_to(line, UP, buff=0.09)
        flag_lbl = Text("← flagged", font_size=18, color=PREC_C)
        flag_lbl.move_to([thr_x(k0) - 0.95, y - 0.42, 0])
        self.play(Create(line), FadeIn(tlab), FadeIn(flag_lbl), run_time=0.7)
        self.beat(0.8)

        # two meters: precision & recall
        p0, r0, f0 = counts(k0)
        mp = self._meter("Precision", PREC_C, p0, [-0.2, -0.55, 0])
        mr = self._meter("Recall", REC_C, r0, [-0.2, -1.7, 0])
        self.play(FadeIn(mp["grp"]), FadeIn(mr["grp"]), run_time=0.7)
        self.beat(1.2)

        def retarget(k, msg, msg_color):
            p, r, f = counts(k)
            cap = self.say(msg, color=msg_color, weight=BOLD)
            self.play(line.animate.move_to([thr_x(k), line.get_center()[1], 0]),
                      tlab.animate.move_to([thr_x(k), tlab.get_center()[1], 0]),
                      flag_lbl.animate.move_to([thr_x(k) - 0.95, y - 0.42, 0]),
                      self._meter_set(mp, p), self._meter_set(mr, r),
                      FadeIn(cap, shift=UP * 0.1) if not hasattr(self, "_tcap")
                      else ReplacementTransform(self._tcap, cap),
                      run_time=1.0)
            self._tcap = cap
            self.beat(1.6)

        retarget(5, "Stricter: precision ↑ 80%, but recall ↓ 50% — misses more.", PREC_C)
        retarget(15, "Looser: recall ↑ 88%, but precision ↓ 47% — more false alarms.", REC_C)
        retarget(10, "You can't push both to 100% at once — that's the trade-off.", INK)

        # transition to F1
        self.play(FadeOut(axcap, leg, line, tlab, flag_lbl, dots, self._tcap),
                  run_time=0.7)
        del self._tcap
        self.play(mp["grp"].animate.move_to([-3.7, 1.4, 0]),
                  mr["grp"].animate.move_to([-3.7, 0.3, 0]), run_time=0.8)

        f1_title = Text("F1 — one number for both", font_size=30, color=F1_C, weight="BOLD")
        f1_title.move_to([2.4, 2.15, 0])
        frac = fraction([("2 · P · R", INK)],
                        [("P + R", INK)], fs=30)
        eqv = Text(f"=  {pct(F1)}", font_size=32, color=F1_C, weight="BOLD")
        f1_formula = VGroup(frac, eqv).arrange(RIGHT, buff=0.3).move_to([2.4, 1.15, 0])
        self.play(FadeIn(f1_title, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeIn(f1_formula, shift=UP * 0.1), run_time=0.8)
        self.beat(1.2)

        note = Text("It's the harmonic mean — not the average.",
                    font_size=24, color=INK).move_to([2.4, 0.2, 0])
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.6)
        self.beat(1.0)

        # the punchline: harmonic mean punishes imbalance
        extreme = VGroup(
            Text("100% precision  ·  1% recall", font_size=24, color=MUTED),
            Text("average says ~50%   →   F1 says 2%", font_size=25, color=INK, weight="BOLD"),
        ).arrange(DOWN, buff=0.18)
        box = RoundedRectangle(width=extreme.width + 0.7, height=extreme.height + 0.5,
                               corner_radius=0.16, stroke_color=F1_C, stroke_width=2.5,
                               fill_color=F1_C, fill_opacity=0.08).move_to(extreme)
        grp = VGroup(box, extreme).move_to([0, -2.15, 0])
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=0.8)
        self.beat(1.2)
        punch = Text("F1 is only high when BOTH are high.",
                     font_size=25, color=F1_C, weight="BOLD").move_to([2.4, -0.75, 0])
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)
        self.wipe()

    def _meter(self, label, color, value, center):
        track_w = 3.4
        track = RoundedRectangle(width=track_w, height=0.34, corner_radius=0.17,
                                 stroke_color=color, stroke_width=2,
                                 fill_color=GRID, fill_opacity=0.6)
        fill = RoundedRectangle(width=max(0.34, track_w * value), height=0.34,
                                corner_radius=0.17, stroke_width=0,
                                fill_color=color, fill_opacity=1.0)
        fill.align_to(track, LEFT)
        lab = Text(label, font_size=20, color=color, weight="BOLD")
        lab.next_to(track, LEFT, buff=0.25)
        num = Text(pct(value), font_size=22, color=INK, weight="BOLD")
        num.next_to(track, RIGHT, buff=0.25)
        grp = VGroup(lab, track, fill, num).move_to(center)
        return {"grp": grp, "track": track, "fill": fill, "num": num,
                "color": color, "w": track_w}

    def _meter_set(self, m, value):
        new_fill = RoundedRectangle(width=max(0.34, m["w"] * value), height=0.34,
                                    corner_radius=0.17, stroke_width=0,
                                    fill_color=m["color"], fill_opacity=1.0)
        new_fill.align_to(m["track"], LEFT).set_y(m["track"].get_y())
        new_num = Text(pct(value), font_size=22, color=INK, weight="BOLD")
        new_num.move_to(m["num"])
        anim = AnimationGroup(Transform(m["fill"], new_fill),
                              Transform(m["num"], new_num))
        return anim

    # ====================================================================== #
    # Scene 5 — Recap: when to maximise what
    # ====================================================================== #
    def scene_recap(self):
        title = Text("When to maximise what", font_size=42, color=INK, weight="BOLD")
        title.to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1.1)
        self.beat(0.6)

        def col(metric, mcolor, formula, headline, examples):
            name = Text(metric, font_size=30, color=mcolor, weight="BOLD")
            f = Text(formula, font_size=20, color=MUTED)
            head = Text(headline, font_size=20, color=INK, weight="BOLD")
            head.set(width=min(3.2, head.width))
            ex = VGroup(*[bullet(t, fs=18, dot=mcolor, dot_r=0.05) for t in examples])
            ex.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
            inner = VGroup(name, f, head, ex).arrange(DOWN, buff=0.2)
            head.align_to(ex, LEFT)
            name.match_x(inner)
            f.match_x(inner)
            box = RoundedRectangle(width=3.9, height=4.0, corner_radius=0.18,
                                   stroke_color=mcolor, stroke_width=2.5,
                                   fill_color=mcolor, fill_opacity=0.07)
            inner.move_to(box).align_to(box, UP).shift(DOWN * 0.3)
            return VGroup(box, inner)

        c_rec = col("Recall", REC_C, "TP / (TP + FN)", "Maximise when a MISS hurts",
                    ["Retrieval / RAG", "Medical screening", "Fraud · security",
                     "Legal e-discovery"])
        c_prec = col("Precision", PREC_C, "TP / (TP + FP)", "Maximise when a FALSE ALARM hurts",
                     ["Spam filtering", "Recommendations", "Autocomplete",
                      "Costly human review"])
        c_f1 = col("F1", F1_C, "2·P·R / (P + R)", "Use when you need BALANCE",
                   ["Imbalanced classes", "Both errors matter", "Model comparison",
                    "A single headline metric"])
        cols = VGroup(c_rec, c_prec, c_f1).arrange(RIGHT, buff=0.35)
        cols.next_to(title, DOWN, buff=0.5)

        for c in cols:
            self.play(FadeIn(c, shift=UP * 0.15), run_time=0.7)
            self.beat(1.0)
        self.beat(1.2)

        self.play(Indicate(c_rec, color=REC_C, scale_factor=1.03), run_time=1.0)
        self.beat(2.0)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_matrix()
        self.scene_precision()
        self.scene_recall()
        self.scene_tradeoff()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_PRBase):
    def construct(self):
        self.play_intro()


class Matrix(_PRBase):
    def construct(self):
        self.scene_matrix()


class Precision(_PRBase):
    def construct(self):
        self.scene_precision()


class Recall(_PRBase):
    def construct(self):
        self.scene_recall()


class Tradeoff(_PRBase):
    def construct(self):
        self.scene_tradeoff()


class Recap(_PRBase):
    def construct(self):
        self.scene_recap()


class Outro(_PRBase):
    def construct(self):
        self.play_outro()


class PrecisionRecallF1(_PRBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    PrecisionRecallF1().render()
