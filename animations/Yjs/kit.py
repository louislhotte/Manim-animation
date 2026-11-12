"""kit.py: the building blocks of the Yjs explainer (film-specific, built on manimx).

Three small engines, each driven by plain attributes that animations tween:

* ``LiveLine``   a line of proportional text that can be typed into, inserted into and
                 deleted from while it stays laid out (the editor, the replica lanes);
* ``ItemRow``    a Yjs document drawn as its real linked list of items: ``Block`` s
                 (one per Item: a run of characters, an id, a length) that can grow,
                 split, receive another block (``Dock``) and turn into tombstones;
* ``Caret``      a collaborator's caret with a name flag that follows either of them.

plus the glyphs around them (avatars, wires, packets, the Item card, state-vector
bars, the editor window). Nothing here uses closures over mobjects, so a whole
editor can be ``copy()``-ed and the copy keeps working (the replicas of scene 1).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from manimx import *

# --------------------------------------------------------------------------- #
# the three writers
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Peer:
    name: str
    cid: int  # the Yjs client id (random 32-bit in real life; 1, 2, 3 in the film)
    color: str
    agent: bool = False


# The three writer colours carry identity in every scene, and any two can sit side by
# side, so they were picked with the dataviz skill's validator rather than by eye: on
# the film's surface (#0E1117) every pair stays apart under protan / deutan simulation
# (worst pair dE 9.8, target 8) and in normal vision (17.9, floor 15), inside the dark
# lightness band. The house SKY / LILAC pair fails both (5.7 and 15.0). To re-check:
#   node <dataviz>/scripts/validate_palette.js "#508FF9,#E26E1A,#C170BB" \
#        --mode dark --surface "#0E1117" --pairs all
ADA_C, BOB_C, AGENT_C = "#508FF9", "#E26E1A", "#C170BB"
ADA = Peer("Ada", 1, ADA_C)
BOB = Peer("Bob", 2, BOB_C)
AGENT = Peer("Agent", 3, AGENT_C, agent=True)
PEERS = {1: ADA, 2: BOB, 3: AGENT}

# A one-hue ramp for "how much" (the order map of scene 6): 8 steps, monotone
# lightness, validated with `--ordinal` on the same surface.
RAMP8 = (
    "#0D534E",
    "#0B6861",
    "#077E76",
    "#0E948B",
    "#0FABA0",
    "#24C2B6",
    "#60D5CA",
    "#90E7DD",
)

WINDOW_BG = "#121722"  # editor page
WINDOW_BAR = "#1A2130"  # editor title bar
TOOL_C = "#566079"  # toolbar glyphs
TOMB = "#6B7385"  # tombstones


def sparkle(color, r=0.15):
    """The four-point "AI" spark."""
    return Star(
        n=4,
        outer_radius=r,
        inner_radius=r * 0.34,
        color=color,
        fill_opacity=1,
        stroke_width=0,
    )


def avatar(peer, r=0.22, ring=None):
    """A collaborator's badge: an initial for people, a spark for the agent."""
    disc = Circle(
        radius=r,
        stroke_color=ring or BG,
        stroke_width=2.5 if ring is None else 3,
        fill_color=peer.color,
        fill_opacity=1,
    )
    if peer.agent:
        mark = sparkle(BG, r=r * 0.66)
    else:
        mark = Text(
            peer.name[0], font_size=max(16, int(r * 92)), color=BG, weight="BOLD"
        )
        if mark.height > r * 1.05:
            mark.scale(r * 1.05 / mark.height)
    mark.move_to(disc)
    g = VGroup(disc, mark)
    g.disc = disc
    return g


def peer_label(peer, fs=20, r=0.2, sub=None):
    """Avatar + name (+ a muted sub-label), laid out in a row."""
    a = avatar(peer, r=r)
    name = Text(peer.name, font_size=fs, color=INK, weight="MEDIUM")
    row = VGroup(a, name).arrange(RIGHT, buff=0.14)
    if sub:
        s = Text(sub, font_size=max(16, fs - 4), color=MUTED)
        s.next_to(name, RIGHT, buff=0.16).align_to(name, DOWN)
        row.add(s)
    return row


def status_pill(text, color, fs=16):
    dot = Dot(radius=0.055, color=color)
    t = Text(text, font_size=fs, color=color, weight="MEDIUM")
    g = VGroup(dot, t).arrange(RIGHT, buff=0.1)
    box = RoundedRectangle(
        width=g.width + 0.3,
        height=g.height + 0.2,
        corner_radius=0.14,
        stroke_color=color,
        stroke_width=1.5,
        fill_color=color,
        fill_opacity=0.1,
    ).move_to(g)
    return VGroup(box, g)


# --------------------------------------------------------------------------- #
# typing (the generic attribute tweens, pulses, packets and bursts this film
# introduced now live in manimx.motion: Tween, Breathe, Throb, ripple, Do, Pop,
# Travel, stream, glow_dot, polyline, mix)
# --------------------------------------------------------------------------- #


class Type(Animation):
    """Reveal characters of one or several spans / blocks, in order.

    ``cps``     keys per second for a person (with ``jitter`` for an uneven rhythm);
    ``chunks``  token sizes for a streamed reveal (an LLM): each chunk lands at once,
                ``tps`` tokens per second.
    """

    def __init__(
        self,
        targets,
        cps=10.0,
        chunks=None,
        tps=6.0,
        jitter=0.35,
        seed=3,
        to=None,
        run_time=None,
        **kw,
    ):
        self.targets = list(targets) if isinstance(targets, list | tuple) else [targets]
        self.to = to
        self.chunks = chunks
        self.jitter = jitter
        self.seed = seed
        total = sum(len(t.text) for t in self.targets) if to is None else to
        if run_time is None:
            run_time = (len(chunks) / tps) if chunks else max(0.05, total / cps)
        super().__init__(
            Mobject(),
            run_time=run_time,
            rate_func=linear,
            remover=True,
            suspend_mobject_updating=False,
            **kw,
        )

    def begin(self):
        self.n0 = sum(t.n for t in self.targets)
        cap = sum(len(t.text) for t in self.targets)
        self.n1 = cap if self.to is None else self.to
        count = max(1, int(round(self.n1 - self.n0)))
        if self.chunks:
            ends = np.cumsum(self.chunks, dtype=float)
            k = len(self.chunks)
            # each chunk ramps in over the first 30 % of its slot, then holds
            xs, ys, prev = [0.0], [0.0], 0.0
            for j, e in enumerate(ends):
                xs += [(j + 0.3) / k, (j + 1) / k]
                ys += [e, e]
                prev = e
            self.xs, self.ys = np.array(xs), np.array(ys) * (self.n1 - self.n0) / prev
        else:
            rng = np.random.default_rng(self.seed)
            gaps = (
                rng.lognormal(0.0, self.jitter, size=count)
                if self.jitter
                else np.ones(count)
            )
            t = np.concatenate([[0.0], np.cumsum(gaps)])
            self.xs = t / t[-1]
            self.ys = np.linspace(0, self.n1 - self.n0, count + 1)
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        v = self.n0 + float(np.interp(alpha, self.xs, self.ys))
        if alpha >= 1:
            v = self.n1
        for t in self.targets:
            cap = len(t.text)
            t.n = float(np.clip(v, 0, cap))
            v -= cap
            if hasattr(t, "refresh"):
                t.refresh()


