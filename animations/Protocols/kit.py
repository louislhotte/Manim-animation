"""kit.py: the pictures of the Protocols film.

One idea runs through all of them: **a clock drives the picture**. The film's data
is a list of events with times (a packet leaves at 105.6 ms and arrives at 158.1 ms,
an acknowledgment comes back, a queue overflows). A ``Clock`` holds "now"; painters
(``manimx.Layer``) draw what the world looks like at that instant: where each packet
is, which bytes of the picture have arrived, how wide the sender's window is. A scene
then only runs the clock (``clock.run(to=210, run_time=6)``) and stops it where the
narrator needs a word.

Painters draw with Cairo straight onto the frame (hundreds of packets cost nothing
that way); text stays ordinary Manim ``Text``.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from manimx import *

HERE = Path(__file__).resolve().parent
STORY = json.loads((HERE / "assets" / "story.json").read_text())
GEO, HTTP, TLS, TCP, IPNET = (
    STORY["geo"],
    STORY["http"],
    STORY["tls"],
    STORY["tcp"],
    STORY["ip"],
)
KERNEL, LEDGER, GATEWAY = STORY["kernel"], STORY["ledger"], STORY["gateway"]
RTT = GEO[
    "round_trip_ms"
]  # the film's unit of time: Paris - Singapore and back, in glass
ONE_WAY = RTT / 2

# ---- colour: one hue per layer (validated as a set, dark surface) ------------- #
IP_C = "#30A46E"  # the network: packets, best effort
TCP_C = "#508FF9"  # the reliable stream
TLS_C = "#C170BB"  # the sealed stream
HTTP_C = "#E26E1A"  # the conversation
LAYERS = (("IP", IP_C), ("TCP", TCP_C), ("TLS", TLS_C), ("HTTP", HTTP_C))
HERO_C = GOLD  # the one to look at
LOST_C = BAD
OK_C = GOOD
STEEL = "#9AA5BD"  # devices, wires
HOST = "api.dispatch.example"
SERVER_IP, PHONE_IP = (
    "203.0.113.24",
    "198.51.100.7",
)  # documentation addresses (RFC 5737)


def rgb(color):
    """A colour as three floats in 0..1."""
    return tuple(float(c) for c in ManimColor(color).to_rgb())


def ink(ctx, color, a=1.0):
    """Set Cairo's colour. Manim's frame is BGRA to Cairo: swap red and blue."""
    r, g, b = color if isinstance(color, tuple) else rgb(color)
    ctx.set_source_rgba(b, g, r, a)


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    """Smooth 0..1."""
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------- #
# devices
# --------------------------------------------------------------------------- #
def phone_icon(h=0.9, color=STEEL):
    w = h * 0.54
    body = RoundedRectangle(width=w, height=h, corner_radius=0.16 * w)
    body.set_stroke(color, width=2.6).set_fill(PANEL, opacity=1)
    screen = RoundedRectangle(width=w * 0.76, height=h * 0.70, corner_radius=0.05 * w)
    screen.set_stroke(width=0).set_fill(mix(PANEL, color, 0.22), opacity=1).move_to(
        body
    ).shift(UP * h * 0.045)
    bar = Line(LEFT * w * 0.16, RIGHT * w * 0.16).set_stroke(color, width=2.2)
    bar.move_to(body.get_bottom() + UP * h * 0.065)
    g = VGroup(body, screen, bar)
    g.body, g.screen = body, screen
    return g


def server_icon(h=0.9, color=STEEL, units=3, led=OK_C):
    w = h * 0.86
    body = RoundedRectangle(width=w, height=h, corner_radius=0.09 * w)
    body.set_stroke(color, width=2.6).set_fill(PANEL, opacity=1)
    g = VGroup(body)
    g.leds = VGroup()
    uh = h * 0.74 / units
    for k in range(units):
        y = body.get_top()[1] - h * 0.13 - uh * (k + 0.5)
        slot = RoundedRectangle(width=w * 0.78, height=uh * 0.62, corner_radius=0.03)
        slot.set_stroke(width=0).set_fill(mix(PANEL, color, 0.22), opacity=1).move_to(
            [body.get_x(), y, 0]
        )
        dot = Dot(radius=0.032 * h / 0.9, color=led).move_to(
            slot.get_left() + RIGHT * 0.1 * h / 0.9
        )
        g.add(slot, dot)
        g.leds.add(dot)
    g.body = body
    return g


def router_icon(r=0.17, color=IP_C):
    ring = Circle(
        radius=r, stroke_color=color, stroke_width=2.6, fill_color=PANEL, fill_opacity=1
    )
    core = Dot(radius=r * 0.34, color=color)
    return VGroup(ring, core)


def database_icon(h=0.9, color=STEEL):
    w = h * 0.82
    e = 0.2 * h
    top = Ellipse(
        width=w,
        height=e,
        stroke_color=color,
        stroke_width=2.6,
        fill_color=mix(PANEL, color, 0.22),
        fill_opacity=1,
    )
    top.move_to([0, h / 2 - e / 2, 0])
    left = Line([-w / 2, h / 2 - e / 2, 0], [-w / 2, -h / 2 + e / 2, 0]).set_stroke(
        color, width=2.6
    )
    right = left.copy().shift(RIGHT * w)
    bottom = ArcBetweenPoints(
        [-w / 2, -h / 2 + e / 2, 0], [w / 2, -h / 2 + e / 2, 0], angle=PI * 0.42
    )
    bottom.set_stroke(color, width=2.6)
    mid = ArcBetweenPoints(
        [-w / 2, 0.02 * h, 0], [w / 2, 0.02 * h, 0], angle=PI * 0.42
    ).set_stroke(color, width=1.8, opacity=0.6)
    fill = Rectangle(
        width=w, height=h - e, stroke_width=0, fill_color=PANEL, fill_opacity=1
    )
    g = VGroup(fill, left, right, bottom, mid, top)
    g.body = fill
    return g


def eye_icon(w=0.62, color=LOST_C):
    """Someone on the path, looking."""
    a, b = np.array([-w / 2, 0, 0]), np.array([w / 2, 0, 0])
    lids = VGroup(
        ArcBetweenPoints(a, b, angle=-PI * 0.55).set_stroke(color, width=3),
        ArcBetweenPoints(a, b, angle=PI * 0.55).set_stroke(color, width=3),
    )
    iris = Circle(
        radius=w * 0.15,
        stroke_color=color,
        stroke_width=3,
        fill_color=color,
        fill_opacity=0.9,
    )
    return VGroup(lids, iris)


def lock_icon(h=0.34, color=TLS_C, shut=True):
    w = h * 0.78
    body = RoundedRectangle(width=w, height=h * 0.58, corner_radius=0.05)
    body.set_stroke(color, width=2.4).set_fill(color, opacity=0.9 if shut else 0.2)
    arc = Arc(
        radius=w * 0.3, start_angle=0, angle=PI, stroke_color=color, stroke_width=2.6
    )
    arc.move_to(body.get_top() + UP * w * 0.3 * 0.5)
    legs = VGroup(
        Line(arc.get_start(), arc.get_start() + DOWN * w * 0.14),
        Line(arc.get_end(), arc.get_end() + DOWN * w * 0.14),
    ).set_stroke(color, width=2.6)
    g = VGroup(arc, legs, body)
    if not shut:
        VGroup(arc, legs).shift(UP * h * 0.12 + LEFT * 0)
    return g


def key_icon(w=0.62, color=TLS_C):
    """A private key: it stays on the machine that owns it."""
    r = w * 0.2
    ring = Circle(
        radius=r, stroke_color=color, stroke_width=3.4, fill_opacity=0
    ).move_to([-w / 2 + r, 0, 0])
    shaft = Line([-w / 2 + 2 * r, 0, 0], [w / 2, 0, 0])
    teeth = [
        Line([w / 2 - k * w, 0, 0], [w / 2 - k * w, -h * w, 0])
        for k, h in ((0.05, 0.2), (0.22, 0.15))
    ]
    return VGroup(ring, VGroup(shaft, *teeth).set_stroke(color, width=3.4))


def signature(w=0.74, color=TLS_C):
    """A signature: only the holder of the private key can make one that checks out."""
    xs = np.linspace(0.0, 1.0, 48)
    pts = [
        [(x - 0.5) * w, 0.13 * w * math.sin(x * 4.5 * math.pi) * (1 - 0.6 * x), 0]
        for x in xs
    ]
    pen = VMobject().set_points_smoothly(pts).set_stroke(color, width=3.2)
    box = RoundedRectangle(width=w + 0.3, height=0.44, corner_radius=0.08)
    box.set_stroke(color, width=2.2).set_fill(BG, opacity=1)
    g = VGroup(box, pen)
    g.box = box
    return g


def tag(
    text,
    color,
    fs=17,
    fill=0.92,
    tcolor=None,
    font=MONO,
    weight="BOLD",
    pad=(0.26, 0.17),
):
    """A small filled label (a flag on a packet, a port, a status code)."""
    t = line_txt(text, fs=fs, color=tcolor or BG, font=font, weight=weight)
    box = RoundedRectangle(
        width=t.body.width + pad[0], height=t.height * 0.62 + pad[1], corner_radius=0.07
    )
    box.set_stroke(color, width=0).set_fill(color, opacity=fill)
    t.move_to(box)
    g = VGroup(box, t)
    g.box, g.label = box, t
    return g


def label(text, fs=18, color=MUTED, **kw):
    return line_txt(text, fs=fs, color=color, **kw)


def mini_stack(lit=None, with_tls=True, s=1.0):
    """The film's compass, top right: the layers as four small sheets; ``lit`` is the
    one this scene is about."""
    g = VGroup()
    names = [n for n, _ in LAYERS if with_tls or n != "TLS"]
    for k, name in enumerate(names):
        color = dict(LAYERS)[name]
        on = (
            lit is None
            or name == lit
            or (isinstance(lit, (tuple, list)) and name in lit)
        )
        sheet = Polygon(
            [-0.34, 0, 0], [0.16, 0, 0], [0.34, 0.13, 0], [-0.16, 0.13, 0],
            stroke_color=color, stroke_width=2.0 if on else 1.4,
            fill_color=color, fill_opacity=0.85 if on else 0.10,
        )  # fmt: skip
        sheet.set_stroke(opacity=1.0 if on else 0.45)
        sheet.shift(UP * 0.15 * k)
        g.add(sheet)
    g.scale(s)
    g.names = names
    return g


# --------------------------------------------------------------------------- #
# the picture that crosses the network
# --------------------------------------------------------------------------- #
def load_ppm(path=HERE / "assets" / "course_map.ppm"):
    raw = Path(path).read_bytes()
    magic, size, depth, body = raw.split(b"\n", 3)
    w, h = map(int, size.split())
    assert magic == b"P6" and depth == b"255" and len(body) == w * h * 3
    return np.frombuffer(body, dtype=np.uint8).reshape(h, w, 3)


class Frame(Shared):
    """The picture as the wire sees it: which segment carries which pixel."""

    def __init__(self):
        self.rgb = load_ppm()
        self.h, self.w = self.rgb.shape[:2]
        f = TCP["transfer"]["facts"]
        self.mss, self.n = f["mss"], f["segments"]
        off = TCP["picture"][
            "offset"
        ]  # the HTTP head and the file's own header come first
        p = np.arange(self.w * self.h).reshape(self.h, self.w)
        self.first = (
            off + 3 * p
        ) // self.mss  # the segment of a pixel's first byte ...
        self.last = (off + 3 * p + 2) // self.mss  # ... and of its last
        assert self.last.max() == self.n - 1
        # a packet's colour: the mean of the pixels it carries, lifted to read on a dark wire
        sums = np.zeros((self.n, 3))
        np.add.at(sums, self.first.ravel(), self.rgb.reshape(-1, 3).astype(float))
        count = np.maximum(1, np.bincount(self.first.ravel(), minlength=self.n))[
            :, None
        ]
        mean = sums / count / 255
        self.tint = np.clip(mean * 1.35 + 0.16, 0, 1)
        self.tint[0] = self.tint[1]
        # rows a segment touches (for marks beside the picture)
        rows = np.arange(self.h)[:, None] * np.ones((1, self.w), dtype=int)
        self.row0 = np.array(
            [
                rows[self.first == i].min() if (self.first == i).any() else 0
                for i in range(self.n)
            ]
        )
        self.row1 = np.array(
            [
                rows[self.last == i].max() if (self.last == i).any() else 0
                for i in range(self.n)
            ]
        )


_FRAME = None


def frame_data() -> Frame:
    global _FRAME
    if _FRAME is None:
        _FRAME = Frame()
    return _FRAME


class Picture(Layer):
    """The map, as far as it has travelled.

    ``seen[i]``      segment ``i`` has arrived (its pixels show);
    ``upto``         segments below this index have been handed to the application:
                     what is ``seen`` beyond a hole waits, veiled (``None``: no such
                     distinction, everything seen shows plainly);
    ``flight``       (a, b): the sender's segments in flight, bracketed; ``b`` onward
                     is not sent yet and stays dim;
    ``marks``        segments to flag in red beside the picture (lost);
    ``reveal``       0..1, how much of the untouched picture shows (the sender's copy
                     arriving on screen).
    ``drive``        called before each paint to set the above from a clock.
    """

    HOLD = (0.082, 0.102, 0.137)  # not there yet

    def __init__(self, at, w=5.0, title=None, drive=None, border=STEEL):
        super().__init__()
        self.data = frame_data()
        self.at, self.w = np.array([at[0], at[1], 0.0]), float(w)
        self.h = self.w * self.data.h / self.data.w
        n = self.data.n
        self.seen = np.zeros(n, dtype=bool)
        self.upto, self.flight, self.marks, self.reveal = None, None, (), 0.0
        self.cursor = False  # draw the "delivered up to here" line
        self.slices = 0.0  # 0..1: show the cuts between segments
        self.scan = (
            None  # 0..1: a bright line sweeping down the picture ("this byte, now")
        )
        self.flag = 1.0  # opacity of the red marks (pulsed while they are talked about)
        self.drive, self.border = drive, border
        self.set_z_index(1)

    # geometry ----------------------------------------------------------------
    def left(self):
        return self.at[0] - self.w / 2

    def right(self):
        return self.at[0] + self.w / 2

    def top(self):
        return self.at[1] + self.h / 2

    def bottom(self):
        return self.at[1] - self.h / 2

    def row_y(self, row):
        """Frame y of the top edge of pixel row ``row``."""
        return self.top() - self.h * row / self.data.h

    def seg_y(self, i):
        """Frame y of the middle of segment ``i``'s band."""
        d = self.data
        i = int(min(max(i, 0), d.n - 1))
        return (self.row_y(d.row0[i]) + self.row_y(d.row1[i] + 1)) / 2

    def edge_y(self, k):
        """Frame y where segment ``k`` starts (the line between delivered and not)."""
        d = self.data
        if k >= d.n:
            return self.bottom()
        return self.row_y(d.row0[int(max(k, 0))])

    # paint ---------------------------------------------------------------------
    def paint(self, camera, pixels):
        if self.drive is not None:
            self.drive(self)
        a = float(self.alpha)
        if a <= 0.003:
            return
        d = self.data
        base = d.rgb.astype(np.float32) / 255
        seen_px = self.seen[d.first] & self.seen[d.last]
        out = np.empty_like(base)
        out[:] = self.HOLD
        if self.reveal > 0:  # the sender's own copy: all there, parts of it dimmed
            out[:] = base
            if self.flight is not None:
                a0, b0 = self.flight
                out[d.first >= b0] *= 0.30  # not sent yet
            out = out * self.reveal + np.array(self.HOLD, dtype=np.float32) * (
                1 - self.reveal
            )
        else:
            if self.upto is None:
                out[seen_px] = base[seen_px]
            else:
                ok = seen_px & (d.last < self.upto)
                wait = seen_px & ~ok
                out[ok] = base[ok]
                veil = np.array(rgb(TCP_C), dtype=np.float32)
                out[wait] = base[wait] * 0.34 + veil * 0.20
        (x0, y0), (x1, y1) = camera.to_pixels(
            np.array([[self.left(), self.top(), 0], [self.right(), self.bottom(), 0]])
        )
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        pw, ph = x1 - x0, y1 - y0
        yi = np.arange(ph) * d.h // ph
        xi = np.arange(pw) * d.w // pw
        big = (out[yi][:, xi] * 255).astype(np.float32)
        view = pixels[y0:y1, x0:x1, :3]
        if a >= 0.999:
            view[:] = big.astype(np.uint8)
        else:
            view[:] = (big * a + view.astype(np.float32) * (1 - a)).astype(np.uint8)

        ctx = camera.get_cairo_context(pixels)
        import cairo

        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        if self.slices > 0:  # where one segment ends and the next begins
            ink(ctx, BG, 0.85 * a * self.slices)
            ctx.set_line_width(0.012)
            for i in range(1, d.n):
                y = self.row_y(d.row0[i])
                ctx.move_to(self.left(), y)
                ctx.line_to(self.right(), y)
            ctx.stroke()
        # the sender's window: a bracket over what is in flight
        if self.reveal > 0 and self.flight is not None:
            a0, b0 = self.flight
            if b0 > a0:
                ya, yb = self.edge_y(a0), self.edge_y(b0)
                ink(ctx, TCP_C, 0.16 * a)
                ctx.rectangle(self.left(), yb, self.w, ya - yb)
                ctx.fill()
                ink(ctx, TCP_C, a)
                ctx.set_line_width(0.045)
                x = self.left() - 0.12
                ctx.move_to(x + 0.1, ya)
                ctx.line_to(x, ya)
                ctx.line_to(x, yb)
                ctx.line_to(x + 0.1, yb)
                ctx.stroke()
        # lost segments, flagged
        for i in self.marks:
            ya, yb = self.row_y(d.row0[i]), self.row_y(d.row1[i] + 1)
            ink(ctx, LOST_C, 0.95 * a * self.flag)
            ctx.rectangle(
                self.left(), min(ya, yb) - 0.006, self.w, abs(ya - yb) + 0.012
            )
            ctx.fill()
        if self.scan is not None and 0.0 < self.scan < 1.0:
            y = self.top() - self.h * self.scan
            ink(ctx, INK, 0.16 * a)
            ctx.rectangle(self.left(), y, self.w, min(0.36, self.top() - y))
            ctx.fill()
            ink(ctx, INK, 0.95 * a)
            ctx.set_line_width(0.03)
            ctx.move_to(self.left(), y)
            ctx.line_to(self.right(), y)
            ctx.stroke()
        # delivered up to here
        if self.cursor and self.upto is not None and 0 < self.upto < d.n:
            y = self.edge_y(self.upto)
            ink(ctx, INK, 0.95 * a)
            ctx.set_line_width(0.028)
            ctx.move_to(self.left() - 0.02, y)
            ctx.line_to(self.right() + 0.14, y)
            ctx.stroke()
        # frame
        ink(ctx, self.border, 0.9 * a)
        ctx.set_line_width(0.022)
        ctx.rectangle(self.left(), self.bottom(), self.w, self.h)
        ctx.stroke()


