"""A* Pathfinding on a Manhattan street map — a ~2-minute explainer, house-style.

How the A* search algorithm finds the shortest route across Manhattan's street
grid, and *why* it explores the way it does: it always expands the node with the
smallest

        f(n) = g(n) + h(n)

where g(n) is the real distance travelled so far and h(n) is a straight-line
(admissible) guess of what remains. That single rule makes the search rush
toward the goal instead of fanning out blindly.

Four scenes, bookended by the channel's intro/outro cards:

    1. MapIntro  -- the Manhattan street network fades in; Start (Times Sq) and
                    Goal (Wall St) flash.
    2. Search    -- A* explores: frontier nodes glow yellow, settled nodes turn
                    blue, a live panel counts nodes/frontier/f(n); the optimal
                    route lights up green when the goal is reached.
    3. Explain   -- freeze and label g(n), h(n) and f(n) = g(n) + h(n) on the map.
    4. FinalPath -- a car drives the found route from Start to Goal.

Design notes
------------
* The map is generated procedurally — an authentic Manhattan grid (rotated ~29°
  off true north, with Broadway cutting across as a diagonal shortcut). No GIS
  stack (osmnx/geopandas) and no network access are required, and the clean grid
  lets you actually *see* A* expand.
* Edge weights and the heuristic both use straight-line (Euclidean) distance in
  screen space, so h never overestimates → A* stays optimal even with Broadway's
  diagonal. A single scale maps screen units to a plausible number of miles.
* Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders without a
  LaTeX install and stays fast to iterate on.

Scenes are exposed both individually (``MapIntro``, ``Search``, ``Explain``,
``FinalPath``, ``Intro``, ``Outro``) and as one continuous film
(``AStarPathfinding``).

Env knobs:
    ASTAR_QUICK=1   shorten every hold for a fast sanity render
"""

from __future__ import annotations

import heapq
import os
from collections import defaultdict

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


QUICK = os.environ.get("ASTAR_QUICK") == "1"
# Single knob for pacing: every on-screen "hold" is scaled by this. QUICK
# collapses the holds for fast iteration; otherwise it sets the reading rhythm.
DELAY = 0.25 if QUICK else 1.4
# Slow every played animation down a touch so motion doesn't feel rushed.
ANIM_SLOW = 1.0 if QUICK else 1.15
# Beat held on a finished scene before it wipes to the next one.
SCENE_GAP = 0.0 if QUICK else 2.0

# ---- palette (the brief's colours, harmonised to the dark house style) ---- #
BG = "#12121F"  # dark background
STREET = "#3A3F55"  # street lines, thin grey
STREET_HI = "#5C6486"  # brighter street (Broadway)
INK = "#F5F3EF"  # warm white text
MUTED = "#8A93A6"  # secondary text
FAINT = "#2A2E40"  # very faint lines / land
PANEL = "#0C0C16"  # info-panel fill
START_C = "#00CC44"  # start green
GOAL_C = "#FF3344"  # goal red
EXPLORED = "#4A90D9"  # settled/explored nodes (blue)
FRONTIER = "#FFD700"  # frontier nodes (yellow)
PATH_C = "#00FF66"  # final path (bright green)
HEUR_C = "#FF8C42"  # heuristic (h) — orange
G_C = "#4A90D9"  # g — blue
F_C = "#FFD166"  # f — gold

# ---- map parameters ------------------------------------------------------- #
N_AVE = 9  # avenues (vertical grid lines, run N–S)
N_ST = 17  # cross streets (horizontal grid lines, run E–W)
AVE_DX = 1.0  # screen spacing between avenues (the long block)
ST_DY = 0.62  # screen spacing between streets (the short block)
THETA = -29 * DEGREES  # Manhattan grid rotation off true north
START = (8, 16)  # "Midtown" — sits at the head of Broadway
GOAL = (0, 1)  # "Wall Street" — off Broadway's line, so A* must fan out to reach it
MILES_STRAIGHT = 4.5  # real Times Sq → Wall St, used to calibrate the miles read-out


def _rot(p, theta=THETA):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([c * p[0] - s * p[1], s * p[0] + c * p[1], 0.0])