# --------------------------------------------------------------------------- #
# characters with exact advance cells
# --------------------------------------------------------------------------- #


class Cell:
    """One character: its glyph (None for a space), advance width and offsets."""

    __slots__ = ("ch", "mob", "w", "dx", "dy", "op", "born", "tint")

    def __init__(self, ch, mob, w, dx, dy):
        self.ch, self.mob, self.w, self.dx, self.dy = ch, mob, w, dx, dy
        self.op = None  # last opacity set
        self.born = None  # time the glyph first appeared (for the "fresh ink" tint)
        self.tint = None


_SPACE_ADV: dict = {}


def _space_adv(font, weight, fs):
    key = (font, weight)
    if key not in _SPACE_ADV:
        kw = {"font_size": 60, "weight": weight, "disable_ligatures": True}
        if font:
            kw["font"] = font
        _SPACE_ADV[key] = (Text("H H", **kw).width - Text("HH", **kw).width) / 60
    return _SPACE_ADV[key] * fs


def prose_cells(s, fs, weight="NORMAL", color=INK, font=None):
    """Glyphs of ``s`` in the house font with a contiguous advance cell per character.

    The string is set once between two sentinels (so kerning and leading / trailing
    spaces are exact); cells are then cut at the midpoints between neighbouring inks.
    Returns ``(cells, cap_height)``; glyph offsets are relative to cell-left / baseline.
    """
    kw = {"font_size": fs, "weight": weight, "color": color, "disable_ligatures": True}
    if font:
        kw["font"] = font
    t = Text("H" + s + "H", **kw)
    mobs = list(t.submobjects)
    assert len(mobs) == len(s) + 2, (s, len(mobs))
    chars = "H" + s + "H"
    sp = _space_adv(font, weight, fs)
    base_y, cap_h = mobs[0].get_bottom()[1], mobs[0].height
    left, right = [0.0] * len(chars), [0.0] * len(chars)
    ink = [i for i, ch in enumerate(chars) if not ch.isspace()]
    for a, b in zip(ink, ink[1:], strict=False):  # consecutive pairs
        gap = mobs[b].get_left()[0] - mobs[a].get_right()[0]
        side = (gap - (b - a - 1) * sp) / 2
        right[a] = mobs[a].get_right()[0] + side
        left[b] = mobs[b].get_left()[0] - side
        x = right[a]
        for j in range(a + 1, b):
            left[j], right[j] = x, x + sp
            x += sp
    cells = []
    for i in range(1, len(s) + 1):
        m = None if chars[i].isspace() else mobs[i]
        c = m.get_center() if m is not None else (0, 0, 0)
        cells.append(
            Cell(
                chars[i],
                m,
                right[i] - left[i],
                (c[0] - left[i]) if m is not None else 0.0,
                (c[1] - base_y) if m is not None else 0.0,
            )
        )
    return cells, cap_h


def mono_cells(s, fs, color=INK, space_color=FAINT):
    """Glyphs of ``s`` in Menlo on its exact grid; spaces are drawn as faint dots."""
    t = Text(
        "H" + s.replace(" ", "·") + "H",
        font=MONO,
        font_size=fs,
        color=color,
        disable_ligatures=True,
    )
    mobs = list(t.submobjects)
    assert len(mobs) == len(s) + 2, (s, len(mobs))
    adv = (mobs[-1].get_center()[0] - mobs[0].get_center()[0]) / (len(s) + 1)
    x0 = mobs[0].get_center()[0] + adv / 2
    base_y, cap_h = mobs[0].get_bottom()[1], mobs[0].height
    cells = []
    for i, ch in enumerate(s):
        m = mobs[i + 1]
        if ch == " ":
            m.set_color(space_color)
        c = m.get_center()
        cells.append(Cell(ch, m, adv, c[0] - (x0 + i * adv), c[1] - base_y))
    return cells, adv, cap_h


# --------------------------------------------------------------------------- #
# LiveLine: proportional text that types, inserts and deletes
# --------------------------------------------------------------------------- #


class Span:
    """A run of characters inside a LiveLine (who typed it, how much is visible)."""

    def __init__(self, text, peer, cells, n, key=None):
        self.text, self.peer, self.cells, self.key = text, peer, cells, key
        self.n = float(n)  # characters typed so far
        self.p = (
            1.0  # presence: 1 = in the text, 0 = collapsed (deleted / not yet merged)
        )
        self.x0 = self.x1 = 0.0