# --------------------------------------------------------------------------- #
# a transfer as a function of time
# --------------------------------------------------------------------------- #
class Transfer(Shared):
    """The TCP model's run, indexed for "what is true at time t"."""

    def __init__(self, run=None):
        run = run or TCP["transfer"]
        self.facts = run["facts"]
        self.data, self.acks, self.window = run["data"], run["acks"], run["window"]
        n, mss = self.facts["segments"], self.facts["mss"]
        self.n, self.mss = n, mss
        inf = float("inf")
        self.arrive = np.full(n, inf)
        for r in self.data:
            if r["t1"] is not None:
                self.arrive[r["i"]] = min(self.arrive[r["i"]], r["t1"])
        got = sorted(
            (r["t1"], math.ceil(r["delivered_to"] / mss))
            for r in self.data
            if r["t1"] is not None
        )
        self.deliv_t = np.array([g[0] for g in got])
        self.deliv_k = np.maximum.accumulate(np.array([g[1] for g in got]))
        self.win_t = np.array([w["t"] for w in self.window])
        self.win_cwnd = np.array(
            [w["shown"] for w in self.window]
        )  # see tcpsim: not the inflated cwnd
        # (ceil: the last segment is short, and counts as acknowledged once its bytes are)
        self.win_una = np.array([math.ceil(w["una"] / mss) for w in self.window])
        self.win_nxt = np.array([math.ceil(w["nxt"] / mss) for w in self.window])
        self.lost = [r for r in self.data if r["lost"]]
        self.resent = [r for r in self.data if r["again"]]
        again = {r["i"]: r for r in self.resent}
        # a hole shows at the receiver from the arrival of the segment after it until
        # the resend lands; on the wire, the spot of the drop stays marked until the
        # resend passes it
        self.holes = [
            (r["i"], float(self.arrive[r["i"] + 1]), float(self.arrive[r["i"]]))
            for r in self.lost
        ]
        self.mended = {i: r["t0"] + Wire.DROP * ONE_WAY for i, r in again.items()}
        self.end = max(a["t1"] for a in self.acks)

    def delivered(self, t):
        k = int(np.searchsorted(self.deliv_t, t, side="right"))
        return int(self.deliv_k[k - 1]) if k else 0

    def sender(self, t):
        k = max(0, int(np.searchsorted(self.win_t, t, side="right")) - 1)
        return int(self.win_una[k]), int(self.win_nxt[k]), float(self.win_cwnd[k])

    def acked_bytes(self, t):
        best = 0
        for a in self.acks:
            if a["t0"] <= t:
                best = max(best, a["ack"])
            else:
                break
        return best


