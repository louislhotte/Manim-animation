"""Film-local glyphs of the Certificates film: keys, seals, the certificate card,
fingerprints as rows of coloured cells, the trust store, the gates of the last scene.

Conventions: a key drawn hollow is public (it is shown around), a key drawn solid is
private (it never leaves its owner). A seal takes the colour of whoever signed.
Whatever a scene animates on its own is a top-level mobject, never a nested part.
"""

from __future__ import annotations

import math

import numpy as np
from manimx import *

import facts as F

CLIENT_C = "#508FF9"  # the browser
SHOP_C = "#E26E1A"  # the server and its key
CA_C = "#C170BB"  # the issuing authority
ROOT_C = "#30A46E"  # the root: what the device already trusts
LOOK_C = GOLD
STEEL = "#9AA5BD"
STOPS = ["#508FF9", "#2EC4B6", "#FFD166", "#E26E1A", "#C170BB", "#F5F3EF"]


def put(mob, x, y):
    """Left edge at ``x``, middle at ``y``."""
    return mob.shift([x - mob.get_left()[0], y - mob.get_center()[1], 0])


def key_icon(color, w=0.9, private=False):
    """A key. Hollow bow: public. Solid bow: private."""
    r, sw = w * 0.27, 4.2 * w / 0.62
    bow = Circle(radius=r, stroke_color=color, stroke_width=sw)
    bow.set_fill(color if private else BG, opacity=1)
    hole = Circle(radius=r * 0.36, stroke_width=0, fill_color=BG, fill_opacity=1)
    end = w - r
    shaft = VGroup(
        Line([r, 0, 0], [end, 0, 0]),
        Line([end - 0.05 * w, 0, 0], [end - 0.05 * w, -r * 0.8, 0]),
        Line([end - 0.3 * w, 0, 0], [end - 0.3 * w, -r * 0.55, 0]),
    ).set_stroke(color, width=sw)
    return VGroup(shaft, bow, hole)


def seal(color, r=0.34):
    """A signature: a scalloped seal in the signer's colour."""
    pts = [
        np.array([math.cos(TAU * k / 28), math.sin(TAU * k / 28), 0.0])
        * (r if k % 2 == 0 else r * 0.86)
        for k in range(28)
    ]
    rim = Polygon(*pts).set_stroke(width=0).set_fill(color, opacity=1)
    ring = Circle(radius=r * 0.6, stroke_color=BG, stroke_width=2.5).set_fill(opacity=0)
    tick = make_tick(BG, sw=4, scale=r * 1.5)
    return VGroup(rim, ring, tick)


def seal_slot(r=0.34):
    """Where the seal will go: a dashed circle."""
    ring = Circle(radius=r, color=MUTED).set_stroke(MUTED, width=2).set_fill(opacity=0)
    return DashedVMobject(ring, num_dashes=16)


def lock_icon(color, shut=True, h=0.32):
    body = RoundedRectangle(width=h * 0.84, height=h * 0.62, corner_radius=0.04)
    body.set_stroke(color, width=2).set_fill(color, opacity=0.9).shift(DOWN * h * 0.19)
    bow = Arc(radius=h * 0.26, start_angle=0, angle=PI, color=color)
    bow.set_stroke(color, width=3).set_fill(opacity=0).shift(UP * h * 0.12)
    if not shut:
        bow.rotate(-0.7, about_point=bow.get_right() + DOWN * h * 0.06)
    return VGroup(bow, body)


def server_icon(h=1.4, color=STEEL, led=GOOD):
    w = h * 0.9
    body = RoundedRectangle(width=w, height=h, corner_radius=0.1)
    body.set_stroke(color, width=3).set_fill(PANEL, opacity=1)
    units = VGroup()
    for k in range(3):
        y = h * (0.28 - 0.28 * k)
        slot = RoundedRectangle(width=w * 0.72, height=h * 0.17, corner_radius=0.04)
        slot.set_stroke(width=0).set_fill(FAINT, opacity=0.9).move_to([0, y, 0])
        lamp = Dot(radius=0.05, color=led).move_to([-w * 0.25, y, 0])
        units.add(slot, lamp)
    return VGroup(body, units)