class LiveLine(VGroup):
    """One line of text made of spans; re-laid out every frame from their ``n`` / ``p``.

    ``parts`` is ``[(text, peer_or_None[, typed_chars[, key]]), ...]`` in final
    document order. ``tint="fresh"`` colours new glyphs with their author's colour
    and lets them settle to ``color``; ``tint="author"`` keeps the author's colour.
    """

    def __init__(
        self,
        parts,
        fs=26,
        weight="NORMAL",
        color=INK,
        at=ORIGIN,
        tint="fresh",
        settle=0.9,
        smooth_p=True,
    ):
        super().__init__()
        full = "".join(p[0] for p in parts)
        cells, self.cap_h = prose_cells(full, fs, weight, color)
        self.spans, i = [], 0
        for part in parts:
            text, peer = part[0], part[1]
            n = part[2] if len(part) > 2 and part[2] is not None else len(text)
            key = part[3] if len(part) > 3 else None
            self.spans.append(Span(text, peer, cells[i : i + len(text)], n, key))
            i += len(text)
        self.base = ManimColor(color)
        self.tint, self.settle, self.time = tint, settle, 0.0
        # the left end of the baseline, and a ruler that measures external scaling
        self.anchor = Dot(at, radius=0.001, fill_opacity=0, stroke_opacity=0)
        self.ruler = Line(at, np.array(at) + RIGHT, stroke_opacity=0)
        self.add(self.anchor, self.ruler, *[c.mob for c in cells if c.mob is not None])
        self._s = 1.0
        self.layout(0.0)
        self.add_updater(LiveLine._tick)

    @staticmethod
    def _tick(m, dt):
        m.layout(dt)

    def span(self, key):
        return next(s for s in self.spans if s.key == key)

    @property
    def scale_now(self):
        return self.ruler.get_length()

    def layout(self, dt=0.0):
        self.time += dt
        s = self.scale_now
        ax, ay = self.anchor.get_center()[:2]
        x = ax
        for sp in self.spans:
            k = int(math.floor(sp.n + 1e-6))
            p = float(np.clip(sp.p, 0, 1))
            sp.x0 = x
            for i, c in enumerate(sp.cells):
                vis = i < k and p > 1e-3
                if c.mob is not None:
                    # a span that opens or closes bunches its glyphs up: let them
                    # fade faster than they move, so they never read as garbled text
                    op = p**3 if vis else 0.0
                    if vis:
                        tx, ty = x + c.dx * s * p, ay + c.dy * s
                        cur = c.mob.get_center()
                        if abs(cur[0] - tx) > 1e-5 or abs(cur[1] - ty) > 1e-5:
                            c.mob.shift([tx - cur[0], ty - cur[1], 0])
                        self._colour(c, sp)
                    else:
                        c.born = None
                    if c.op is None or abs(c.op - op) > 1e-3:
                        c.mob.set_opacity(op)
                        c.op = op
                if vis:
                    x += c.w * s * p
            sp.x1 = x
        self.x1 = x

    def _colour(self, c, sp):
        if sp.peer is None or self.tint is None:
            return
        if self.tint == "author":
            if c.tint != "author":
                c.mob.set_color(sp.peer.color)
                c.tint = "author"
            return
        if c.born is None:
            c.born, c.tint = self.time, None
        age = (self.time - c.born) / self.settle
        if age >= 1:
            if c.tint != "base":
                c.mob.set_color(self.base)
                c.tint = "base"
        else:
            c.mob.set_color(mix(sp.peer.color, self.base, age**1.6))
            c.tint = None

    # geometry helpers ---------------------------------------------------------
    def point_after(self, span):
        """Where the caret sits after the visible part of ``span``."""
        ay = self.anchor.get_center()[1]
        return np.array([span.x1, ay + self.cap_h * self.scale_now * 0.5, 0.0])

    def end_point(self):
        ay = self.anchor.get_center()[1]
        return np.array([self.x1, ay + self.cap_h * self.scale_now * 0.5, 0.0])

    def text_now(self):
        out = []
        for sp in self.spans:
            if sp.p > 0.5:
                out.append(sp.text[: int(math.floor(sp.n + 1e-6))])
        return "".join(out)


# --------------------------------------------------------------------------- #
# Block / ItemRow: the Yjs linked list of items
# --------------------------------------------------------------------------- #


class Spacer:
    """An invisible slot that opens in a row while a block flies in."""

    def __init__(self, w=0.0):
        self.w, self.gap, self.x, self.y = w, 0.0, 0.0, 0.0

    @property
    def gap_now(self):
        return 0.0

    def refresh(self):
        pass