def receiver_drive(clock, tr, t_off=0.0):
    def drive(pic):
        t = clock.t - t_off
        pic.seen = tr.arrive <= t
        pic.upto = tr.delivered(t)
        pic.marks = tuple(i for i, a, b in tr.holes if a <= t < b)

    return drive


def sender_drive(clock, tr, t_off=0.0):
    def drive(pic):
        una, nxt, _ = tr.sender(clock.t - t_off)
        pic.flight = (una, nxt)

    return drive


class Wire(Layer):
    """Two lanes between the server (right) and the phone (left): data travels one
    way, acknowledgments the other. Every glyph sits where the clock puts it."""

    DROP = 0.56  # how far along the wire a lost packet gets

    def __init__(self, clock, tr, x_phone, x_server, y, t_off=0.0, lane=0.17):
        super().__init__()
        self.clock, self.tr, self.t_off = clock, tr, t_off
        self.xp, self.xs, self.y, self.lane = x_phone, x_server, y, lane
        self.tint = frame_data().tint
        self.show_acks, self.rails = 1.0, 1.0
        self.set_z_index(3)

    def x_data(self, f):
        return lerp(self.xs, self.xp, f)

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        t = self.clock.t - self.t_off
        yd, ya = self.y + self.lane, self.y - self.lane
        if self.rails > 0:
            for y in (yd, ya):
                ink(ctx, FAINT, 0.9 * a * self.rails)
                ctx.set_line_width(0.018)
                ctx.move_to(self.xp, y)
                ctx.line_to(self.xs, y)
                ctx.stroke()
        d = ONE_WAY
        w, h = 0.078, 0.25
        drops = []
        for r in self.tr.data:
            if r["t0"] > t:
                break
            if r["lost"]:
                f = (t - r["t0"]) / d
                if f <= self.DROP:
                    self._packet(ctx, self.x_data(f), yd, w, h, self.tint[r["i"]], a)
                else:
                    drops.append((r, f))
                continue
            if t >= r["t1"]:
                continue
            f = (t - r["t0"]) / d
            if r["again"]:
                x = self.x_data(f)
                ink(ctx, HERO_C, 0.22 * a)
                self._rr(ctx, x - 0.13, yd - 0.22, 0.26, 0.44, 0.06)
                ctx.fill()
                self._packet(ctx, x, yd, 0.11, 0.31, rgb(HERO_C), a, edge=INK)
            else:
                self._packet(ctx, self.x_data(f), yd, w, h, self.tint[r["i"]], a)
        if self.show_acks > 0:
            for k in self.tr.acks:
                if k["t0"] > t:
                    break
                if t >= k["t1"]:
                    continue
                f = (t - k["t0"]) / d
                x = lerp(self.xp, self.xs, f)
                ink(ctx, HERO_C if k["dup"] else TCP_C, a * self.show_acks)
                self._rr(ctx, x - 0.02, ya - 0.085, 0.04, 0.17, 0.012)
                ctx.fill()
        for (
            r,
            f,
        ) in drops:  # a lost packet falls off the wire, a ring bursts, a cross stays
            x = self.x_data(self.DROP)
            g = (f - self.DROP) / 0.28
            if g < 1:
                ink(ctx, LOST_C, a * (1 - g * g))
                self._rr(ctx, x - 0.07, yd - 0.2 - 1.0 * g * g, 0.14, 0.4, 0.03)
                ctx.fill()
                b = min(1.0, g / 0.5)
                ink(ctx, LOST_C, a * (1 - b))
                ctx.set_line_width(0.05)
                ctx.arc(x, yd, 0.16 + 0.55 * b, 0, math.tau)
                ctx.stroke()
            mended = self.tr.mended.get(r["i"])
            keep = 1.0 if mended is None else 1 - ease((t - mended) / 8.0)
            if keep > 0:
                ink(ctx, LOST_C, a * keep)
                ctx.set_line_width(0.055)
                for sx in (1, -1):
                    ctx.move_to(x - 0.11, yd - 0.11 * sx)
                    ctx.line_to(x + 0.11, yd + 0.11 * sx)
                    ctx.stroke()

    @staticmethod
    def _rr(ctx, x, y, w, h, r):
        ctx.new_sub_path()
        ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
        ctx.close_path()

    def _packet(self, ctx, x, y, w, h, color, a, edge=None):
        ink(ctx, tuple(color), a)
        self._rr(ctx, x - w / 2, y - h / 2, w, h, 0.02)
        ctx.fill()
        if edge is not None:
            ink(ctx, edge, a)
            ctx.set_line_width(0.018)
            self._rr(ctx, x - w / 2, y - h / 2, w, h, 0.02)
            ctx.stroke()


