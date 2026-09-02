"""
LangGraph: Orchestrating a Team of Agents  (no-voiceover explainer)

Scenes
------
Intro     - house title card
Problem   - one overloaded do-everything agent -> need specialists + a coordinator
Graph     - the LangGraph identity: State, nodes, edges, a conditional edge, a cycle
Team      - the supervisor pattern: route to Researcher / Analyst / Writer, loop
            until done, shared State visibly grows  (the heart of the film)
Parallel  - Send() fan-out: workers run at the same time, then reduce + synthesize
Takeaway  - one-line recap card
Outro     - house thank-you card

LangGraphFilm runs all of them end to end.

Real, current LangGraph on screen: StateGraph / MessagesState, add_conditional_edges,
Command(goto=..., update=...), Send, and ChatAnthropic(model="claude-opus-4-8").
"""

import os

import numpy as np
from manim import *

# --------------------------------------------------------------------------- #
# Fonts + crisp text                                                          #
# --------------------------------------------------------------------------- #
FONT = "Helvetica Neue"
MONO = "Menlo"
try:
    Text.set_default(font=FONT)
except Exception:
    pass

# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Render every glyph at
# a large base size and scale the mobject *down*. Shadows manim's ``Text`` so every
# call benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


# --------------------------------------------------------------------------- #
# Palette (house core + Transformer-series accents + agent roles)             #
# --------------------------------------------------------------------------- #
BG = "#0E1117"       # dark slate background
INK = "#F5F3EF"      # warm white text
MUTED = "#8A93A6"    # secondary text / inert edges
FAINT = "#3A4152"    # gridlines / panel strokes
GOLD = "#FFD166"     # accent / the coordinator
GOOD = "#3DD68C"     # pass / START
BAD = "#FF5C5C"      # danger / stress
ACCENT = GOLD

# agent / node roles
SUPER = "#FFD166"        # supervisor  (gold)
RESEARCH = "#5B8DEF"     # researcher  (blue)
ANALYST = "#2EC4B6"      # analyst     (teal)
WRITER = "#C792EA"       # writer      (violet)
USERC = "#5B8DEF"        # the human   (blue)
TOOLC = "#2EC4B6"        # a tool call (teal)

# code panel
CODE_FS = 20
PLAIN = INK
COMMENT = MUTED
CODE_BG = "#0A0E15"
BAR_BG = "#141C29"

LG_T2C = {
    "StateGraph": RESEARCH, "MessagesState": RESEARCH,
    "START": GOOD, "END": BAD,
    "Command": GOLD, "Send": GOLD,
    "add_node": MUTED, "add_edge": MUTED, "add_conditional_edges": GOLD,
    "compile": RESEARCH, "invoke": RESEARCH, "ChatAnthropic": WRITER,
    "goto": GOLD, "update": ANALYST,
    '"agent"': GOLD, '"tools"': TOOLC, '"supervisor"': GOLD, '"worker"': RESEARCH,
    "def": WRITER, "return": WRITER, "for": WRITER, "import": MUTED, "from": MUTED,
    "claude-opus-4-8": GOOD,
}


# --------------------------------------------------------------------------- #
# Text helpers                                                                #
# --------------------------------------------------------------------------- #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    kw.update(extra)
    return Text(text, **kw)


def mono(text, fs=22, color=INK, **kw):
    return txt(text, fs=fs, color=color, font=MONO, **kw)


def _safe_t2c(s, table):
    """Per-line text->colour map, pruned so no key overlaps another present key."""
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


def P(x, y):
    return np.array([x, y, 0.0])


# --------------------------------------------------------------------------- #
# Glyphs                                                                       #
# --------------------------------------------------------------------------- #
def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, weight="NORMAL", radius=0.12):
    label = txt(text, fs=fs, color=INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    g.label = label
    return g


def pill(text, color, fs=22, fill=0.18, weight="BOLD"):
    t = txt(text, fs=fs, color=INK, weight=weight)
    box = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.3,
                           corner_radius=0.16, stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    box.move_to(t)
    g = VGroup(box, t)
    g.box = box
    return g


def arr(a, b, color=MUTED, sw=4, buff=0.12, tip=0.2):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.4, tip_length=tip)