class Block(VGroup):
    """One Yjs Item: a run of characters by one client, an id and a length.

    Attributes that animations tween: ``n`` (characters typed), ``p`` (presence),
    ``dead`` (0 live .. 1 tombstone), ``sel`` (selection sweep), ``gap`` (space
    after the block, ``None`` = the row's), ``glow`` (highlight ring).
    """

    def __init__(
        self,
        text,
        peer,
        clock,
        *,
        fs=24,
        col=None,
        h=None,
        pad=0.1,
        ids="start",
        tag_fs=16,
        show_len=False,
        n=None,
        fill=0.17,
        tag_gap=0.13,
    ):
        super().__init__()
        self.text, self.peer, self.clock = text, peer, clock
        self.style = dict(
            fs=fs,
            col=col,
            h=h,
            pad=pad,
            ids=ids,
            tag_fs=tag_fs,
            show_len=show_len,
            fill=fill,
            tag_gap=tag_gap,
        )
        self.cells, adv, self.cap_h = mono_cells(text, fs)
        self.adv = adv  # the font's own advance; ``col`` may be wider (big cells)
        self.col = col or adv
        self.pad, self.fill, self.ids = pad, fill, ids
        self.h = h or self.cap_h + 0.34
        self.tag_fs, self.show_len, self.tag_gap = tag_fs, show_len, tag_gap
        self.n = float(len(text) if n is None else n)
        self.p, self.dead, self.sel, self.glow = 1.0, 0.0, 0.0, 0.0
        self.alpha = 1.0  # plain opacity multiplier (``fade`` is a Mobject method)
        self.tag_n = 1e9  # how many id tags are shown (tween it to stamp them in)
        self.sel_color = peer.color
        self.gap = None
        self.x, self.y = 0.0, 0.0
        self.box = RoundedRectangle(width=0.2, height=self.h, corner_radius=0.09)
        self.selbox = Rectangle(
            width=0.1, height=self.h - 0.1, stroke_width=0, fill_opacity=0
        )
        self.ring = RoundedRectangle(width=0.2, height=self.h, corner_radius=0.12)
        self.ring.set_stroke(GOLD, width=4, opacity=0).set_fill(opacity=0)
        self.glyphs = VGroup(*[c.mob for c in self.cells])
        self.strike = Line(LEFT, RIGHT, stroke_color=TOMB, stroke_width=2.5)
        self.strike.set_stroke(opacity=0)
        self.tag = VGroup()
        self._tag_key = None
        self.add(self.selbox, self.box, self.glyphs, self.strike, self.tag, self.ring)
        self._state = None
        self.refresh()

    # ---- geometry ----------------------------------------------------------- #
    @property
    def shown(self):
        return min(1.0, max(0.0, self.n))

    @property
    def w(self):
        return (2 * self.pad * self.shown + self.col * max(self.n, 0.0)) * self.p

    @property
    def full_w(self):
        return 2 * self.pad + self.col * len(self.text)

    @property
    def gap_now(self):
        return self.shown * self.p

    def id_of(self, i=0):
        return f"{self.peer.cid}:{self.clock + i}"

    def col_x(self, i):
        """Centre x of character column ``i`` (at full presence)."""
        return self.x + self.pad + (i + 0.5) * self.col

    def right_x(self):
        return self.x + self.w

    def center_point(self):
        return np.array([self.x + self.w / 2, self.y, 0.0])

    def place(self, x, y):
        self.x, self.y = float(x), float(y)
        self.refresh()
        return self

    def clone(self, **over):
        b = Block(self.text, self.peer, self.clock, **{**self.style, **over})
        b.n, b.dead = self.n, self.dead
        return b.place(self.x, self.y)

    # ---- drawing -------------------------------------------------------------- #
    def _tag_label(self):
        k = int(math.floor(self.n + 1e-6))
        if self.ids == "each":
            return ("each", k)
        if self.ids == "start":
            return ("start", k if self.show_len else 0)
        return None

    def _build_tag(self, key):
        c = mix(self.peer.color, TOMB, self.dead)
        if key is None:
            return VGroup()
        if key[0] == "each":
            return VGroup(
                *[mono(self.id_of(i), fs=self.tag_fs, color=c) for i in range(key[1])]
            )
        label = self.id_of()
        g = VGroup(mono(label, fs=self.tag_fs, color=c))
        if self.show_len and key[1] > 1:
            n = mono(f"×{key[1]}", fs=self.tag_fs, color=mix(MUTED, TOMB, self.dead))
            # the length only where it fits under its own block (short runs: id alone)
            if g.width + 0.1 + n.width <= 2 * self.pad + self.col * key[1] + 0.02:
                g.add(n)
                g.arrange(RIGHT, buff=0.1)
        return g

    def refresh(self):
        state = (
            round(self.x, 5),
            round(self.y, 5),
            round(self.n, 4),
            round(self.p, 4),
            round(self.dead, 3),
            round(self.sel, 3),
            round(self.glow, 3),
            round(self.alpha, 3),
            round(min(self.tag_n, 1e6), 3),
        )
        if state == self._state:
            return
        self._state = state
        k = int(math.floor(self.n + 1e-6))
        p = float(np.clip(self.p, 0, 1))
        vis = self.shown * p * self.alpha
        w = max(self.w, 1e-3)
        x, y = self.x, self.y
        col_c = mix(self.peer.color, TOMB, self.dead)

        box = RoundedRectangle(
            width=w, height=self.h, corner_radius=min(0.09, w / 2.05)
        ).move_to([x + w / 2, y, 0])
        box.set_stroke(col_c, width=2.2, opacity=vis * (1 - 0.35 * self.dead))
        box.set_fill(col_c, opacity=vis * self.fill * (1 - 0.8 * self.dead))
        self.box.become(box)

        ring = RoundedRectangle(
            width=w + 0.14,
            height=self.h + 0.14,
            corner_radius=min(0.13, (w + 0.14) / 2.05),
        ).move_to([x + w / 2, y, 0])
        ring.set_stroke(GOLD, width=4, opacity=vis * self.glow).set_fill(opacity=0)
        self.ring.become(ring)

        sw = max(1e-3, (w - 0.08) * self.sel)
        sel = Rectangle(width=sw, height=self.h - 0.1, stroke_width=0)
        sel.set_fill(self.sel_color, opacity=0.45 * vis * min(1.0, self.sel * 4))
        sel.move_to([x + 0.04 + sw / 2, y, 0])
        self.selbox.become(sel)

        gy = y - self.cap_h / 2
        ink = mix(INK, TOMB, self.dead)
        for i, c in enumerate(self.cells):
            on = i < k
            if on:
                off = c.dx - self.adv / 2  # glyph centre relative to its cell centre
                tx = x + (self.pad + (i + 0.5) * self.col + off) * p
                cur = c.mob.get_center()
                c.mob.shift([tx - cur[0], gy + c.dy - cur[1], 0])
                if self.dead > 0 and c.ch != " ":
                    c.mob.set_color(ink)
            op = vis if on else 0.0
            if c.op is None or abs(c.op - op) > 1e-3:
                c.mob.set_opacity(op)
                c.op = op

        if self.dead > 1e-3 and w > 0.12:
            a = np.array([x + 0.07, y, 0])
            b = np.array([x + 0.07 + (w - 0.14) * self.dead, y, 0])
            self.strike.put_start_and_end_on(a, b)
            self.strike.set_stroke(TOMB, width=2.5, opacity=vis)
        else:
            self.strike.set_stroke(opacity=0)

        key = self._tag_label()
        tkey = (key, round(self.dead, 2))
        if tkey != self._tag_key:
            self._tag_key = tkey
            # swap, never `become`: labels of different lengths have different glyphs.
            # Hide the old one first: the renderer froze its list of moving mobjects
            # when this play started, so a removed mobject is still drawn until it ends.
            self.tag.set_opacity(0)
            self.remove(self.tag)
            self.tag = self._build_tag(key)
            self.add(self.tag)
        self._place_tag(x, y, w, vis, k)

    def _place_tag(self, x, y, w, vis, k):
        if len(self.tag) == 0:
            return
        ty = (
            y - self.h / 2 - self.tag_gap - self.tag.height / 2
            if self.ids != "each"
            else None
        )
        if self.ids == "each":
            for i, t in enumerate(self.tag):
                t.move_to(
                    [self.col_x(i), y - self.h / 2 - self.tag_gap - t.height / 2, 0]
                )
                t.set_opacity(vis if i < k and i < self.tag_n - 0.5 else 0)
            return
        if self.tag.width > w - 0.12:
            self.tag.move_to([x + w / 2, ty, 0])
        else:
            self.tag.move_to([x + self.pad * 0.6 + self.tag.width / 2, ty, 0])
        self.tag.set_opacity(vis * float(np.clip(self.tag_n, 0, 1)))