class WindowChart(Layer):
    """The sender's window over time, drawn as the clock runs: the staircase of slow
    start, then the cut after a loss."""

    def __init__(self, clock, tr, at, w=2.5, h=1.5, t_off=0.0, t_max=None, y_max=110):
        super().__init__()
        self.clock, self.tr, self.t_off = clock, tr, t_off
        self.at, self.w, self.h = np.array([at[0], at[1], 0.0]), w, h
        self.t_max = t_max or tr.end
        self.y_max = y_max
        self.set_z_index(3)

    def p(self, t, v):
        return (
            self.at[0] - self.w / 2 + self.w * min(1.0, max(0.0, t / self.t_max)),
            self.at[1] - self.h / 2 + self.h * min(1.0, v / self.y_max),
        )

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        import cairo

        ctx = camera.get_cairo_context(pixels)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        x0, y0 = self.at[0] - self.w / 2, self.at[1] - self.h / 2
        ink(ctx, FAINT, a)
        ctx.set_line_width(0.02)
        ctx.move_to(x0, y0 + self.h)
        ctx.line_to(x0, y0)
        ctx.line_to(x0 + self.w, y0)
        ctx.stroke()
        t = self.clock.t - self.t_off
        k = int(np.searchsorted(self.tr.win_t, t, side="right"))
        if k < 1:
            return
        ts, vs = self.tr.win_t[:k], self.tr.win_cwnd[:k]
        pts = [self.p(ts[0], vs[0])]
        for i in range(1, k):  # a window holds its value until the next change
            pts.append(self.p(ts[i], vs[i - 1]))
            pts.append(self.p(ts[i], vs[i]))
        pts.append(self.p(t, vs[-1]))
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        ctx.line_to(pts[-1][0], y0)
        ctx.line_to(pts[0][0], y0)
        ctx.close_path()
        ink(ctx, TCP_C, 0.20 * a)
        ctx.fill()
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        ink(ctx, TCP_C, a)
        ctx.set_line_width(0.04)
        ctx.stroke()
        ink(ctx, INK, a)
        ctx.arc(pts[-1][0], pts[-1][1], 0.055, 0, math.tau)
        ctx.fill()


# --------------------------------------------------------------------------- #
# the network alone: routers, roads, a queue that overflows
# --------------------------------------------------------------------------- #
class Roads(Shared):
    """The best-effort run, indexed by time."""

    def __init__(self, run=None):
        run = run or IPNET
        self.facts, self.packets = run["facts"], run["packets"]
        self.n = len(self.packets)
        inf = float("inf")
        self.arrive = np.array(
            [pk["hops"][-1][1] if pk["lost_at"] is None else inf for pk in self.packets]
        )
        self.lost = [pk["i"] for pk in self.packets if pk["lost_at"]]
        self.end = float(np.max(self.arrive[np.isfinite(self.arrive)]))
        self.edges = sorted(
            {
                (a[0], b[0])
                for pk in self.packets
                for a, b in zip(pk["hops"], pk["hops"][1:], strict=False)
            }
        )
        self.slow = self.facts["slow_router"]

    def arrived(self, t):
        return int(np.sum(self.arrive <= t))


class Mesh(Layer):
    """Packets on their roads. ``edges`` (0..1) draws the roads in."""

    def __init__(self, clock, roads, nodes, t_off=0.0):
        super().__init__()
        self.clock, self.roads, self.t_off = clock, roads, t_off
        self.nodes = {k: np.array([v[0], v[1]], dtype=float) for k, v in nodes.items()}
        self.tint = frame_data().tint
        self.edges = 1.0
        self.set_z_index(2)

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        P, t = self.nodes, self.clock.t - self.t_off
        if self.edges > 0:
            ink(ctx, IP_C, 0.34 * a * self.edges)
            ctx.set_line_width(0.022)
            for u, v in self.roads.edges:
                ctx.move_to(*P[u])
                ctx.line_to(*P[v])
                ctx.stroke()
        s = 0.105
        waiting = []
        for pk in self.roads.packets:
            hops = pk["hops"]
            if t < hops[0][2]:
                continue
            pos = None
            for k in range(len(hops) - 1):
                (u, _, dep), (v, arr, dep2) = hops[k], hops[k + 1]
                if dep <= t < arr:
                    pos = lerp(P[u], P[v], (t - dep) / (arr - dep))
                    break
                if arr <= t < dep2:
                    if v == self.roads.slow:
                        waiting.append((dep2, pk["i"]))
                    else:
                        pos = P[v]
                    break
            if pos is None and pk["lost_at"] and t >= hops[-1][1]:
                g = (t - hops[-1][1]) / 16.0  # it falls out of the full queue
                if g < 1:
                    q = P[pk["lost_at"]] + np.array([0.26, -0.12 - 0.55 * g * g])
                    ink(ctx, LOST_C, a * (1 - g * g))
                    Wire._rr(ctx, q[0] - s / 2, q[1] - s / 2, s, s, 0.02)
                    ctx.fill()
                continue
            if pos is not None:
                ink(ctx, tuple(self.tint[pk["i"]]), a)
                Wire._rr(ctx, pos[0] - s / 2, pos[1] - s / 2, s, s, 0.022)
                ctx.fill()
        # the queue of the slow router: who leaves next stands closest
        for rank, (_, i) in enumerate(sorted(waiting)):
            q = P[self.roads.slow] + np.array([0.27 + 0.135 * rank, 0.0])
            ink(ctx, tuple(self.tint[i]), a)
            Wire._rr(ctx, q[0] - s / 2, q[1] - s / 2, s, s, 0.022)
            ctx.fill()
            ink(ctx, HERO_C, 0.9 * a)
            ctx.set_line_width(0.014)
            Wire._rr(ctx, q[0] - s / 2, q[1] - s / 2, s, s, 0.022)
            ctx.stroke()


def roads_drive(clock, roads, t_off=0.0):
    def drive(pic):
        pic.seen = roads.arrive <= clock.t - t_off

    return drive


def packet_card(i=0, w=2.5):
    """One packet, opened: where it goes, and the bytes it carries."""
    d = frame_data()
    strip = d.rgb[d.row0[i] : d.row1[i] + 1]
    head = RoundedRectangle(width=w, height=0.5, corner_radius=0.07)
    head.set_stroke(IP_C, width=2).set_fill(IP_C, opacity=0.9)
    to = line_txt("to " + PHONE_IP, fs=17, color=BG, font=MONO, weight="BOLD").move_to(
        head
    )
    body = (
        Rectangle(width=w, height=0.62)
        .set_stroke(IP_C, width=2)
        .set_fill(PANEL, opacity=1)
    )
    body.next_to(head, DOWN, buff=0)
    img = ImageMobject(np.repeat(np.repeat(strip, 12, axis=0), 4, axis=1))
    img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    img.stretch_to_fit_width(w - 0.24).stretch_to_fit_height(0.34).move_to(body)
    g = Group(head, to, body, img)
    g.head, g.body, g.img = head, body, img
    return g


# --------------------------------------------------------------------------- #
# space and time: who sent what, when
# --------------------------------------------------------------------------- #
class Ladder(Layer):
    """A sequence diagram that draws itself: two lifelines, time running down, and
    one trace per packet, as long as the packet has travelled.

    ``events``: dicts with ``t0``, ``t1`` (clock units), ``xa``, ``xb`` (frame x of
    the two ends), ``color``; ``stop`` marks a packet that dies at ``xb`` (a cross
    instead of an arrow head). ``rate`` is frame units per clock unit.
    """

    def __init__(self, clock, events, x0, x1, y0, rate, y_min=-3.1, wall=None):
        super().__init__()
        self.clock, self.events = clock, events
        # (``scale`` is Manim's: an attribute of that name breaks every fade)
        self.x0, self.x1, self.y0, self.rate, self.y_min = x0, x1, y0, rate, y_min
        self.wall = wall  # x of a third, dashed lifeline (something on the path)
        self.rails = 1.0
        self.set_z_index(2)

    def y(self, t):
        return self.y0 - t * self.rate

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        import cairo

        ctx = camera.get_cairo_context(pixels)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        if self.rails > 0:
            ink(ctx, FAINT, a * self.rails)
            ctx.set_line_width(0.022)
            for x in (self.x0, self.x1):
                ctx.move_to(x, self.y0 + 0.12)
                ctx.line_to(x, self.y_min)
                ctx.stroke()
            if self.wall is not None:
                ink(ctx, LOST_C, 0.55 * a * self.rails)
                ctx.set_dash([0.09, 0.09])
                ctx.move_to(self.wall, self.y0 + 0.12)
                ctx.line_to(self.wall, self.y_min)
                ctx.stroke()
                ctx.set_dash([])
        now = self.clock.t
        for e in self.events:
            if now < e["t0"]:
                continue
            span = max(e["t1"] - e["t0"], 1e-9)
            f = min(1.0, (now - e["t0"]) / span)
            if e.get("grow"):  # an instant packet, drawn over ``grow`` clock units
                f = min(1.0, (now - e["t0"]) / e["grow"])
            xa, ya = e["xa"], self.y(e["t0"])
            xb, yb = lerp(e["xa"], e["xb"], f), self.y(lerp(e["t0"], e["t1"], f))
            if ya < self.y_min:
                continue
            ink(ctx, e["color"], a)
            ctx.set_line_width(e.get("lw", 0.05))
            ctx.move_to(xa, ya)
            ctx.line_to(xb, yb)
            ctx.stroke()
            ux, uy = xb - xa, yb - ya
            n = math.hypot(ux, uy) or 1.0
            ux, uy = ux / n, uy / n
            if e.get("stop") and f >= 1.0:  # it died here
                ink(ctx, LOST_C, a)
                ctx.set_line_width(0.05)
                r = 0.085
                for sx in (1, -1):
                    ctx.move_to(xb - r, yb - r * sx)
                    ctx.line_to(xb + r, yb + r * sx)
                    ctx.stroke()
            else:
                h = 0.17
                ctx.move_to(xb, yb)
                ctx.line_to(xb - ux * h - uy * h * 0.5, yb - uy * h + ux * h * 0.5)
                ctx.line_to(xb - ux * h + uy * h * 0.5, yb - uy * h - ux * h * 0.5)
                ctx.close_path()
                ctx.fill()


