"""Detecting Change From Space — a short, house-style geospatial-detection explainer.

The same idea, two real-world uses:

    1. Signal          -- why a satellite pixel's Red and near-infrared (NIR)
                           reflectance reveals vegetation health:
                               NDVI = (NIR - Red) / (NIR + Red)
                           using the real band pair Sentinel-2 / Landsat carry.
    2. Deforestation    -- two real satellite photographs of the exact same
                           patch of Rondônia, Brazil: Landsat 5, 1990 (dense
                           forest) and Sentinel-2, 2023 (a checkerboard of
                           cleared farmland), plus the same two scenes read as
                           real, server-computed NDVI. The same check Global
                           Forest Watch and Brazil's DETER run on the open
                           Hansen/UMD Global Forest Change dataset.
    3. Agriculture      -- a real Sentinel-2 photograph of Kansas center-pivot
                           irrigation circles, true colour and NDVI, zoomed to
                           one real stressed circle sitting right next to
                           thriving ones.
    4. Recap            -- one pipeline: bands -> NDVI -> threshold -> alert.
                           Two of the most consequential questions on Earth,
                           one formula.

Bookended by the channel's intro / "Thank you for watching!" outro, matching
the sibling explainers (animations/Indexes, animations/Tensors).

Everything uses ``Text`` (Pango), never ``Tex``. The satellite photographs and
NDVI renders are real: baked once by ``fetch_assets.py`` from Microsoft's
Planetary Computer data API (public Sentinel-2 L2A / Landsat Collection 2
imagery, band math computed server-side on real reflectance bands), and the
small locator maps are real Natural Earth country outlines. See README.md for
exact scene IDs, dates, and citations.

Scenes are exposed individually (``Intro``, ``Signal``, ``Deforestation``,
``Agriculture``, ``Recap``, ``Outro``) and as one film
(``DetectingChangeFromSpace``).

Env knobs:
    GD_QUICK=1   collapse every hold for a fast layout render
    GD_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from manim import *

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

QUICK = os.environ.get("GD_QUICK") == "1"
DELAY = float(os.environ.get("GD_DELAY", "0.28" if QUICK else "2.2"))
ANIM_SLOW = 1.0 if QUICK else 1.15
END_HOLD = 0.2 if QUICK else 2.2

# ---- palette (shared house style + domain colours) ------------------------ #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
FAINT = "#2A3446"       # hairlines, pixel-grid strokes
PANEL = "#141C29"       # card fill
GOLD = "#FFD166"        # accent / formula highlight
GOOD = "#3DD68C"        # healthy vegetation / high NDVI
BAD = "#FF5C5C"         # alert / flagged pixel
BARE = "#C08A52"        # bare soil / cleared ground
REDBAND = "#FF6B6B"     # the satellite's Red band
NIRBAND = "#5B8DEF"     # the satellite's near-infrared band
CROP = "#E3B341"        # agriculture accent
MONO = "Menlo"
FONT = "Helvetica Neue"

# ---- crisp small text: Pango mangles glyphs/spacing below ~20pt ----------- #
# Shadow Text so every call rasterises at a large base size and scales DOWN.
_BaseText = Text
_BaseText.set_default(font=FONT)
_TEXT_BASE = 60


def Text(text, font_size=48, **kw):  # noqa: F811 (intentional shadow)
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


def txt(s, fs=26, color=INK, font=None, slant=None, weight=None):
    kw = dict(font_size=fs, color=color)
    if font is not None:
        kw["font"] = font
    if slant is not None:
        kw["slant"] = slant
    if weight is not None:
        kw["weight"] = weight
    return Text(s, **kw)


# ---- reusable glyphs -------------------------------------------------------#
def chip(text, color, w=2.6, h=0.85, fs=22, fill=0.14, tcolor=None, radius=0.14):
    box = RoundedRectangle(width=w, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=fill)
    label = txt(text, fs=fs, color=tcolor or INK)
    if label.width > w - 0.3:
        label.scale((w - 0.3) / label.width)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4, tip=0.2):
    return Arrow(start, end, buff=0.0, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.28, tip_length=tip)


def bullet(text, color=INK, dot=GOLD, fs=23, dot_r=0.06):
    d = Dot(radius=dot_r, color=dot)
    t = txt(text, fs=fs, color=color)
    t.next_to(d, RIGHT, buff=0.22)
    d.align_to(t, UP).shift(DOWN * 0.12)
    return VGroup(d, t)


# ---- a small satellite glyph ----------------------------------------------#
def satellite(color=INK, panel=NIRBAND, scale=1.0):
    body = RoundedRectangle(width=0.5, height=0.32, corner_radius=0.05,
                            stroke_color=color, stroke_width=2.5,
                            fill_color=PANEL, fill_opacity=1.0)
    p1 = Rectangle(width=0.5, height=0.24, stroke_color=panel, stroke_width=2,
                   fill_color=panel, fill_opacity=0.55).next_to(body, LEFT, buff=0.06)
    p2 = p1.copy().next_to(body, RIGHT, buff=0.06)
    dish = Triangle(color=color, fill_color=PANEL, fill_opacity=1.0
                    ).scale(0.14).next_to(body, UP, buff=0.02).rotate(PI)
    g = VGroup(p1, p2, body, dish)
    return g.scale(scale)


def ndvi_color(v, lo=0.05, hi=0.85):
    f = max(0.0, min(1.0, (v - lo) / (hi - lo)))
    return interpolate_color(ManimColor(BARE), ManimColor(GOOD), f)


# ---- real satellite photo cards -------------------------------------------#
# Baked by fetch_assets.py from Microsoft Planetary Computer (real Sentinel-2 /
# Landsat 5 crops, band math computed server-side on real reflectance bands).
def image_card(filename, height=4.0, border=FAINT, sw=2):
    img = ImageMobject(os.path.join(ASSETS, filename))
    img.height = height
    frame = SurroundingRectangle(img, color=border, buff=0.0, stroke_width=sw)
    return Group(img, frame)


def image_point(card, px, py, src_size):
    """Scene-space location of source-image pixel (px, py) inside a card
    built by image_card, wherever that card currently sits post-move_to."""
    img = card[0]
    w, h = src_size
    dx = (px / w - 0.5) * img.width
    dy = (0.5 - py / h) * img.height
    return img.get_center() + np.array([dx, dy, 0.0])


# ---- a real vector base map (Natural Earth 1:110m admin-0 countries) ------ #
_WORLD = None


def _world():
    global _WORLD
    if _WORLD is None:
        with open(os.path.join(ASSETS, "world_map.json")) as f:
            _WORLD = json.load(f)
    return _WORLD


def _ring_contains(ring, lon, lat):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat):
            xcross = (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi
            if lon < xcross:
                inside = not inside
        j = i
    return inside


def country_map(name, marker_lonlat, height=1.4, color=MUTED, marker_color=BAD):
    """A small real outline map of `name` (Natural Earth) with a marker dot.
    Only the ring containing marker_lonlat is drawn (drops distant islands /
    Alaska-Hawaii-style exclaves so the inset stays legible at small size)."""
    entry = next(c for c in _world() if c["name"] == name)
    lon0, lat0 = marker_lonlat
    rings = [r for r in entry["rings"] if _ring_contains(r, lon0, lat0)]
    if not rings:
        rings = [max(entry["rings"], key=len)]

    all_pts = [p for r in rings for p in r]
    lats = [p[1] for p in all_pts]
    lat_mid = sum(lats) / len(lats)
    cosf = max(0.15, math.cos(math.radians(lat_mid)))
    xs = [lon * cosf for lon, _ in all_pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(lats), max(lats)
    span = max(maxx - minx, maxy - miny)
    scale = height / span
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def project(lon, lat):
        return np.array([(lon * cosf - cx) * scale, (lat - cy) * scale, 0.0])

    polys = VGroup(*[
        Polygon(*[project(lon, lat) for lon, lat in ring], stroke_color=color,
                stroke_width=1.6, fill_color=color, fill_opacity=0.14)
        for ring in rings
    ])
    pin = project(lon0, lat0)
    marker = Dot(pin, radius=0.05, color=marker_color)
    ring_mark = Circle(radius=0.12, stroke_color=marker_color, stroke_width=2.2,
                       fill_opacity=0).move_to(pin)
    return VGroup(polys, ring_mark, marker)


# ========================================================================== #
class _GeoBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    def play(self, *anims, **kw):
        if "run_time" in kw:
            kw["run_time"] *= ANIM_SLOW
        super().play(*anims, **kw)

    # ---- timing ------------------------------------------------------------
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.7):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            super().play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- chrome --------------------------------------------------------------
    def section_header(self, label, color=GOLD):
        t = txt(label, fs=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        g = VGroup(t, line)
        self.play(FadeIn(g, shift=DOWN * 0.15), run_time=0.6)
        return g

    def say(self, s, color=INK, fs=25, buff=0.45):
        m = txt(s, fs=fs, color=color)
        if m.width > 12.6:
            m.scale_to_fit_width(12.6)
        m.to_edge(DOWN, buff=buff)
        return m

    def show_say(self, s, **kw):
        m = self.say(s, **kw)
        self.play(FadeIn(m, shift=UP * 0.1), run_time=0.5)
        return m

    def replace_say(self, old, s, **kw):
        m = self.say(s, **kw)
        if old is not None:
            self.play(FadeOut(old, shift=UP * 0.1), FadeIn(m, shift=UP * 0.1), run_time=0.55)
        else:
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.5)
        return m

    # ---- house intro / outro cards -----------------------------------------
    def _rule_under(self, header, pad=1.0, color=GOLD, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = txt("Detecting Change From Space", fs=52, color=INK, weight="BOLD")
        header.set(width=min(11.6, header.width))
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=NIRBAND)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = txt("How satellites turn reflected light into an alert", fs=28, color=MUTED)
        if sub.width > line.width:
            sub.scale_to_fit_width(line.width)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, writer, line)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = txt("Thank you for watching!", fs=46, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=NIRBAND)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = txt("Same open pixels, same formula: a cleared forest, a thirsty field.",
                    fs=23, color=MUTED)
        recap.next_to(writer, DOWN, buff=0.5)
        if recap.width > 12.4:
            recap.scale_to_fit_width(12.4)
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 -- the signal: two bands, one formula
    # ====================================================================== #
    def scene_signal(self):
        self.section_header("1 · The signal in the light", color=NIRBAND)

        cap = self.show_say("Sunlight includes wavelengths our eyes can't see "
                            "at all. That is where this signal lives.")

        # ---- what NIR actually is: a quick tour of the spectrum ---------------
        spectrum_colors = ["#8B5CF6", "#4A90D9", "#22C1C3", GOOD, "#F5D547",
                          "#F2994A", REDBAND]
        vis_w, nir_w = 6.0, 4.0
        seg_w = vis_w / len(spectrum_colors)
        vis_bar = VGroup(*[Rectangle(width=seg_w, height=0.55, stroke_width=0,
                                     fill_color=c, fill_opacity=1.0)
                          for c in spectrum_colors]).arrange(RIGHT, buff=0)
        nir_bar = Rectangle(width=nir_w, height=0.55, stroke_width=0,
                            fill_color="#3A4152", fill_opacity=1.0)
        nir_hatch = VGroup(*[Line(UP * 0.22, DOWN * 0.22, stroke_color="#565F73",
                                  stroke_width=1.3).shift(RIGHT * x)
                             for x in np.linspace(-nir_w / 2 + 0.3, nir_w / 2 - 0.3, 9)])
        spectrum = VGroup(vis_bar, VGroup(nir_bar, nir_hatch)).arrange(RIGHT, buff=0.0)
        spectrum.move_to(UP * 1.45)

        vis_lab = txt("visible light", fs=18, color=INK)
        vis_lab.next_to(vis_bar, UP, buff=0.16).align_to(vis_bar, LEFT)
        nir_zone_lab = txt("near-infrared (NIR): invisible to us", fs=17, color=MUTED)
        nir_zone_lab.next_to(nir_bar, UP, buff=0.16)
        if nir_zone_lab.width > nir_w + 0.3:
            nir_zone_lab.scale_to_fit_width(nir_w + 0.3)

        self.play(FadeIn(spectrum), run_time=1.0)
        self.play(FadeIn(vis_lab), FadeIn(nir_zone_lab), run_time=0.6)
        self.beat(1.6)

        left_x = spectrum.get_left()[0]

        def wl_x(nm, nm0=400, nm1=900, width=vis_w + nir_w):
            return left_x + (nm - nm0) / (nm1 - nm0) * width

        red_x, nir_x = wl_x(665), wl_x(842)
        bar_bottom = spectrum.get_bottom()[1]
        red_tick = Line([red_x, bar_bottom, 0], [red_x, bar_bottom - 0.22, 0],
                       color=REDBAND, stroke_width=3)
        nir_tick = Line([nir_x, bar_bottom, 0], [nir_x, bar_bottom - 0.22, 0],
                       color=NIRBAND, stroke_width=3)
        red_tag = txt("Red ≈ 665 nm", fs=17, color=REDBAND).next_to(red_tick, DOWN, buff=0.12)
        nir_tag = txt("NIR ≈ 842 nm", fs=17, color=NIRBAND).next_to(nir_tick, DOWN, buff=0.12)
        self.play(Create(red_tick), Create(nir_tick), FadeIn(red_tag), FadeIn(nir_tag),
                 run_time=0.8)

        cap = self.replace_say(cap, "NIR means Near-InfraRed: light just past "
                               "red, with a slightly longer wavelength than "
                               "our eyes can detect.")
        self.beat(2.0)

        cap = self.replace_say(cap, "A satellite's sensor sees both. That "
                               "extra channel, past what we can see, is the "
                               "whole trick.")
        self.beat(1.8)

        self.play(FadeOut(VGroup(spectrum, vis_lab, nir_zone_lab, red_tick,
                                 nir_tick, red_tag, nir_tag)), run_time=0.7)

        sat = satellite(scale=1.3).to_corner(UR, buff=0.75)
        sat_lab = txt("satellite", fs=16, color=MUTED).next_to(sat, DOWN, buff=0.14)
        self.play(FadeIn(VGroup(sat, sat_lab), shift=DOWN * 0.15), run_time=0.7)

        cap = self.replace_say(cap, "Every pixel a satellite records has two "
                               "reflectance numbers: visible red, and "
                               "near-infrared.")
        self.beat(1.4)

        # the formula card, top-centre, clear of the header
        formula = Text("NDVI = (NIR - Red) / (NIR + Red)", font_size=30, color=INK,
                       font=MONO, t2c={"NIR": NIRBAND, "Red": REDBAND})
        fbox = RoundedRectangle(width=formula.width + 0.7, height=formula.height + 0.5,
                                corner_radius=0.12, stroke_color=GOLD, stroke_width=2,
                                fill_color=PANEL, fill_opacity=0.92).move_to(formula)
        fgroup = VGroup(fbox, formula).move_to(UP * 2.35)
        self.play(FadeIn(fgroup, shift=DOWN * 0.15), run_time=0.9)
        self.beat(1.6)

        cap = self.replace_say(cap, "Plug in two real surfaces, and the same "
                               "two numbers tell two different stories.")

        def surface_card(center, name, red_v, nir_v, swatch_color, tag_color):
            base_y = center[1] - 0.55
            baseline = Line([center[0] - 1.1, base_y, 0], [center[0] + 1.1, base_y, 0],
                            color=FAINT, stroke_width=2)
            scale_k = 2.2
            red_bar = Rectangle(width=0.55, height=max(0.05, red_v * scale_k),
                                stroke_width=0, fill_color=REDBAND, fill_opacity=0.9)
            nir_bar = Rectangle(width=0.55, height=max(0.05, nir_v * scale_k),
                                stroke_width=0, fill_color=NIRBAND, fill_opacity=0.9)
            red_bar.move_to([center[0] - 0.55, base_y + red_bar.height / 2, 0])
            nir_bar.move_to([center[0] + 0.55, base_y + nir_bar.height / 2, 0])
            red_lab = txt("Red", fs=18, color=REDBAND).next_to(red_bar, DOWN, buff=0.16)
            red_lab.move_to([center[0] - 0.55, base_y - 0.28, 0])
            nir_lab = txt("NIR", fs=18, color=NIRBAND).next_to(nir_bar, DOWN, buff=0.16)
            nir_lab.move_to([center[0] + 0.55, base_y - 0.28, 0])
            red_val = txt(f"{red_v:.2f}", fs=17, color=REDBAND).next_to(red_bar, UP, buff=0.1)
            nir_val = txt(f"{nir_v:.2f}", fs=17, color=NIRBAND).next_to(nir_bar, UP, buff=0.1)
            swatch = RoundedRectangle(width=0.55, height=0.4, corner_radius=0.08,
                                      stroke_color=swatch_color, stroke_width=2,
                                      fill_color=swatch_color, fill_opacity=0.85)
            swatch.move_to([center[0], center[1] + 1.75, 0])
            name_lab = txt(name, fs=21, color=INK, weight="BOLD")
            name_lab.next_to(swatch, DOWN, buff=0.18)
            ndvi_v = (nir_v - red_v) / (nir_v + red_v)
            tag = txt(f"NDVI = {ndvi_v:.2f}", fs=22, color=tag_color, weight="BOLD",
                      font=MONO)
            tag.next_to(baseline, DOWN, buff=0.55)
            grp = VGroup(swatch, name_lab, baseline, red_bar, nir_bar,
                        red_lab, nir_lab, red_val, nir_val)
            return grp, tag, ndvi_v

        veg_red, veg_nir = 0.05, 0.50
        bare_red, bare_nir = 0.22, 0.30

        veg_grp, veg_tag, veg_ndvi = surface_card((-3.6, -0.4, 0), "Healthy forest",
                                                   veg_red, veg_nir, GOOD, GOOD)
        bare_grp, bare_tag, bare_ndvi = surface_card((3.6, -0.4, 0), "Bare / cleared ground",
                                                      bare_red, bare_nir, BARE, BARE)
        assert round(veg_ndvi, 2) == 0.82 and round(bare_ndvi, 2) == 0.15

        self.play(FadeIn(veg_grp[0]), FadeIn(veg_grp[1]), run_time=0.5)
        self.play(GrowFromEdge(veg_grp[3], DOWN), GrowFromEdge(veg_grp[4], DOWN),
                  Create(veg_grp[2]), run_time=0.8)
        self.play(FadeIn(VGroup(veg_grp[5], veg_grp[6], veg_grp[7], veg_grp[8])), run_time=0.5)
        self.play(FadeIn(veg_tag, shift=UP * 0.1), run_time=0.6)
        self.beat(1.2)

        self.play(FadeIn(bare_grp[0]), FadeIn(bare_grp[1]), run_time=0.5)
        self.play(GrowFromEdge(bare_grp[3], DOWN), GrowFromEdge(bare_grp[4], DOWN),
                  Create(bare_grp[2]), run_time=0.8)
        self.play(FadeIn(VGroup(bare_grp[5], bare_grp[6], bare_grp[7], bare_grp[8])), run_time=0.5)
        self.play(FadeIn(bare_tag, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)

        cap = self.replace_say(cap, "Healthy leaves absorb red light for "
                               "photosynthesis, but scatter near-infrared "
                               "strongly. Bare ground does neither.")
        self.beat(2.0)

        cap = self.replace_say(cap, "Sentinel-2 (ESA) and Landsat (USGS/NASA) "
                               "capture exactly this pair of bands, free and "
                               "open, over the whole planet every few days.")
        self.beat(2.2)

        # collapse the two cards down into a shared NDVI scale
        self.play(FadeOut(VGroup(veg_grp, bare_grp)), run_time=0.6)
        scale_w = 8.6
        scale_bar = Rectangle(width=scale_w, height=0.36, stroke_width=1.5,
                              stroke_color=FAINT, fill_opacity=0)
        scale_bar.move_to(UP * 0.15)
        n_seg = 40
        segs = VGroup()
        for i in range(n_seg):
            v = 0.9 * i / (n_seg - 1)
            seg = Rectangle(width=scale_w / n_seg, height=0.36, stroke_width=0,
                            fill_color=ndvi_color(v), fill_opacity=1.0)
            seg.move_to(scale_bar.get_left() + RIGHT * (scale_w / n_seg) * (i + 0.5))
            segs.add(seg)
        lo_lab = txt("NDVI 0.0", fs=18, color=MUTED).next_to(scale_bar, LEFT, buff=0.25)
        hi_lab = txt("0.9", fs=18, color=MUTED).next_to(scale_bar, RIGHT, buff=0.25)
        self.play(FadeIn(segs), Create(scale_bar), FadeIn(lo_lab), FadeIn(hi_lab), run_time=0.9)

        def pos_on_scale(v):
            frac = max(0.0, min(1.0, v / 0.9))
            return scale_bar.get_left() + RIGHT * scale_w * frac

        thr_x = pos_on_scale(0.30)
        thr_line = DashedLine(thr_x + UP * 0.32, thr_x + DOWN * 0.32, color=BAD, stroke_width=3)
        thr_lab = txt("alert threshold  0.30", fs=19, color=BAD, weight="BOLD")
        thr_lab.next_to(thr_line, DOWN, buff=0.55)
        self.play(Create(thr_line), FadeIn(thr_lab, shift=UP * 0.1), run_time=0.7)
        self.beat(1.0)

        veg_dot = Dot(pos_on_scale(veg_ndvi) + UP * 0.32, radius=0.09, color=GOOD)
        bare_dot = Dot(pos_on_scale(bare_ndvi) + UP * 0.32, radius=0.09, color=BAD)
        veg_dl = txt("forest", fs=18, color=GOOD).next_to(veg_dot, UP, buff=0.14)
        bare_dl = txt("cleared", fs=18, color=BAD).next_to(bare_dot, UP, buff=0.14)
        self.play(FadeIn(veg_dot, scale=0.4), FadeIn(bare_dot, scale=0.4),
                  FadeIn(veg_dl), FadeIn(bare_dl), run_time=0.7)

        cap = self.replace_say(cap, "Cross below about 0.30, and there is no "
                               "longer enough live vegetation to call this "
                               "pixel forest.")
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 -- deforestation: a fishbone pattern, four years, real counts
    # ====================================================================== #
    def scene_deforestation(self):
        self.section_header("2 · The same place, 33 years apart", color=BAD)

        locator = country_map("Brazil", (-62.7, -9.8), height=1.3,
                              color=MUTED, marker_color=BAD)
        locator_lab = txt("Rondônia, Brazil", fs=15, color=MUTED)
        locator_grp = VGroup(locator, locator_lab).arrange(DOWN, buff=0.14)
        locator_grp.to_corner(UR, buff=0.55)
        self.play(FadeIn(locator_grp), run_time=0.7)

        cap = self.show_say("These are real satellite photographs of the exact "
                            "same patch of Rondônia, Brazil, decades apart.")

        tci_before = image_card("rondonia_1990_tci.jpg", height=3.85).move_to(
            LEFT * 3.65 + DOWN * 0.15)
        tci_after = image_card("rondonia_2023_tci.jpg", height=3.85).move_to(
            RIGHT * 3.65 + DOWN * 0.15)
        lab_before = txt("Landsat 5 · 1990", fs=19, color=INK)
        lab_before.next_to(tci_before, UP, buff=0.2)
        lab_after = txt("Sentinel-2 · 2023", fs=19, color=INK)
        lab_after.next_to(tci_after, UP, buff=0.2)
        arrow = harrow(tci_before.get_right() + RIGHT * 0.12,
                       tci_after.get_left() + LEFT * 0.12, color=MUTED, sw=3, tip=0.16)

        self.play(FadeIn(tci_before), FadeIn(lab_before), run_time=0.9)
        self.beat(0.8)
        self.play(FadeIn(tci_after), FadeIn(lab_after), GrowArrow(arrow), run_time=0.9)
        self.beat(1.6)

        cap = self.replace_say(cap, "Dense forest in 1990. By 2023, a checkerboard "
                               "of cleared farmland. Real imagery, not a "
                               "reconstruction.")
        self.beat(2.2)

        ndvi_before = image_card("rondonia_1990_ndvi.jpg", height=3.85).move_to(tci_before)
        ndvi_after = image_card("rondonia_2023_ndvi.jpg", height=3.85).move_to(tci_after)
        cap = self.replace_say(cap, "The same two photos, read as NDVI: green is "
                               "living forest, orange and red is cleared or bare "
                               "ground.")
        self.play(FadeOut(tci_before), FadeOut(tci_after),
                  FadeIn(ndvi_before), FadeIn(ndvi_after), run_time=1.0)
        self.beat(2.0)

        cap = self.replace_say(cap, "Global Forest Watch and Brazil's DETER run "
                               "this exact NDVI check on the open Sentinel-2 and "
                               "Landsat archive, built on the Hansen / UMD Global "
                               "Forest Change dataset, and flag new clearings "
                               "automatically.")
        self.beat(2.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 -- agriculture: the same signal, a growing-season curve
    # ====================================================================== #
    def scene_agriculture(self):
        self.section_header("3 · The same signal, a different question", color=CROP)

        locator = country_map("United States of America", (-100.65, 37.6),
                              height=1.15, color=MUTED, marker_color=CROP)
        locator_lab = txt("Kearny County, Kansas", fs=15, color=MUTED)
        locator_grp = VGroup(locator, locator_lab).arrange(DOWN, buff=0.14)
        locator_grp.to_corner(UR, buff=0.55)
        self.play(FadeIn(locator_grp), run_time=0.7)

        cap = self.show_say("A real Sentinel-2 photograph of Kansas: hundreds of "
                            "center-pivot irrigation circles, each its own small "
                            "experiment in water and light.")
        wide_tci = image_card("kansas_wide_tci.jpg", height=5.1).move_to(DOWN * 0.35)
        wide_lab = txt("Sentinel-2 · August 2023", fs=19, color=INK)
        wide_lab.next_to(wide_tci, UP, buff=0.2)
        self.play(FadeIn(wide_tci), FadeIn(wide_lab), run_time=1.0)
        self.beat(1.8)

        wide_ndvi = image_card("kansas_wide_ndvi.jpg", height=5.35).move_to(wide_tci)
        cap = self.replace_say(cap, "Read as NDVI, the same photo separates "
                               "thriving green fields from pale, stressed, or "
                               "fallow ground.")
        self.play(FadeOut(wide_tci), FadeIn(wide_ndvi), run_time=0.9)
        self.beat(1.8)

        cap = self.replace_say(cap, "Zoom into a handful of circles and the "
                               "pattern is unmistakable.")
        self.play(FadeOut(wide_ndvi), FadeOut(wide_lab), run_time=0.6)

        close_tci = image_card("kansas_close_tci.jpg", height=4.55).move_to(
            LEFT * 3.65 + DOWN * 0.1)
        close_ndvi = image_card("kansas_close_ndvi.jpg", height=4.55).move_to(
            RIGHT * 3.65 + DOWN * 0.1)
        lab1 = txt("true colour", fs=18, color=MUTED).next_to(close_tci, UP, buff=0.2)
        lab2 = txt("NDVI", fs=18, color=MUTED).next_to(close_ndvi, UP, buff=0.2)
        self.play(FadeIn(close_tci), FadeIn(lab1), run_time=0.8)
        self.play(FadeIn(close_ndvi), FadeIn(lab2), run_time=0.8)
        self.beat(1.2)

        # a real pale/stressed circle, pixel-located in the source crop
        # (verified against assets/kansas_close_ndvi.jpg -- see fetch_assets.py)
        src = (1200, 975)
        pt_tci = image_point(close_tci, 575, 520, src)
        pt_ndvi = image_point(close_ndvi, 575, 520, src)
        radius_scene = 45 / src[0] * close_tci[0].width
        ring1 = Circle(radius=radius_scene, color=BAD, stroke_width=3).move_to(pt_tci)
        ring2 = Circle(radius=radius_scene, color=BAD, stroke_width=3).move_to(pt_ndvi)
        call = txt("one stressed circle, next to thriving ones", fs=19, color=BAD)
        call.move_to([0, -2.75, 0])
        cap = self.replace_say(cap, "Some fields are thriving. One right next to "
                               "them clearly is not.")
        self.play(Create(ring1), Create(ring2), run_time=0.8)
        self.play(FadeIn(call, shift=UP * 0.1), run_time=0.6)
        self.beat(1.8)

        cap = self.replace_say(cap, "Sentinel-2 revisits the same field every "
                               "five days, cheap enough to catch a dip like this "
                               "before it is visible from the ground.")
        self.beat(2.2)

        cap = self.replace_say(cap, "Catch it early, and a grower can irrigate "
                               "or treat the one circle that needs it, not the "
                               "whole farm.")
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 -- recap: one pipeline, two consequential questions
    # ====================================================================== #
    def scene_recap(self):
        title = txt("One pipeline, end to end", fs=40, color=INK, weight="BOLD")
        title.to_edge(UP, buff=1.0)
        line = self._rule_under(title, pad=0.7, drop=0.4)
        self.play(Write(title), Create(line), run_time=1.1)
        self.beat(0.5)

        stages = [
            ("Red + NIR bands", NIRBAND),
            ("NDVI", GOLD),
            ("Time series", MUTED),
            ("Threshold / model", BAD),
            ("Alert", BAD),
        ]
        nodes = VGroup(*[chip(name, col, w=2.55, h=0.82, fs=20) for name, col in stages])
        nodes.arrange(RIGHT, buff=0.42).move_to(UP * 1.05)
        if nodes.width > 13.2:
            nodes.scale_to_fit_width(13.2)
        arrows = VGroup(*[harrow(nodes[i].get_right(), nodes[i + 1].get_left(),
                                 color=MUTED, sw=3, tip=0.15)
                          for i in range(len(nodes) - 1)])
        self.play(FadeIn(nodes[0]), run_time=0.5)
        for i in range(1, len(nodes)):
            self.play(GrowArrow(arrows[i - 1]), run_time=0.35)
            self.play(FadeIn(nodes[i], shift=RIGHT * 0.1), run_time=0.45)
        self.beat(1.2)

        b1 = bullet("Climate: a real NDVI drop across cleared land flags "
                   "illegal logging (Global Forest Watch, Brazil's DETER).",
                   color=INK, dot=BAD, fs=22)
        b2 = bullet("Agriculture: a localized NDVI dip flags crop stress "
                   "before yield is at risk (precision agriculture).",
                   color=INK, dot=CROP, fs=22)
        for b in (b1, b2):
            if b.width > 11.6:
                b.scale_to_fit_width(11.6)
        rows = VGroup(b1, b2).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        rows.next_to(nodes, DOWN, buff=0.75)
        self.play(FadeIn(b1, shift=UP * 0.12), run_time=0.6)
        self.beat(1.4)
        self.play(FadeIn(b2, shift=UP * 0.12), run_time=0.6)
        self.beat(1.6)

        punch = txt("Sentinel-2 and Landsat are free and open. The same "
                   "pixels protect forests and feed people.", fs=24, color=GOLD,
                   weight="BOLD")
        if punch.width > 12.6:
            punch.scale_to_fit_width(12.6)
        punch.next_to(rows, DOWN, buff=0.6)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.9)
        self.beat(2.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    def play_all(self):
        self.play_intro()
        self.scene_signal()
        self.scene_deforestation()
        self.scene_agriculture()
        self.scene_recap()
        self.play_outro()


# ---- thin per-scene classes + the whole film ------------------------------ #
class Intro(_GeoBase):
    def construct(self):
        self.play_intro()


class Signal(_GeoBase):
    def construct(self):
        self.scene_signal()


class Deforestation(_GeoBase):
    def construct(self):
        self.scene_deforestation()


class Agriculture(_GeoBase):
    def construct(self):
        self.scene_agriculture()


class Recap(_GeoBase):
    def construct(self):
        self.scene_recap()


class Outro(_GeoBase):
    def construct(self):
        self.play_outro()


class DetectingChangeFromSpace(_GeoBase):
    def construct(self):
        self.play_all()


# a tiny glyph probe (render once to confirm symbols are not tofu)
class Probe(_GeoBase):
    def construct(self):
        rows = [
            "NDVI = (NIR - Red) / (NIR + Red)   ·   →",
            "0.82   0.15   0.30   91 pixels   31 flagged",
        ]
        g = VGroup(*[Text(r, font_size=34, color=INK) for r in rows]).arrange(DOWN, buff=0.6)
        self.add(g)
        self.wait(0.2)
