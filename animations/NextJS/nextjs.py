"""What is Next.js? — a short, house-style explainer.

Next.js is a React framework that ships with its own Node.js server, which is
exactly what plain React is missing: a classic single-page app sends the
browser an empty div plus a JavaScript bundle, and every piece of data needs a
second application (a separate backend) built and deployed on the side.
Next.js folds that backend into the framework.

The film builds the idea in six beats:

    1. Problem      — what a real React SPA actually ships (a REAL Vite
                      build's index.html: one empty div), and the separate
                      backend it still needs
    2. Definition   — what Next.js is, and file-system routing: a folder in
                      app/ becomes a URL
    3. Server       — Server Components: a page that queries SQLite directly,
                      with the REAL curl'd HTML (data already inside, and a
                      per-request timestamp that changes between two requests)
    4. Api          — route handlers: app/api/books/route.js answered a REAL
                      curl -i with 200 / application/json / rows from SQLite
    5. Modes        — the REAL `next build` route table: static ○ vs dynamic ƒ,
                      chosen route by route
    6. FullStack    — the whole architecture in one picture: browser ->
                      middleware -> components / handlers -> database,
                      one repo, one deploy

All terminal panels show REAL output baked by generate_assets.py from a real
Next.js 16 app (demo/) that was npm-installed, built, and served; nothing is
mocked. Everything is drawn with Manim ``Text`` (Pango), never ``Tex``.
Scenes render individually (``Problem``, ``Definition``, ``ServerComponents``,
``ApiRoutes``, ``RenderModes``, ``FullStack``, ``Intro``, ``Outro``) or as one
film (``WhatIsNextJS``).

Env knobs:
    NX_QUICK=1   collapse every hold for a fast sanity render
    NX_DELAY=..  reading-rhythm multiplier for small inter-step pauses
    NX_READ=..   absolute hold after a caption lands (seconds) — reading time
"""
from __future__ import annotations

import json
import os

import numpy as np
from manimx import *