def ride(mob, clock, t0, t1, xa, xb, y, park=60.0):
    """Keep ``mob`` on the wire: at ``xa`` when the clock reads ``t0``, at ``xb`` at
    ``t1``, out of the frame the rest of the time."""

    def place(m):
        t = clock.t
        if t0 <= t < t1:
            m.move_to([lerp(xa, xb, (t - t0) / (t1 - t0)), y, 0])
        else:
            m.move_to([0, park, 0])

    mob.add_updater(place)
    place(mob)
    return mob


def wall_icon(w=0.5, h=0.62, color=LOST_C):
    """Something on the path that lets nothing through."""
    g = VGroup()
    rows, bh = 4, h / 4
    for r in range(rows):
        y = h / 2 - bh * (r + 0.5)
        xs = [-w / 2, 0, w / 2] if r % 2 == 0 else [-w / 2, -w / 4, w / 4, w / 2]
        for a, b in zip(xs, xs[1:], strict=False):
            brick = Rectangle(width=b - a, height=bh).move_to([(a + b) / 2, y, 0])
            brick.set_stroke(BG, width=2).set_fill(color, opacity=0.9)
            g.add(brick)
    return g


def port_tag(number, open_=False, fs=15):
    """A numbered door on a server: lit when a program listens behind it."""
    t = tag(
        str(number),
        TCP_C if open_ else FAINT,
        fs=fs,
        fill=0.92 if open_ else 0.0,
        tcolor=BG if open_ else MUTED,
    )
    if not open_:
        t.box.set_stroke(FAINT, width=2)
    return t


def error_chip(text, fs=17, color=LOST_C, w=None):
    """A real error message, as the program prints it (a string, or several lines)."""
    lines = [text] if isinstance(text, str) else list(text)
    rows = VGroup(
        *[line_txt(t, fs=fs, color=color, font=MONO, weight="MEDIUM") for t in lines]
    )
    rows.arrange(DOWN, buff=0.0, aligned_edge=LEFT)
    width = max(r.body.width for r in rows)
    box = RoundedRectangle(
        width=(w or width + 0.5), height=rows.height + 0.2, corner_radius=0.09
    )
    box.set_stroke(color, width=2).set_fill(CODE_BG, opacity=0.96)
    rows.move_to(box)
    g = VGroup(box, rows)
    g.box, g.label = box, rows
    return g


class Timeline(Layer):
    """Seconds on a line: a tick each time something happened, and a playhead."""

    def __init__(self, clock, marks, x0, x1, y, t_max):
        super().__init__()
        self.clock, self.marks = clock, list(marks)
        self.x0, self.x1, self.y, self.t_max = x0, x1, y, t_max
        self.set_z_index(2)

    def x(self, t):
        return lerp(self.x0, self.x1, min(1.0, max(0.0, t / self.t_max)))

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        import cairo

        ctx = camera.get_cairo_context(pixels)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ink(ctx, FAINT, a)
        ctx.set_line_width(0.026)
        ctx.move_to(self.x0, self.y)
        ctx.line_to(self.x1, self.y)
        ctx.stroke()
        t = self.clock.t
        for s in self.marks:
            if t < s:
                continue
            g = ease((t - s) / 0.5)
            x = self.x(s)
            ink(ctx, TCP_C, a)
            ctx.set_line_width(0.05)
            ctx.move_to(x, self.y)
            ctx.line_to(x, self.y + 0.5 * g)
            ctx.stroke()
            if g >= 1:
                ink(ctx, LOST_C, a)
                ctx.set_line_width(0.04)
                r, yc = 0.047, self.y + 0.5 + 0.12
                for sx in (1, -1):
                    ctx.move_to(x - r, yc - r * sx)
                    ctx.line_to(x + r, yc + r * sx)
                    ctx.stroke()
        if 0 <= t:
            x = self.x(t)
            done = t >= self.t_max
            ink(ctx, LOST_C if done else INK, a)
            ctx.set_line_width(0.05 if done else 0.026)
            ctx.move_to(x, self.y - 0.14)
            ctx.line_to(x, self.y + (0.86 if done else 0.78))
            ctx.stroke()


# --------------------------------------------------------------------------- #
# the conversation: a pipe, and the text that goes down it
# --------------------------------------------------------------------------- #
class Pipe(Layer):
    """The connection, as the programs see it: bytes in at one end, the same bytes
    out at the other. ``send`` queues a train of cells; the clock moves them."""

    CELL_W, CELL_H, PITCH = 0.072, 0.21, 0.118

    def __init__(self, clock, x0, x1, y, color=TCP_C, r=0.21):
        super().__init__()
        self.clock, self.x0, self.x1, self.y, self.hue, self.r = (
            clock,
            x0,
            x1,
            y,
            color,
            r,
        )
        self.flows = []
        self.glow = 0.0  # 0..1: the tube lights up (it is kept open)
        self.tap = None  # x of someone on the path: cells passed it may be altered
        self.set_z_index(3)

    def speed(self):
        return (self.x1 - self.x0) / ONE_WAY

    def send(
        self, t0, way, n, color, sealed=False, colors=None, bad=(), a=None, b=None
    ):
        """A train of ``n`` cells leaving at ``t0``. Returns when its last cell lands.
        ``a`` / ``b``: where it enters and leaves the pipe (default: the two ends)."""
        a = (self.x0 if way == ">" else self.x1) if a is None else a
        b = (self.x1 if way == ">" else self.x0) if b is None else b
        self.flows.append(
            dict(
                t0=t0,
                way=way,
                n=n,
                color=color,
                sealed=sealed,
                colors=colors,
                bad=set(bad),
                a=a,
                b=b,
            )
        )
        return t0 + (abs(b - a) + n * self.PITCH) / self.speed()

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        r = self.r
        ink(ctx, self.hue, (0.07 + 0.10 * self.glow) * a)
        Wire._rr(ctx, self.x0, self.y - r, self.x1 - self.x0, 2 * r, r)
        ctx.fill()
        ink(ctx, self.hue, (0.55 + 0.45 * self.glow) * a)
        ctx.set_line_width(0.026 + 0.014 * self.glow)
        Wire._rr(ctx, self.x0, self.y - r, self.x1 - self.x0, 2 * r, r)
        ctx.stroke()
        t, v = self.clock.t, self.speed()
        w, h, pitch = self.CELL_W, self.CELL_H, self.PITCH
        lo, hi = self.x0 + 0.09, self.x1 - 0.09
        for fl in self.flows:
            if t < fl["t0"]:
                continue
            head = v * (t - fl["t0"])  # distance travelled by the first cell
            if head - fl["n"] * pitch > abs(fl["b"] - fl["a"]):
                continue
            sgn = 1 if fl["way"] == ">" else -1
            xs = [fl["a"] + sgn * (head - k * pitch) for k in range(fl["n"])]
            x_lo, x_hi = max(lo, min(fl["a"], fl["b"])), min(hi, max(fl["a"], fl["b"]))
            vis = [(k, x) for k, x in enumerate(xs) if x_lo <= x <= x_hi]
            if not vis:
                continue
            if fl["sealed"]:  # one record: a sealed capsule around its bytes
                xa, xb = min(x for _, x in vis) - 0.085, max(x for _, x in vis) + 0.085
                ink(ctx, TLS_C, 0.22 * a)
                Wire._rr(ctx, xa, self.y - h / 2 - 0.045, xb - xa, h + 0.09, 0.06)
                ctx.fill()
                ink(ctx, TLS_C, a)
                ctx.set_line_width(0.022)
                Wire._rr(ctx, xa, self.y - h / 2 - 0.045, xb - xa, h + 0.09, 0.06)
                ctx.stroke()
            for k, x in vis:
                col = (
                    fl["colors"][k % len(fl["colors"])] if fl["colors"] else fl["color"]
                )
                if k in fl["bad"] and self.tap is not None and (x - self.tap) * sgn > 0:
                    col = LOST_C
                ink(ctx, col, a)
                Wire._rr(ctx, x - w / 2, self.y - h / 2, w, h, 0.018)
                ctx.fill()