def browser(center, w=4.6, h=3.3, host=F.HOST):
    """A browser window with its address bar. Attributes: ``lock_at``, ``page``
    (centre of the page), ``box``."""
    cx, cy = center
    box = RoundedRectangle(width=w, height=h, corner_radius=0.16)
    box.set_stroke(CLIENT_C, width=3).set_fill(PANEL, opacity=0.7).move_to([cx, cy, 0])
    top = cy + h / 2
    pill = RoundedRectangle(width=w - 0.44, height=0.5, corner_radius=0.25)
    pill.set_stroke(FAINT, width=2).set_fill(BG, opacity=1).move_to([cx, top - 0.44, 0])
    url = put(line_txt(host, fs=21, font=MONO), pill.get_left()[0] + 0.74, top - 0.44)
    rule = Line([cx - w / 2, top - 0.88, 0], [cx + w / 2, top - 0.88, 0])
    rule.set_stroke(FAINT, width=1.5)
    g = VGroup(box, pill, url, rule)
    g.box = box
    g.lock_at = np.array([pill.get_left()[0] + 0.37, top - 0.44, 0.0])
    g.page = np.array([cx, cy - 0.44, 0.0])
    return g


def name_tag(text, color=STEEL, fs=21):
    label = line_txt(text, fs=fs, font=MONO)
    box = RoundedRectangle(width=label.width + 0.4, height=0.52, corner_radius=0.12)
    box.set_stroke(color, width=2.5).set_fill(PANEL, opacity=1).move_to(label)
    return VGroup(box, label)


def byte_color(b):
    t = b / 255 * (len(STOPS) - 1)
    i = min(int(t), len(STOPS) - 2)
    return mix(STOPS[i], STOPS[i + 1], t - i)


def strip(data: bytes, cell=0.225, height=0.5, left=(0.0, 0.0)):
    """A digest as a row of cells, one per byte, coloured by its value."""
    row = VGroup()
    for k, b in enumerate(data):
        bar = Rectangle(width=cell * 0.88, height=height, stroke_width=0)
        bar.set_fill(byte_color(b), opacity=1)
        row.add(bar.move_to([left[0] + cell * (k + 0.5), left[1], 0]))
    return row


class Cert:
    """The certificate, large: a title, four rows (label, value), and the place of
    the seal. Every part is its own mobject (``mobs()``)."""

    W, H, PITCH = 5.3, 4.3, 0.8

    def __init__(self, center, name=F.HOST):
        cx, cy = center
        x0, top = cx - self.W / 2, cy + self.H / 2
        self.box = RoundedRectangle(width=self.W, height=self.H, corner_radius=0.18)
        self.box.set_stroke(STEEL, width=3).set_fill(PANEL, opacity=1).move_to([cx, cy, 0])
        self.title = put(line_txt("certificate", fs=19, color=STEEL, weight="MEDIUM"), x0 + 0.32, top - 0.42)
        self.rule = Line([x0 + 0.32, top - 0.72, 0], [x0 + self.W - 0.32, top - 0.72, 0])
        self.rule.set_stroke(FAINT, width=1.5)
        self.labels, self.values, self.ys = [], [], []
        vx = x0 + 1.72
        for i, (label, text) in enumerate(F.fields(name)):
            y = top - 1.22 - self.PITCH * i
            lab = put(line_txt(label, fs=17, color=MUTED), x0 + 0.32, y)
            if label == "name":
                val = line_txt(text, fs=22, font=MONO, disable_ligatures=True)
            elif label == "public key":
                val = key_icon(SHOP_C, w=0.86)
            else:
                val = line_txt(text, fs=20, color=CA_C if label == "issued by" else INK)
            self.labels.append(lab)
            self.values.append(put(val, vx, y))
            self.ys.append(y)
        self.seal_at = np.array([x0 + self.W - 0.72, top - self.H + 0.7, 0.0])
        self.slot = seal_slot(0.42).move_to(self.seal_at)

    def mobs(self):
        return [self.box, self.title, self.rule, *self.labels, *self.values, self.slot]

    def row_box(self, i, color=LOOK_C):
        """A highlight around row ``i``."""
        w = self.W - 0.3
        box = RoundedRectangle(width=w, height=self.PITCH - 0.12, corner_radius=0.12)
        box.set_stroke(color, width=3).set_fill(color, opacity=0.12)
        return box.move_to([self.box.get_center()[0], self.ys[i], 0])

    def letter(self, k):
        """The k-th glyph of the name."""
        return self.values[0].body.submobjects[k]