def agent_node(label, color, w=2.4, h=1.05, sub=None):
    """A titled rounded box with a little hex 'agent' glyph. .body is the box."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.15,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=0.10)
    hexd = RegularPolygon(n=6, start_angle=PI / 6, radius=0.16,
                          stroke_color=color, stroke_width=2.5,
                          fill_color=color, fill_opacity=0.5)
    name = txt(label, fs=22, color=INK, weight="BOLD")
    row = VGroup(hexd, name).arrange(RIGHT, buff=0.16)
    if row.width > w - 0.3:
        row.scale((w - 0.3) / row.width)
    parts = VGroup(box, row)
    if sub:
        s = txt(sub, fs=15, color=color)
        if s.width > w - 0.3:
            s.scale((w - 0.3) / s.width)
        row.shift(UP * 0.16)
        s.move_to(box).shift(DOWN * 0.28)
        parts.add(s)
    row.move_to(box) if not sub else row.move_to([box.get_center()[0], box.get_center()[1] + 0.16, 0])
    parts.body = box
    parts.name = name
    parts.color = color
    return parts


def diamond(label="route", color=GOLD, r=0.62):
    d = RegularPolygon(n=4, radius=r, stroke_color=color, stroke_width=3,
                       fill_color=color, fill_opacity=0.12)
    t = txt(label, fs=16, color=color, weight="BOLD").move_to(d)
    if t.width > 2 * r * 0.72:
        t.scale((2 * r * 0.72) / t.width)
    g = VGroup(d, t)
    g.body = d
    return g


def state_chip(text, color, w=2.55):
    body = txt(text, fs=16, color=INK)
    if body.width > w - 0.42:
        body.scale((w - 0.42) / body.width)
    box = RoundedRectangle(width=w, height=0.5, corner_radius=0.1,
                           stroke_color=color, stroke_width=2,
                           fill_color=color, fill_opacity=0.15)
    dot = Dot(radius=0.05, color=color).move_to(box.get_left() + RIGHT * 0.2)
    body.move_to(box).shift(RIGHT * 0.12)
    return VGroup(box, dot, body)


def token(color=GOLD, r=0.14):
    d = Dot(radius=r, color=color)
    d.set_z_index(8)
    return d


# --------------------------------------------------------------------------- #
# Base scene                                                                   #
# --------------------------------------------------------------------------- #
QUICK = os.environ.get("LG_QUICK") == "1"
DELAY = float(os.environ.get("LG_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("LG_READ", 0.35 if QUICK else 2.4))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.0


class _LGBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None

    # ---- timing ----------------------------------------------------------- #
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

    # ---- chrome ----------------------------------------------------------- #
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

    # ---- Menlo code panel ------------------------------------------------- #
    def code_panel(self, spec, title="agent.py", fs=CODE_FS, t2c=None,
                   indent_unit=0.5, line_buff=0.18, target_h=5.2, target_w=8.2):
        table = LG_T2C if t2c is None else t2c
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.28, fill_opacity=0, stroke_opacity=0)
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
                              fill_color=CODE_BG, fill_opacity=1.0)
        bg.move_to(code)
        bar = RoundedRectangle(width=bg.width, height=0.5, corner_radius=0.16,
                               stroke_width=0, fill_color=BAR_BG, fill_opacity=1.0)
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

    def hl_line(self, panel, line, color=ACCENT, opacity=0.18, pad=0.06, xpad=0.34):
        rect = RoundedRectangle(width=panel[0].width - xpad,
                                height=line.height + 2 * pad,
                                corner_radius=0.08, stroke_width=0,
                                fill_color=color, fill_opacity=opacity)
        rect.move_to([panel[0].get_center()[0], line.get_center()[1], 0])
        return rect

    # ---- house intro / outro --------------------------------------------- #
    def _rule_under(self, header, color=GOLD, pad=1.0, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = txt("LangGraph", fs=64, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=RESEARCH)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = txt("Orchestrating a team of agents", fs=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = txt("nodes, edges, shared state, and a router", fs=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.3)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = txt("Thank you for watching!", fs=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=RESEARCH)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = txt("A graph, a router, and shared state.", fs=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap, shift=UP * 0.1), run_time=0.8)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ---- edge / token travel --------------------------------------------- #
    def travel(self, tok, target, color, edge=None, rt=0.9, arc=None):
        tok.set_color(color)
        anims = []
        if arc is not None:
            anims.append(MoveAlongPath(tok, arc))
        else:
            anims.append(tok.animate.move_to(target))
        if edge is not None:
            anims.append(edge.animate.set_stroke(color=color, width=6))
        self.play(*anims, run_time=rt, rate_func=rate_functions.ease_in_out_sine)
        if edge is not None:
            self.play(edge.animate.set_stroke(color=MUTED, width=4), run_time=0.3)


# --------------------------------------------------------------------------- #
# Scene 1 - The problem                                                        #
# --------------------------------------------------------------------------- #
class Problem(_LGBase):
    def construct(self):
        self.build_problem()

    def build_problem(self):
        hdr = self.section_header("01", "One agent, every job")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.7)

        task = chip("\"Research the market, crunch the numbers, write the brief.\"",
                    USERC, fs=21, w=9.2, h=0.72)
        task.move_to([0, 2.35, 0])
        self.play(FadeIn(task, shift=DOWN * 0.2), run_time=0.8)
        self.beat(1.2)

        solo = agent_node("Agent", GOLD, w=2.8, h=1.25, sub="does everything")
        solo.move_to([0, -0.5, 0])
        self.play(FadeIn(solo, scale=0.9), run_time=0.7)
        self.set_cap("One agent wired to every tool.", color=MUTED)
        self.beat(0.8)

        # a ring of tools all hanging off the one agent
        names = ["web search", "database", "calculator", "code run", "docs", "email"]
        cols = [RESEARCH, ANALYST, GOLD, WRITER, GOOD, "#E5884A"]
        ring = VGroup()
        edges = VGroup()
        R = 2.7
        for i, (nm, c) in enumerate(zip(names, cols)):
            ang = PI / 2 - i * (TAU / len(names))
            pos = P(R * 1.4 * np.cos(ang), -0.5 + R * np.sin(ang) * 0.62)
            t = chip(nm, c, fs=17, h=0.5)
            t.move_to(pos)
            e = arr(solo.get_center(), pos, color=c, sw=2.5, buff=0.7)
            ring.add(t)
            edges.add(e)
        self.play(LaggedStart(*[GrowArrow(e) for e in edges], lag_ratio=0.08, run_time=1.1),
                  LaggedStart(*[FadeIn(t, scale=0.8) for t in ring], lag_ratio=0.08, run_time=1.1))
        self.read(1.0)

        self.set_cap("Every job in one context: it bloats, and focus blurs.", color=BAD)
        self.play(Indicate(solo, color=BAD, scale_factor=1.12), run_time=0.8)
        self.flash_red(0.16)
        self.beat(1.2)

        # collapse to the idea: split the work, add a coordinator
        self.play(FadeOut(ring), FadeOut(edges), run_time=0.6)
        idea = txt("Split the work. One job each. Add a coordinator.",
                   fs=30, color=INK, weight="BOLD")
        idea.move_to([0, -0.1, 0])
        self.play(ReplacementTransform(solo, idea), run_time=0.9)
        self.set_cap("That is what LangGraph is for.", color=GOLD)
        self.read(1.4)

        self.settle()
        self.wipe()


# --------------------------------------------------------------------------- #
# Scene 2 - The graph, from first principles                                   #
# --------------------------------------------------------------------------- #
class Graph(_LGBase):
    def construct(self):
        self.build_graph()

    def build_graph(self):
        hdr = self.section_header("02", "The graph")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.7)

        spec = [
            (0, "from langgraph.graph import StateGraph, START, END"),
            (0, ""),
            (0, "g = StateGraph(MessagesState)   # shared state"),
            (0, 'g.add_node("agent", agent)      # a node'),
            (0, 'g.add_node("tools", tools)'),
            (0, 'g.add_edge(START, "agent")      # an edge'),
            (0, 'g.add_conditional_edges("agent", route)'),
            (0, 'g.add_edge("tools", "agent")    # a cycle'),
            (0, "app = g.compile()"),
        ]
        panel, lines = self.code_panel(spec, title="graph.py", target_h=4.6, target_w=6.0)
        panel.move_to([-3.1, -0.2, 0])
        self.play(FadeIn(panel, shift=RIGHT * 0.2), run_time=0.9)
        self.beat(0.8)

        # graph diagram on the right, built line by line
        # vertical spine: START -> agent -> route -> tools, END branches left,
        # the cycle loops up the right side (clean gentle C).
        start = pill("START", GOOD, fs=18).move_to([4.3, 2.35, 0])
        agent = agent_node("agent", GOLD, w=1.95, h=0.85).move_to([4.3, 1.05, 0])
        route = diamond("route", GOLD, r=0.55).move_to([4.3, -0.35, 0])
        tools = agent_node("tools", TOOLC, w=1.85, h=0.8).move_to([4.3, -1.65, 0])
        endp = pill("END", BAD, fs=18).move_to([2.05, -0.35, 0])

        e_sa = arr(start.get_bottom(), agent.body.get_top(), sw=3.5)
        e_ar = arr(agent.body.get_bottom(), route.body.get_top(), sw=3.5)
        e_rt = arr(route.body.get_bottom(), tools.body.get_top(), color=GOLD, sw=3.5)
        e_re = arr(route.body.get_left(), endp.get_right(), color=GOLD, sw=3.5)
        # the cycle as a clean orthogonal elbow up the right side (a CurvedArrow here
        # bows/hooks awkwardly — a routed right-angle edge reads unambiguously).
        _xr = 6.05
        _ty = tools.body.get_right()[1]
        _ay = agent.body.get_right()[1]
        cyc = VGroup(
            Line(tools.body.get_right(), [_xr, _ty, 0], color=TOOLC, stroke_width=3.5),
            Line([_xr, _ty, 0], [_xr, _ay, 0], color=TOOLC, stroke_width=3.5),
            arr([_xr, _ay, 0], agent.body.get_right(), color=TOOLC, sw=3.5, buff=0.05, tip=0.22),
        )

        def light(idx):
            box = self.hl_line(panel, lines[idx])
            self.add(box)
            return box

        # StateGraph(MessagesState) -> a State badge
        b = light(2)
        state_badge = chip("State = messages[]", GOLD, fs=17, h=0.52)
        state_badge.move_to([4.3, 3.2, 0])
        self.play(FadeIn(state_badge, shift=DOWN * 0.15), run_time=0.7)
        self.set_cap("State is a shared object every node reads and writes.", color=GOLD)
        self.read(0.9)
        self.remove(b)

        # nodes
        b = light(3)
        self.play(FadeIn(agent, scale=0.9), run_time=0.6)
        self.remove(b)
        b = light(4)
        self.play(FadeIn(tools, scale=0.9), run_time=0.6)
        self.set_cap("Nodes are the units of work: agents or tools.", color=INK)
        self.remove(b)
        self.beat(0.7)

        # edges
        b = light(5)
        self.play(FadeIn(start, shift=DOWN * 0.1), GrowArrow(e_sa), run_time=0.7)
        self.set_cap("Edges are the control flow between nodes.", color=INK)
        self.remove(b)
        self.beat(0.6)

        # conditional edge -> router diamond, fan to tools + END
        b = light(6)
        self.play(GrowArrow(e_ar), FadeIn(route, scale=0.8), run_time=0.7)
        self.play(GrowArrow(e_rt), GrowArrow(e_re), FadeIn(endp), run_time=0.7)
        self.set_cap("A conditional edge is a router: it picks the next node.", color=GOLD)
        self.read(1.0)
        self.remove(b)

        # cycle
        b = light(7)
        self.play(Create(cyc), run_time=0.8)
        self.play(Indicate(cyc, color=TOOLC, scale_factor=1.05), run_time=0.7)
        self.set_cap("And edges can loop. A cycle is what makes it an agent.", color=TOOLC)
        self.read(1.1)
        self.remove(b)

        # compile
        b = light(8)
        graph_grp = VGroup(start, agent, route, tools, endp, e_sa, e_ar, e_rt, e_re, cyc,
                           state_badge)
        self.play(Flash(agent.body, color=GOLD, line_length=0.2, num_lines=12),
                  graph_grp.animate.set_stroke(opacity=1.0), run_time=0.8)
        self.set_cap("compile() turns it into a runnable graph.", color=INK)
        self.read(1.0)
        self.remove(b)

        self.settle()
        self.wipe()


# --------------------------------------------------------------------------- #
# Scene 3 - The supervisor team + a live run  (the heart)                      #
# --------------------------------------------------------------------------- #
class Team(_LGBase):
    def construct(self):
        self.build_team()

    def build_team(self):
        hdr = self.section_header("03", "The supervisor")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.7)

        # ---- phase A: the code ------------------------------------------- #
        spec = [
            (0, "from langgraph.types import Command"),
            (0, 'model = ChatAnthropic(model="claude-opus-4-8")'),
            (0, ""),
            (0, "def supervisor(state) -> Command:"),
            (1, "# ask the model who should act next"),
            (1, "nxt = decide(state[\"messages\"])"),
            (1, "return Command(goto=nxt)     # route, or END"),
            (0, ""),
            (0, "def researcher(state) -> Command:"),
            (1, "out = research_agent.invoke(state)"),
            (1, 'return Command(goto="supervisor",'),
            (2, "        update={\"messages\": out})"),
        ]
        panel, lines = self.code_panel(spec, title="supervisor.py", target_h=5.0, target_w=9.2)
        panel.move_to([0, -0.15, 0])
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.9)
        self.set_cap("A supervisor node decides who acts next.", color=GOLD)
        self.read(0.8)

        b = self.hl_line(panel, lines[6], color=GOLD)
        self.add(b)
        self.beat(1.0)
        self.play(FadeOut(b), run_time=0.2)
        b = self.hl_line(panel, lines[10], color=ANALYST)
        b2 = self.hl_line(panel, lines[11], color=ANALYST)
        self.add(b, b2)
        self.set_cap("Each worker hands control back and writes to shared state.",
                     color=ANALYST)
        self.read(1.2)
        self.play(FadeOut(b), FadeOut(b2), FadeOut(panel), run_time=0.6)
        self.clear_cap()

        # ---- phase B: the live run --------------------------------------- #
        # state panel (left)
        px, ptop, pw = -5.15, 2.55, 2.95
        pbox = RoundedRectangle(width=pw, height=5.1, corner_radius=0.16,
                                stroke_color=FAINT, stroke_width=2,
                                fill_color=CODE_BG, fill_opacity=1.0)
        pbox.move_to([px, -0.2, 0])
        pttl = VGroup(txt("State", fs=20, color=GOLD, weight="BOLD"),
                      mono("messages[]", fs=15, color=MUTED)).arrange(RIGHT, buff=0.16)
        pttl.move_to([px, ptop, 0])
        self.play(FadeIn(pbox), FadeIn(pttl), run_time=0.6)

        # graph (right)
        start = pill("START", GOOD, fs=17).move_to([-2.45, 2.45, 0])
        supr = agent_node("Supervisor", GOLD, w=2.6, h=1.15, sub="router").move_to([-0.15, 0.7, 0])
        res = agent_node("Researcher", RESEARCH, w=2.35, h=1.0).move_to([4.35, 2.45, 0])
        ana = agent_node("Analyst", ANALYST, w=2.35, h=1.0).move_to([4.35, 0.4, 0])
        wri = agent_node("Writer", WRITER, w=2.35, h=1.0).move_to([4.35, -1.65, 0])
        endp = pill("END", BAD, fs=17).move_to([-0.15, -2.5, 0])

        sr = supr.body.get_right()
        e_st = arr(start.get_bottom(), supr.body.get_left() + UP * 0.15, sw=3.2)
        e_re = arr(sr + UP * 0.28, res.body.get_left(), color=MUTED, sw=3.2)
        e_an = arr(sr + UP * 0.0, ana.body.get_left(), color=MUTED, sw=3.2)
        e_wr = arr(sr + DOWN * 0.28, wri.body.get_left(), color=MUTED, sw=3.2)
        e_en = arr(supr.body.get_bottom(), endp.get_top(), color=GOLD, sw=3.2)
        route_tag = txt("route()", fs=15, color=GOLD).next_to(e_an, UP, buff=0.06).shift(RIGHT * 0.1)

        self.play(FadeIn(start), FadeIn(supr, scale=0.9), GrowArrow(e_st), run_time=0.8)
        self.play(LaggedStart(FadeIn(res, scale=0.9), FadeIn(ana, scale=0.9),
                              FadeIn(wri, scale=0.9), lag_ratio=0.2, run_time=1.0),
                  LaggedStart(GrowArrow(e_re), GrowArrow(e_an), GrowArrow(e_wr),
                              lag_ratio=0.2, run_time=1.0))
        self.play(FadeIn(route_tag), GrowArrow(e_en), FadeIn(endp), run_time=0.7)
        self.set_cap("One coordinator. Three specialists. One shared state.", color=INK)
        self.read(1.1)

        # state chips accumulate
        chips = []

        def add_state(text, color):
            c = state_chip(text, color)
            y = 1.95 - len(chips) * 0.62
            c.move_to([px, y, 0])
            chips.append(c)
            self.play(FadeIn(c, shift=UP * 0.12), run_time=0.5)
            return c

        tok = token(USERC).move_to(start.get_center())
        self.add(tok)
        add_state("Human: the task", USERC)
        self.set_cap("The task lands in state and goes to the supervisor.", color=USERC)
        self.travel(tok, supr.body.get_center(), GOLD, edge=e_st, rt=0.8)
        self.play(Indicate(supr, color=GOLD, scale_factor=1.08), run_time=0.6)
        self.beat(0.5)

        def visit(node, edge, color, produced, ret_angle):
            self.set_cap(f"Supervisor routes to the {node.name.text.lower()}.", color=color)
            self.travel(tok, node.body.get_left() + RIGHT * 0.35, color, edge=edge, rt=0.85)
            self.play(Indicate(node, color=color, scale_factor=1.08), run_time=0.6)
            add_state(produced, color)
            back = ArcBetweenPoints(node.body.get_bottom(),
                                    supr.body.get_right() + DOWN * 0.1,
                                    angle=ret_angle)
            self.set_cap("Then hands control back to the supervisor.", color=MUTED)
            self.travel(tok, None, color, arc=back, rt=0.85)
            self.play(Indicate(supr, color=GOLD, scale_factor=1.05), run_time=0.5)

        visit(res, e_re, RESEARCH, "search results", -1.1)
        visit(ana, e_an, ANALYST, "the analysis", -0.9)
        visit(wri, e_wr, WRITER, "the draft answer", 1.0)

        # supervisor decides it is done -> END
        self.set_cap("Nothing left to do. The supervisor routes to END.", color=GOLD)
        self.travel(tok, endp.get_center(), GOLD, edge=e_en, rt=0.8)
        self.play(Indicate(endp, color=GOOD, scale_factor=1.15), run_time=0.6)
        self.flash_good(0.12)
        self.play(FadeOut(tok), run_time=0.3)
        self.set_cap("A team, coordinated by a graph.", color=GOLD)
        self.read(1.3)

        self.settle()
        self.wipe()


# --------------------------------------------------------------------------- #
# Scene 4 - Parallel fan-out (Send)                                            #
# --------------------------------------------------------------------------- #
class Parallel(_LGBase):
    def construct(self):
        self.build_parallel()

    def build_parallel(self):
        hdr = self.section_header("04", "In parallel")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.7)

        spec = [
            (0, "from langgraph.types import Send"),
            (0, ""),
            (0, "def dispatch(state):"),
            (1, "# one worker per subtopic, all at once"),
            (1, 'return [Send("worker", {"topic": t})'),
            (2, "        for t in state[\"subtopics\"]]"),
        ]
        panel, lines = self.code_panel(spec, title="fanout.py", target_h=2.4, target_w=8.6)
        panel.move_to([0, 0.85, 0])
        self.play(FadeIn(panel, shift=DOWN * 0.15), run_time=0.8)
        self.set_cap("Send() launches a copy of a node for each item, at once.", color=GOLD)
        self.read(1.0)
        self.play(panel.animate.scale(0.62).to_corner(UR, buff=0.3), run_time=0.7)

        # planner sits left and the workers drop lower so the fan-out arrows stay
        # clear of the tucked fanout.py panel in the top-right corner.
        planner = agent_node("Planner", GOLD, w=2.2, h=0.95).move_to([-4.2, 2.05, 0])
        topics = ["pricing", "demand", "rivals", "risks"]
        wx = [-4.9, -2.35, 0.2, 2.75]
        workers = VGroup()
        for nm, x in zip(topics, wx):
            workers.add(agent_node(nm, RESEARCH, w=1.85, h=0.85).move_to([x, -0.7, 0]))
        synth = agent_node("Synthesize", WRITER, w=2.6, h=0.95).move_to([-1.05, -2.4, 0])

        fan = VGroup(*[arr(planner.body.get_bottom(), w.body.get_top(), color=MUTED, sw=2.6)
                       for w in workers])
        st = synth.body.get_top()
        gdx = [-0.9, -0.35, 0.35, 0.9]
        gather = VGroup(*[arr(w.body.get_bottom(),
                              np.array([st[0] + dx, st[1], 0]), color=MUTED, sw=2.6)
                          for w, dx in zip(workers, gdx)])

        self.play(FadeIn(planner, scale=0.9), run_time=0.6)
        self.play(LaggedStart(*[GrowArrow(a) for a in fan], lag_ratio=0.05, run_time=0.7),
                  LaggedStart(*[FadeIn(w, scale=0.85) for w in workers],
                              lag_ratio=0.05, run_time=0.7))
        self.set_cap("The planner fans the work out to four workers.", color=INK)
        self.beat(0.9)

        # all four run at the SAME time
        clock = VGroup(Circle(radius=0.2, stroke_color=GOOD, stroke_width=3),
                       Line(ORIGIN, UP * 0.13, stroke_color=GOOD, stroke_width=3),
                       Line(ORIGIN, RIGHT * 0.1, stroke_color=GOOD, stroke_width=3))
        same = txt("same time", fs=18, color=GOOD, weight="BOLD")
        badge = VGroup(clock, same).arrange(RIGHT, buff=0.16).move_to([-1.2, 1.9, 0])
        self.play(FadeIn(badge, scale=0.8),
                  *[Indicate(w, color=RESEARCH, scale_factor=1.12) for w in workers],
                  run_time=1.0)
        toks = VGroup(*[token(RESEARCH, r=0.1).move_to(w.body.get_top() + DOWN * 0.16)
                        for w in workers])
        self.add(toks)
        self.set_cap("All four run concurrently: this is the map step.", color=RESEARCH)
        self.read(1.0)

        # gather / reduce into synthesize
        self.play(FadeIn(synth, scale=0.9),
                  LaggedStart(*[GrowArrow(a) for a in gather], lag_ratio=0.05, run_time=0.8))
        self.play(*[t.animate.move_to(synth.body.get_center()) for t in toks],
                  *[g.animate.set_stroke(color=WRITER, width=5) for g in gather],
                  run_time=0.9, rate_func=rate_functions.ease_in_out_sine)
        self.play(FadeOut(toks), Indicate(synth, color=WRITER, scale_factor=1.1), run_time=0.6)
        self.set_cap("Results reduce back into one state, then synthesize.", color=WRITER)
        self.flash_good(0.1)
        self.read(1.2)

        self.settle()
        self.wipe()


# --------------------------------------------------------------------------- #
# Scene 5 - Takeaway                                                           #
# --------------------------------------------------------------------------- #
class Takeaway(_LGBase):
    def construct(self):
        self.build_takeaway()

    def build_takeaway(self):
        title = txt("Orchestration is just a graph.", fs=40, color=INK, weight="BOLD")
        title.move_to([0, 2.35, 0])
        line = Line(title.get_left() + LEFT * 0.4, title.get_right() + RIGHT * 0.4,
                    color=GOLD, stroke_width=3).next_to(title, DOWN, buff=0.25)
        self.play(Write(title), Create(line), run_time=1.3)
        self.read(0.7)

        rows = [
            ("Nodes are agents.", "Edges are the control flow.", MUTED),
            ("A router decides", "the next step to take.", GOLD),
            ("Shared state carries the work;", "loops let it iterate.", ANALYST),
        ]
        items = VGroup()
        for a, b, c in rows:
            dot = Dot(radius=0.08, color=c)
            t = txt(f"{a} {b}", fs=27, color=INK, t2c={a.split()[0]: c})
            items.add(VGroup(dot, t).arrange(RIGHT, buff=0.28))
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, -0.25, 0])
        for it in items:
            self.play(FadeIn(it, shift=RIGHT * 0.2), run_time=0.7)
            self.beat(0.7)

        self.read(1.0)
        kicker = txt("Add specialists, not complexity.", fs=30, color=GOLD, weight="BOLD")
        kicker.move_to([0, -3.1, 0])
        self.play(FadeIn(kicker, shift=UP * 0.15), run_time=0.9)
        self.read(1.6)

        self.settle()
        self.wipe()


# --------------------------------------------------------------------------- #
# Bookend scenes + full film                                                   #
# --------------------------------------------------------------------------- #
class Intro(_LGBase):
    def construct(self):
        self.play_intro()


class Outro(_LGBase):
    def construct(self):
        self.play_outro()


class LangGraphFilm(_LGBase):
    def construct(self):
        self.play_intro()
        self.build_problem()
        self.build_graph()
        self.build_team()
        self.build_parallel()
        self.build_takeaway()
        self.play_outro()

    # pull in the scene bodies
    build_problem = Problem.build_problem
    build_graph = Graph.build_graph
    build_team = Team.build_team
    build_parallel = Parallel.build_parallel
    build_takeaway = Takeaway.build_takeaway