class Card:
    """An HTTP message as it is on the wire: lines of text in a panel.

    ``rows``: strings; ``""`` is the empty line that ends the headers (drawn as a
    short rule). The parts are separate mobjects (``mobs()``), so a line can be
    swapped without Manim taking the card apart. ``sent`` (in characters) lights the
    text up as it goes down the pipe.
    """

    def __init__(
        self,
        rows,
        at,
        w=7.1,
        fs=18,
        body_fs=16,
        title="",
        pitch=0.37,
        body_rows=0,
        edge=FAINT,
    ):
        self.fs, self.body_fs, self.pitch = fs, body_fs, pitch
        x0, top = at[0] - w / 2, at[1]
        self.left = x0 + 0.3
        y = top - 0.22
        self.rows, self.ys, self.kinds = [], [], []
        n_head = len(rows) - body_rows
        for k, text in enumerate(rows):
            body = k >= n_head
            if text == "":
                y -= 0.13
                rule = Line([self.left, y, 0], [self.left + 0.42, y, 0]).set_stroke(
                    MUTED, width=2.5, opacity=0.7
                )
                self.rows.append(rule)
                self.ys.append(y)
                self.kinds.append("gap")
                y -= 0.13
                continue
            step = 0.345 if body else pitch
            y -= step / 2
            self.rows.append(self._line(text, body, y))
            self.ys.append(y)
            self.kinds.append("body" if body else "head")
            y -= step / 2
        self.bottom = y - 0.2
        self.box = RoundedRectangle(
            width=w, height=top - self.bottom, corner_radius=0.14
        )
        self.box.set_stroke(edge, width=2).set_fill(CODE_BG, opacity=1).move_to(
            [at[0], (top + self.bottom) / 2, 0]
        )
        self.title = label(title, fs=16).move_to([0, top - 0.3, 0])
        self.title.shift(RIGHT * (x0 + w - 0.28 - self.title.get_right()[0]))
        self.sent = None  # None: all lit
        self.blank = next(
            (r for r, kd in zip(self.rows, self.kinds, strict=True) if kd == "gap"),
            None,
        )

    def _line(self, text, body, y):
        m = line_txt(
            text,
            fs=self.body_fs if body else self.fs,
            font=MONO,
            color=INK,
            disable_ligatures=True,
        )
        m.shift([self.left - m.body.get_left()[0], y - m.get_center()[1], 0])
        m.string = text
        return m

    def mobs(self):
        return [self.box, self.title, *self.rows]

    def chars(self, i, a=0, b=None):
        return VGroup(*self.rows[i].body.submobjects[a:b])

    def find(self, i, token):
        a = self.rows[i].string.index(token)
        return self.chars(i, a, a + len(token))

    def mark(self, i, token=None, color=HERO_C, buff=None):
        """A box around a token of line ``i`` (or the whole line)."""
        buff = (
            (0.04 if token and self.kinds[i] == "body" else 0.07)
            if buff is None
            else buff
        )
        target = self.find(i, token) if token else self.rows[i].body
        box = SurroundingRectangle(target, buff=buff, corner_radius=0.07, color=color)
        box.set_stroke(color, width=2.5).set_fill(color, opacity=0.14)
        return box

    def refresh(self):
        if self.sent is None:
            return
        k = 0
        for row, kind in zip(self.rows, self.kinds, strict=True):
            if kind == "gap":
                row.set_stroke(opacity=0.7 if k < self.sent else 0.2)
                k += 2
                continue
            for ch in row.body.submobjects:
                ch.set_opacity(1.0 if k < self.sent else 0.22)
                k += 1
            k += 2  # the line's CR LF

    def total(self):
        return sum(
            2 if kd == "gap" else len(r.string) + 2
            for r, kd in zip(self.rows, self.kinds, strict=True)
        )

    def dim(self):
        self.sent = 0
        self.refresh()
        return self

    def swap(self, i, text):
        """Line ``i`` leaves, ``text`` arrives in its place: (old, new) to fade."""
        old = self.rows[i]
        new = self._line(text, self.kinds[i] == "body", self.ys[i])
        self.rows[i] = new
        return old, new


def phone_app(at, w=2.1, h=4.3, stops=None, earns=None):
    """Lea's screen: her map, her next stops, what the hour will pay. ``skeleton``
    holds the grey bars shown while nothing has arrived; ``real`` the content."""
    stops = stops or STORY["course"]["stops"]
    earns = STORY["course"]["earns"] if earns is None else earns
    body = (
        RoundedRectangle(width=w, height=h, corner_radius=0.24)
        .set_stroke(STEEL, width=3)
        .set_fill(PANEL, 1)
    )
    body.move_to([at[0], at[1], 0])
    notch = (
        Line(LEFT * 0.22, RIGHT * 0.22)
        .set_stroke(STEEL, width=3)
        .move_to(body.get_top() + DOWN * 0.16)
    )
    top = body.get_top()[1] - 0.36
    mw = w - 0.3
    mh = mw * 0.75
    slot = (
        Rectangle(width=mw, height=mh)
        .set_stroke(FAINT, width=1.5)
        .set_fill(mix(PANEL, STEEL, 0.12), 1)
    )
    slot.move_to([at[0], top - mh / 2, 0])
    hint = (
        VGroup(
            VMobject().set_points_as_corners(
                [
                    [-0.42, -0.2, 0],
                    [-0.12, 0.12, 0],
                    [0.08, -0.06, 0],
                    [0.2, 0.04, 0],
                    [0.42, -0.2, 0],
                ]
            ),
            Circle(radius=0.07).move_to([0.24, 0.2, 0]),
        )
        .set_stroke(mix(PANEL, STEEL, 0.4), width=2.4)
        .set_fill(opacity=0)
        .move_to(slot)
    )
    y = slot.get_bottom()[1] - 0.3
    skeleton, real, dots = VGroup(), VGroup(), VGroup()
    x0 = body.get_left()[0] + 0.24
    for k, name in enumerate(stops):
        d = Dot(radius=0.055, color=HERO_C).move_to([x0 + 0.06, y, 0])
        bar = RoundedRectangle(
            width=0.7 + 0.22 * ((k * 3) % 4), height=0.14, corner_radius=0.07
        )
        bar.set_stroke(width=0).set_fill(FAINT, 1).move_to(
            [x0 + 0.3, y, 0], aligned_edge=LEFT
        )
        t = line_txt(name, fs=17).move_to([0, y, 0])
        t.shift(RIGHT * (x0 + 0.3 - t.body.get_left()[0]))
        dots.add(d)
        skeleton.add(bar)
        real.add(t)
        y -= 0.335
    y -= 0.12
    money_bar = (
        RoundedRectangle(width=1.0, height=0.2, corner_radius=0.1)
        .set_stroke(width=0)
        .set_fill(FAINT, 1)
    )
    money_bar.move_to([at[0], y, 0])
    money = line_txt(f"€{earns:.2f}", fs=26, color=HERO_C, weight="BOLD").move_to(
        [at[0], y, 0]
    )
    g = VGroup(body, notch, slot, hint, dots)
    g.body, g.slot, g.skeleton, g.real, g.money_bar, g.money, g.dots = (
        body,
        slot,
        skeleton,
        real,
        money_bar,
        money,
        dots,
    )
    g.money_y = y
    return g


def app_map(app):
    """The course map, sized for the app's picture slot."""
    img = ImageMobject(load_ppm())
    img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["cubic"])
    img.stretch_to_fit_width(app.slot.width).stretch_to_fit_height(
        app.slot.height
    ).move_to(app.slot)
    return img


def verdict(code, color, who=None):
    """A status family and whose fault it is: nobody's, the caller's, the server's."""
    t = tag(code, color, fs=18)
    if who == "phone":
        icon = phone_icon(0.5, color)
    elif who == "server":
        icon = server_icon(0.5, color, led=color)
    else:
        icon = make_tick(color, sw=5, scale=0.9)
    icon.next_to(t, RIGHT, buff=0.16)
    g = VGroup(t, icon)
    g.code = t
    return g


def trips(colors, unit=0.5, h=0.34, gap=0.05, stacked=None):
    """Round trips as blocks: one block, one trip to the server and back."""
    g = VGroup()
    x = 0.0
    for k, c in enumerate(colors):
        n = (stacked or {}).get(k, 1)
        for j in range(n):
            b = RoundedRectangle(
                width=unit, height=(h - gap * (n - 1)) / n, corner_radius=0.045
            )
            b.set_stroke(width=0).set_fill(c, opacity=0.95)
            b.move_to([x + unit / 2, h / 2 - (h / n) * (j + 0.5), 0])
            g.add(b)
        x += unit + gap
    return g


# --------------------------------------------------------------------------- #
# keys and certificates
# --------------------------------------------------------------------------- #
_KEY_STOPS = [TCP_C, "#2EC4B6", GOLD, HTTP_C, TLS_C, "#F5F3EF"]


def byte_color(b):
    """A byte as a colour, so that 32 bytes can be compared at a glance."""
    x = b / 255 * (len(_KEY_STOPS) - 1)
    k = min(int(x), len(_KEY_STOPS) - 2)
    return mix(_KEY_STOPS[k], _KEY_STOPS[k + 1], x - k)