def build_manhattan():
    """Build the procedural Manhattan graph.

    Returns a dict with screen-space node positions, the edge set, the Broadway
    edges, adjacency (with Euclidean weights), the miles scale, and helpers.
    """
    raw = {}
    for a in range(N_AVE):
        for s in range(N_ST):
            raw[(a, s)] = np.array([a * AVE_DX, s * ST_DY, 0.0])

    edges = set()
    for a in range(N_AVE):
        for s in range(N_ST):
            if (a + 1, s) in raw:
                edges.add(frozenset([(a, s), (a + 1, s)]))
            if (a, s + 1) in raw:
                edges.add(frozenset([(a, s), (a, s + 1)]))

    # Broadway: a diagonal shortcut stepping one avenue over for every two
    # streets down (7,14)->(6,12)->...->(0,0), crossing the grid.
    bw_nodes = []
    a, s = START
    bw_nodes.append((a, s))
    while a - 1 >= 0 and s - 2 >= 0:
        a, s = a - 1, s - 2
        bw_nodes.append((a, s))
    broadway = set()
    for u, v in zip(bw_nodes, bw_nodes[1:]):
        e = frozenset([u, v])
        edges.add(e)
        broadway.add(e)

    # rotate, then fit the rotated cloud into a framing box (map on the left,
    # info panel on the right).
    rotated = {k: _rot(v) for k, v in raw.items()}
    xs = [p[0] for p in rotated.values()]
    ys = [p[1] for p in rotated.values()]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    BOXW, BOXH = 9.1, 6.0
    BOX_CX, BOX_CY = -2.05, -0.35
    scale = min(BOXW / (maxx - minx), BOXH / (maxy - miny))

    def rs_to_screen(rp):
        return np.array(
            [(rp[0] - cx) * scale + BOX_CX, (rp[1] - cy) * scale + BOX_CY, 0.0]
        )

    def to_screen(rawpt):
        return rs_to_screen(_rot(rawpt))

    pos = {k: to_screen(v) for k, v in raw.items()}

    adj = defaultdict(list)
    for e in edges:
        u, v = tuple(e)
        w = float(np.linalg.norm(pos[u] - pos[v]))
        adj[u].append((v, w))
        adj[v].append((u, w))

    miles_k = MILES_STRAIGHT / float(np.linalg.norm(pos[START] - pos[GOAL]))

    # land silhouette: the grid rectangle's four corners (rotated) with a margin.
    pad_a, pad_s = 0.55 * AVE_DX, 0.55 * ST_DY
    corners = [
        (-pad_a, -pad_s),
        ((N_AVE - 1) * AVE_DX + pad_a, -pad_s),
        ((N_AVE - 1) * AVE_DX + pad_a, (N_ST - 1) * ST_DY + pad_s),
        (-pad_a, (N_ST - 1) * ST_DY + pad_s),
    ]
    land = [to_screen(np.array([x, y, 0.0])) for x, y in corners]

    return dict(
        raw=raw,
        edges=edges,
        broadway=broadway,
        bw_nodes=bw_nodes,
        pos=pos,
        adj=adj,
        miles_k=miles_k,
        land=land,
    )


def astar(adj, pos, start, goal):
    """A* with a straight-line heuristic. Returns (steps, path, cost).

    ``steps`` records the search chronologically so it can be replayed: each
    entry is the node expanded plus the frontier it opened and running counts.
    """

    def h(n):
        return float(np.linalg.norm(pos[n] - pos[goal]))

    g = {start: 0.0}
    came = {}
    open_heap = [(h(start), 0.0, start)]
    in_open = {start}
    closed = set()
    steps = []

    while open_heap:
        f, gc, u = heapq.heappop(open_heap)
        if u in closed:
            continue
        closed.add(u)
        in_open.discard(u)

        newf = []
        if u != goal:
            for v, w in adj[u]:
                if v in closed:
                    continue
                cand = g[u] + w
                if v not in g or cand < g[v] - 1e-9:
                    g[v] = cand
                    came[v] = u
                    heapq.heappush(open_heap, (cand + h(v), cand, v))
                    in_open.add(v)
                    newf.append((v, u))

        steps.append(
            dict(
                node=u,
                g=g[u],
                h=h(u),
                f=g[u] + h(u),
                newf=newf,
                n_closed=len(closed),
                n_open=len(in_open),
            )
        )
        if u == goal:
            break

    path = [goal]
    while path[-1] != start:
        path.append(came[path[-1]])
    path.reverse()
    return steps, path, g[goal], came