class ItemRow(VGroup):
    """A replica's document as its list of items, left-anchored, always laid out."""

    def __init__(self, at, gap=0.09):
        super().__init__()
        self.gap = gap
        self.anchor = Dot(at, radius=0.001, fill_opacity=0, stroke_opacity=0)
        self.blocks: list = []
        self.add(self.anchor)
        self.x1 = float(at[0])
        self.add_updater(ItemRow._tick)

    @staticmethod
    def _tick(m):
        m.layout()

    @property
    def y(self):
        return float(self.anchor.get_center()[1])

    @property
    def x0(self):
        return float(self.anchor.get_center()[0])

    def push(self, *blocks):
        for b in blocks:
            self.blocks.append(b)
            self.add(b)
        self.layout()
        return self

    def insert(self, index, block):
        """Put ``block`` at ``index`` (give it ``n=0`` and ``Type`` it to grow in place)."""
        self.blocks.insert(index, block)
        self.add(block)
        self.layout()
        return block

    def drop(self, block):
        """Take ``block`` out of the row (collapse it with ``Tween(block, p=0)`` first)."""
        self.blocks.remove(block)
        self.remove(block)
        self.layout()
        return self

    def slot_x(self, index):
        """Centre x of the block currently at ``index``."""
        b = self.blocks[index]
        return self.left_of(index) + b.w / 2

    def _gap_after(self, b):
        g = self.gap if getattr(b, "gap", None) is None else b.gap
        return g * b.gap_now if g > 0 else g

    def layout(self):
        x, y = self.x0, self.y
        for b in self.blocks:
            b.x, b.y = x, y
            b.refresh()
            x += b.w + self._gap_after(b)
        self.x1 = x
        return self

    def left_of(self, index):
        x = self.x0
        for b in self.blocks[:index]:
            x += b.w + self._gap_after(b)
        return x

    def real(self):
        return [b for b in self.blocks if isinstance(b, Block)]

    def find(self, peer, clock):
        """The block holding id ``peer:clock`` and the offset inside it."""
        for b in self.real():
            if b.peer.cid == peer.cid and b.clock <= clock < b.clock + len(b.text):
                return b, clock - b.clock
        raise KeyError((peer.cid, clock))

    def split(self, block, k):
        """Split ``block`` after ``k`` characters (what Yjs does when an item lands inside
        a run). The halves start glued together; tween ``left.gap`` to open them."""
        i = self.blocks.index(block)
        a = Block(block.text[:k], block.peer, block.clock, **block.style)
        b = Block(block.text[k:], block.peer, block.clock + k, **block.style)
        a.dead = b.dead = block.dead
        a.gap = -2 * block.pad
        b.gap = block.gap
        self.blocks[i : i + 1] = [a, b]
        self.remove(block)
        self.add(a, b)
        self.layout()
        return a, b

    def text_now(self):
        return "".join(
            b.text[: int(math.floor(b.n + 1e-6))] for b in self.real() if b.dead < 0.5
        )

    def end_x(self):
        return self.x1


class Dock(Animation):
    """Fly ``block`` into ``row`` at ``index`` while the row opens a slot for it."""

    def __init__(
        self,
        row,
        block,
        index,
        run_time=0.8,
        rate_func=smooth,
        lift=0.0,
        appear=False,
        **kw,
    ):
        self.row, self.block, self.index, self.lift = row, block, index, lift
        self.appear = appear  # fade the block in during the first third of the flight
        if appear:
            block.alpha = 0.0
            block.refresh()
        super().__init__(block, run_time=run_time, rate_func=rate_func, **kw)

    def begin(self):
        self.spacer = Spacer(0.0)
        self.row.blocks.insert(self.index, self.spacer)
        self.x0, self.y0 = self.block.x, self.block.y
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        a = self.rate_func(alpha)
        self.spacer.w = (self.block.full_w + self.row.gap) * a
        i = self.row.blocks.index(self.spacer)
        tx, ty = self.row.left_of(i), self.row.y
        self.block.x = self.x0 + (tx - self.x0) * a
        self.block.y = self.y0 + (ty - self.y0) * a + self.lift * math.sin(math.pi * a)
        if self.appear:
            self.block.alpha = min(1.0, alpha / 0.35)
        self.block.refresh()

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        i = self.row.blocks.index(self.spacer)
        self.row.blocks[i] = self.block
        scene.remove(self.block)
        self.row.add(self.block)
        self.row.layout()


# --------------------------------------------------------------------------- #
# carets
# --------------------------------------------------------------------------- #