def key_row(hex_bytes, cell=0.118, cols=16, edge=None):
    """32 bytes as two rows of coloured cells. ``hex_bytes=None``: a value that is
    kept hidden (grey cells)."""
    data = bytes.fromhex(hex_bytes) if hex_bytes else None
    cells = VGroup()
    n = 32
    for i in range(n):
        sq = Square(side_length=cell * 0.86, stroke_width=0)
        sq.set_fill(byte_color(data[i]) if data else FAINT, opacity=1 if data else 0.9)
        sq.move_to([(i % cols - (cols - 1) / 2) * cell, (0.5 - i // cols) * cell, 0])
        cells.add(sq)
    box = RoundedRectangle(
        width=cols * cell + 0.14, height=2 * cell + 0.14, corner_radius=0.06
    )
    box.set_stroke(edge or STEEL, width=2.2).set_fill(BG, opacity=1)
    g = VGroup(box, cells)
    g.box, g.cells = box, cells
    return g


def secret_box(cell=0.118):
    """A number that never leaves its machine."""
    row = key_row(None, cell=cell)
    row.box.set_stroke(TLS_C, width=2.2)
    lock = lock_icon(0.36, TLS_C).next_to(row, LEFT, buff=0.14)
    g = VGroup(row, lock)
    g.row = row
    return g


def cert_card(name, w=2.7, color=STEEL, self_signed=False, fs=17):
    """A certificate: a name, and a seal."""
    box = RoundedRectangle(width=w, height=0.98, corner_radius=0.1)
    box.set_stroke(color, width=2.4).set_fill(PANEL, opacity=1)
    t = line_txt(name, fs=fs, weight="MEDIUM")
    if t.body.width > w - 0.72:
        t.scale((w - 0.72) / t.body.width)
    seal = VGroup(
        Circle(
            radius=0.15,
            stroke_color=color,
            stroke_width=2.4,
            fill_color=color,
            fill_opacity=0.25,
        ),
        Circle(radius=0.06, stroke_width=0, fill_color=color, fill_opacity=1),
    )
    seal.move_to(box.get_right() + LEFT * 0.3)
    t.move_to(box.get_left() + RIGHT * (0.2 + t.body.width / 2))
    t.shift(RIGHT * (box.get_left()[0] + 0.2 - t.body.get_left()[0]))
    g = VGroup(box, t, seal)
    g.box, g.seal, g.label = box, seal, t
    return g


def trust_tray(n, mine=None, cols=15, cell=0.15, color=STEEL):
    """The authorities a machine trusts before it has talked to anyone: one dot each."""
    dots = VGroup()
    for i in range(n):
        d = Dot(radius=cell * 0.27, color=color).set_opacity(0.55)
        d.move_to([(i % cols) * cell, -(i // cols) * cell, 0])
        dots.add(d)
    dots.move_to(ORIGIN)
    box = SurroundingRectangle(dots, buff=0.14, corner_radius=0.1)
    box.set_stroke(color, width=2).set_fill(PANEL, opacity=1)
    g = VGroup(box, dots)
    g.dots, g.box = dots, box
    g.mine = dots[mine if mine is not None else n // 2 + 3]
    return g


def chunks(text, width):
    return [text[i : i + width] for i in range(0, len(text), width)]


# --------------------------------------------------------------------------- #
# the stack: four flat sheets, seen from the side (no camera: an oblique drawing)
# --------------------------------------------------------------------------- #
class Sheets(Shared):
    """Layers as parallel sheets. ``pt(k, u, v)`` is the frame point of sheet ``k``
    (0 = bottom) at ``u`` along the wire (0 phone .. 1 server) and ``v`` in depth."""

    def __init__(
        self, at, w=4.4, skew=(1.0, 0.44), gap=0.82, names=("IP", "TCP", "TLS", "HTTP")
    ):
        self.at = np.array([at[0], at[1], 0.0])
        self.w, self.skew, self.gap, self.names = w, skew, gap, list(names)
        self.level = {n: float(k) for k, n in enumerate(self.names)}  # may be animated
        self.sheet, self.name = {}, {}
        for n in self.names:
            self.sheet[n] = self._poly(n)
            self.name[n] = self._label(n)

    def origin(self, n):
        total = (len(self.names) - 1) * self.gap + self.skew[1]
        x = self.at[0] - (self.w + self.skew[0]) / 2
        return np.array([x, self.at[1] - total / 2 + self.level[n] * self.gap, 0.0])

    def pt(self, n, u, v=0.5):
        o = self.origin(n)
        return o + np.array([u * self.w + v * self.skew[0], v * self.skew[1], 0.0])

    def _poly(self, n):
        color = dict(LAYERS)[n]
        m = Polygon(
            self.pt(n, 0, 0), self.pt(n, 1, 0), self.pt(n, 1, 1), self.pt(n, 0, 1)
        )
        m.set_stroke(color, width=2.6).set_fill(color, opacity=0.16)
        return m

    def _label(self, n):
        t = line_txt(n, fs=21, color=dict(LAYERS)[n], weight="BOLD")
        corner = self.pt(n, 0, 0)
        t.move_to([corner[0] - 0.22 - t.body.width / 2, self.pt(n, 0, 0.5)[1], 0])
        return t

    def wire(self, n, a=0.07, b=0.93):
        return Line(self.pt(n, a), self.pt(n, b)).set_stroke(
            dict(LAYERS)[n], width=2.2, opacity=0.75
        )

    def ends(self, n, a=0.07, b=0.93):
        return self.pt(n, a), self.pt(n, b)

    def group(self, names=None):
        names = names or self.names
        return VGroup(*[VGroup(self.sheet[n], self.name[n]) for n in names])


class SheetFlow(Layer):
    """What moves on each sheet of the stack for one fresh HTTPS request: six
    crossings below, four on TLS, two on HTTP. A crossing = (t0, t1, way)."""

    def __init__(self, clock, sheets, rtt=None):
        super().__init__()
        self.clock, self.sheets = clock, sheets
        d = (rtt or RTT) / 2
        hops = [(k * d, (k + 1) * d, ">" if k % 2 == 0 else "<") for k in range(6)]
        self.plan = {"IP": hops, "TCP": hops, "TLS": hops[2:], "HTTP": hops[4:]}
        self.only = None  # show one sheet's traffic only
        self.loop = (
            False  # past the last crossing, start the request again (ambient traffic)
        )
        self.set_z_index(4)

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        t, end = self.clock.t, self.plan["IP"][-1][1]
        if self.loop and t > end:
            t = t % end
        for n in self.sheets.names:
            if n not in self.plan or (self.only is not None and n not in self.only):
                continue
            p, q = self.sheets.ends(n)
            for t0, t1, way in self.plan[n]:
                if not (t0 <= t <= t1):
                    continue
                f = (t - t0) / (t1 - t0)
                f = f if way == ">" else 1 - f
                x, y = lerp(p[0], q[0], f), lerp(p[1], q[1], f)
                sgn = 1 if way == ">" else -1
                for j in range(7):  # a short tail behind it
                    g = 1 - j / 7
                    ink(ctx, dict(LAYERS)[n], a * (0.9 * g * g))
                    ctx.arc(
                        x - sgn * 0.085 * j, y, 0.085 * (0.55 + 0.45 * g), 0, math.tau
                    )
                    ctx.fill()
                ink(ctx, INK, a)
                ctx.arc(x, y, 0.045, 0, math.tau)
                ctx.fill()


# --------------------------------------------------------------------------- #
# between servers: a relay of connections
# --------------------------------------------------------------------------- #
class Hop(Layer):
    """One connection between two machines, drawn as a tube from ``p0`` to ``p1``
    (any direction). ``send`` queues a short train; the clock (seconds) moves it."""

    def __init__(self, clock, p0, p1, color=TCP_C, r=0.17, cross=0.9):
        super().__init__()
        self.clock = clock
        self.p0, self.p1 = np.array(p0[:2], dtype=float), np.array(p1[:2], dtype=float)
        self.hue, self.r, self.cross = (
            color,
            r,
            cross,
        )  # ``cross``: seconds to get through
        self.flows, self.glow, self.broken = [], 0.0, 0.0
        self.set_z_index(3)

    def send(self, t0, way, n, color, sealed=False):
        self.flows.append(dict(t0=t0, way=way, n=n, color=color, sealed=sealed))
        return t0 + self.cross * (1 + n * 0.05)

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        d = self.p1 - self.p0
        length = float(np.hypot(*d))
        ctx.translate(*self.p0)
        ctx.rotate(math.atan2(d[1], d[0]))
        r = self.r
        hue = mix(self.hue, LOST_C, self.broken)
        ink(ctx, hue, (0.08 + 0.12 * self.glow) * a)
        Wire._rr(ctx, 0, -r, length, 2 * r, r)
        ctx.fill()
        ink(ctx, hue, (0.6 + 0.4 * self.glow) * a)
        ctx.set_line_width(0.026 + 0.012 * self.glow)
        Wire._rr(ctx, 0, -r, length, 2 * r, r)
        ctx.stroke()
        t = self.clock.t
        w, h, pitch = 0.07, 0.19, 0.115
        for fl in self.flows:
            if t < fl["t0"]:
                continue
            head = (t - fl["t0"]) / self.cross * length
            if head - fl["n"] * pitch > length:
                continue
            xs = [head - k * pitch for k in range(fl["n"])]
            if fl["way"] == "<":
                xs = [length - x for x in xs]
            vis = [x for x in xs if 0.08 <= x <= length - 0.08]
            if not vis:
                continue
            if fl["sealed"]:
                xa, xb = min(vis) - 0.08, max(vis) + 0.08
                ink(ctx, TLS_C, 0.22 * a)
                Wire._rr(ctx, xa, -h / 2 - 0.04, xb - xa, h + 0.08, 0.05)
                ctx.fill()
                ink(ctx, TLS_C, a)
                ctx.set_line_width(0.02)
                Wire._rr(ctx, xa, -h / 2 - 0.04, xb - xa, h + 0.08, 0.05)
                ctx.stroke()
            for x in vis:
                ink(ctx, fl["color"], a)
                Wire._rr(ctx, x - w / 2, -h / 2, w, h, 0.016)
                ctx.fill()


def balancer_icon(h=1.0, color=STEEL):
    """A load balancer: one way in, several ways out."""
    w = h * 0.86
    body = RoundedRectangle(width=w, height=h, corner_radius=0.09 * w)
    body.set_stroke(color, width=2.6).set_fill(PANEL, opacity=1)
    a = np.array([-w * 0.3, 0, 0])
    lines = VGroup(
        *[Line(a, [w * 0.3, dy * h, 0]) for dy in (0.26, 0.0, -0.26)]
    ).set_stroke(color, width=2.4)
    dots = VGroup(
        Dot(a, radius=0.05, color=color),
        *[
            Dot([w * 0.3, dy * h, 0], radius=0.045, color=color)
            for dy in (0.26, 0.0, -0.26)
        ],
    )
    g = VGroup(body, lines, dots)
    g.body = body
    return g


def node(icon, name, at, fs=18):
    icon.move_to([at[0], at[1], 0])
    t = label(name, fs=fs, color=INK).next_to(icon, DOWN, buff=0.16)
    g = VGroup(icon, t)
    g.icon, g.label = icon, t
    return g


def timer_bar(clock, seconds, at, w=2.0, color=STEEL):
    """A wait: the bar fills in real time, up to ``seconds``."""
    box = (
        RoundedRectangle(width=w, height=0.2, corner_radius=0.1)
        .set_stroke(color, width=2)
        .set_fill(BG, 1)
    )
    box.move_to([at[0], at[1], 0])
    fill = always_redraw(
        lambda: (
            RoundedRectangle(
                width=max(0.02, (w - 0.06) * min(1.0, max(0.0, clock.t) / seconds)),
                height=0.14,
                corner_radius=0.07,
            )
            .set_stroke(width=0)
            .set_fill(color, 1)
            .move_to(box.get_left() + RIGHT * 0.03, aligned_edge=LEFT)
        )
    )
    return box, fill


# --------------------------------------------------------------------------- #
# the world: where the round trip comes from
# --------------------------------------------------------------------------- #
LAND, COAST = "#161D2B", "#2A3550"


class Atlas(Shared):
    """A flat map of the window between Paris and Singapore (plate carree)."""

    def __init__(self):
        self.view = GEO["view"]
        self.land = self._land()
        self.paris, self.singapore = (
            self.xy(*GEO["from"]["at"]),
            self.xy(*GEO["to"]["at"]),
        )
        self.route = [self.xy(lat, lon) for lat, lon in GEO["path"]]

    def xy(self, lat, lon):
        lon0, lon1, lat0, lat1 = self.view
        fx, fy = config.frame_x_radius, config.frame_y_radius
        return np.array(
            [
                lerp(-fx, fx, (lon - lon0) / (lon1 - lon0)),
                lerp(-fy, fy, (lat - lat0) / (lat1 - lat0)),
                0.0,
            ]
        )

    def _land(self):
        rings = json.loads((HERE / "assets" / "world.json").read_text())
        g = VGroup()
        for ring in rings:
            pts = [self.xy(lat, lon) for lon, lat in ring]
            if len(pts) < 4:
                continue
            m = VMobject().set_points_as_corners(pts + [pts[0]])
            m.set_stroke(COAST, width=1.2).set_fill(LAND, opacity=1)
            g.add(m)
        return g.set_z_index(-5)

    def arc(self, upto=1.0, color=STEEL, width=2.6):
        """The great circle from Paris, as far as ``upto`` of the way to Singapore."""
        n = max(2, int(round(upto * (len(self.route) - 1))) + 1)
        m = (
            VMobject().set_points_smoothly(self.route[:n])
            if n > 2
            else Line(self.route[0], self.route[1])
        )
        return m.set_stroke(color, width=width)

    def back(self, color=STEEL, width=2.6):
        m = VMobject().set_points_smoothly(self.route[::-1])
        return m.set_stroke(color, width=width)


def city_dot(p, color=INK, r=0.085):
    return VGroup(
        Circle(radius=r * 2.3, stroke_width=0, fill_color=color, fill_opacity=0.18),
        Circle(radius=r, stroke_width=0, fill_color=color, fill_opacity=1),
    ).move_to(p)


def band(y0, y1, op=0.9):
    """A dark strip of frame, so that text reads over the map."""
    r = (
        Rectangle(width=14.4, height=y1 - y0)
        .set_stroke(width=0)
        .set_fill(BG, opacity=op)
    )
    return r.move_to([0, (y0 + y1) / 2, 0]).set_z_index(-2)


def client_lines():
    """The five lines of ``demo/client.py`` that the film is about."""
    text = (HERE / "demo" / "client.py").read_text().splitlines()
    a = next(i for i, ln in enumerate(text) if "the film's five lines" in ln)
    lines = [ln.strip() for ln in text[a + 1 : a + 6]]
    assert lines[0].startswith("ip, port = lookup(") and lines[4].startswith(
        "reply = read_reply("
    ), lines
    return lines


CLIENT_COLORS = {
    "lookup": FUNC, "socket.create_connection": FUNC, "ctx.wrap_socket": FUNC, "tls.sendall": FUNC,
    "read_reply": FUNC, "server_hostname": PLAIN,
}  # fmt: skip
# What each of the five lines speaks. The lookup is a service of its own (DNS), not a
# layer of the stack; IP is under the connection of line 2, and under everything else.
LINE_LAYER = ("DNS", "TCP", "TLS", "HTTP", "HTTP")
DNS_C = STEEL
LINE_COLOR = tuple(DNS_C if n == "DNS" else dict(LAYERS)[n] for n in LINE_LAYER)


class Shimmer(Animation):
    """Let a group's fill breathe for the whole ``run_time``: something is waiting."""

    def __init__(self, mob, run_time, lo=0.35, hi=1.0, period=1.1):
        self.lo, self.hi = lo, hi
        self.cycles = max(1, round(run_time / period))
        super().__init__(mob, run_time=run_time, rate_func=linear)

    def interpolate_mobject(self, alpha):
        v = 0.5 + 0.5 * math.cos(2 * math.pi * self.cycles * alpha)
        self.mobject.set_fill(opacity=self.lo + (self.hi - self.lo) * v)


def port_panel(at, rows, w=5.2, pitch=0.76):
    """A server, opened: its numbered doors, what usually lives behind each, and the
    program that is listening there (or nobody). ``rows``: (port, service, program)."""
    h = len(rows) * pitch + 1.02
    box = (
        RoundedRectangle(width=w, height=h, corner_radius=0.16)
        .set_stroke(STEEL, width=2.6)
        .set_fill(PANEL, 1)
    )
    box.move_to([at[0], at[1], 0])
    addr = tag(SERVER_IP, IP_C, fs=16)
    addr.move_to(box.get_corner(UL) + RIGHT * (0.3 + addr.width / 2) + DOWN * 0.42)
    g = VGroup(box, addr)
    g.door, g.line, g.program = {}, {}, {}
    x0, y = box.get_left()[0], box.get_top()[1] - 0.86
    for port, service, program in rows:
        y -= pitch / 2
        door = port_tag(port, program is not None, fs=19)
        door.move_to([x0 + 0.85, y, 0])
        name = label(service, fs=17).move_to([0, y, 0])
        name.shift(RIGHT * (x0 + 1.62 - name.get_left()[0]))
        if program is None:
            slot = DashedVMobject(
                RoundedRectangle(width=1.55, height=0.44, corner_radius=0.08),
                num_dashes=26,
            )
            slot.set_stroke(FAINT, width=2).move_to([x0 + w - 1.12, y, 0])
        else:
            slot = tag(
                program,
                STEEL,
                fs=15,
                fill=0.0,
                tcolor=INK,
                weight="MEDIUM",
                pad=(0.3, 0.2),
            )
            slot.box.set_stroke(TCP_C, width=2.2)
            slot.move_to([x0 + w - 1.12, y, 0])
        row = VGroup(door, name, slot)
        g.add(row)
        g.door[port], g.line[port], g.program[port] = door, row, slot
        y -= pitch / 2
    g.box = box
    return g