# ========================================================================== #
# Base scene: house-style timing, cards, palette.
# ========================================================================== #
class _AStarBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # Slow every played animation uniformly (see ANIM_SLOW); never scale waits.
    def play(self, *anims, **kwargs):
        is_wait = any(type(a).__name__ == "Wait" for a in anims)
        if not QUICK and anims and not is_wait:
            rt = kwargs.get("run_time")
            if rt is None:
                rts = [r for r in (getattr(a, "run_time", None) for a in anims) if r]
                rt = max(rts) if rts else 1.0
            kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def wipe(self, rt=0.7, gap=True):
        if gap and SCENE_GAP:
            self.wait(SCENE_GAP)
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- house-style intro / outro cards ---------------------------------- #
    def introduction(self, title1, title2):
        header = Text(title1, font_size=52, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=F_C)
        writer = Text("Created by Ptolémé", font_size=28, color=EXPLORED)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.8)
        sub = Text(title2, font_size=34, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.2)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "A* Pathfinding",
            "finding the shortest route across Manhattan",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.4)

    def play_outro(self):
        self.card_wait(0.6)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=F_C)
        writer = Text("Created by Ptolémé", font_size=28, color=EXPLORED)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.2)
        self.card_wait(2.4)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.4)
        self.card_wait(0.6)

    # ====================================================================== #
    # Shared map construction
    # ====================================================================== #
    def _build(self):
        """Build the graph, run A*, and construct (but don't add) the mobjects."""
        if getattr(self, "_built", False):
            return
        m = build_manhattan()
        self.pos = m["pos"]
        self.edges = m["edges"]
        self.broadway = m["broadway"]
        self.adj = m["adj"]
        self.miles_k = m["miles_k"]
        self.land_pts = m["land"]
        self.start, self.goal = START, GOAL
        self.steps, self.path, self.cost, self.came = astar(
            self.adj, self.pos, START, GOAL
        )
        self.path_miles = self.cost * self.miles_k

        # land body
        self.land = Polygon(*self.land_pts, stroke_width=0).set_fill(FAINT, 0.55)

        # streets (reused throughout: colouring them shows the explored network)
        self.lines = {}
        street_group = VGroup()
        for e in self.edges:
            u, v = tuple(e)
            ln = Line(self.pos[u], self.pos[v])
            if e in self.broadway:
                ln.set_stroke(STREET_HI, 2.6, 0.85)
            else:
                ln.set_stroke(STREET, 2.0, 0.6)
            self.lines[e] = ln
            street_group.add(ln)
        self.street_group = street_group

        # intersections
        self.dots = {}
        dot_group = VGroup()
        for k in self.pos:
            d = Dot(self.pos[k], radius=0.05).set_fill(MUTED, 0.55).set_stroke(width=0)
            self.dots[k] = d
            dot_group.add(d)
        self.dot_group = dot_group

        # start / goal markers
        self.s_marker = self._marker(self.pos[START], "S", START_C)
        self.g_marker = self._marker(self.pos[GOAL], "G", GOAL_C)

        # labels
        self.map_title = Text(
            "New York City Street Network", font_size=32, color=INK, weight="BOLD"
        )
        self.map_title.move_to([-2.05, 3.55, 0])
        ts = Text("Midtown", font_size=17, color=MUTED).next_to(
            self.s_marker, DOWN, buff=0.1
        )
        ws = Text("Wall Street", font_size=17, color=MUTED).next_to(
            self.g_marker, RIGHT, buff=0.12
        )
        # Broadway label, aligned to the diagonal
        p0 = self.pos[m["bw_nodes"][2]]
        p1 = self.pos[m["bw_nodes"][4]]
        ang = np.arctan2((p1 - p0)[1], (p1 - p0)[0])
        bw = Text("BROADWAY", font_size=15, color=STREET_HI)
        bw.rotate(ang).move_to((p0 + p1) / 2 + np.array([0.45, 0.25, 0.0]))
        self.landmarks = VGroup(ts, ws, bw)

        self._built = True

    def _marker(self, p, letter, color):
        d = Dot(p, radius=0.15).set_fill(color, 1.0).set_stroke(INK, 1.5)
        halo = Circle(radius=0.24, color=color).set_stroke(color, 3, 0.5).move_to(p)
        lab = Text(letter, font_size=20, color=BG, weight="BOLD").move_to(p)
        return VGroup(halo, d, lab)

    def _show_map_instant(self):
        """Put the whole (unexplored) map on screen with no animation."""
        self._build()
        if getattr(self, "_map_on", False):
            return
        self.add(
            self.land,
            self.street_group,
            self.dot_group,
            self.s_marker,
            self.g_marker,
            self.map_title,
            self.landmarks,
        )
        self._map_on = True

    def _line(self, u, v):
        return self.lines[frozenset([u, v])]

    def _route_to(self, n):
        """The route A* found from the start to node ``n`` (via the parent map)."""
        route = [n]
        while route[-1] != self.start:
            route.append(self.came[route[-1]])
        route.reverse()
        return route

    def _pick_illustrative_node(self):
        """An explored node offset from the straight start→goal line, so its real
        route (g) bends clearly away from the straight-line guess (h)."""
        s, g = self.pos[self.start], self.pos[self.goal]
        d = g - s
        L = float(np.linalg.norm(d))
        dhat = d / L
        best, best_perp = None, -1.0
        for n in self.came:
            if not (4 <= len(self._route_to(n)) <= 8):
                continue
            v = self.pos[n] - s
            along = float(np.dot(v, dhat))
            perp = float(np.linalg.norm(v - along * dhat))
            if 0.30 * L < along < 0.72 * L and perp > best_perp:
                best_perp, best = perp, n
        return best if best is not None else self.path[len(self.path) // 2]

    # ---- the live info panel --------------------------------------------- #
    def _build_panel(self):
        bg = RoundedRectangle(
            width=3.5, height=3.55, corner_radius=0.14
        ).set_fill(PANEL, 0.88).set_stroke(MUTED, 1.5, 0.55)
        bg.to_corner(UR, buff=0.35)
        head = Text("A*  SEARCH", font_size=24, color=INK, weight="BOLD")
        head.next_to(bg.get_top(), DOWN, buff=0.22)

        self.n_explored = Integer(0).set_color(EXPLORED)
        self.n_frontier = Integer(0).set_color(FRONTIER)
        self.cur_f = DecimalNumber(0, num_decimal_places=1).set_color(F_C)

        def row(label, value, y):
            lab = Text(label, font_size=20, color=MUTED)
            value.scale(0.62)  # DecimalNumber/Integer render large; bring in line
            lab.move_to([bg.get_left()[0] + 0.28, y, 0], aligned_edge=LEFT)
            value.move_to([bg.get_right()[0] - 0.32, y, 0], aligned_edge=RIGHT)
            return VGroup(lab, value)

        r1 = row("Nodes explored", self.n_explored, head.get_bottom()[1] - 0.55)
        r2 = row("Frontier size", self.n_frontier, head.get_bottom()[1] - 1.02)
        # f-row carries a "mi" unit; align the value + unit together on the right
        # so the unit stays inside the panel.
        lab3 = Text("Current f(n)", font_size=20, color=MUTED)
        self.cur_f.scale(0.62)
        f_unit = Text("mi", font_size=15, color=MUTED)
        fval = VGroup(self.cur_f, f_unit).arrange(RIGHT, buff=0.08, aligned_edge=DOWN)
        y3 = head.get_bottom()[1] - 1.49
        lab3.move_to([bg.get_left()[0] + 0.28, y3, 0], aligned_edge=LEFT)
        fval.move_to([bg.get_right()[0] - 0.32, y3, 0], aligned_edge=RIGHT)
        r3 = VGroup(lab3, fval)

        sep = Line(
            [bg.get_left()[0] + 0.25, head.get_bottom()[1] - 1.82, 0],
            [bg.get_right()[0] - 0.25, head.get_bottom()[1] - 1.82, 0],
        ).set_stroke(MUTED, 1, 0.4)

        legend = VGroup()
        for color, txt in [
            (START_C, "Start"),
            (GOAL_C, "Goal"),
            (FRONTIER, "Frontier"),
            (EXPLORED, "Explored"),
            (PATH_C, "Best path"),
        ]:
            dot = Dot(radius=0.07).set_fill(color, 1).set_stroke(width=0)
            lab = Text(txt, font_size=18, color=INK)
            legend.add(VGroup(dot, lab.next_to(dot, RIGHT, buff=0.14)))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        legend.next_to(sep, DOWN, buff=0.2).align_to(bg, LEFT).shift(RIGHT * 0.28)

        self.panel = VGroup(bg, head, r1, r2, r3, f_unit, sep, legend)
        return self.panel

    def _update_panel(self, step):
        self.n_explored.set_value(step["n_closed"])
        self.n_frontier.set_value(step["n_open"])
        self.cur_f.set_value(step["f"] * self.miles_k)

    # ====================================================================== #
    # Scene 1 — the map
    # ====================================================================== #
    def scene_map_intro(self):
        self._build()
        self.play(FadeIn(self.land), run_time=0.8)
        self.play(
            Create(self.street_group, lag_ratio=0.02),
            run_time=2.6,
        )
        self.play(FadeIn(self.dot_group, lag_ratio=0.002), run_time=1.0)
        self.play(Write(self.map_title), run_time=1.2)
        self.add(self.landmarks)
        self.play(FadeIn(self.landmarks), run_time=0.8)
        self._map_on = True
        self.beat(0.6)

        # flash start & goal
        self.play(FadeIn(self.s_marker, scale=0.4), run_time=0.6)
        self.play(Flash(self.pos[START], color=START_C, line_length=0.2), run_time=0.6)
        self.play(FadeIn(self.g_marker, scale=0.4), run_time=0.6)
        self.play(Flash(self.pos[GOAL], color=GOAL_C, line_length=0.2), run_time=0.6)
        self.beat(1.2)

    # ====================================================================== #
    # Scene 2 — the A* search
    # ====================================================================== #
    def scene_search(self):
        self._show_map_instant()
        self.play(FadeIn(self._build_panel()), run_time=0.8)
        self.beat(0.5)

        teach = 0 if QUICK else 5
        steps = self.steps

        # --- teaching phase: a few expansions in slow motion --------------- #
        heur_arrow = None
        for i in range(min(teach, len(steps))):
            step = steps[i]
            u = step["node"]
            anims = [
                self.dots[u].animate.set_fill(EXPLORED, 0.9).set_stroke(width=0),
            ]
            for v, par in step["newf"]:
                anims.append(
                    self._line(par, v).animate.set_stroke(EXPLORED, 3.0, 0.6)
                )
                anims.append(
                    self.dots[v].animate.set_fill(FRONTIER, 1.0).set_stroke(width=0)
                )
            glow = Circle(radius=0.2).set_stroke(FRONTIER, 4, 0.9).move_to(self.pos[u])
            self.play(FadeIn(glow, scale=1.6), *anims, run_time=0.5)
            self._update_panel(step)

            # heuristic arrow toward the goal, and the f = g + h read-out
            new_arrow = Arrow(
                self.pos[u],
                self.pos[self.goal],
                buff=0.18,
                stroke_width=3,
                color=HEUR_C,
                max_tip_length_to_length_ratio=0.05,
                max_stroke_width_to_length_ratio=3,
            ).set_opacity(0.55)
            chip = self._f_chip(step).next_to(self.pos[u], UR, buff=0.12)
            if heur_arrow is None:
                self.play(GrowArrow(new_arrow), FadeIn(chip, shift=UP * 0.1), run_time=0.4)
            else:
                self.play(
                    Transform(heur_arrow, new_arrow),
                    FadeIn(chip, shift=UP * 0.1),
                    run_time=0.4,
                )
            if heur_arrow is None:
                heur_arrow = new_arrow
            self.beat(0.5)
            self.play(FadeOut(chip), FadeOut(glow), run_time=0.3)

        if heur_arrow is not None:
            self.play(FadeOut(heur_arrow), run_time=0.4)

        # --- bulk phase: expand fast, in batches (instant recolour) -------- #
        i = teach
        batch = 1 if QUICK else 4
        while i < len(steps):
            grp = steps[i : i + batch]
            for step in grp:
                u = step["node"]
                self.dots[u].set_fill(EXPLORED, 0.85).set_stroke(width=0)
                for v, par in step["newf"]:
                    self._line(par, v).set_stroke(EXPLORED, 3.0, 0.55)
                    self.dots[v].set_fill(FRONTIER, 1.0).set_stroke(width=0)
            self._update_panel(grp[-1])
            self.wait(0.05 if QUICK else 0.16)
            i += batch

        # keep S / G on top of the recoloured dots
        self.add(self.s_marker, self.g_marker)
        self.beat(0.7)

        # --- reveal the optimal path -------------------------------------- #
        self._reveal_path(animate=True)
        self.beat(1.0)
        self._searched = True

    def _f_chip(self, step):
        g = step["g"] * self.miles_k
        h = step["h"] * self.miles_k
        f = step["f"] * self.miles_k
        txt = Text(
            f"f = g + h\n= {g:.1f} + {h:.1f}\n= {f:.1f} mi",
            font_size=18,
            color=INK,
            line_spacing=0.6,
        )
        box = RoundedRectangle(
            width=txt.width + 0.3,
            height=txt.height + 0.24,
            corner_radius=0.1,
        ).set_fill(PANEL, 0.92).set_stroke(F_C, 1.5, 0.8)
        txt.move_to(box)
        return VGroup(box, txt)

    def _reveal_path(self, animate=True):
        line_anims = []
        for a, b in zip(self.path, self.path[1:]):
            ln = self._line(a, b)
            if animate:
                line_anims.append(ln.animate.set_stroke(PATH_C, 7, 1.0))
            else:
                ln.set_stroke(PATH_C, 7, 1.0)
        for n in self.path[1:-1]:
            if animate:
                line_anims.append(
                    self.dots[n].animate.set_fill(PATH_C, 1.0).set_stroke(width=0)
                )
            else:
                self.dots[n].set_fill(PATH_C, 1.0).set_stroke(width=0)
        if animate:
            self.play(LaggedStart(*line_anims, lag_ratio=0.12), run_time=2.4)
            self.play(
                Flash(self.pos[self.goal], color=PATH_C, line_length=0.25), run_time=0.6
            )
        self.add(self.s_marker, self.g_marker)

    # ====================================================================== #
    # Scene 3 — explain g, h, f
    # ====================================================================== #
    def scene_explain(self):
        self._show_map_instant()
        if not getattr(self, "_searched", False):
            self._reveal_path(animate=False)
            self.add(self.s_marker, self.g_marker)

        # dim the map so the annotations read; retire the search panel (done its job)
        dim = VGroup(self.street_group, self.dot_group, self.landmarks)
        anims = [dim.animate.set_opacity(0.28)]
        if getattr(self, "panel", None) is not None and self.panel in self.mobjects:
            anims.append(FadeOut(self.panel))
        self.play(*anims, run_time=0.8)

        # pick an explored node off the straight line, so its real route bends
        n = self._pick_illustrative_node()
        route = self._route_to(n)
        node_dot = Dot(self.pos[n], radius=0.1).set_fill(INK, 1).set_stroke(BG, 2)
        node_lab = Text("n", font_size=22, color=INK, weight="BOLD").next_to(
            node_dot, UR, buff=0.08
        )

        # g(n): the winding route A* actually travelled to reach n (blue)
        g_line = VMobject().set_points_as_corners(
            [self.pos[k] for k in route]
        ).set_stroke(G_C, 7, 1.0)
        # h(n): the straight-line guess from n to the goal, dashed orange
        h_line = DashedLine(
            self.pos[n], self.pos[self.goal], dash_length=0.14
        ).set_stroke(HEUR_C, 6, 1.0)
        # on-map tags so the lines are self-labelling
        g_tag = Text("g(n)", font_size=19, color=G_C, weight="BOLD").move_to(
            g_line.point_from_proportion(0.55) + np.array([0.0, 0.28, 0.0])
        )
        h_tag = Text("h(n)", font_size=19, color=HEUR_C, weight="BOLD").move_to(
            (self.pos[n] + self.pos[self.goal]) / 2 + np.array([-0.1, -0.28, 0.0])
        )

        self.play(Create(g_line), run_time=1.2)
        self.play(FadeIn(node_dot, scale=0.5), FadeIn(node_lab), FadeIn(g_tag), run_time=0.5)
        self.play(Create(h_line), FadeIn(h_tag), run_time=1.0)
        self.beat(0.6)

        # text boxes: left h, right g, bottom f
        g_box = self._explain_box(
            "g(n)",
            "distance already\ntravelled",
            G_C,
        ).to_corner(UL, buff=0.4)
        h_box = self._explain_box(
            "h(n)",
            "straight-line guess\nto the goal",
            HEUR_C,
        ).to_corner(UR, buff=0.4)
        f_box = self._explain_box(
            "f(n) = g(n) + h(n)",
            "expand the most promising node first",
            F_C,
            wide=True,
        ).to_edge(DOWN, buff=0.5)

        self.play(FadeIn(g_box, shift=RIGHT * 0.2), run_time=0.6)
        self.beat(0.7)
        self.play(FadeIn(h_box, shift=LEFT * 0.2), run_time=0.6)
        self.beat(0.7)
        self.play(FadeIn(f_box, shift=UP * 0.2), run_time=0.7)
        self.beat(1.6)

        # tidy up: restore the map for the final scene
        self.play(
            FadeOut(
                VGroup(
                    g_box, h_box, f_box, g_line, h_line, g_tag, h_tag, node_dot, node_lab
                )
            ),
            run_time=0.7,
        )
        self.play(dim.animate.set_opacity(1.0), run_time=0.6)
        # the path was dimmed with the streets; relight it
        self._reveal_path(animate=False)
        self.add(self.s_marker, self.g_marker)

    def _explain_box(self, title, body, color, wide=False):
        t = Text(title, font_size=26, color=color, weight="BOLD")
        b = Text(body, font_size=20, color=INK, line_spacing=0.7)
        b.next_to(t, DOWN, buff=0.16)
        grp = VGroup(t, b)
        w = grp.width + (0.9 if wide else 0.6)
        box = RoundedRectangle(
            width=w, height=grp.height + 0.5, corner_radius=0.12
        ).set_fill(PANEL, 0.92).set_stroke(color, 2, 0.85)
        grp.move_to(box)
        return VGroup(box, grp)

    # ====================================================================== #
    # Scene 4 — drive the route
    # ====================================================================== #
    def scene_final(self):
        self._show_map_instant()
        if not getattr(self, "_searched", False):
            self._reveal_path(animate=False)
        # fade out the panel if it's around
        if getattr(self, "panel", None) is not None and self.panel in self.mobjects:
            self.play(FadeOut(self.panel), run_time=0.6)

        self.add(self.s_marker, self.g_marker)

        # dim the green path; the car will relight it as it drives (progress feel)
        for a, b in zip(self.path, self.path[1:]):
            self._line(a, b).set_stroke(PATH_C, 7, 0.32)

        route = VMobject().set_points_as_corners([self.pos[n] for n in self.path])
        car = VGroup(
            Dot(radius=0.13).set_fill(PATH_C, 1).set_stroke(INK, 1.5),
            Dot(radius=0.26).set_fill(PATH_C, 0.22).set_stroke(width=0),
        )
        car.move_to(self.pos[self.start])
        trail = TracedPath(
            car[0].get_center, stroke_color=PATH_C, stroke_width=7
        )
        self.add(trail, car)

        banner = Text(
            "A* finds the optimal route through NYC's grid!",
            font_size=28,
            color=INK,
            weight="BOLD",
        )
        banner.move_to([-2.05, 3.55, 0])
        self.play(
            FadeOut(self.map_title) if self.map_title in self.mobjects else Wait(0.01),
            run_time=0.3,
        )
        self.play(Write(banner), run_time=1.0)

        self.play(
            MoveAlongPath(car, route),
            run_time=1.0 if QUICK else 4.5,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.play(Flash(self.pos[self.goal], color=PATH_C, line_length=0.25), run_time=0.6)

        # final stat
        stat = Text(
            f"Route ≈ {self.path_miles:.1f} miles   ·   "
            f"{self.steps[-1]['n_closed']} nodes explored",
            font_size=22,
            color=MUTED,
        )
        stat.next_to(banner, DOWN, buff=0.25).align_to(banner, LEFT)
        self.play(FadeIn(stat, shift=UP * 0.1), run_time=0.8)
        self.beat(2.0)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_map_intro()
        self.scene_search()
        self.scene_explain()
        self.scene_final()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_AStarBase):
    def construct(self):
        self.play_intro()


class MapIntro(_AStarBase):
    def construct(self):
        self.scene_map_intro()


class Search(_AStarBase):
    def construct(self):
        self.scene_search()


class Explain(_AStarBase):
    def construct(self):
        self.scene_explain()


class FinalPath(_AStarBase):
    def construct(self):
        self.scene_final()


class Outro(_AStarBase):
    def construct(self):
        self.play_outro()


class AStarPathfinding(_AStarBase):
    """The whole ~2-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    AStarPathfinding().render()