class Caret(VGroup):
    """A collaborator's caret with a name flag. Follows a LiveLine span or a Block.

    ``follow_spans(line, spans)``: sits after the last of ``spans`` that has text;
    ``follow_block(block)``: sits at the typing point of a block;
    ``follow_col(block, i)``: sits in front of character ``i`` of a block;
    ``follow_after(block, off)``: sits in the gap next to a block (one cell per character).
    """

    def __init__(self, peer, h=0.44, flag=True, fs=16, blink=True, show=1.0):
        super().__init__()
        self.peer, self.blink = peer, blink
        self.h0 = h  # bar height at the scale the caret was built at
        self.show = float(
            show
        )  # 0 hidden .. 1 visible (tween it to make the caret appear)
        self.bar = Rectangle(
            width=0.05, height=h, stroke_width=0, fill_color=peer.color, fill_opacity=1
        )
        self.add(self.bar)
        self.flag = None
        if flag:
            name = Text(peer.name, font_size=fs, color=BG, weight="BOLD")
            inner = name
            if peer.agent:
                inner = VGroup(sparkle(BG, r=0.07), name).arrange(RIGHT, buff=0.06)
            tag = RoundedRectangle(
                width=inner.width + 0.18,
                height=name.height + 0.14,
                corner_radius=0.06,
                stroke_width=0,
                fill_color=peer.color,
                fill_opacity=1,
            )
            inner.move_to(tag)
            self.flag = VGroup(tag, inner)
            self.flag.next_to(self.bar, UP, buff=0).align_to(self.bar, LEFT)
            self.add(self.flag)
        self.mode, self.ref, self.spans = None, None, None
        self.idle = 0.0
        self._shown = None
        self.add_updater(Caret._tick)
        self.step(0)

    @staticmethod
    def _tick(m, dt):
        m.step(dt)

    def resize(self, h):
        """Change the bar height (in the units the caret was built in)."""
        if abs(h - self.h0) > 1e-6:
            self.bar.stretch(h / self.h0, 1)
            self.h0 = h
            if self.flag is not None:
                self.flag.next_to(self.bar, UP, buff=0).align_to(self.bar, LEFT)
        return self

    def follow_spans(self, line, spans, fit=True):
        self.mode, self.ref = "spans", line
        self.spans = list(spans) if isinstance(spans, list | tuple) else [spans]
        if fit:
            self.resize(line.cap_h * 1.6)
        return self.step(0)

    def follow_block(self, block, fit=True):
        self.mode, self.ref = "block", block
        if fit:
            self.resize(block.h * 0.74)
        return self.step(0)

    def follow_col(self, block, i, fit=True):
        """Sit in front of character ``i`` of a block (a position inside a run)."""
        self.mode, self.ref, self.col_i = "col", block, i
        if fit:
            self.resize(block.h * 0.74)
        return self.step(0)

    def follow_after(self, block, off=0.08, fit=True):
        """Sit in the gap beside a block: after it once it has text, before it while it
        is still empty (``off`` = half the row's gap), so the caret never enters a cell."""
        self.mode, self.ref, self.off = "after", block, off
        if fit:
            self.resize(block.h * 0.74)
        return self.step(0)

    def aim(self):
        """The point the caret should sit on (``target`` is taken by Mobject)."""
        if self.mode == "spans":
            sp = self.spans[0]
            for cand in self.spans:
                if cand.n > 1e-6:
                    sp = cand
            return self.ref.point_after(sp)
        if self.mode == "block":
            b = self.ref
            return np.array(
                [b.x + (b.pad * b.shown + b.col * max(b.n, 0)) * b.p + 0.03, b.y, 0]
            )
        if self.mode == "col":
            b = self.ref
            return np.array([b.x + b.pad + self.col_i * b.col, b.y, 0])
        if self.mode == "after":
            b = self.ref
            return np.array([b.x + b.w + self.off * (2 * b.shown - 1), b.y, 0])
        return None

    def step(self, dt):
        t = self.aim()
        if t is not None:
            d = t - self.bar.get_center()
            if np.linalg.norm(d[:2]) > 1e-5:
                self.shift([d[0], d[1], 0])
                self.idle = 0.0
        self.idle += dt
        on = (not self.blink) or self.idle < 0.45 or (self.idle % 1.06) < 0.6
        state = (round(self.show, 3), on)
        if state != self._shown:
            self._shown = state
            self.bar.set_opacity(self.show * (1.0 if on else 0.18))
            if self.flag is not None:
                self.flag.set_opacity(self.show)
        return self

    def refresh(self):
        self.step(0)


# --------------------------------------------------------------------------- #
# network glyphs
# --------------------------------------------------------------------------- #


def wifi(color=GOOD, s=1.0, off=False):
    """The connection glyph: three arcs over a dot (struck through when offline)."""
    g = VGroup(Dot([0, 0, 0], radius=0.05 * s, color=color))
    for r in (0.16, 0.29, 0.42):
        g.add(
            Arc(
                radius=r * s,
                start_angle=PI / 4,
                angle=PI / 2,
                stroke_color=color,
                stroke_width=4 * s,
            )
        )
    if off:
        g.add(
            Line(
                [-0.36 * s, -0.06 * s, 0],
                [0.36 * s, 0.5 * s, 0],
                stroke_color=color,
                stroke_width=4 * s,
            )
        )
    return g


def server_glyph(color=MUTED, w=0.92, h=0.66, led=GOOD):
    """A small server: a case with two bays and status lights."""
    case = RoundedRectangle(
        width=w,
        height=h,
        corner_radius=0.1,
        stroke_color=color,
        stroke_width=2.5,
        fill_color=PANEL,
        fill_opacity=1,
    )
    mid = Line(
        [-w / 2 + 0.08, 0, 0],
        [w / 2 - 0.08, 0, 0],
        stroke_color=color,
        stroke_width=1.5,
    )
    leds = VGroup(
        Dot([-w / 2 + 0.2, h / 4, 0], radius=0.045, color=led),
        Dot([-w / 2 + 0.2, -h / 4, 0], radius=0.045, color=led),
    )
    slots = VGroup(
        Line([-w / 2 + 0.36, h / 4, 0], [w / 2 - 0.16, h / 4, 0]),
        Line([-w / 2 + 0.36, -h / 4, 0], [w / 2 - 0.16, -h / 4, 0]),
    ).set_stroke(FAINT, width=3)
    g = VGroup(case, mid, slots, leds)
    g.case, g.leds = case, leds
    return g


def db_cylinder(color=MINT, w=1.0, h=0.9):
    """A database."""
    ry = 0.14
    top = Ellipse(width=w, height=2 * ry, stroke_color=color, stroke_width=2.5)
    top.set_fill(color, opacity=0.3).move_to([0, h / 2 - ry, 0])
    body = Rectangle(
        width=w, height=h - 2 * ry, stroke_width=0, fill_color=color, fill_opacity=0.14
    )
    sides = VGroup(
        Line([-w / 2, h / 2 - ry, 0], [-w / 2, -h / 2 + ry, 0]),
        Line([w / 2, h / 2 - ry, 0], [w / 2, -h / 2 + ry, 0]),
    ).set_stroke(color, width=2.5)
    bottom = Arc(
        radius=1, start_angle=PI, angle=PI, stroke_color=color, stroke_width=2.5
    )
    bottom.stretch_to_fit_width(w).stretch_to_fit_height(ry).move_to(
        [0, -h / 2 + ry / 2, 0]
    )
    g = VGroup(body, sides, bottom, top)
    g.body = body
    return g


# --------------------------------------------------------------------------- #
# the Item card (the real struct) and the state vector
# --------------------------------------------------------------------------- #


def strut(text, fs, color):
    """Mono text behind an invisible full-height bar, so every row has the same box
    (rows of a table then line up on their baselines, whatever their letters)."""
    t = Text("|" + text, font=MONO, font_size=fs, color=color, disable_ligatures=True)
    t[0].set_opacity(0)
    return t