QUICK = quick_mode("NX")
DELAY = float(os.environ.get("NX_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("NX_READ", 0.32 if QUICK else 2.35))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.1  # settle held on a finished scene before it wipes

# ---- palette (dark house style, shared across the series) ----------------- #
FAINT = "#2A3140"       # gridlines / faint wires

NEXT_C = "#EDEDED"      # Next.js itself (its brand is monochrome) — HERO
REACT_C = "#61DAFB"     # React / the client side (React cyan)
SRV = "#3DD68C"         # things that run on the server (green)
CLIENT_C = "#5B8DEF"    # the browser / static files (indigo)
DB_C = "#C792EA"        # the database (violet)


NBSP = " "         # Pango trims real leading spaces; NBSP survives

# ---- real, baked data (see generate_assets.py) ----------------------------- #
_NEXT_FALLBACK = {
    "next_version": "16.4.3", "node_version": "v25.6.0",
    "build_table": [
        "Route (app)", "┌ ○ /", "├ ○ /_not-found", "├ ƒ /api/books",
        "└ ƒ /books", "",
        "○  (Static)   prerendered as static content",
        "ƒ  (Dynamic)  server-rendered on demand",
    ],
    "books_rows": [
        "<main>", "<h1>Books</h1>", "<ul>",
        "<li>The Mythical Man-Month (1975)</li>",
        "<li>The C Programming Language (1978)</li>",
        "<li>Structure and Interpretation of Computer Programs (1985)</li>",
        "<li>Design Patterns (1994)</li>",
        "<li>The Pragmatic Programmer (1999)</li>",
        "</ul>", "<p>rendered at 2026-10-26T14:10:20.827Z</p>", "</main>",
    ],
    "books_ts": ["2026-10-26T14:10:20.827Z", "2026-10-26T14:10:22.148Z"],
    "api_status": "HTTP/1.1 200 OK",
    "api_content_type": "application/json",
    "api_body": (
        '[{"title":"The Mythical Man-Month","year":1975},'
        '{"title":"The C Programming Language","year":1978},'
        '{"title":"Structure and Interpretation of Computer Programs","year":1985},'
        '{"title":"Design Patterns","year":1994},'
        '{"title":"The Pragmatic Programmer","year":1999}]'
    ),
}

_SPA_FALLBACK = {
    "vite_version": "8.3.5",
    "index_html": (
        "<!doctype html>\n<html lang=\"en\">\n  <head>\n"
        "    <meta charset=\"UTF-8\" />\n"
        "    <link rel=\"icon\" type=\"image/svg+xml\" href=\"/favicon.svg\" />\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n"
        "    <title>spa</title>\n"
        "    <script type=\"module\" crossorigin src=\"/assets/index-DSXtc1GT.js\"></script>\n"
        "    <link rel=\"stylesheet\" crossorigin href=\"/assets/index-DykytF2W.css\">\n"
        "  </head>\n  <body>\n    <div id=\"root\"></div>\n  </body>\n</html>\n"
    ),
}


def _load_asset(name, fallback):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", name)
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return dict(fallback)


NEXT = _load_asset("next.json", _NEXT_FALLBACK)
SPA = _load_asset("spa.json", _SPA_FALLBACK)
_API_ROWS = json.loads(NEXT["api_body"])
assert len(_API_ROWS) == 5 and _API_ROWS[0]["year"] == 1975, _API_ROWS
assert NEXT["books_ts"][0] != NEXT["books_ts"][1], NEXT["books_ts"]
NEXT_MAJOR = NEXT["next_version"].split(".")[0]

# ---- code-panel syntax colours --------------------------------------------- #
CODE_FS = 19
PLAIN = "#D6DEEB"       # default code text
COMMENT = "#5F6B7E"     # comments (grey-blue)
KW = "#C792EA"          # keywords (violet)
TAG = "#38BDF8"         # JSX / HTML tags (cyan)
FUNC = "#82AAFF"        # function names
STR = "#C3E88D"         # strings

JS_T2C = {
    "import": KW, "export": KW, "const": KW, "default": KW, "function": KW,
    "return": KW, "async": KW, "new": KW, "from": KW,
    "prepare": FUNC, ".all": FUNC, ".map": FUNC, "toISOString": FUNC,
    "Response.json": FUNC, "GET": FUNC, "Books": FUNC, "Date": FUNC,
    "<main>": TAG, "</main>": TAG, "<h1>": TAG, "</h1>": TAG,
    "<ul>": TAG, "</ul>": TAG, "<li": TAG, "</li>": TAG, "<p>": TAG, "</p>": TAG,
    '"../../lib/db"': STR, '"../../../lib/db"': STR,
    '"SELECT title, year FROM books ORDER BY year"': STR,
    '"force-dynamic"': STR,
    "`${b.title} (${b.year})`": STR, "`rendered at ${at}`": STR,
}


def _wrap_line(line, width=58):
    """Terminal-style soft wrap; continuations indent 8 spaces."""
    out, cur = [], line.rstrip()
    while len(cur) > width:
        cut = cur.rfind(" ", 20, width)
        if cut < 20:
            cut = width
        out.append(cur[:cut])
        cur = "        " + cur[cut:].lstrip()
    out.append(cur)
    return out


def html_rows(lines, width=58, data_tags=("<li", "<h1", "<p")):
    """Real captured HTML -> coloured terminal rows (content pops, tags calm)."""
    rows = []
    for ln in lines:
        color = INK if ln.lstrip().startswith(data_tags) else MUTED
        weight = "NORMAL"
        for piece in _wrap_line(ln, width):
            rows.append((piece, color, weight))
    return rows


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight, **extra}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    return Text(text, **kw)


def mono(text, fs=18, color=INK, weight="NORMAL"):
    return Text(text, font_size=fs, color=color, font=MONO, weight=weight)


def wire(a, b, color=MUTED, sw=2.0, op=0.75):
    """A thin connecting line that sits behind the glyphs."""
    ln = Line(a, b, stroke_color=color, stroke_width=sw, stroke_opacity=op)
    ln.set_z_index(-1)
    return ln


def make_tick(color=SRV, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


# ---- glyphs (all hand-drawn Manim mobjects, no image assets) -------------- #
def next_mark(color=NEXT_C, s=1.0):
    """A ring with an N — a nod to the Next.js logo, drawn by hand."""
    ring = Circle(radius=0.46, stroke_color=color, stroke_width=5,
                  fill_color=PANEL, fill_opacity=1.0)
    n = txt("N", fs=34, color=color, weight="BOLD").move_to(ring)
    return VGroup(ring, n).scale(s)


def browser(w=3.0, h=2.1, url="localhost:3000", color=CLIENT_C):
    """A browser window: title bar with dots + URL field, and a content zone."""
    bg = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                          stroke_color=color, stroke_width=2.6,
                          fill_color=PANEL, fill_opacity=1.0)
    bar = Rectangle(width=w - 0.06, height=0.44, stroke_width=0,
                    fill_color="#141C29", fill_opacity=1.0)
    bar.move_to(bg).align_to(bg, UP).shift(DOWN * 0.04)
    dots = VGroup(*[Dot(radius=0.04, color=c)
                    for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.09)
    dots.move_to([bg.get_left()[0] + 0.36, bar.get_center()[1], 0])
    field = RoundedRectangle(width=w - 1.0, height=0.26, corner_radius=0.08,
                             stroke_width=0, fill_color=BG, fill_opacity=1.0)
    field.move_to([bg.get_center()[0] + 0.33, bar.get_center()[1], 0])
    u = mono(url, fs=12, color=MUTED)
    if u.width > field.width - 0.16:
        u.scale((field.width - 0.16) / u.width)
    u.move_to(field)
    zone = Rectangle(width=w - 0.3, height=h - 0.75, stroke_width=0, fill_opacity=0)
    zone.move_to([bg.get_center()[0], bar.get_bottom()[1] - (h - 0.75) / 2 - 0.08, 0])
    g = VGroup(bg, bar, dots, field, u, zone)
    g.box = bg
    g.zone = zone
    return g


def phone(h=1.5, color=MUTED):
    """A phone outline (a non-browser client for the API)."""
    w = h * 0.52
    body = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                            stroke_color=color, stroke_width=2.4,
                            fill_color=PANEL, fill_opacity=1.0)
    speaker = Line([-w * 0.16, 0, 0], [w * 0.16, 0, 0],
                   stroke_color=color, stroke_width=2.4)
    speaker.move_to([0, h / 2 - 0.14, 0])
    home = Line([-w * 0.2, 0, 0], [w * 0.2, 0, 0], stroke_color=color, stroke_width=2.4)
    home.move_to([0, -h / 2 + 0.12, 0])
    return VGroup(body, speaker, home)


def db_cylinder(color=DB_C, w=1.6, h=1.5, label="SQLite", fs=17):
    """The classic database cylinder (explicit colours — Ellipse defaults RED)."""
    yt, yb = h / 2, -h / 2
    ew = 0.44
    body = Rectangle(width=w, height=h, stroke_width=0, fill_color=color, fill_opacity=0.10)
    left = Line([-w / 2, yb, 0], [-w / 2, yt, 0], stroke_color=color, stroke_width=2.6)
    right = Line([w / 2, yb, 0], [w / 2, yt, 0], stroke_color=color, stroke_width=2.6)
    bot = Ellipse(width=w, height=ew, stroke_color=color, stroke_width=2.6,
                  fill_color=BG, fill_opacity=1.0).move_to([0, yb, 0])
    mid = Arc(radius=w / 2, start_angle=PI, angle=-PI, arc_center=[0, yt - ew * 0.9, 0],
              stroke_color=color, stroke_width=1.6).stretch_to_fit_height(ew * 0.5)
    top = Ellipse(width=w, height=ew, stroke_color=color, stroke_width=2.6,
                  fill_color=color, fill_opacity=0.22).move_to([0, yt, 0])
    glyph = VGroup(body, bot, left, right, mid, top)
    glyph.body = body
    if label:
        lab = txt(label, fs=fs, color=color, weight="BOLD").next_to(glyph, DOWN, buff=0.16)
        glyph.add(lab)
        glyph.label = lab
    return glyph


# ========================================================================== #
class _NextBase(ExplainerScene):
    pace = Pace(
        quick=QUICK, delay=DELAY, read=READ, anim_slow=ANIM_SLOW, end_hold=END_HOLD,
        card=(0.3, 1.0), stretch="given",
    )

    # ---- text helpers ----------------------------------------------------- #
    def section_header(self, label, color):
        t = txt(label, fs=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=23, y=-3.42, weight="NORMAL"):
        """A bottom caption, width-clamped so it never runs off-screen."""
        m = txt(text, fs=fs, color=color, weight=weight)
        if m.width > 12.7:
            m.scale_to_fit_width(12.7)
        m.move_to([0, y, 0])
        return m

    # ---- code panel ------------------------------------------------------- #
    def code_panel(self, spec, table=JS_T2C, title="page.jsx", fs=CODE_FS,
                   indent_unit=0.46, line_buff=0.16, target_h=5.6, target_w=7.2):
        """spec: list of (indent, text); "" is a blank line. Returns (panel, lines)."""
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.26, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith(("#", "//")):
                m = txt(s, fs=fs, color=COMMENT, font=MONO, slant=ITALIC)
            else:
                m = Text(s, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(s, table))
            m._indent = indent
            lines.append(m)
        code = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * indent_unit * m._indent)
        f = min(target_h / code.height, target_w / code.width)
        if f < 1:
            code.scale(f)

        bg = RoundedRectangle(width=code.width + 0.9, height=code.height + 1.15,
                              corner_radius=0.16, stroke_color=FAINT, stroke_width=2,
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(code)
        bar = RoundedRectangle(width=bg.width, height=0.5, corner_radius=0.16,
                               stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=15, color=MUTED, font=MONO)
        max_ttl_w = bg.width - 1.5
        if ttl.width > max_ttl_w:
            ttl.scale_to_fit_width(max_ttl_w)
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.2)
        panel = VGroup(bg, bar, dots, ttl, code)
        panel.code = code
        return panel, lines

    def unfocus(self, rt=0.3):
        if self.hlrect is not None:
            self.play(FadeOut(self.hlrect), run_time=rt)
            self.hlrect = None

    # ---- terminal panel for REAL captured output ---------------------------- #
    def term_panel(self, rows, title="terminal", fs=16, line_buff=0.13,
                   target_h=4.3, target_w=7.4):
        """rows: list of (text, color, weight) — text shown verbatim.

        Pango/Manim strip LEADING whitespace (even NBSP) from a Text, which
        would wreck aligned gutters — so leading spaces become an explicit
        x-shift measured in real Menlo character widths, and only the interior
        spaces are NBSP-protected.
        """
        char_w = Text("0" * 10, font=MONO, font_size=fs).width / 10
        lines = VGroup()
        for text, color, weight in rows:
            if text.strip() == "":
                m = Rectangle(width=0.02, height=0.2,
                              fill_opacity=0, stroke_opacity=0)
                m._lead = 0.0
            else:
                lead = len(text) - len(text.lstrip(" "))
                m = Text(text.lstrip(" ").replace(" ", NBSP), font=MONO,
                         font_size=fs, color=color, weight=weight)
                m._lead = lead * char_w
            lines.add(m)
        lines.arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * m._lead)
        f = min(target_h / lines.height, target_w / lines.width)
        if f < 1:
            lines.scale(f)
        bg = RoundedRectangle(width=lines.width + 0.8, height=lines.height + 1.05,
                              corner_radius=0.16, stroke_color=FAINT, stroke_width=2,
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(lines)
        bar = RoundedRectangle(width=bg.width, height=0.48, corner_radius=0.16,
                               stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=14, color=MUTED, font=MONO)
        if ttl.width > bg.width - 1.5:
            ttl.scale_to_fit_width(bg.width - 1.5)
        ttl.next_to(dots, RIGHT, buff=0.3).set_y(bar.get_center()[1])
        lines.shift(DOWN * 0.18)
        panel = VGroup(bg, bar, dots, ttl, lines)
        panel.rows = lines
        panel.fscale = min(f, 1.0)
        panel.fs = fs
        return panel

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("Next.js", font_size=74, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1.6, header.get_bottom()[1] - 0.42, 0],
            [header.get_right()[0] + 1.6, header.get_bottom()[1] - 0.42, 0],
        ).set_stroke(width=3, color=GOLD)
        mark = next_mark(s=0.85)
        mark.move_to(line.get_right() + RIGHT * 0.5 + UP * 0.34)
        writer = Text("Created by Ptolémé", font_size=28, color=CLIENT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.5)
        self.play(FadeIn(mark, shift=DOWN * 0.15), run_time=0.9)
        self.read(0.7)
        sub = Text("The React framework that brings its own backend.",
                   font_size=29, color=MUTED)
        if sub.width > 12.6:
            sub.scale_to_fit_width(12.6)
        sub.move_to(header)
        self.play(Transform(header, sub), FadeOut(mark), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("Server Components · API routes · Rendering modes · One deploy",
                   font_size=22, color=MUTED)
        if src.width > 12.0:
            src.scale_to_fit_width(12.0)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.3)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=CLIENT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Your frontend and your backend, one framework.",
                     font_size=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.5)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — the problem: React alone stops at the browser
    # ====================================================================== #
    def scene_problem(self):
        header = self.section_header("React alone stops at the browser", REACT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        br = browser(w=3.2, h=2.2, url="myshop.com").move_to([-4.4, 1.45, 0])
        blab = txt("the user's browser", fs=16, color=CLIENT_C).next_to(br, DOWN, buff=0.16)
        host = chip("static file host", REACT_C, fs=20, h=0.8).move_to([4.2, 1.45, 0])
        hlab = txt("it only hands over files", fs=15, color=MUTED).next_to(host, DOWN, buff=0.14)
        cap = self.say("A classic React app is a single-page app. All of it runs in the user's browser.")
        self.play(FadeIn(br), FadeIn(blab), FadeIn(cap), run_time=0.7)
        self.read(1.0)
        self.play(FadeIn(host, scale=0.85), FadeIn(hlab), run_time=0.5)

        a_req = arr(br.get_right() + UP * 0.35, host.get_left() + UP * 0.31, color=CLIENT_C, sw=3.5)
        req_l = mono("GET /", fs=14, color=CLIENT_C).next_to(a_req, UP, buff=0.08)
        a_res = arr(host.get_left() + DOWN * 0.31, br.get_right() + DOWN * 0.35, color=REACT_C, sw=3.5)
        res_l = mono("index.html", fs=14, color=REACT_C).next_to(a_res, DOWN, buff=0.08)
        self.play(GrowArrow(a_req), FadeIn(req_l), run_time=0.5)
        self.play(GrowArrow(a_res), FadeIn(res_l), run_time=0.5)
        cap = self.swap_cap(cap, "When someone visits, the server's only job is to hand over one HTML file.")
        self.read(1.0)

        spa_rows = []
        for ln in SPA["index_html"].rstrip().splitlines():
            color = INK if 'id="root"' in ln else (STR if "<script" in ln else MUTED)
            for piece in _wrap_line(ln, 64):
                spa_rows.append((piece, color, "BOLD" if 'id="root"' in ln else "NORMAL"))
        spa_panel = self.term_panel(spa_rows, title="spa/dist/index.html", fs=15,
                                    target_h=2.75, target_w=8.6)
        spa_panel.move_to([0, -1.32, 0])
        vlab = txt(f"a real React SPA, built with Vite {SPA['vite_version']}",
                   fs=15, color=MUTED)
        vlab.next_to(spa_panel, RIGHT, buff=0.3).align_to(spa_panel, UP)
        if vlab.get_right()[0] > 6.9:
            vlab.next_to(spa_panel, LEFT, buff=0.3).align_to(spa_panel, UP)
        cap = self.swap_cap(cap, "Here is that file from a real React build. The whole application is one empty div.")
        self.play(FadeIn(spa_panel, shift=UP * 0.15), FadeIn(vlab), run_time=0.7)
        self.read(1.2)

        root_idx = next(i for i, (t, _, _) in enumerate(spa_rows) if 'id="root"' in t)
        hl = self.hl_lines(spa_panel, list(spa_panel.rows), [root_idx], color=BAD, opacity=0.2)
        self.play(FadeIn(hl), run_time=0.4)
        cap = self.swap_cap(cap, "There is no content in it. This server knows nothing about your data.")
        self.read(1.1)

        self.play(FadeOut(spa_panel), FadeOut(hl), FadeOut(vlab),
                  FadeOut(a_req), FadeOut(req_l), FadeOut(a_res), FadeOut(res_l), run_time=0.5)

        steps = VGroup(
            chip("download JS", CLIENT_C, fs=18),
            chip("run React", REACT_C, fs=18),
            chip("fetch data", GOLD, fs=18),
            chip("finally paint", SRV, fs=18),
        )
        steps.arrange(RIGHT, buff=0.95).move_to([0, -0.7, 0])
        step_arrows = VGroup(*[arr(steps[i].get_right(), steps[i + 1].get_left(), sw=3)
                               for i in range(3)])
        cap = self.swap_cap(cap, "So the browser downloads the bundle, runs React, fetches data, and only then paints the page.")
        for i, s in enumerate(steps):
            self.play(FadeIn(s, scale=0.85), run_time=0.35)
            if i < 3:
                self.play(GrowArrow(step_arrows[i]), run_time=0.3)
        self.read(1.2)

        api = chip("API server (Express)", BAD, fs=17, w=2.6, h=0.72).move_to([4.1, -0.7, 0])
        dbx = db_cylinder(w=1.1, h=1.0, label=None).move_to([6.25, -0.7, 0])
        link = wire(api.get_right(), dbx.get_left() + LEFT * 0.06, color=DB_C, sw=2.2)
        a_api = arr(steps[2].get_right(), api.get_left(), color=BAD, sw=3)
        self.play(FadeOut(steps[3]), FadeOut(step_arrows[2]), run_time=0.3)
        self.play(FadeIn(api, scale=0.85), FadeIn(dbx), Create(link), GrowArrow(a_api), run_time=0.7)
        cap = self.swap_cap(cap, "And the data comes from a second application, a separate backend you must build and deploy.")
        self.read(1.3)

        pains = VGroup(
            pill("blank first paint", BAD, fs=20),
            pill("a second codebase", BAD, fs=20),
            pill("no safe place for secrets", BAD, fs=20),
        ).arrange(RIGHT, buff=0.5).move_to([0, -2.35, 0])
        for p in pains:
            self.play(FadeIn(p, scale=0.85), run_time=0.4)
        self.beat(0.8)
        cap = self.swap_cap(cap, "React needs a server behind it. Next.js makes that server part of the framework.",
                            color=GOLD)
        self.read(1.3)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — what Next.js is + file-system routing
    # ====================================================================== #
    def scene_definition(self):
        header = self.section_header("What is Next.js?", NEXT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        mark = next_mark(s=1.05)
        name = txt("Next.js", fs=44, color=INK, weight="BOLD")
        lockup = VGroup(mark, name).arrange(RIGHT, buff=0.3).move_to([0.6, 2.05, 0])
        self.play(FadeIn(mark, scale=0.6), FadeIn(name, shift=LEFT * 0.1), run_time=0.7)
        cap = self.say("Next.js is an open source React framework, created by Vercel in 2016.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        facts = [
            "You still write React components. Next.js wraps them in a real Node.js server.",
            "That one server renders pages, serves files, and answers API calls.",
            f"Version {NEXT_MAJOR} today. Sites like Netflix Jobs, TikTok, and ChatGPT run on it.",
        ]
        rows = VGroup()
        for f in facts:
            d = Dot(radius=0.06, color=NEXT_C)
            rows.add(VGroup(d, txt(f, fs=22, color=INK)).arrange(RIGHT, buff=0.24))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.46).move_to([0, 0.0, 0])
        for row in rows:
            self.play(FadeIn(row, shift=RIGHT * 0.12), run_time=0.5)
            self.read(0.75)

        self.play(FadeOut(rows), run_time=0.4)
        cap = self.swap_cap(cap, "Routing is just the file system. Every folder inside app becomes a URL on the site.")

        tree_lines = [
            ("app/", NEXT_C, "BOLD"),
            ("├─ page.jsx", PLAIN, "NORMAL"),
            ("├─ books/", MUTED, "NORMAL"),
            ("│  └─ page.jsx", PLAIN, "NORMAL"),
            ("└─ api/", MUTED, "NORMAL"),
            ("   └─ books/", MUTED, "NORMAL"),
            ("      └─ route.js", PLAIN, "NORMAL"),
            ("lib/", NEXT_C, "BOLD"),
            ("└─ db.js", PLAIN, "NORMAL"),
        ]
        tree = self.term_panel(tree_lines, title="the project", fs=17,
                               target_h=3.2, target_w=4.4)
        tree.move_to([-3.9, -0.65, 0])
        self.play(FadeIn(tree, shift=UP * 0.15), run_time=0.6)
        self.read(0.9)

        rows_v = list(tree.rows)
        targets = [
            (1, chip("/", CLIENT_C, fs=19, w=1.7)),
            (3, chip("/books", CLIENT_C, fs=19, w=1.7)),
            (6, chip("/api/books", GOLD, fs=19, w=2.2)),
        ]
        chips, arrows = VGroup(), VGroup()
        for i, c in targets:
            c.move_to([2.6, rows_v[i].get_center()[1], 0])
            chips.add(c)
            arrows.add(arr(tree[0].get_right() * RIGHT + rows_v[i].get_center() * UP,
                           c.get_left(), color=MUTED, sw=3))
        for c, a in zip(chips, arrows):
            self.play(GrowArrow(a), FadeIn(c, scale=0.85), run_time=0.45)
        self.beat(0.9)

        srv_pill = pill("no URL: server-only code", SRV, fs=18, weight="NORMAL")
        srv_pill.move_to([3.3, rows_v[8].get_center()[1], 0])
        a_srv = arr(tree[0].get_right() * RIGHT + rows_v[8].get_center() * UP,
                    srv_pill.get_left(), color=SRV, sw=3)
        self.play(GrowArrow(a_srv), FadeIn(srv_pill, scale=0.9), run_time=0.5)
        cap = self.swap_cap(cap, "Files with no route, like the database helper, stay on the server and are never sent out.")
        self.read(1.2)

        cap = self.swap_cap(cap, "Pages, API endpoints, and database code all live in one tree. That tree is the whole app.",
                            color=GOLD)
        self.read(1.3)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Server Components: the page queries the database directly
    # ====================================================================== #
    def scene_server(self):
        header = self.section_header("Components that run on the server", SRV)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("Components inside app are Server Components by default. They execute on the server.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        spec = [
            (0, 'import { db } from "../../lib/db";'),
            (0, ""),
            (0, 'export const dynamic = "force-dynamic";'),
            (0, ""),
            (0, "export default function Books() {"),
            (1, "const books = db"),
            (2, '.prepare("SELECT title, year FROM books ORDER BY year")'),
            (2, ".all();"),
            (1, "const at = new Date().toISOString();"),
            (1, "return ("),
            (2, "<main>"),
            (3, "<h1>Books</h1>"),
            (3, "<ul>"),
            (4, "{books.map((b) => ("),
            (5, "<li key={b.title}>{`${b.title} (${b.year})`}</li>"),
            (4, "))}"),
            (3, "</ul>"),
            (3, "<p>{`rendered at ${at}`}</p>"),
            (2, "</main>"),
            (1, ");"),
            (0, "}"),
        ]
        panel, lines = self.code_panel(spec, title="app/books/page.jsx",
                                       target_h=4.6, target_w=7.4)
        panel.move_to([0, -0.35, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.7)
        self.read(0.8)

        self.focus(panel, lines, [0])
        cap = self.swap_cap(cap, "This page opens a real SQLite database, imported like any other module.")
        self.read(1.0)
        self.focus(panel, lines, [5, 6, 7])
        cap = self.swap_cap(cap, "It runs a real SQL query directly inside the component. No fetch, no API call in between.")
        self.read(1.2)
        self.focus(panel, lines, [10, 11, 12, 13, 14, 15, 16, 17, 18])
        cap = self.swap_cap(cap, "On each request, the server runs this function and renders the JSX into plain HTML.")
        self.read(1.1)
        self.unfocus()

        self.play(panel.animate.scale(0.78).move_to([-3.85, -0.35, 0]), run_time=0.7)
        rows = [("$ curl -s localhost:3000/books", SRV, "BOLD"), ("", PLAIN, "NORMAL")]
        rows += html_rows(NEXT["books_rows"], width=52)
        term = self.term_panel(rows, title="terminal", fs=15, target_h=4.2, target_w=6.2)
        term.move_to([3.45, -0.35, 0])
        cap = self.swap_cap(cap, "This is the real response of a real Next.js server. The data is already inside the HTML.")
        self.play(FadeIn(term, shift=UP * 0.15), run_time=0.7)
        self.read(1.4)

        ts_idx = next(i for i, (t, _, _) in enumerate(rows) if "rendered at" in t)
        ts_row = list(term.rows)[ts_idx]
        hl = self.hl_lines(term, list(term.rows), [ts_idx], color=GOLD, opacity=0.18)
        self.play(FadeIn(hl), run_time=0.4)
        cap = self.swap_cap(cap, "Watch the timestamp. Request the page again:")
        self.beat(0.9)

        new_text = rows[ts_idx][0].replace(NEXT["books_ts"][0], NEXT["books_ts"][1])
        new_row = Text(new_text.replace(" ", NBSP), font=MONO, font_size=term.fs, color=INK)
        new_row.scale(term.fscale).move_to(ts_row, aligned_edge=LEFT)
        self.play(FadeOut(ts_row, run_time=0.25), FadeIn(new_row, run_time=0.25))
        cap = self.swap_cap(cap, "It changed. The server re-ran the component for this request. That is server-side rendering.")
        self.read(1.3)

        self.play(FadeOut(panel), FadeOut(term), FadeOut(hl), FadeOut(new_row), run_time=0.5)
        perks = VGroup(
            pill("server code never reaches the browser", SRV, fs=20, weight="NORMAL"),
            pill("database secrets stay on the server", SRV, fs=20, weight="NORMAL"),
            pill("less JavaScript to download", SRV, fs=20, weight="NORMAL"),
        ).arrange(DOWN, buff=0.34).move_to([0, -0.4, 0])
        for p in perks:
            self.play(FadeIn(p, shift=RIGHT * 0.12), run_time=0.4)
            self.beat(0.6)
        cap = self.swap_cap(cap, "Half of your app just moved behind the network, and it is still just React.",
                            color=GOLD)
        self.read(1.3)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — API routes: a backend endpoint in a file
    # ====================================================================== #
    def scene_api(self):
        header = self.section_header("A backend endpoint in a file", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("Pages are not the only thing this server can answer with. It can also serve pure data.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        spec = [
            (0, 'import { db } from "../../../lib/db";'),
            (0, ""),
            (0, "export async function GET() {"),
            (1, "const books = db"),
            (2, '.prepare("SELECT title, year FROM books ORDER BY year")'),
            (2, ".all();"),
            (1, "return Response.json(books);"),
            (0, "}"),
        ]
        panel, lines = self.code_panel(spec, title="app/api/books/route.js",
                                       target_h=2.9, target_w=5.7)
        panel.move_to([-3.5, 0.95, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.7)
        cap = self.swap_cap(cap, "A file named route.js becomes an HTTP endpoint. You export one function per HTTP method.")
        self.read(1.2)

        methods = VGroup(*[chip(m, c, fs=17, w=1.35, h=0.5)
                           for m, c in [("GET", SRV), ("POST", GOLD),
                                        ("PUT", CLIENT_C), ("DELETE", BAD)]])
        methods.arrange(RIGHT, buff=0.32).next_to(panel, DOWN, buff=0.42)
        self.play(LaggedStart(*[FadeIn(m, scale=0.85) for m in methods],
                              lag_ratio=0.12, run_time=0.7))
        self.beat(0.8)

        body_wrapped = []
        for piece in _wrap_line(NEXT["api_body"], 46):
            body_wrapped.append((piece, INK, "NORMAL"))
        rows = [
            ("$ curl -i localhost:3000/api/books", SRV, "BOLD"),
            ("", PLAIN, "NORMAL"),
            (NEXT["api_status"], GOLD, "BOLD"),
            ("content-type: " + NEXT["api_content_type"], GOLD, "NORMAL"),
            ("", PLAIN, "NORMAL"),
        ] + body_wrapped
        term = self.term_panel(rows, title="terminal", fs=15, target_h=3.8, target_w=6.1)
        term.move_to([3.55, 0.25, 0])
        self.play(FadeIn(term, shift=UP * 0.15), run_time=0.7)
        cap = self.swap_cap(cap, "Again, this is the server really answering: status 200, a JSON content type, rows from SQLite.")
        self.read(1.4)

        self.play(FadeOut(panel), FadeOut(methods), run_time=0.4)
        caller_pages = VGroup(browser(w=2.0, h=1.3, url="myshop.com"),
                              txt("your own pages", fs=15, color=MUTED)
                              ).arrange(DOWN, buff=0.14).move_to([-4.9, 1.85, 0])
        caller_phone = VGroup(phone(h=1.1),
                              txt("a mobile app", fs=15, color=MUTED)
                              ).arrange(DOWN, buff=0.14).move_to([-4.9, 0.0, 0])
        caller_svc = VGroup(chip("another service", MUTED, fs=17),
                            ).move_to([-4.9, -1.7, 0])
        callers = VGroup(caller_pages, caller_phone, caller_svc)
        a_calls = VGroup(*[arr(c.get_right() + RIGHT * 0.05,
                               term.get_left() + UP * dy, color=MUTED, sw=2.6)
                           for c, dy in zip(callers, (1.0, 0.0, -1.0))])
        self.play(LaggedStart(*[FadeIn(c) for c in callers], lag_ratio=0.15, run_time=0.8))
        self.play(*[GrowArrow(a) for a in a_calls], run_time=0.6)
        cap = self.swap_cap(cap, "Your pages can call it, and so can a mobile app or another service. It is a normal API.")
        self.read(1.2)

        cap = self.swap_cap(cap, "The backend stopped being a second project. It is a folder inside your app.",
                            color=GOLD)
        self.read(1.3)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — rendering modes: the real `next build` route table
    # ====================================================================== #
    def scene_modes(self):
        header = self.section_header("The server chooses, route by route", DB_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("A strong backend also knows when not to compute. Next.js decides this per route.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        rows = [("$ npx next build", SRV, "BOLD"), ("", PLAIN, "NORMAL")]
        tbl_start = len(rows)
        for ln in NEXT["build_table"]:
            if not ln.strip():
                continue
            if ln.startswith("Route"):
                rows.append((ln, INK, "BOLD"))
            elif "○" in ln:
                rows.append((ln, CLIENT_C, "NORMAL"))
            elif "ƒ" in ln:
                rows.append((ln, SRV, "NORMAL"))
            else:
                rows.append((ln, PLAIN, "NORMAL"))
        term = self.term_panel(rows, title="terminal", fs=17, target_h=3.0, target_w=8.6)
        term.move_to([0, 0.85, 0])
        self.play(FadeIn(term, shift=UP * 0.15), run_time=0.7)
        cap = self.swap_cap(cap, "This is the real build output of our little app. Next.js classified every route.")
        self.read(1.2)

        rv = list(term.rows)
        static_idx = [i for i, (t, _, _) in enumerate(rows) if "○" in t and "/" in t and "(" not in t]
        dyn_idx = [i for i, (t, _, _) in enumerate(rows) if "ƒ" in t and "(" not in t]
        legend_idx = [i for i, (t, _, _) in enumerate(rows) if "(" in t and ")" in t]

        hl = self.hl_lines(term, rv, static_idx, color=CLIENT_C, opacity=0.16)
        self.play(FadeIn(hl), run_time=0.4)
        cap = self.swap_cap(cap, "The home page uses no per-request data, so it was rendered once, at build time.")
        self.read(1.2)

        hl2 = self.hl_lines(term, rv, dyn_idx, color=SRV, opacity=0.16)
        self.play(ReplacementTransform(hl, hl2), run_time=0.4)
        cap = self.swap_cap(cap, "The books page and the API asked for fresh data, so they render on the server per request.")
        self.read(1.2)
        self.play(FadeOut(hl2), run_time=0.3)

        modes = VGroup(
            chip("○ static: built once", CLIENT_C, fs=17, h=0.6),
            chip("ƒ dynamic: rendered per request", SRV, fs=17, h=0.6),
            chip("revalidate: refreshed every N seconds", GOLD, fs=17, h=0.6),
        ).arrange(RIGHT, buff=0.42).move_to([0, -2.35, 0])
        if modes.width > 12.8:
            modes.scale_to_fit_width(12.8)
        for m in modes:
            self.play(FadeIn(m, shift=RIGHT * 0.12), run_time=0.4)
            self.beat(0.5)
        cap = self.swap_cap(cap, "There is a middle mode too: a static page that re-renders in the background every N seconds.")
        self.read(1.2)

        cap = self.swap_cap(cap, "Static speed where possible, live data where it matters. One line per route decides.",
                            color=GOLD)
        self.read(1.3)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — the full picture: one codebase, both halves
    # ====================================================================== #
    def scene_fullstack(self):
        header = self.section_header("One codebase, both halves", NEXT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        br = browser(w=2.7, h=1.9, url="myshop.com").move_to([-5.15, 0.35, 0])
        blab = txt("the browser", fs=15, color=CLIENT_C).next_to(br, DOWN, buff=0.14)

        srv_bg = RoundedRectangle(width=5.6, height=3.5, corner_radius=0.18,
                                  stroke_color=NEXT_C, stroke_width=2.6,
                                  fill_color=PANEL, fill_opacity=0.9).move_to([0.55, 0.35, 0])
        srv_title = VGroup(next_mark(s=0.42),
                           txt("Next.js server · Node.js", fs=19, color=NEXT_C, weight="BOLD"))
        srv_title.arrange(RIGHT, buff=0.18)
        srv_title.move_to([srv_bg.get_center()[0], srv_bg.get_top()[1] - 0.38, 0])
        mw = chip("middleware: runs before everything", GOLD, fs=16, w=4.9, h=0.52)
        mw.move_to([srv_bg.get_center()[0], srv_bg.get_top()[1] - 1.0, 0])
        sc = chip("Server Components", SRV, fs=17, w=2.45, h=0.95)
        rh = chip("Route Handlers", GOLD, fs=17, w=2.25, h=0.95)
        inner = VGroup(sc, rh).arrange(RIGHT, buff=0.3)
        inner.move_to([srv_bg.get_center()[0], srv_bg.get_bottom()[1] + 0.95, 0])
        sc_lab = txt("HTML", fs=14, color=SRV).next_to(sc, DOWN, buff=0.1)
        rh_lab = txt("JSON", fs=14, color=GOLD).next_to(rh, DOWN, buff=0.1)

        dbx = db_cylinder(w=1.6, h=1.5, label="SQLite").move_to([5.55, 0.35, 0])

        cap = self.say("Put together, one Next.js server carries the whole application.")
        self.play(FadeIn(br), FadeIn(blab), FadeIn(cap), run_time=0.6)
        self.play(FadeIn(srv_bg), FadeIn(srv_title), run_time=0.6)
        self.read(1.0)

        y_hi, y_lo = 0.95, -0.35
        a_req = arr([br.get_right()[0], y_hi, 0], [srv_bg.get_left()[0], y_hi, 0],
                    color=CLIENT_C, sw=3.5)
        req_l = mono("request", fs=13, color=CLIENT_C).next_to(a_req, UP, buff=0.07)
        self.play(GrowArrow(a_req), FadeIn(req_l), run_time=0.5)

        self.play(FadeIn(mw, scale=0.9), run_time=0.5)
        cap = self.swap_cap(cap, "Middleware runs before any page. It is the natural place for auth checks and redirects.")
        self.read(1.2)

        db_x = dbx.body.get_left()[0]
        a_db = arr([srv_bg.get_right()[0], 0.75, 0], [db_x, 0.75, 0], color=DB_C, sw=3.5)
        db_l = mono("SQL", fs=13, color=DB_C).next_to(a_db, UP, buff=0.07)
        a_db2 = arr([db_x, 0.15, 0], [srv_bg.get_right()[0], 0.15, 0], color=DB_C, sw=3.5)
        self.play(FadeIn(inner), FadeIn(sc_lab), FadeIn(rh_lab), FadeIn(dbx), run_time=0.6)
        self.play(GrowArrow(a_db), FadeIn(db_l), GrowArrow(a_db2), run_time=0.6)
        cap = self.swap_cap(cap, "Server Components answer with HTML, route handlers with JSON. Both can reach the database.")
        self.read(1.3)

        a_res = arr([srv_bg.get_left()[0], y_lo, 0], [br.get_right()[0], y_lo, 0],
                    color=SRV, sw=3.5)
        res_l = mono("HTML or JSON", fs=13, color=SRV).next_to(a_res, DOWN, buff=0.07)
        self.play(GrowArrow(a_res), FadeIn(res_l), run_time=0.5)
        self.beat(0.8)

        deploy = VGroup(
            pill("one repo", NEXT_C, fs=20),
            pill("one build", NEXT_C, fs=20),
            pill("one deploy", NEXT_C, fs=20),
        ).arrange(RIGHT, buff=0.5).move_to([0, -2.5, 0])
        self.play(LaggedStart(*[FadeIn(p, scale=0.85) for p in deploy],
                              lag_ratio=0.15, run_time=0.8))
        cap = self.swap_cap(cap, "One repository, one build, one deploy. The frontend and the backend cannot drift apart.")
        self.read(1.2)

        cap = self.swap_cap(cap, "Forms can even submit straight to a server function. Next.js calls these Server Actions.")
        self.read(1.2)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("React in front. A real backend behind.",
                      "One framework, one codebase, one deploy.", c2=GOLD)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_definition()
        self.scene_server()
        self.scene_api()
        self.scene_modes()
        self.scene_fullstack()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_NextBase):
    def construct(self):
        self.play_intro()


class Problem(_NextBase):
    def construct(self):
        self.scene_problem()


class Definition(_NextBase):
    def construct(self):
        self.scene_definition()


class ServerComponents(_NextBase):
    def construct(self):
        self.scene_server()


class ApiRoutes(_NextBase):
    def construct(self):
        self.scene_api()


class RenderModes(_NextBase):
    def construct(self):
        self.scene_modes()


class FullStack(_NextBase):
    def construct(self):
        self.scene_fullstack()


class Outro(_NextBase):
    def construct(self):
        self.play_outro()


class WhatIsNextJS(_NextBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    WhatIsNextJS().render()