def mini_cert(name, issuer, key_c, seal_c, center, w=5.0, h=1.35):
    """A certificate, small: whose key (left), for which name, issued by whom, and
    the issuer's seal (right). One group; ``key``, ``seal``, ``by``, ``title``."""
    cx, cy = center
    box = RoundedRectangle(width=w, height=h, corner_radius=0.16)
    box.set_stroke(STEEL, width=3).set_fill(PANEL, opacity=1).move_to([cx, cy, 0])
    key = key_icon(key_c, w=0.72).move_to([cx - w / 2 + 0.62, cy, 0])
    x = cx - w / 2 + 1.2
    title = put(line_txt(name, fs=21, weight="BOLD"), x, cy + 0.22)
    by = put(line_txt(f"issued by {issuer}", fs=17, color=MUTED, t2c={issuer: seal_c}), x, cy - 0.26)
    stamp_ = seal(seal_c, r=0.34).move_to([cx + w / 2 - 0.56, cy, 0])
    g = VGroup(box, key, title, by, stamp_)
    g.box, g.key, g.title, g.by, g.seal = box, key, title, by, stamp_
    return g


def trust_grid(center, cols=16, cell=0.36):
    """The roots a device ships with, one cell each."""
    cx, cy = center
    rows = math.ceil(F.ROOTS_HERE / cols)
    cells = VGroup()
    for k in range(F.ROOTS_HERE):
        sq = RoundedRectangle(width=cell * 0.8, height=cell * 0.8, corner_radius=0.05)
        sq.set_stroke(width=0).set_fill(mix(ROOT_C, BG, 0.62), opacity=1)
        sq.move_to(
            [cx + cell * (k % cols - (cols - 1) / 2), cy - cell * (k // cols - (rows - 1) / 2), 0]
        )
        cells.add(sq)
    return cells


def gate(x, label, y=0.55, w=3.3, h=2.5):
    """A check the certificate has to pass: an arch, a lamp, a word."""
    arch = RoundedRectangle(width=w, height=h, corner_radius=0.24)
    arch.set_stroke(STEEL, width=3.5).set_fill(opacity=0).move_to([x, y, 0])
    lamp = Circle(radius=0.15, stroke_color=STEEL, stroke_width=3).set_fill(BG, opacity=1)
    lamp.move_to([x, y + h / 2, 0])
    word = line_txt(label, fs=22, weight="MEDIUM").move_to([x, y + h / 2 + 0.5, 0])
    g = VGroup(arch, lamp, word)
    g.arch, g.lamp, g.word, g.x = arch, lamp, word, x
    return g


def lamp_on(g, color):
    """The lamp of a gate, lit (to fade in over the idle one)."""
    lit = Circle(radius=0.15, stroke_color=color, stroke_width=3).set_fill(color, opacity=1)
    return lit.move_to(g.lamp)


def error_chip(text, at):
    label = line_txt(text, fs=18, font=MONO, color=BAD)
    box = RoundedRectangle(width=label.width + 0.4, height=0.52, corner_radius=0.12)
    box.set_stroke(BAD, width=2.5).set_fill(mix(BAD, BG, 0.88), opacity=1).move_to(label)
    return VGroup(box, label).move_to(at)


def glow(box, color, width=7):
    """An outline lights up and dies down: "this one"."""
    halo = box.copy().set_fill(opacity=0).set_stroke(color, width=width, opacity=0.95)
    return Succession(FadeIn(halo, run_time=0.25), FadeOut(halo, run_time=0.75))