def id_text(idpair, fs=22):
    """An id ``client:clock`` coloured by its client; ``null`` when absent."""
    if idpair is None:
        return strut("null", fs, MUTED)
    return strut(f"{idpair[0]}:{idpair[1]}", fs, PEERS[idpair[0]].color)


def item_card(peer, id_, origin, right, content, fs=24, w=3.7, pitch=None):
    """A Yjs ``Item`` as its real fields: id, origin, rightOrigin, content."""
    rows = [
        ("id", id_text(id_, fs)),
        ("origin", id_text(origin, fs)),
        ("rightOrigin", id_text(right, fs)),
        ("content", strut(f'"{content}"', fs, STR)),
    ]
    keys = VGroup(*[strut(k, fs, MUTED) for k, _ in rows])
    vals = VGroup(*[v for _, v in rows])
    pitch = pitch or keys[0].height + 0.1
    val_x = max(k.width for k in keys) + 0.3
    for i, (k, v) in enumerate(zip(keys, vals, strict=True)):
        k.move_to([k.width / 2, -i * pitch, 0])
        v.move_to([val_x + v.width / 2, -i * pitch, 0])
    body = VGroup(keys, vals)
    bg = RoundedRectangle(
        width=max(w, body.width + 0.6),
        height=body.height + 0.92,
        corner_radius=0.14,
        stroke_color=peer.color,
        stroke_width=2.5,
        fill_color=CODE_BG,
        fill_opacity=1,
    )
    title = mono("Item", fs=fs - 4, color=peer.color)
    body.move_to(bg).shift(DOWN * 0.2).align_to(bg, LEFT).shift(RIGHT * 0.2)
    title.move_to(
        [bg.get_left()[0] + 0.36 + title.width / 2, bg.get_top()[1] - 0.28, 0]
    )
    rule = Line(
        [bg.get_left()[0] + 0.2, bg.get_top()[1] - 0.5, 0],
        [bg.get_right()[0] - 0.2, bg.get_top()[1] - 0.5, 0],
        stroke_color=FAINT,
        stroke_width=1.5,
    )
    g = VGroup(bg, title, rule, body)
    g.bg, g.keys, g.vals = bg, keys, vals
    g.f_id, g.f_origin, g.f_right, g.f_content = vals
    return g


class SVPanel(VGroup):
    """A state vector: for every client, the highest clock this copy has seen.

    ``val[cid]`` is the clock (animatable through ``Tween(panel.bars[cid], v=...)``);
    ``ghost[cid]`` marks a range the copy is missing.
    """

    class Bar:
        def __init__(self, v):
            self.v, self.ghost, self.ghost_op = float(v), float(v), 0.0

    def __init__(
        self, clocks, vmax=17, w=2.5, title="state vector", fs=17, row_h=0.3, thick=0.5
    ):
        super().__init__()
        self.vmax, self.w, self.row_h, self.fs = vmax, w, row_h, fs
        self.bar_h = row_h * thick
        self.bars = {cid: SVPanel.Bar(v) for cid, v in clocks.items()}
        self.title = mono(title, fs=fs - 1, color=MUTED)
        self.names, self.tracks, self.fills, self.ghosts, self.nums = {}, {}, {}, {}, {}
        self._num_key = {}
        rows = VGroup()
        for cid in clocks:
            peer = PEERS[cid]
            # names wear ink: the bar beside each one carries the writer's colour
            name = Text(peer.name, font_size=fs, color=INK, weight="MEDIUM")
            track = Rectangle(
                width=w,
                height=self.bar_h,
                stroke_width=0,
                fill_color=FAINT,
                fill_opacity=0.45,
            )
            fill = Rectangle(
                width=w,
                height=self.bar_h,
                stroke_width=0,
                fill_color=peer.color,
                fill_opacity=0.95,
            )
            ghost = Rectangle(
                width=0.1, height=self.bar_h, stroke_color=peer.color, stroke_width=1.5
            )
            ghost.set_fill(peer.color, opacity=0)
            num = VGroup(
                mono(str(int(clocks[cid])), fs=fs, color=INK)
            )  # holder: digits get swapped
            self.names[cid], self.tracks[cid], self.fills[cid] = name, track, fill
            self.ghosts[cid], self.nums[cid] = ghost, num
            rows.add(VGroup(name, track, fill, ghost, num))
        self.rows = rows
        self.add(self.title, rows)
        self.x, self.y = 0.0, 0.0
        self.name_w = max(n.width for n in self.names.values())
        self.place(0, 0)
        self.add_updater(SVPanel._tick)

    @staticmethod
    def _tick(m):
        m.refresh()

    def place(self, x, y):
        """``(x, y)`` = left end of the first bar track's centre line."""
        self.x, self.y = float(x), float(y)
        self._key = None
        self.refresh()
        return self

    def bar_point(self, cid, v):
        i = list(self.bars).index(cid)
        return np.array([self.x + self.w * v / self.vmax, self.y - i * self.row_h, 0])

    def refresh(self):
        key = tuple((b.v, b.ghost, b.ghost_op) for b in self.bars.values()) + (
            self.x,
            self.y,
        )
        if key == getattr(self, "_key", None):
            return
        self._key = key
        self.title.move_to(
            [
                self.x - self.name_w - 0.18 + self.title.width / 2,
                self.y + self.row_h * 0.95,
                0,
            ]
        )
        for i, (cid, b) in enumerate(self.bars.items()):
            y = self.y - i * self.row_h
            self.names[cid].move_to([self.x - 0.18 - self.names[cid].width / 2, y, 0])
            self.tracks[cid].move_to([self.x + self.w / 2, y, 0])
            fw = max(1e-3, self.w * b.v / self.vmax)
            f = Rectangle(width=fw, height=self.bar_h, stroke_width=0)
            f.set_fill(PEERS[cid].color, opacity=0.95).move_to([self.x + fw / 2, y, 0])
            self.fills[cid].become(f)
            gw = max(1e-3, self.w * (b.ghost - b.v) / self.vmax)
            g = Rectangle(width=gw, height=self.bar_h)
            g.set_stroke(PEERS[cid].color, width=1.8, opacity=b.ghost_op)
            g.set_fill(PEERS[cid].color, opacity=0.22 * b.ghost_op)
            g.move_to([self.x + fw + gw / 2, y, 0])
            self.ghosts[cid].become(g)
            shown = str(int(round(b.v)))
            if self._num_key.get(cid) != shown:
                self._num_key[cid] = shown
                holder = self.nums[cid]
                for (
                    old
                ) in holder.submobjects:  # hidden, then removed (see Block.refresh)
                    old.set_opacity(0)
                holder.remove(*holder.submobjects)
                holder.add(mono(shown, fs=self.fs, color=INK))
            self.nums[cid].move_to(
                [self.x + self.w + 0.16 + self.nums[cid].width / 2, y, 0]
            )


