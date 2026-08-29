"""A* Pathfinding — 3D perspective city, multiple A→B examples.

A "not top-down", realistic-looking take on the A* explainer: a dense, irregular
street network with extruded low-rise buildings and a central Central Park gap,
viewed at a cinematic angle. A* is demonstrated on *several* start→goal pairs —
the first in detail (with the f = g + h teaching + explainer), the rest as quick
follow-ups, including one that must detour around the park.

Reuses the A* engine and palette from ``astar_pathfinding``; everything the
viewer reads (title, panel, captions, explainer boxes, cards) is a fixed-in-frame
HUD so it stays put while the city sits in 3D.

Scenes: ``Intro | MapIntro | Search | Explain | MoreExamples | FinalPath | Outro``
and the full film ``AStarCity``. Env knob ``ASTAR_QUICK=1`` collapses the holds.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
from manim import *

from astar_pathfinding import (
    ANIM_SLOW,
    BG,
    DELAY,
    EXPLORED,
    F_C,
    FRONTIER,
    G_C,
    GOAL_C,
    HEUR_C,
    INK,
    MUTED,
    PANEL,
    PATH_C,
    QUICK,
    SCENE_GAP,
    START_C,
    THETA,
    Text,  # crisp-Text wrapper (renders large, scales down)
    astar,
)

# ---- city parameters ------------------------------------------------------ #
NA, NB = 12, 22  # avenues, cross streets (denser network → more nodes)
AVE, ST = 1.35, 0.85  # block sizes (world units, pre-scale)
BLD_LO = "#2b3352"  # short building base colour
BLD_HI = "#4a5c93"  # tall building base colour (glassier / lighter)
BLD_EDGE = "#8290c0"
GROUND = "#0f131d"
STREET_C = "#556084"
BWAY_C = "#8f98c4"
PARK_FILL = "#1f5c37"
PARK_EDGE = "#2f8f4f"

# a central park left as a gap in the network — a real obstacle to route around
PARK_A = range(4, 7)
PARK_S = range(12, 16)
PARK_NODES = {(a, s) for a in PARK_A for s in PARK_S}

# A → B examples (grid coords). The first is the detailed/teaching one; it fans
# out ~68 nodes and rides Broadway. The second must detour around the park.
EXAMPLES = [
    ((10, 21), (0, 2), "Uptown → Wall Street"),
    ((1, 20), (10, 3), "across Central Park"),
    ((10, 19), (2, 16), "a short crosstown hop"),
    ((2, 2), (9, 20), "the length of the island"),
]


def _broadway_nodes():
    a, s = NA - 1, NB - 1
    seq = [(a, s)]
    while a - 1 >= 0 and s - 2 >= 0:
        a, s = a - 1, s - 2
        seq.append((a, s))
    return seq


def _rot(p, th=THETA):
    c, s = np.cos(th), np.sin(th)
    return np.array([c * p[0] - s * p[1], s * p[0] + c * p[1], p[2]])


def _lighten(c, t):
    return interpolate_color(ManimColor(c), WHITE, t)


def _darken(c, t):
    return interpolate_color(ManimColor(c), BLACK, t)


def build_city(seed=7):
    rng = np.random.default_rng(seed)
    raw = {}
    for a in range(NA):
        for s in range(NB):
            j = rng.uniform(-0.10, 0.10, 2)
            raw[(a, s)] = np.array([a * AVE + j[0], s * ST + j[1], 0.0])

    rot = {k: _rot(v) for k, v in raw.items()}
    xs = [p[0] for p in rot.values()]
    ys = [p[1] for p in rot.values()]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    sc = 10.0 / span
    pos = {
        k: np.array([(p[0] - cx) * sc, (p[1] - cy) * sc, 0.0]) for k, p in rot.items()
    }

    amin, amax = min(PARK_A), max(PARK_A)
    smin, smax = min(PARK_S), max(PARK_S)
    park_poly = [
        pos[(amin, smin)],
        pos[(amax, smin)],
        pos[(amax, smax)],
        pos[(amin, smax)],
    ]
    active = {k for k in raw if k not in PARK_NODES}

    edges = set()
    for a in range(NA):
        for s in range(NB):
            if (a, s) not in active:
                continue
            if (a + 1, s) in active:
                edges.add(frozenset([(a, s), (a + 1, s)]))
            if (a, s + 1) in active:
                edges.add(frozenset([(a, s), (a, s + 1)]))

    broadway = set()
    seq = _broadway_nodes()
    for u, v in zip(seq, seq[1:]):
        if u in active and v in active:
            edges.add(frozenset([u, v]))
            broadway.add(frozenset([u, v]))

    adj = defaultdict(list)
    for e in edges:
        u, v = tuple(e)
        w = float(np.linalg.norm(pos[u] - pos[v]))
        adj[u].append((v, w))
        adj[v].append((u, w))

    buildings = []
    for a in range(NA - 1):
        for s in range(NB - 1):
            quad = [(a, s), (a + 1, s), (a + 1, s + 1), (a, s + 1)]
            if any(q in PARK_NODES for q in quad):
                continue
            if not all(q in pos for q in quad):
                continue
            if rng.random() < 0.07:  # empty lot / plaza — irregularity
                continue
            center = np.mean([pos[q] for q in quad], axis=0)
            dx = float(np.linalg.norm(pos[(a + 1, s)] - pos[(a, s)])) * 0.60
            dy = float(np.linalg.norm(pos[(a, s + 1)] - pos[(a, s)])) * 0.60
            gx, gy = a / (NA - 2), s / (NB - 2)
            centr = max(0.0, 1 - 2 * max(abs(gx - 0.5), abs(gy - 0.5)))
            h = 0.10 + (0.12 + 0.88 * centr) * float(rng.uniform(0.3, 1.0)) * 0.5
            buildings.append((center, dx, dy, h))

    diag = float(np.linalg.norm(pos[(0, 0)] - pos[(NA - 1, NB - 1)]))
    miles_k = 6.0 / diag  # island diagonal ≈ 6 mi (consistent across examples)

    return dict(
        raw=raw,
        edges=edges,
        broadway=broadway,
        pos=pos,
        adj=adj,
        buildings=buildings,
        park_poly=park_poly,
        active=active,
        miles_k=miles_k,
    )


def _building(center, dx, dy, h):
    """A box from per-face-shaded polygons so it reads as solid in Cairo's unlit
    3D: bright roof, two lit sides, two in shadow."""
    base = interpolate_color(
        ManimColor(BLD_LO), ManimColor(BLD_HI), float(min(1.0, h / 1.1))
    )
    roof_c = _lighten(base, 0.30)
    sun_c = _lighten(base, 0.06)
    sha_c = _darken(base, 0.34)
    hx, hy = dx / 2, dy / 2
    corners = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    side_cols = [sha_c, sun_c, sun_c, sha_c]
    faces = VGroup()
    for i in range(4):
        x0, y0 = corners[i]
        x1, y1 = corners[(i + 1) % 4]
        quad = Polygon(
            np.array([x0, y0, 0.0]),
            np.array([x1, y1, 0.0]),
            np.array([x1, y1, h]),
            np.array([x0, y0, h]),
        )
        quad.set_fill(side_cols[i], 1.0).set_stroke(BLD_EDGE, 0.7, 0.5)
        faces.add(quad)
    roof = Polygon(*[np.array([x, y, h]) for x, y in corners])
    roof.set_fill(roof_c, 1.0).set_stroke(BLD_EDGE, 0.8, 0.65)
    faces.add(roof)
    faces.rotate(THETA, axis=OUT)
    faces.shift(np.array([center[0], center[1], 0.0]))
    return faces


def _pin(p, color, h=0.6):
    """A map-pin: a bright vertical stalk topped with a sphere."""
    stalk = Line(p, p + OUT * h).set_stroke(color, 4, 0.95)
    head = Dot3D(point=p + OUT * h, radius=0.14, color=color)
    return VGroup(stalk, head)


# camera
CAM_PHI = 58 * DEGREES
CAM_THETA = -52 * DEGREES
CAM_ZOOM = 1.05


# ========================================================================== #
# Base 3D scene
# ========================================================================== #
class _CityBase(ThreeDScene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None
        self.pins = None

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

    # ---- build the city + mobjects (no path/endpoints baked) -------------- #
    def _build(self):
        if getattr(self, "_built", False):
            return
        m = build_city()
        self.pos = m["pos"]
        self.edges = m["edges"]
        self.broadway = m["broadway"]
        self.adj = m["adj"]
        self.active = m["active"]
        self.miles_k = m["miles_k"]

        xs = [p[0] for p in self.pos.values()]
        ys = [p[1] for p in self.pos.values()]
        gw, gh = (max(xs) - min(xs)) + 1.6, (max(ys) - min(ys)) + 1.6
        self.ground = (
            Rectangle(width=gw, height=gh)
            .set_fill(GROUND, 1.0)
            .set_stroke("#1b2233", 1.0, 0.6)
            .move_to([0, 0, -0.02])
        )
        self.park = (
            Polygon(*[p + OUT * 0.01 for p in m["park_poly"]])
            .set_fill(PARK_FILL, 0.8)
            .set_stroke(PARK_EDGE, 1.5, 0.7)
        )

        self.lines = {}
        street_group = VGroup()
        for e in self.edges:
            u, v = tuple(e)
            ln = Line(self.pos[u] + OUT * 0.02, self.pos[v] + OUT * 0.02)
            ln.set_stroke(BWAY_C if e in self.broadway else STREET_C, 2.4, 0.9)
            self.lines[e] = ln
            street_group.add(ln)
        self.street_group = street_group

        self.dots = {}
        dot_group = VGroup()
        for k in self.active:
            d = Dot(point=self.pos[k] + OUT * 0.03, radius=0.05)
            d.set_fill(MUTED, 0.7).set_stroke(width=0)
            self.dots[k] = d
            dot_group.add(d)
        self.dot_group = dot_group

        self.buildings = VGroup(
            *[_building(c, dx, dy, h) for (c, dx, dy, h) in m["buildings"]]
        )
        self._built = True

    def _line(self, u, v):
        return self.lines[frozenset([u, v])]

    def _solve(self, s, g):
        return astar(self.adj, self.pos, s, g)

    def _route_to(self, came, n, start):
        route = [n]
        while route[-1] != start:
            route.append(came[route[-1]])
        route.reverse()
        return route

    def _pick_illustrative_node(self, came, s, g):
        sp, gp = self.pos[s], self.pos[g]
        d = gp - sp
        L = float(np.linalg.norm(d))
        dhat = d / L
        best, best_perp = None, -1.0
        for n in came:
            if not (4 <= len(self._route_to(came, n, s)) <= 8):
                continue
            v = self.pos[n] - sp
            along = float(np.dot(v, dhat))
            perp = float(np.linalg.norm(v - along * dhat))
            if 0.30 * L < along < 0.72 * L and perp > best_perp:
                best_perp, best = perp, n
        return best

    def _add_city(self):
        self._build()
        if getattr(self, "_city_on", False):
            return
        self.set_camera_orientation(phi=CAM_PHI, theta=CAM_THETA, zoom=CAM_ZOOM)
        self.add(self.ground, self.park, self.street_group, self.dot_group, self.buildings)
        self._city_on = True

    def _reset_network(self):
        for d in self.dots.values():
            d.set_fill(MUTED, 0.7)
        for e, ln in self.lines.items():
            ln.set_stroke(BWAY_C if e in self.broadway else STREET_C, 2.4, 0.9)

    def _make_pins(self, s, g):
        if self.pins is not None and self.pins in self.mobjects:
            self.remove(self.pins)
        self.pins = VGroup(_pin(self.pos[s], START_C), _pin(self.pos[g], GOAL_C))
        self.add(self.pins)
        self._cur_g = g

    # ---- fixed-frame HUD -------------------------------------------------- #
    def _hud_title(self, text="New York City Street Network"):
        return Text(text, font_size=32, color=INK, weight="BOLD").to_corner(UL, buff=0.4)

    def _show_caption(self, idx, name):
        line1 = Text(f"EXAMPLE {idx}", font_size=20, color=F_C, weight="BOLD")
        line2 = Text(name, font_size=28, color=INK, weight="BOLD")
        grp = VGroup(line1, line2).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        grp.to_corner(UL, buff=0.4)
        self.add_fixed_in_frame_mobjects(grp)
        self.remove(grp)
        # clear the previous caption instantly (it sits in the same spot, so a
        # cross-fade would overlap and garble the text)
        if self._cap is not None and self._cap in self.mobjects:
            self.remove(self._cap)
        anims = [FadeIn(grp)]
        if getattr(self, "map_title", None) is not None and self.map_title in self.mobjects:
            anims.append(FadeOut(self.map_title))
        self.play(*anims, run_time=0.5)
        self._cap = grp

    def _build_panel(self):
        # Build the content first, then size the box to WRAP it, so the legend
        # can never spill outside the panel again.
        W = 3.6
        xl, xr = -W / 2 + 0.28, W / 2 - 0.30

        head = Text("A*  SEARCH", font_size=23, color=INK, weight="BOLD")
        head.move_to([0, 0, 0])

        self.n_explored = Integer(0).set_color(EXPLORED).scale(0.6)
        self.n_frontier = Integer(0).set_color(FRONTIER).scale(0.6)
        self.cur_f = DecimalNumber(0, num_decimal_places=1).set_color(F_C).scale(0.6)

        def row(label, value, y):
            lab = Text(label, font_size=19, color=MUTED)
            lab.move_to([xl, y, 0], aligned_edge=LEFT)
            value.move_to([xr, y, 0], aligned_edge=RIGHT)
            return VGroup(lab, value)

        r1 = row("Nodes explored", self.n_explored, -0.62)
        r2 = row("Frontier size", self.n_frontier, -1.04)
        lab3 = Text("Current f(n)", font_size=19, color=MUTED)
        lab3.move_to([xl, -1.46, 0], aligned_edge=LEFT)
        f_unit = Text("mi", font_size=14, color=MUTED)
        fval = VGroup(self.cur_f, f_unit).arrange(RIGHT, buff=0.07, aligned_edge=DOWN)
        fval.move_to([xr, -1.46, 0], aligned_edge=RIGHT)
        r3 = VGroup(lab3, fval)

        sep = Line([xl - 0.02, -1.82, 0], [xr + 0.02, -1.82, 0]).set_stroke(
            MUTED, 1, 0.4
        )

        legend = VGroup()
        for color, txt in [
            (START_C, "Start"),
            (GOAL_C, "Goal"),
            (FRONTIER, "Frontier"),
            (EXPLORED, "Explored"),
            (PATH_C, "Best path"),
        ]:
            dot = Dot(radius=0.06).set_fill(color, 1).set_stroke(width=0)
            lab = Text(txt, font_size=17, color=INK)
            legend.add(VGroup(dot, lab.next_to(dot, RIGHT, buff=0.13)))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.11)
        legend.next_to(sep, DOWN, buff=0.16).align_to([xl, 0, 0], LEFT)

        content = VGroup(head, r1, r2, r3, sep, legend)
        box = (
            RoundedRectangle(width=W, height=content.height + 0.5, corner_radius=0.14)
            .set_fill(PANEL, 0.92)
            .set_stroke(MUTED, 1.5, 0.6)
        )
        box.move_to(content)
        self.panel = VGroup(box, content).to_corner(UR, buff=0.35)
        return self.panel

    def _ensure_panel(self):
        if getattr(self, "panel", None) is not None and self.panel in self.mobjects:
            return
        panel = self._build_panel()
        self.add_fixed_in_frame_mobjects(panel)
        self.remove(panel)
        self.play(FadeIn(panel), run_time=0.6)

    def _update_panel(self, step):
        self.n_explored.set_value(step["n_closed"])
        self.n_frontier.set_value(step["n_open"])
        self.cur_f.set_value(step["f"] * self.miles_k)
        # set_value rebuilds glyph submobjects (they drop fixed-in-frame status
        # and get projected into 3D). Re-register the whole panel — its family
        # covers the rebuilt glyphs and the VGroup stays intact for later fades.
        self.add_fixed_in_frame_mobjects(self.panel)

    # ---- the search animation (shared) ----------------------------------- #
    def _teach_readout(self, step):
        g = step["g"] * self.miles_k
        h = step["h"] * self.miles_k
        f = step["f"] * self.miles_k
        txt = Text(
            f"expanding a node:   f = g + h = {g:.1f} + {h:.1f} = {f:.1f} mi",
            font_size=24,
            color=INK,
        )
        box = (
            RoundedRectangle(
                width=txt.width + 0.5, height=txt.height + 0.34, corner_radius=0.12
            )
            .set_fill("#1b2233", 0.97)
            .set_stroke(F_C, 2.2, 1.0)
        )
        txt.move_to(box)
        grp = VGroup(box, txt).to_edge(DOWN, buff=0.6)
        self.add_fixed_in_frame_mobjects(grp)
        self.remove(grp)
        return grp

    def _animate_search(self, steps, teach=False):
        teach_n = 0 if (QUICK or not teach) else 5
        heur = None
        for i in range(min(teach_n, len(steps))):
            step = steps[i]
            u = step["node"]
            anims = [self.dots[u].animate.set_fill(EXPLORED, 0.95)] if u in self.dots else []
            for v, par in step["newf"]:
                anims.append(self._line(par, v).animate.set_stroke(EXPLORED, 3.2, 0.85))
                if v in self.dots:
                    anims.append(self.dots[v].animate.set_fill(FRONTIER, 1.0))
            glow = (
                Circle(radius=0.16)
                .set_stroke(FRONTIER, 4, 0.9)
                .move_to(self.pos[u] + OUT * 0.04)
            )
            self.play(FadeIn(glow, scale=1.6), *anims, run_time=0.5)
            self._update_panel(step)
            new_heur = Arrow(
                self.pos[u] + OUT * 0.05,
                self.pos[self._cur_g] + OUT * 0.05,
                buff=0.16,
                stroke_width=3,
                color=HEUR_C,
                max_tip_length_to_length_ratio=0.05,
            ).set_opacity(0.6)
            chip = self._teach_readout(step)
            if heur is None:
                self.play(GrowArrow(new_heur), FadeIn(chip), run_time=0.4)
                heur = new_heur
            else:
                self.play(Transform(heur, new_heur), FadeIn(chip), run_time=0.4)
            self.beat(0.5)
            self.play(FadeOut(glow), FadeOut(chip), run_time=0.3)
        if heur is not None:
            self.play(FadeOut(heur), run_time=0.4)

        i = teach_n
        batch = 1 if QUICK else (4 if teach else 6)
        while i < len(steps):
            for step in steps[i : i + batch]:
                u = step["node"]
                if u in self.dots:
                    self.dots[u].set_fill(EXPLORED, 0.9)
                for v, par in step["newf"]:
                    self._line(par, v).set_stroke(EXPLORED, 3.0, 0.8)
                    if v in self.dots:
                        self.dots[v].set_fill(FRONTIER, 1.0)
            self._update_panel(steps[min(i + batch, len(steps)) - 1])
            self.wait(0.05 if QUICK else (0.16 if teach else 0.10))
            i += batch

    def _reveal_path(self, path, animate=True):
        anims = []
        for a, b in zip(path, path[1:]):
            ln = self._line(a, b)
            if animate:
                anims.append(ln.animate.set_stroke(PATH_C, 6, 1.0))
            else:
                ln.set_stroke(PATH_C, 6, 1.0)
        for n in path[1:-1]:
            if n in self.dots:
                if animate:
                    anims.append(self.dots[n].animate.set_fill(PATH_C, 1.0))
                else:
                    self.dots[n].set_fill(PATH_C, 1.0)
        if animate and anims:
            self.play(LaggedStart(*anims, lag_ratio=0.08), run_time=2.0)

    # ---- intro / outro cards (fixed frame) -------------------------------- #
    def _card(self, title, sub, transform_to=None):
        header = Text(title, font_size=52, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=F_C)
        writer = Text("Created by Ptolémé", font_size=28, color=EXPLORED)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.add_fixed_in_frame_mobjects(header, line, writer)
        self.remove(header, line, writer)
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.8)
        if transform_to:
            s = Text(transform_to, font_size=34, color=MUTED).move_to(header)
            self.add_fixed_in_frame_mobjects(s)
            self.remove(s)
            self.play(Transform(header, s), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        return VGroup(header, line, writer)

    def play_intro(self):
        grp = self._card(
            "A* Pathfinding", None, transform_to="finding the shortest route across a city"
        )
        self.card_wait(2.0)
        self.play(FadeOut(grp), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        grp = self._card("Thank you for watching!", None)
        self.card_wait(2.2)
        self.play(FadeOut(grp), run_time=1.2)

    # ====================================================================== #
    # Scene 1 — establish the city
    # ====================================================================== #
    def scene_map_intro(self):
        self._build()
        self.set_camera_orientation(phi=42 * DEGREES, theta=-70 * DEGREES, zoom=0.92)
        self.add(self.ground, self.park)
        self.play(
            Create(self.street_group, lag_ratio=0.015),
            FadeIn(self.dot_group, lag_ratio=0.002),
            run_time=2.8,
        )
        self.play(FadeIn(self.buildings, lag_ratio=0.003), run_time=2.2)
        self.move_camera(phi=CAM_PHI, theta=CAM_THETA, zoom=CAM_ZOOM, run_time=2.6)
        self._city_on = True

        title = self._hud_title()
        self.add_fixed_in_frame_mobjects(title)
        self.remove(title)
        self.play(Write(title), run_time=1.2)
        self.map_title = title
        self.beat(1.0)

    # ====================================================================== #
    # Scene 2 — the detailed example (teaching)
    # ====================================================================== #
    def scene_search(self):
        self._add_city()
        self._ensure_panel()
        s, g, name = EXAMPLES[0]
        self._show_caption(1, name)
        self._make_pins(s, g)
        self.play(FadeIn(self.pins, shift=OUT * 0.5), run_time=0.6)
        self.beat(0.4)

        steps, path, cost, came = self._solve(s, g)
        self.ex0 = dict(steps=steps, path=path, cost=cost, came=came, s=s, g=g)
        self._animate_search(steps, teach=True)
        self.beat(0.4)
        self._reveal_path(path, animate=True)
        self.beat(0.9)
        self._searched = True

    # ====================================================================== #
    # Scene 3 — explain g, h, f (on the first example)
    # ====================================================================== #
    def scene_explain(self):
        self._add_city()
        if not getattr(self, "ex0", None):
            s, g, _ = EXAMPLES[0]
            steps, path, cost, came = self._solve(s, g)
            self.ex0 = dict(steps=steps, path=path, cost=cost, came=came, s=s, g=g)
            self._reveal_path(path, animate=False)
        ex = self.ex0

        dim = VGroup(self.buildings, self.dot_group, self.street_group)
        anims = [dim.animate.set_opacity(0.32)]
        for attr in ("panel", "_cap"):
            mob = getattr(self, attr, None)
            if mob is not None and mob in self.mobjects:
                anims.append(FadeOut(mob))
        self.play(*anims, run_time=0.8)

        n = self._pick_illustrative_node(ex["came"], ex["s"], ex["g"])
        if n is None:
            n = ex["path"][len(ex["path"]) // 2]
        route = self._route_to(ex["came"], n, ex["s"])
        node_dot = Dot3D(self.pos[n] + OUT * 0.05, radius=0.1, color=INK)
        g_line = (
            VMobject()
            .set_points_as_corners([self.pos[k] + OUT * 0.07 for k in route])
            .set_stroke(G_C, 7, 1.0)
        )
        h_line = DashedLine(
            self.pos[n] + OUT * 0.07, self.pos[ex["g"]] + OUT * 0.07, dash_length=0.14
        ).set_stroke(HEUR_C, 6, 1.0)

        self.play(Create(g_line), run_time=1.2)
        self.play(FadeIn(node_dot, scale=0.5), run_time=0.4)
        self.play(Create(h_line), run_time=1.0)
        self.beat(0.5)

        g_box = self._explain_box("g(n)", "distance already\ntravelled", G_C).to_corner(
            UL, buff=0.4
        )
        h_box = self._explain_box(
            "h(n)", "straight-line guess\nto the goal", HEUR_C
        ).to_corner(UR, buff=0.4)
        f_box = self._explain_box(
            "f(n) = g(n) + h(n)", "expand the most promising node first", F_C, wide=True
        ).to_edge(DOWN, buff=0.5)
        for b in (g_box, h_box, f_box):
            self.add_fixed_in_frame_mobjects(b)
            self.remove(b)
        self.play(FadeIn(g_box), run_time=0.6)
        self.beat(0.6)
        self.play(FadeIn(h_box), run_time=0.6)
        self.beat(0.6)
        self.play(FadeIn(f_box), run_time=0.7)
        self.beat(1.5)

        self.play(
            FadeOut(VGroup(g_box, h_box, f_box)),
            FadeOut(VGroup(g_line, h_line, node_dot)),
            run_time=0.7,
        )
        self.play(dim.animate.set_opacity(1.0), run_time=0.6)
        self._reveal_path(ex["path"], animate=False)

    def _explain_box(self, title, body, color, wide=False):
        t = Text(title, font_size=26, color=color, weight="BOLD")
        b = Text(body, font_size=20, color=INK, line_spacing=0.7)
        b.next_to(t, DOWN, buff=0.16)
        grp = VGroup(t, b)
        w = grp.width + (0.9 if wide else 0.6)
        box = (
            RoundedRectangle(width=w, height=grp.height + 0.5, corner_radius=0.12)
            .set_fill(PANEL, 0.94)
            .set_stroke(color, 2, 0.85)
        )
        grp.move_to(box)
        return VGroup(box, grp)

    # ====================================================================== #
    # Scene 4 — more A → B examples
    # ====================================================================== #
    def scene_more_examples(self):
        self._add_city()
        self._ensure_panel()
        if getattr(self, "_cap", None) is None:
            self._show_caption(1, EXAMPLES[0][2])  # standalone: give a baseline
        for idx, (s, g, name) in enumerate(EXAMPLES[1:], start=2):
            self._reset_network()
            self._make_pins(s, g)
            self._show_caption(idx, name)
            self.play(FadeIn(self.pins, shift=OUT * 0.5), run_time=0.4)
            steps, path, cost, came = self._solve(s, g)
            self._animate_search(steps, teach=False)
            self.beat(0.3)
            self._reveal_path(path, animate=True)
            self.beat(1.1)

    # ====================================================================== #
    # Scene 5 — drive the (first) route
    # ====================================================================== #
    def scene_final(self):
        self._add_city()
        s, g, name = EXAMPLES[0]
        if not getattr(self, "ex0", None):
            steps, path, cost, came = self._solve(s, g)
            self.ex0 = dict(steps=steps, path=path, cost=cost, came=came, s=s, g=g)
        ex = self.ex0
        self._reset_network()
        self._make_pins(s, g)
        self._reveal_path(ex["path"], animate=False)

        for attr in ("panel", "_cap", "map_title"):
            mob = getattr(self, attr, None)
            if mob is not None and mob in self.mobjects:
                self.play(FadeOut(mob), run_time=0.4)

        for a, b in zip(ex["path"], ex["path"][1:]):
            self._line(a, b).set_stroke(PATH_C, 6, 0.3)

        route = VMobject().set_points_as_corners(
            [self.pos[n] + OUT * 0.1 for n in ex["path"]]
        )
        car = VGroup(
            Dot3D(ORIGIN, radius=0.14, color=PATH_C),
            Sphere(radius=0.26, resolution=(8, 8)).set_color(PATH_C).set_opacity(0.18),
        )
        car.move_to(self.pos[s] + OUT * 0.1)
        trail = TracedPath(lambda: car[0].get_center(), stroke_color=PATH_C, stroke_width=6)
        self.add(trail, car)

        banner = Text(
            "A* finds the optimal route through the grid!",
            font_size=30,
            color=INK,
            weight="BOLD",
        ).to_corner(UL, buff=0.4)
        stat = Text(
            f"Route ≈ {ex['cost'] * self.miles_k:.1f} miles   ·   "
            f"{ex['steps'][-1]['n_closed']} nodes explored",
            font_size=22,
            color=MUTED,
        ).next_to(banner, DOWN, buff=0.22).align_to(banner, LEFT)
        self.add_fixed_in_frame_mobjects(banner, stat)
        self.remove(banner, stat)

        self.play(Write(banner), run_time=1.0)
        self.play(
            MoveAlongPath(car, route),
            run_time=1.0 if QUICK else 4.5,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.play(FadeIn(stat, shift=UP * 0.1), run_time=0.8)
        self.beat(2.0)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_map_intro()
        self.scene_search()
        self.scene_explain()
        self.scene_more_examples()
        self.scene_final()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_CityBase):
    def construct(self):
        self.play_intro()


class MapIntro(_CityBase):
    def construct(self):
        self.scene_map_intro()


class Search(_CityBase):
    def construct(self):
        self.scene_search()


class Explain(_CityBase):
    def construct(self):
        self.scene_explain()


class MoreExamples(_CityBase):
    def construct(self):
        self.scene_more_examples()


class FinalPath(_CityBase):
    def construct(self):
        self.scene_final()


class Outro(_CityBase):
    def construct(self):
        self.play_outro()


class AStarCity(_CityBase):
    """The whole film in 3D, intro card to outro card, several A→B examples."""

    def construct(self):
        self.play_all()


# ---- quick static look-test ---------------------------------------------- #
class CityStill(ThreeDScene):
    def construct(self):
        self.camera.background_color = BG
        m = build_city()
        pos = m["pos"]
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        ground = (
            Rectangle(width=(max(xs) - min(xs)) + 1.6, height=(max(ys) - min(ys)) + 1.6)
            .set_fill(GROUND, 1.0)
            .set_stroke("#1b2233", 1.0, 0.6)
            .move_to([0, 0, -0.02])
        )
        park = (
            Polygon(*[p + OUT * 0.01 for p in m["park_poly"]])
            .set_fill(PARK_FILL, 0.8)
            .set_stroke(PARK_EDGE, 1.5, 0.7)
        )
        streets = VGroup()
        for e in m["edges"]:
            u, v = tuple(e)
            ln = Line(pos[u] + OUT * 0.02, pos[v] + OUT * 0.02)
            ln.set_stroke(BWAY_C if e in m["broadway"] else STREET_C, 2.4, 0.9)
            streets.add(ln)
        blds = VGroup(*[_building(c, dx, dy, h) for (c, dx, dy, h) in m["buildings"]])
        s, g, _ = EXAMPLES[0]
        steps, path, cost, came = astar(m["adj"], pos, s, g)
        ribbon = VGroup(
            *[
                Line(pos[a] + OUT * 0.12, pos[b] + OUT * 0.12).set_stroke(PATH_C, 7, 1)
                for a, b in zip(path, path[1:])
            ]
        )
        self.add(ground, park, streets, blds, ribbon)
        self.add(_pin(pos[s], START_C), _pin(pos[g], GOAL_C))
        self.set_camera_orientation(phi=CAM_PHI, theta=CAM_THETA, zoom=CAM_ZOOM)
        self.wait(0.1)
