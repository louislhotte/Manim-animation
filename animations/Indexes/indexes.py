"""What are indexes? — a short, house-style database explainer.

A self-explanatory (no voice-over) film that shows *why* a database index makes a
lookup fast, building all the way to the point most people miss: a composite
(two-column) index, and why column order matters.

    1. Scan      -- SELECT ... WHERE last_name='Vasquez' with no index: the engine
                    reads every row (a full table scan). O(n) — 10,000,000 reads.
    2. Index     -- an index is the column, *copied and kept sorted*, each entry
                    pointing back to its row (the rowid). Pull the column out and
                    watch it sort itself.
    3. Seek      -- sorted data means binary search: check the middle, throw away
                    half, repeat. ~23 checks for 10,000,000 rows. Real databases
                    keep this as a B-tree: wide fan-out, ~3 hops to any row.
    4. Composite -- WHERE last_name='Vasquez' AND city='Denver'. A composite index
                    on (last_name, city) is sorted by both, so it seeks straight to
                    the pair. Column order matters — the leftmost-prefix rule: it
                    serves last_name (and last_name+city), but NOT city alone.
    5. Recap     -- what an index buys you, and what it costs (space + slower writes).

Bookended by the channel's intro / "Thank you for watching!" outro, matching the
sibling explainers (animations/PrecisionRecall, animations/RBAC).

Everything uses ``Text`` (Pango), never ``Tex`` — no LaTeX toolchain. Every count
and every number on screen is derived from the eight concrete rows in ``ROWS``,
not faked (see the asserts in ``scene_scan`` / ``scene_composite``).

Scenes are exposed individually (``Scan``, ``IndexIntro``, ``Seek``,
``Composite``, ``Recap``, ``Intro``, ``Outro``) and as one film (``WhatAreIndexes``).

Env knobs:
    IDX_QUICK=1   shorten every hold for a fast sanity render
    IDX_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("IDX_QUICK") == "1"
# One knob for pacing: every reading "hold" is scaled by this. QUICK collapses the
# holds for fast iteration; otherwise it sets a comfortable reading rhythm.
DELAY = float(os.environ.get("IDX_DELAY", "0.3" if QUICK else "1.6"))
# Extra hold on each scene's final frame before it wipes to the next scene.
END_HOLD = 0.2 if QUICK else 1.5

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
FAINT = "#2A3446"       # panel strokes / gridlines
PANEL = "#0A0E15"       # code / query panel fill
HEAD_BG = "#1C2536"     # table header band
ROW_A = "#161C28"       # table row band (even)
ROW_B = "#10161F"       # table row band (odd)

IDX_C = "#FFD166"       # the index / the fast path (gold)
SLOW_C = "#FF5C5C"      # the slow full scan (red)
FAST_C = "#3DD68C"      # the fast seek / a match (green)
KEY1 = "#5B8DEF"        # last_name column (blue)
KEY2 = "#C77DFF"        # city column (violet)

# ---- code (Night-Owl-ish) palette for SQL --------------------------------- #
MONO = "Menlo"
PLAIN = "#D6DEEB"
KW = "#C792EA"          # SQL keywords
STR = "#7FDBCA"         # string literals

SQL_T2C = {
    "SELECT": KW, "FROM": KW, "WHERE": KW, "AND": KW,
    "CREATE": KW, "INDEX": KW, "ON": KW,
    "users": INK,
    "last_name": KEY1, "city": KEY2,
    "'Vasquez'": STR, "'Denver'": STR,
}

# ---- the running example — eight concrete rows (heap / insert order) ------- #
# id, last_name, city.  Vasquez appears 3x (Austin, Denver, Miami); exactly one
# (Vasquez, Denver).  Denver rows are deliberately scattered so the leftmost-prefix
# demo can show city-alone can't use a (last_name, city) index.
ROWS = [
    (1, "Chen",    "Denver"),
    (2, "Vasquez", "Austin"),
    (3, "Adams",   "Boston"),
    (4, "Vasquez", "Denver"),
    (5, "Okafor",  "Denver"),
    (6, "Nguyen",  "Austin"),
    (7, "Vasquez", "Miami"),
    (8, "Patel",   "Denver"),
]
N_TOTAL = 10_000_000    # the pretend row count (only 8 are drawn)


# ---- crisp text: render big, scale down (Pango mangles small sizes) -------- #
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    kw.update(extra)
    return Text(text, **kw)


def _safe_t2c(s, table):
    """Per-line text->colour map, pruned so no key overlaps another (manim raises
    on overlapping ``t2c`` ranges, even for the same colour)."""
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


def hrow(*mobs, buff=0.14, aligned_edge=DOWN):
    return VGroup(*mobs).arrange(RIGHT, buff=buff, aligned_edge=aligned_edge)


def bullet(text, color=INK, fs=21, dot=IDX_C, dot_r=0.055):
    d = Dot(radius=dot_r, color=dot)
    t = txt(text, fs=fs, color=color)
    t.next_to(d, RIGHT, buff=0.2)
    d.align_to(t, UP).shift(DOWN * 0.1)
    return VGroup(d, t)


# ========================================================================== #
# The reusable database table
# ========================================================================== #
def make_table(headers, rows, widths, row_h=0.46, fs=20, header_fs=20,
               aligns=None, key_cols=None, id_color=MUTED):
    """A banded data table. Returns a VGroup with attributes:

        .row_bg[i]     the full-width background rect of data row i
        .cells[i][j]   the Text in row i, column j
        .col_cells[j]  VGroup of every cell (incl. header) in column j
        .header_bg     the header band     .outline  the rounded border
        .total_w / .row_h
    """
    aligns = aligns or (["c"] + ["l"] * (len(headers) - 1))
    key_cols = key_cols or {}
    total_w = sum(widths)

    def col_left(j):
        return -total_w / 2 + sum(widths[:j])

    def place(t, j, y):
        maxw = widths[j] - 0.28
        if t.width > maxw:
            t.scale_to_fit_width(maxw)
        if aligns[j] == "l":
            t.set_y(y)
            t.align_to(np.array([col_left(j) + 0.2, y, 0]), LEFT)
        else:
            t.move_to([col_left(j) + widths[j] / 2, y, 0])
        return t

    grp = VGroup()
    grp.total_w, grp.row_h = total_w, row_h
    grp.row_bg, grp.cells = [], []
    grp.col_cells = [VGroup() for _ in headers]

    hb = Rectangle(width=total_w, height=row_h, stroke_width=0,
                   fill_color=HEAD_BG, fill_opacity=1.0).move_to([0, 0, 0])
    grp.header_bg = hb
    grp.add(hb)
    for j, h in enumerate(headers):
        t = place(txt(h, fs=header_fs, color=INK, weight="BOLD"), j, 0)
        grp.add(t)
        grp.col_cells[j].add(t)

    for i, row in enumerate(rows):
        y = -(i + 1) * row_h
        bg = Rectangle(width=total_w, height=row_h, stroke_width=0,
                       fill_color=(ROW_A if i % 2 == 0 else ROW_B),
                       fill_opacity=1.0).move_to([0, y, 0])
        grp.row_bg.append(bg)
        grp.add(bg)
        rowcells = []
        for j, val in enumerate(row):
            color = key_cols.get(headers[j], id_color if j == 0 else INK)
            t = place(txt(str(val), fs=fs, color=color), j, y)
            grp.add(t)
            rowcells.append(t)
            grp.col_cells[j].add(t)
        grp.cells.append(rowcells)

    n = len(rows)
    outline = RoundedRectangle(width=total_w + 0.05, height=row_h * (n + 1) + 0.05,
                               corner_radius=0.11, stroke_color=FAINT,
                               stroke_width=2, fill_opacity=0)
    outline.move_to(grp)
    sep = Line([-total_w / 2, -row_h / 2, 0], [total_w / 2, -row_h / 2, 0])
    sep.set_stroke(FAINT, 2)
    grp.add(outline, sep)
    grp.outline = outline
    return grp


def row_highlight(table, i, color, opacity=0.0, sw=4):
    """A stroked highlight sized to data row i of a table."""
    bg = table.row_bg[i]
    r = RoundedRectangle(width=bg.width - 0.03, height=bg.height - 0.02,
                         corner_radius=0.06, stroke_color=color, stroke_width=sw,
                         fill_color=color, fill_opacity=opacity)
    r.move_to(bg)
    return r


# ========================================================================== #
class _IdxBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.25))

    def wipe(self, rt=0.7):
        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color):
        t = txt(label, fs=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=25, y=-3.35, weight=NORMAL):
        cap = txt(text, fs=fs, color=color, weight=weight)
        if cap.width > 12.8:
            cap.scale_to_fit_width(12.8)
        cap.move_to([0, y, 0])
        return cap

    def clamp_w(self, mob, w=6.6):
        if mob.width > w:
            mob.scale_to_fit_width(w)
        return mob

    def query_bar(self, sql, center=(0, 2.55, 0), fs=24, max_w=11.5, scale=1.0):
        code = Text(sql, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(sql, SQL_T2C))
        if code.width > max_w:
            code.scale_to_fit_width(max_w)
        box = RoundedRectangle(width=code.width + 0.6, height=code.height + 0.44,
                               corner_radius=0.12, stroke_color=FAINT, stroke_width=2,
                               fill_color=PANEL, fill_opacity=1.0)
        box.move_to(code)
        grp = VGroup(box, code).scale(scale).move_to(center)
        grp.code = code
        return grp

    # ---- house-style intro / outro cards ---------------------------------- #
    def _byline_and_rule(self, header):
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=IDX_C)
        writer = txt("Created by Ptolémé", fs=28, color=KEY1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        return line, writer

    def introduction(self, title1, title2):
        header = txt(title1, fs=54, color=INK, weight="BOLD")
        header.set(width=min(10.5, header.width))
        line, writer = self._byline_and_rule(header)
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = txt(title2, fs=32, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "What are indexes?",
            "How a database finds one row among millions — instantly",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = txt("Thank you for watching!", fs=48, color=INK, weight="BOLD")
        line, writer = self._byline_and_rule(header)
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — The full table scan (the problem)
    # ====================================================================== #
    def scene_scan(self):
        header = self.section_header("Without an index", SLOW_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        q = self.query_bar("SELECT * FROM users WHERE last_name = 'Vasquez'",
                           center=(0, 2.65, 0))
        self.play(FadeIn(q, shift=DOWN * 0.15), run_time=0.7)
        self.beat(1.0)

        table = make_table(["id", "last_name", "city"],
                           [(f"#{i}", ln, c) for i, ln, c in ROWS],
                           widths=[1.0, 2.25, 1.85], row_h=0.46,
                           key_cols={"last_name": INK})
        table.scale(0.96).move_to([0, -0.35, 0])
        tlabel = txt(f"users  ·  {N_TOTAL:,} rows  (8 shown)", fs=19, color=MUTED)
        tlabel.next_to(table, UP, buff=0.18)
        self.play(FadeIn(table, shift=UP * 0.15), FadeIn(tlabel), run_time=0.9)
        self.beat(0.8)

        # a scanning beam sweeps top -> bottom; a counter ticks with it
        beam = row_highlight(table, 0, SLOW_C, opacity=0.22, sw=3)
        readout = txt("rows scanned:", fs=22, color=MUTED)
        num = DecimalNumber(0, num_decimal_places=0, color=SLOW_C, font_size=30)
        counter = VGroup(readout, num).arrange(RIGHT, buff=0.2)
        counter.next_to(table, DOWN, buff=0.3)
        tracker = ValueTracker(0)
        num.add_updater(lambda m: m.set_value(int(tracker.get_value())))

        self.play(FadeIn(beam), FadeIn(counter), run_time=0.5)
        self.play(beam.animate.move_to(table.row_bg[-1]),
                  tracker.animate.set_value(len(ROWS)),
                  run_time=2.4, rate_func=linear)
        num.clear_updaters()
        self.beat(0.5)

        # the scan doesn't stop at 8 — it must read all of them
        more = txt(f"… every one of {N_TOTAL:,} rows", fs=22, color=SLOW_C, weight="BOLD")
        more.move_to(counter)
        self.play(FadeOut(counter), FadeIn(more, shift=UP * 0.1),
                  beam.animate.set_opacity(0.0), run_time=0.7)
        self.remove(beam)
        self.beat(1.2)

        # reveal the 3 matches
        match_idx = [i for i, (_, ln, _) in enumerate(ROWS) if ln == "Vasquez"]
        assert match_idx == [1, 3, 6]
        checks = VGroup(*[row_highlight(table, i, FAST_C, opacity=0.12, sw=3)
                          for i in match_idx])
        cap = self.say("Found 3 matches — after reading all ten million rows.",
                       color=INK)
        self.play(LaggedStart(*[Create(c) for c in checks], lag_ratio=0.2),
                  FadeIn(cap, shift=UP * 0.1), run_time=1.2)
        self.beat(1.6)

        # the verdict
        verdict = txt("This is a full table scan — O(n).", fs=30, color=SLOW_C,
                      weight="BOLD")
        verdict.move_to(more)
        self.play(ReplacementTransform(more, verdict), run_time=0.7)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — What an index actually is (a sorted copy + row pointers)
    # ====================================================================== #
    def scene_index(self):
        header = self.section_header("What an index is", IDX_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # table on the left, in heap (insert) order
        table = make_table(["id", "last_name", "city"],
                           [(f"#{i}", ln, c) for i, ln, c in ROWS],
                           widths=[0.9, 2.0, 1.7], row_h=0.46,
                           key_cols={"last_name": KEY1})
        table.scale(0.9).move_to([-3.9, -0.35, 0])
        ttl = txt("the table (unordered)", fs=19, color=MUTED).next_to(table, UP, buff=0.16)
        self.play(FadeIn(table, shift=RIGHT * 0.15), FadeIn(ttl), run_time=0.8)
        self.beat(0.8)

        # highlight the last_name column — this is what we'll index
        colbox = SurroundingRectangle(table.col_cells[1], color=KEY1, buff=0.08,
                                      corner_radius=0.08).set_stroke(width=3)
        cap = self.say("An index copies one column and keeps it sorted.", color=KEY1)
        self.play(Create(colbox), FadeIn(cap, shift=UP * 0.1), run_time=0.8)
        self.beat(1.2)

        # copy the last_name cells and float them to the right, then SORT them
        sorted_rows = sorted(ROWS, key=lambda r: r[1])   # by last_name, stable
        rowid_order = [r[0] for r in sorted_rows]         # [3,1,6,5,8,2,4,7]
        assert rowid_order == [3, 1, 6, 5, 8, 2, 4, 7]

        x_key, y_top, dy = 2.3, 1.55, 0.46
        slot_y = {rid: y_top - k * dy for k, rid in enumerate(rowid_order)}

        copies = {}
        anims = []
        for i, (rid, ln, _) in enumerate(ROWS):
            c = table.cells[i][1].copy()
            copies[rid] = c
            target = np.array([x_key, slot_y[rid], 0])
            anims.append(c.animate.move_to(target).set_color(IDX_C))
        self.add(*copies.values())
        cap2 = self.say("Pull the column out … and sort it.", color=IDX_C)
        self.play(FadeOut(colbox), ReplacementTransform(cap, cap2),
                  LaggedStart(*anims, lag_ratio=0.06), run_time=2.2)
        self.beat(0.8)

        # add the rowid pointer to each sorted entry: "Vasquez -> #4"
        ptrs = VGroup()
        for rid in rowid_order:
            c = copies[rid]
            ar = txt("→", fs=22, color=MUTED).next_to(c, RIGHT, buff=0.9)
            ar.set_x(x_key + 1.35)
            pid = txt(f"#{rid}", fs=20, color=MUTED).next_to(ar, RIGHT, buff=0.16)
            ptrs.add(VGroup(ar, pid))
        idx_box = RoundedRectangle(
            width=3.5, height=dy * len(ROWS) + 0.55, corner_radius=0.14,
            stroke_color=IDX_C, stroke_width=2.5, fill_color=IDX_C, fill_opacity=0.05)
        idx_box.move_to([x_key + 0.65, y_top - (len(ROWS) - 1) * dy / 2, 0])
        idx_title = txt("INDEX  ·  last_name", fs=19, color=IDX_C, weight="BOLD")
        idx_title.next_to(idx_box, UP, buff=0.16)
        self.play(Create(idx_box), FadeIn(idx_title), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(p, shift=LEFT * 0.1) for p in ptrs],
                              lag_ratio=0.05), run_time=1.0)
        self.beat(1.0)

        # demonstrate a pointer actually points back to the row (the 3 Vasquez)
        cap3 = self.say("Each entry points back to its row (the rowid).", color=INK)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        vas_ids = [2, 4, 7]
        arrows = VGroup()
        for rid in vas_ids:
            row_i = rid - 1
            start = ptrs[rowid_order.index(rid)].get_right() + RIGHT * 0.05
            end = table.row_bg[row_i].get_right() + LEFT * 0.02
            a = CurvedArrow(start, end, angle=-TAU / 7, color=FAST_C,
                            stroke_width=3, tip_length=0.16)
            arrows.add(a)
        vas_rows = VGroup(*[row_highlight(table, r - 1, FAST_C, opacity=0.10, sw=2.5)
                            for r in vas_ids])
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.15),
                  *[Create(v) for v in vas_rows], run_time=1.3)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Why it's fast: binary search on the sorted index -> B-tree
    # ====================================================================== #
    def scene_seek(self):
        header = self.section_header("Why it's fast", FAST_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the sorted index as a single column of keys
        sorted_rows = sorted(ROWS, key=lambda r: r[1])
        keys = [r[1] for r in sorted_rows]
        rowids = [r[0] for r in sorted_rows]
        n = len(keys)
        x_key, y_top, dy = -4.4, 2.0, 0.5

        entries = VGroup()
        boxes = []
        for k, (ln, rid) in enumerate(zip(keys, rowids)):
            y = y_top - k * dy
            b = RoundedRectangle(width=2.3, height=0.42, corner_radius=0.08,
                                 stroke_color=FAINT, stroke_width=1.5,
                                 fill_color=ROW_A, fill_opacity=1.0)
            b.move_to([x_key, y, 0])
            t = txt(ln, fs=20, color=IDX_C).move_to(b)
            boxes.append(b)
            entries.add(VGroup(b, t))
        idx_title = txt("sorted index", fs=19, color=IDX_C, weight="BOLD")
        idx_title.next_to(entries, UP, buff=0.16)
        self.play(FadeIn(entries, shift=RIGHT * 0.1), FadeIn(idx_title), run_time=0.9)
        self.beat(0.6)

        q = txt("find  last_name = 'Vasquez'", fs=24, color=INK)
        q.move_to([2.6, 2.75, 0])
        self.play(FadeIn(q, shift=DOWN * 0.1), run_time=0.6)
        self.beat(0.6)

        # binary search: probe the middle, discard half, repeat
        def probe(lo, hi):
            return (lo + hi) // 2

        cap = self.say("Sorted data → binary search: check the middle, drop half.",
                       color=FAST_C)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)

        lo, hi = 0, n - 1
        pointer = None
        dimmed = set()
        step = 0
        while lo <= hi:
            mid = probe(lo, hi)
            ring = SurroundingRectangle(entries[mid], color=FAST_C, buff=0.04,
                                        corner_radius=0.08).set_stroke(width=4)
            if pointer is None:
                pointer = ring
                self.play(Create(pointer), run_time=0.5)
            else:
                self.play(Transform(pointer, ring), run_time=0.5)
            step += 1
            if keys[mid] == "Vasquez":
                break
            # discard the half that can't contain 'Vasquez'
            if keys[mid] < "Vasquez":
                drop = list(range(lo, mid + 1))
                lo = mid + 1
            else:
                drop = list(range(mid, hi + 1))
                hi = mid - 1
            fades = [entries[d].animate.set_opacity(0.22) for d in drop
                     if d not in dimmed]
            dimmed.update(drop)
            if fades:
                self.play(*fades, run_time=0.5)
            self.beat(0.5)

        # the Vasquez block is contiguous — highlight all three
        vblock = [k for k, ln in enumerate(keys) if ln == "Vasquez"]
        block_hi = SurroundingRectangle(VGroup(*[entries[k] for k in vblock]),
                                        color=FAST_C, buff=0.06,
                                        corner_radius=0.1).set_stroke(width=4)
        self.play(Transform(pointer, block_hi),
                  *[entries[k].animate.set_opacity(1.0) for k in vblock], run_time=0.7)
        found = txt(f"{step} checks — the matches sit together.", fs=22, color=FAST_C,
                    weight="BOLD").move_to([2.6, 1.85, 0])
        self.play(FadeIn(found, shift=UP * 0.1), run_time=0.6)
        self.beat(1.6)

        # generalise: log2(N) and the B-tree
        self.play(FadeOut(q), FadeOut(found), run_time=0.4)
        big = int(np.ceil(np.log2(N_TOTAL)))
        contrast = VGroup(
            txt(f"{N_TOTAL:,} rows", fs=26, color=MUTED),
            txt("full scan:", fs=24, color=SLOW_C, weight="BOLD"),
            txt(f"{N_TOTAL:,} reads", fs=30, color=SLOW_C, weight="BOLD"),
            txt("binary search:", fs=24, color=FAST_C, weight="BOLD"),
            txt(f"≈ {big} checks", fs=30, color=FAST_C, weight="BOLD"),
        )
        contrast[0].move_to([2.9, 2.6, 0])
        VGroup(contrast[1], contrast[2]).arrange(DOWN, buff=0.1).move_to([2.9, 1.55, 0])
        VGroup(contrast[3], contrast[4]).arrange(DOWN, buff=0.1).move_to([2.9, 0.35, 0])
        self.play(FadeIn(contrast[0]), run_time=0.4)
        self.play(FadeIn(contrast[1], contrast[2], shift=UP * 0.1), run_time=0.6)
        self.beat(0.8)
        self.play(FadeIn(contrast[3], contrast[4], shift=UP * 0.1), run_time=0.6)
        cap2 = self.say("Each step throws away half the rows — that's O(log n).",
                        color=INK)
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.beat(1.6)

        # the B-tree coda
        self.play(FadeOut(contrast), run_time=0.4)
        tree = self._btree(center=[2.7, 0.6, 0])
        cap3 = self.say("Real databases store the index as a B-tree — wide fan-out, "
                        "~3–4 levels for millions of rows.", color=IDX_C)
        self.play(FadeIn(tree["all"], shift=UP * 0.1),
                  ReplacementTransform(cap2, cap3), run_time=1.0)
        self.beat(0.8)
        # light the descent path root -> right child -> Vasquez leaf
        self.play(*[e.animate.set_stroke(FAST_C, 4) for e in tree["path_edges"]],
                  *[b.animate.set_stroke(FAST_C, 3) for b in tree["path_nodes"]],
                  run_time=1.0)
        hops = txt("3 hops, not ten million.", fs=24, color=FAST_C, weight="BOLD")
        hops.next_to(tree["all"], DOWN, buff=0.3)
        self.play(FadeIn(hops, shift=UP * 0.1), run_time=0.6)
        self.beat(2.0)
        self.wipe()

    def _btree(self, center=ORIGIN):
        """A small schematic B-tree: a root of separators over three leaves."""
        node_fill = "#141C29"

        def node(labels, color=IDX_C, w_each=0.62):
            cells = VGroup()
            for s in labels:
                b = RoundedRectangle(width=w_each, height=0.5, corner_radius=0.07,
                                     stroke_color=color, stroke_width=2,
                                     fill_color=node_fill, fill_opacity=1.0)
                t = txt(s, fs=17, color=INK).move_to(b)
                if t.width > w_each - 0.12:
                    t.scale_to_fit_width(w_each - 0.12)
                cells.add(VGroup(b, t))
            cells.arrange(RIGHT, buff=0.0)
            box = SurroundingRectangle(cells, color=color, buff=0.04,
                                       corner_radius=0.09).set_stroke(width=2)
            return VGroup(box, cells), [c[0] for c in cells]

        root, root_boxes = node(["N", "P"], color=MUTED)
        root.move_to([0, 1.0, 0])
        leaf1, l1b = node(["Ad", "Ch"], color=MUTED)
        leaf2, l2b = node(["Ng", "Ok"], color=MUTED)
        leaf3, l3b = node(["Pa", "Va"], color=IDX_C)
        leaves = VGroup(leaf1, leaf2, leaf3).arrange(RIGHT, buff=0.5)
        leaves.next_to(root, DOWN, buff=0.7)

        edges = VGroup()
        path_edges = []
        for k, leaf in enumerate([leaf1, leaf2, leaf3]):
            e = Line(root.get_bottom(), leaf.get_top(), color=FAINT, stroke_width=2)
            edges.add(e)
            if k == 2:
                path_edges.append(e)
        all_ = VGroup(edges, root, leaves).move_to(center)
        return {"all": all_, "root": root, "leaf3": leaf3, "edges": edges,
                "path_edges": path_edges, "path_nodes": [root_boxes[1], leaf3[0]]}

    # ====================================================================== #
    # Scene 4 — The composite (two-column) index + leftmost-prefix rule
    # ====================================================================== #
    def scene_composite(self):
        header = self.section_header("A two-column index", KEY2)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        q = self.query_bar(
            "SELECT * FROM users WHERE last_name = 'Vasquez' AND city = 'Denver'",
            center=(0, 2.6, 0), fs=23)
        self.play(FadeIn(q, shift=DOWN * 0.15), run_time=0.7)
        self.beat(1.0)

        # the composite index: sorted by last_name, THEN by city
        comp = sorted(ROWS, key=lambda r: (r[1], r[2]))
        assert [r[0] for r in comp] == [3, 1, 6, 5, 8, 2, 4, 7]
        answer_rid = 4
        assert [r for r in ROWS if r[1] == "Vasquez" and r[2] == "Denver"][0][0] == answer_rid

        x0, y_top, dy = -3.4, 1.28, 0.43
        rows_ui = []
        grp = VGroup()
        for k, (rid, ln, city) in enumerate(comp):
            y = y_top - k * dy
            b = RoundedRectangle(width=4.6, height=0.4, corner_radius=0.07,
                                 stroke_color=FAINT, stroke_width=1.4,
                                 fill_color=(ROW_A if k % 2 == 0 else ROW_B),
                                 fill_opacity=1.0).move_to([x0, y, 0])
            t_ln = txt(ln, fs=19, color=KEY1)
            t_ln.set_y(y).align_to(np.array([x0 - 2.1, y, 0]), LEFT)
            t_ct = txt(city, fs=19, color=KEY2)
            t_ct.set_y(y).align_to(np.array([x0 - 0.15, y, 0]), LEFT)
            t_id = txt(f"→ #{rid}", fs=17, color=MUTED)
            t_id.set_y(y).align_to(np.array([x0 + 1.35, y, 0]), LEFT)
            rows_ui.append({"bg": b, "ln": t_ln, "ct": t_ct, "id": t_id, "rid": rid,
                            "city": city, "name": ln})
            grp.add(b, t_ln, t_ct, t_id)
        idx_box = RoundedRectangle(width=4.9, height=dy * len(comp) + 0.5,
                                   corner_radius=0.14, stroke_color=KEY2,
                                   stroke_width=2.5, fill_opacity=0)
        idx_box.move_to([x0, y_top - (len(comp) - 1) * dy / 2, 0])
        idx_title = txt("INDEX  ·  (last_name, city)", fs=19, color=KEY2, weight="BOLD")
        idx_title.next_to(idx_box, UP, buff=0.14)
        self.play(Create(idx_box), FadeIn(idx_title), FadeIn(grp, shift=RIGHT * 0.1),
                  run_time=1.0)
        self.beat(0.6)

        note = txt("Sorted by last_name,\nthen by city.", fs=22, color=INK,
                   line_spacing=0.8)
        note.move_to([3.45, 1.5, 0])
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.6)
        self.beat(1.2)

        # seek: jump to the Vasquez block, then within it straight to Denver
        vblock = [k for k, r in enumerate(comp) if r[1] == "Vasquez"]
        v_hi = SurroundingRectangle(VGroup(*[rows_ui[k]["bg"] for k in vblock]),
                                    color=KEY1, buff=0.05, corner_radius=0.1
                                    ).set_stroke(width=4)
        cap = self.say("Seek to the 'Vasquez' block …", color=KEY1)
        self.play(Create(v_hi), FadeIn(cap, shift=UP * 0.1), run_time=0.8)
        self.beat(1.0)

        ans_k = [k for k, r in enumerate(comp) if r[0] == answer_rid][0]
        ans_hi = row_highlight_line(rows_ui[ans_k]["bg"], FAST_C)
        cap2 = self.say("… and within it, city is already sorted → land on Denver. "
                        "One seek.", color=FAST_C)
        self.play(Transform(v_hi, ans_hi), ReplacementTransform(cap, cap2),
                  Indicate(rows_ui[ans_k]["ct"], color=FAST_C, scale_factor=1.3),
                  run_time=1.0)
        self.beat(1.4)

        contrast = txt("A last_name-only index would still scan every Vasquez for "
                       "the city.", fs=20, color=MUTED)
        self.clamp_w(contrast, 6.2).move_to([3.45, 0.15, 0])
        self.play(FadeIn(contrast, shift=UP * 0.1), run_time=0.6)
        self.beat(1.8)

        # ---- the leftmost-prefix rule ------------------------------------- #
        self.play(FadeOut(note), FadeOut(contrast), FadeOut(v_hi), run_time=0.5)
        rule_title = txt("Column order matters:  the leftmost-prefix rule", fs=23,
                         color=IDX_C, weight="BOLD")
        rule_title.move_to([3.25, 1.82, 0])
        self.play(FadeIn(rule_title, shift=DOWN * 0.1), run_time=0.6)

        def rule_row(cond, ok, why):
            mark = txt("✓" if ok else "✗", fs=26,
                       color=FAST_C if ok else SLOW_C, weight="BOLD")
            c = Text(cond, font=MONO, font_size=18, color=PLAIN,
                     t2c=_safe_t2c(cond, SQL_T2C))
            if c.width > 3.3:
                c.scale_to_fit_width(3.3)
            w = txt(why, fs=16, color=MUTED)
            line = VGroup(mark, c).arrange(RIGHT, buff=0.25)
            block = VGroup(line, w).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            w.align_to(c, LEFT)
            return block

        r1 = rule_row("last_name='Vasquez' AND city='Denver'", True, "uses both columns")
        r2 = rule_row("last_name='Vasquez'", True, "uses the leftmost column")
        r3 = rule_row("city='Denver'", False, "can't — city isn't leftmost")
        rules = VGroup(r1, r2, r3).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        rules.move_to([3.25, -0.05, 0])
        for r in rules:
            self.play(FadeIn(r, shift=RIGHT * 0.12), run_time=0.6)
            self.beat(0.9)
        self.beat(0.6)

        # show WHY city-alone fails: the Denver rows are scattered, not contiguous
        cap3 = self.say("city='Denver' alone: those rows are scattered through the "
                        "index — no shortcut.", color=SLOW_C)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        denver_k = [k for k, r in enumerate(comp) if r[2] == "Denver"]
        scatter = VGroup(*[row_highlight_line(rows_ui[k]["bg"], SLOW_C, opacity=0.14)
                           for k in denver_k])
        self.play(LaggedStart(*[Create(s) for s in scatter], lag_ratio=0.15),
                  Indicate(r3, color=SLOW_C, scale_factor=1.05), run_time=1.2)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Recap: what it buys, what it costs
    # ====================================================================== #
    def scene_recap(self):
        title = txt("Indexes, in one card", fs=42, color=INK, weight="BOLD")
        title.to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1.0)
        self.beat(0.5)

        def panel(head, color, items, sign):
            h = txt(head, fs=26, color=color, weight="BOLD")
            rows = VGroup(*[bullet(t, fs=20, dot=color, dot_r=0.05) for t in items])
            rows.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
            body = VGroup(h, rows).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
            box = RoundedRectangle(width=5.7, height=body.height + 0.7,
                                   corner_radius=0.16, stroke_color=color,
                                   stroke_width=2.5, fill_color=color, fill_opacity=0.07)
            box.move_to(body)
            return VGroup(box, body)

        wins = panel("What it buys you", FAST_C, [
            "O(n) scan  →  O(log n) seek",
            "A sorted map: value → rowid",
            "Composite index covers many columns",
            "Serves ORDER BY & ranges too",
        ], "+")
        costs = panel("What it costs", SLOW_C, [
            "Extra storage — a second copy",
            "Every write updates the index too",
            "Order matters: leftmost prefix",
            "Index only the columns you query",
        ], "-")
        cols = VGroup(wins, costs).arrange(RIGHT, buff=0.6)
        cols.next_to(title, DOWN, buff=0.55)
        for c in cols:
            self.play(FadeIn(c, shift=UP * 0.15), run_time=0.7)
            self.beat(1.0)
        self.beat(0.8)

        punch = txt("An index trades a little space and slower writes "
                    "for dramatically faster reads.",
                    fs=24, color=IDX_C, weight="BOLD")
        self.clamp_w(punch, 12.6).next_to(cols, DOWN, buff=0.5)
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.8)
        self.beat(2.4)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_scan()
        self.scene_index()
        self.scene_seek()
        self.scene_composite()
        self.scene_recap()
        self.play_outro()


def row_highlight_line(bg_rect, color, opacity=0.0, sw=4):
    """Stroked highlight sized to a single index-row background rectangle."""
    r = RoundedRectangle(width=bg_rect.width - 0.02, height=bg_rect.height + 0.02,
                         corner_radius=0.08, stroke_color=color, stroke_width=sw,
                         fill_color=color, fill_opacity=opacity)
    r.move_to(bg_rect)
    return r


# ---- individually renderable scenes -------------------------------------- #
class Intro(_IdxBase):
    def construct(self):
        self.play_intro()


class Scan(_IdxBase):
    def construct(self):
        self.scene_scan()


class IndexIntro(_IdxBase):
    def construct(self):
        self.scene_index()


class Seek(_IdxBase):
    def construct(self):
        self.scene_seek()


class Composite(_IdxBase):
    def construct(self):
        self.scene_composite()


class Recap(_IdxBase):
    def construct(self):
        self.scene_recap()


class Outro(_IdxBase):
    def construct(self):
        self.play_outro()


class WhatAreIndexes(_IdxBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    WhatAreIndexes().render()