# --------------------------------------------------------------------------- #
# the editor window (a Tiptap-style rich text editor)
# --------------------------------------------------------------------------- #


def _tool(label, weight="BOLD", slant=None, fs=16):
    t = txt(label, fs=fs, color=TOOL_C, weight=weight, slant=slant)
    box = RoundedRectangle(
        width=max(0.36, t.width + 0.18),
        height=0.34,
        corner_radius=0.07,
        stroke_color=FAINT,
        stroke_width=1.2,
        fill_opacity=0,
    )
    t.move_to(box)
    return VGroup(box, t)


class EditorWindow(VGroup):
    """A dark rich-text editor window: title bar, toolbar, page and presence avatars.

    ``line(y_from_top, parts, ...)`` adds a ``LiveLine`` on the page; ``join(peer)``
    returns the animation of a collaborator appearing in the presence bar.
    """

    def __init__(self, w=11.4, h=4.6, title="notes", bar_h=0.5, tool_h=0.5):
        super().__init__()
        self.w0, self.h0, self.bar_h, self.tool_h = w, h, bar_h, tool_h
        r = 0.16
        bg = RoundedRectangle(width=w, height=h, corner_radius=r, stroke_width=0)
        bg.set_fill(WINDOW_BG, opacity=1)
        head = RoundedRectangle(width=w, height=bar_h, corner_radius=r, stroke_width=0)
        head.set_fill(WINDOW_BAR, opacity=1).align_to(bg, UP)
        head_sq = Rectangle(width=w, height=bar_h / 2, stroke_width=0)
        head_sq.set_fill(WINDOW_BAR, opacity=1).align_to(head, DOWN)
        tool_bg = Rectangle(width=w, height=tool_h, stroke_width=0)
        tool_bg.set_fill("#161C28", opacity=1).next_to(head, DOWN, buff=0)
        rule = Line(
            tool_bg.get_corner(DL),
            tool_bg.get_corner(DR),
            stroke_color=FAINT,
            stroke_width=1.5,
        )
        dots = VGroup(
            *[Dot(radius=0.055, color=c) for c in ("#FF5F57", "#FEBC2E", "#28C840")]
        )
        dots.arrange(RIGHT, buff=0.12)
        dots.move_to([bg.get_left()[0] + 0.5, head.get_center()[1], 0])
        ttl = Text(title, font_size=17, color=MUTED, weight="MEDIUM")
        ttl.next_to(dots, RIGHT, buff=0.3).set_y(head.get_center()[1])
        tools = VGroup(
            _tool("B"),
            _tool("I", weight="NORMAL", slant=ITALIC),
            _tool("S", weight="NORMAL"),
            _tool("H1", fs=16),
            _tool("H2", fs=16),
            _tool("•", fs=18),
            _tool("“", fs=20),
            _tool("</>", fs=16, weight="NORMAL"),
        ).arrange(RIGHT, buff=0.12)
        tools.move_to(
            [bg.get_left()[0] + 0.5 + tools.width / 2, tool_bg.get_center()[1], 0]
        )
        border = RoundedRectangle(
            width=w, height=h, corner_radius=r, stroke_color=FAINT, stroke_width=2
        )
        border.set_fill(opacity=0)
        self.bg, self.head, self.tool_bg, self.border = bg, head, tool_bg, border
        self.chrome = VGroup(bg, head, head_sq, tool_bg, rule, dots, ttl, tools)
        # a ruler so children can tell how much the window has been scaled
        self.ruler = Line(
            bg.get_corner(UL), bg.get_corner(UL) + RIGHT, stroke_opacity=0
        )
        self.presence = VGroup()
        self.lines: list[LiveLine] = []
        self.carets: dict = {}
        self.body = VGroup()
        self.add(self.chrome, self.ruler, self.body, self.presence, border)
        self.margin = 0.75

    @property
    def s(self):
        return self.ruler.get_length()

    def page_point(self, y_from_top, x=0.0):
        """A point on the page: ``y_from_top`` below the toolbar, ``x`` right of the margin."""
        ul = self.ruler.get_start()
        s = self.s
        return np.array(
            [
                ul[0] + (self.margin + x) * s,
                ul[1] - (self.bar_h + self.tool_h + y_from_top) * s,
                0,
            ]
        )

    def line(self, y_from_top, parts, fs=26, weight="NORMAL", color=INK, **kw):
        ln = LiveLine(
            parts,
            fs=fs,
            weight=weight,
            color=color,
            at=self.page_point(y_from_top),
            **kw,
        )
        self.lines.append(ln)
        self.body.add(ln)
        return ln

    def caret(self, peer, h=0.44, **kw):
        c = Caret(peer, h=h, **kw)
        self.carets[peer.cid] = c
        self.body.add(c)
        return c

    def presence_slot(self, i, r=0.17):
        ur = self.bg.get_corner(UR)
        s = self.s
        return np.array([ur[0] - (0.5 + i * 0.4) * s, ur[1] - self.bar_h * s / 2, 0])

    def join(self, peer, r=0.18, shown=False):
        """Add ``peer``'s avatar to the presence bar, parked at near-zero size.

        Returns ``(avatar, width)``: play ``Pop(avatar, width)`` to make it appear.
        """
        a = avatar(peer, r=r, ring=WINDOW_BAR)
        a.scale(self.s).move_to(self.presence_slot(len(self.presence)))
        width = a.width
        if not shown:
            a.scale(1e-3)
        self.presence.add(a)
        return a, width

    def owner(self, peer):
        """Mark the window as ``peer``'s private copy (border in their colour)."""
        self.border.set_stroke(peer.color, width=2.5)
        return self
