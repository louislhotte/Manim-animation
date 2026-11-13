"""stage.py: the 3D side of the Terraform film: a small cloud drawn as a diorama.

The picture is the reconciliation model itself:

* a **ghost** (a glass block in blueprint blue) is what the file *declares*;
* a **solid** (a shaded block) is what really *exists* in the cloud;
* ``apply`` fills ghosts with solids, a manual change makes a solid stick out of its
  ghost (drift), a plan is the difference between the two.

Everything is attribute-driven (see ``manimx.motion``): a ``Part`` exposes plain
floats (``rise``, ``size``, ``alpha``, ``tint``) that ``Tween`` animates, and rebuilds
its faces from local geometry in ``refresh()``.

Cairo has neither a z-buffer nor lighting, so the stage brings its own:

* ``StageCamera`` draws faces in explicit layers (ground, plates, solids), sorts
  solids by the depth of their *object* (not of each face), culls back faces, and
  can shift the projected picture sideways so a HUD column fits beside it;
* faces are shaded once from their normal and a fixed light direction.
"""

from __future__ import annotations

import math

import numpy as np
from manim import ThreeDCamera
from manim.camera.camera import Camera
from manimx import *

# ---- colours ---------------------------------------------------------------- #
# Four resources carry a hue of their own, as plates, fences, icons, cards and table
# rows that sit side by side, so the hues were checked with the dataviz skill's
# validator instead of picked by eye: on the film's surface every pair stays apart
# under colour-vision-deficiency simulation (worst pair dE 9.8, target 8) and in
# normal vision (17.9, floor 15). The house SKY / LILAC pair fails both (5.7, 15.0);
# a teal bucket fails against the purple (dE 4 to 7). Servers are neutral steel:
# their shape identifies them. To re-check:
#   node <dataviz>/scripts/validate_palette.js "#C170BB,#508FF9,#E26E1A,#30A46E" \
#        --mode dark --surface "#0E1117" --pairs all
SLAB_C = "#1B2433"  # the region slab
SLAB_EDGE = "#44536F"
VPC_C = "#C170BB"  # network
SUBNET_C = "#508FF9"  # subnet
SG_C = "#E26E1A"  # security group (firewall)
SERVER_C = "#C5D0E4"  # servers: brushed steel
BUCKET_C = "#30A46E"  # storage
BLUEPRINT = "#9CC2FF"  # what the file declares (ghosts)
SHADOW = "#080B11"

LIGHT = np.array([-0.38, -0.55, 0.74])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
FLOOR, PLATE, SOLID = 0, 1, 2  # draw layers, back to front


def lit(color, normal, ambient=0.40, diffuse=0.66):
    """``color`` as lit by the stage light on a face with this ``normal``."""
    k = ambient + diffuse * max(0.0, float(np.dot(normal, LIGHT)))
    c = mix("#05070B", color, min(1.0, k))
    return mix(c, WHITE, 0.10) if k > 0.86 else c


# --------------------------------------------------------------------------- #
# camera
# --------------------------------------------------------------------------- #
class StageCamera(ThreeDCamera):
    """A 3D camera that draws staged faces in layers and can sit off-centre.

    * ``screen_shift``: added to every projected point, so the 3D subject can live
      in the right part of the frame while the camera still orbits *it*;
    * ``hud_roots``: groups whose whole (current) family is fixed in the frame,
      even when their updaters rebuild submobjects;
    * staged faces (``face.stage = (layer, order)``) are drawn first, sorted by
      layer, order, then by the depth of ``face.anchor`` (the base of the object
      the face belongs to); faces looking away from the camera are skipped.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.screen_shift = np.zeros(3)
        self.hud_roots = []

    def capture_mobjects(self, mobjects, **kwargs):
        for root in self.hud_roots:
            self.fixed_in_frame_mobjects.update(root.get_family())
        super().capture_mobjects(mobjects, **kwargs)

    def project_points(self, points):
        return super().project_points(points) + self.screen_shift

    def get_mobjects_to_display(self, *args, **kwargs):
        mobs = Camera.get_mobjects_to_display(self, *args, **kwargs)
        rot = self.get_rotation_matrix()
        centre = self.frame_center
        axis = rot[2]  # world direction pointing at the camera
        eye = centre + self.get_focal_distance() * axis
        staged, rest = [], []
        for i, m in enumerate(mobs):
            st = getattr(m, "stage", None)
            if st is None:
                rest.append(m)
                continue
            facing = True
            if m.normal is not None:
                facing = float(np.dot(m.normal, eye - m.center_w)) > 0
                if not facing and not m.two_sided:
                    continue
            depth = float(np.dot(m.anchor - centre, axis))
            if m.bias:
                depth += m.bias if facing else -m.bias
            staged.append((st[0], st[1], depth, i, m))
        staged.sort(key=lambda t: t[:4])

        def z_key(mob):  # Manim's own rule for everything that is not staged
            if not getattr(mob, "shade_in_3d", False):
                return np.inf
            return np.dot(mob.get_z_index_reference_point(), rot.T)[2]

        return [t[4] for t in staged] + sorted(rest, key=z_key)


# --------------------------------------------------------------------------- #
# parts
# --------------------------------------------------------------------------- #
class Part(VGroup):
    """One thing on the stage, built from faces given in local coordinates.

    ``origin`` is the centre of its base. Animate the plain attributes with
    ``Tween``: ``rise`` (height factor, 0..1), ``size`` (uniform scale about the
    base), ``alpha`` (presence), ``tint`` (0..1, colours pulled toward ``tint_c``).
    """

    def __init__(self, origin, layer=SOLID, order=0.0):
        super().__init__()
        self.origin = np.array(origin, dtype=float)
        self.layer, self.order = layer, order
        self.rise, self.size, self.alpha, self.tint = 1.0, 1.0, 1.0, 0.0
        self.tint_c = GOLD
        self._sig = None

    # ---- building ---------------------------------------------------------- #
    def face(
        self,
        pts,
        fill,
        normal=None,
        op=1.0,
        stroke=None,
        sw=1.2,
        sop=0.9,
        order=None,
        two_sided=False,
        bias=0.0,
        tint_k=1.0,
        closed=True,
    ):
        """Add a polygon (or an open polyline when ``closed`` is False)."""
        f = VMobject()
        f.local = np.array(pts, dtype=float)
        f.closed = closed
        f.fill_c = ManimColor(fill)
        f.fill_op = op if closed else 0.0
        f.stroke_c = ManimColor(stroke if stroke is not None else fill)
        f.sw, f.stroke_op = sw, (sop if sw else 0.0)
        f.tint_k = tint_k
        f.stage = (self.layer, self.order if order is None else order)
        f.anchor = self.origin
        f.normal = None if normal is None else np.array(normal, dtype=float)
        f.two_sided, f.bias = two_sided, bias
        f.center_w = self.origin.copy()
        self.add(f)
        self._sig = None
        return f

    def decal(self, mob, order=None, op=1.0):
        """Add a flat mobject (painted text, a line) that only follows ``alpha``."""
        for m in mob.family_members_with_points():
            m.stage = (self.layer, self.order if order is None else order)
            m.anchor = self.origin
            m.normal, m.two_sided, m.bias = None, True, 0.0
            m.center_w = self.origin
            m.decal_op = (m.get_fill_opacity() * op, m.get_stroke_opacity() * op)
        self.add(mob)
        self._sig = None
        return mob

    # ---- drawing ------------------------------------------------------------ #
    def refresh(self):
        sig = (self.rise, self.size, self.alpha, self.tint, str(self.tint_c))
        if sig == self._sig:
            return self
        self._sig = sig
        k = np.array([self.size, self.size, self.size * max(self.rise, 1e-3)])
        a = float(np.clip(self.alpha, 0, 1))
        for f in self.get_family():  # (faces have no points before their first refresh)
            if hasattr(f, "local"):
                p = f.local * k + self.origin
                f.center_w = p.mean(axis=0)
                f.set_points_as_corners([*p, p[0]] if f.closed else list(p))
                t = self.tint * f.tint_k
                f.set_fill(mix(f.fill_c, self.tint_c, t), opacity=f.fill_op * a)
                f.set_stroke(
                    mix(f.stroke_c, self.tint_c, t), width=f.sw, opacity=f.stroke_op * a
                )
            elif hasattr(f, "decal_op"):
                f.set_fill(opacity=f.decal_op[0] * a)
                f.set_stroke(opacity=f.decal_op[1] * a)
        return self

    def top(self, lift=0.0):
        """The world point above the middle of the part (for tags)."""
        h = max(
            (f.local[:, 2].max() for f in self.submobjects if hasattr(f, "local")),
            default=0.0,
        )
        return self.origin + np.array([0, 0, h * self.size * self.rise + lift])


def _rect(x0, x1, y0, y1, z):
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


SIDES = (  # (normal, corner picker) of the four walls of a box
    ((0, -1, 0), lambda w, d: ((-w, -d), (w, -d))),  # front
    ((1, 0, 0), lambda w, d: ((w, -d), (w, d))),  # right
    ((0, 1, 0), lambda w, d: ((w, d), (-w, d))),  # back
    ((-1, 0, 0), lambda w, d: ((-w, d), (-w, -d))),  # left
)


def add_box(part, w, d, h, color, z0=0.0, edge=None, top=None, sw=1.2, op=1.0):
    """The five visible faces of a box centred on the part's origin."""
    hw, hd = w / 2, d / 2
    edge = edge if edge is not None else mix(color, WHITE, 0.35)
    for n, pick in SIDES:
        (xa, ya), (xb, yb) = pick(hw, hd)
        part.face(
            [(xa, ya, z0), (xb, yb, z0), (xb, yb, z0 + h), (xa, ya, z0 + h)],
            lit(color, np.array(n)),
            normal=n,
            op=op,
            stroke=edge,
            sw=sw,
        )
    part.face(
        _rect(-hw, hw, -hd, hd, z0 + h),
        lit(top if top is not None else color, np.array([0, 0, 1])),
        normal=(0, 0, 1),
        op=op,
        stroke=edge,
        sw=sw,
    )
    return part


def ground_plate(origin, w, d, color, order, h=0.07, base=SLAB_C, k=0.26, layer=PLATE):
    """A thin tinted plate lying on the slab (a VPC, a subnet)."""
    p = Part(origin, layer=layer, order=order)
    add_box(p, w, d, h, mix(base, color, k), edge=color, sw=2.2)
    p.w, p.d, p.h = w, d, h
    return p


def ghost_box(origin, w, d, h, order=0.0, layer=SOLID, color=BLUEPRINT):
    """What the file declares: a glass block (only the faces toward the camera)."""
    p = Part(origin, layer=layer, order=order)
    hw, hd = w / 2, d / 2
    for n, pick in SIDES:
        (xa, ya), (xb, yb) = pick(hw, hd)
        p.face(
            [(xa, ya, 0), (xb, yb, 0), (xb, yb, h), (xa, ya, h)],
            color,
            normal=n,
            op=0.07,
            stroke=color,
            sw=1.8,
            sop=0.95,
        )
    p.face(_rect(-hw, hw, -hd, hd, h), color, normal=(0, 0, 1), op=0.10, sw=1.8)
    p.w, p.d, p.h = w, d, h
    return p


def ghost_plate(origin, w, d, order, layer=PLATE, color=BLUEPRINT):
    """A declared plate: a blueprint outline on the floor."""
    p = Part(origin, layer=layer, order=order)
    p.face(_rect(-w / 2, w / 2, -d / 2, d / 2, 0.012), color, op=0.05, sw=1.8, sop=0.9)
    p.w, p.d = w, d
    return p


SERVER_W, SERVER_D, SERVER_H = 0.80, 0.96, 1.16


def server(origin, color=SERVER_C):
    """A rack server: a steel box with drive bays and a status light on its front."""
    p = Part(origin)
    w, d, h = SERVER_W, SERVER_D, SERVER_H
    add_box(p, w, d, h, color, edge=mix(color, WHITE, 0.5), sw=1.3)
    y = -d / 2 - 0.004
    front = (0, -1, 0)
    dark = mix(color, "#05070B", 0.78)
    for k in range(4):  # drive bays
        z = h * (0.16 + 0.17 * k)
        p.face(
            [(-w * 0.34, y, z), (w * 0.34, y, z), (w * 0.34, y, z + h * 0.085),
             (-w * 0.34, y, z + h * 0.085)],
            dark, normal=front, sw=0, tint_k=0.3,
        )  # fmt: skip
    z = h * 0.86
    p.led = p.face(
        [(w * 0.20, y, z), (w * 0.34, y, z), (w * 0.34, y, z + h * 0.06),
         (w * 0.20, y, z + h * 0.06)],
        GOOD, normal=front, sw=0, tint_k=0.0,
    )  # fmt: skip
    p.face(  # a vent on the roof
        _rect(-w * 0.28, w * 0.28, -d * 0.30, d * 0.30, h + 0.004),
        mix(color, "#05070B", 0.30),
        normal=(0, 0, 1),
        sw=0,
        tint_k=0.5,
    )
    p.w, p.d, p.h = w, d, h
    return p


BUCKET_R, BUCKET_H = 0.56, 0.86


def bucket(origin, color=BUCKET_C, n=14):
    """An S3 bucket: a pail that widens toward its rim."""
    p = Part(origin)
    rb, rt, h = BUCKET_R * 0.76, BUCKET_R, BUCKET_H
    edge = mix(color, WHITE, 0.4)
    ang = [2 * math.pi * k / n for k in range(n + 1)]
    for a0, a1 in zip(ang, ang[1:], strict=False):
        am = (a0 + a1) / 2
        nrm = np.array([math.cos(am), math.sin(am), -0.18])
        nrm /= np.linalg.norm(nrm)
        p.face(
            [
                (rb * math.cos(a0), rb * math.sin(a0), 0),
                (rb * math.cos(a1), rb * math.sin(a1), 0),
                (rt * math.cos(a1), rt * math.sin(a1), h),
                (rt * math.cos(a0), rt * math.sin(a0), h),
            ],
            lit(color, nrm, ambient=0.34, diffuse=0.8),
            normal=nrm,
            stroke=lit(color, nrm, ambient=0.34, diffuse=0.8),
            sw=0.8,
        )
    ring = [(rt * math.cos(a), rt * math.sin(a), h) for a in ang[:-1]]
    p.face(ring, lit(color, np.array([0, 0, 1])), normal=(0, 0, 1), stroke=edge, sw=1.4)
    r2 = rt * 0.80
    hole = [(r2 * math.cos(a), r2 * math.sin(a), h + 0.004) for a in ang[:-1]]
    p.face(hole, mix(color, "#05070B", 0.72), normal=(0, 0, 1), sw=0, tint_k=0.4)
    p.w = p.d = 2 * rt
    p.h = h
    return p


def ghost_bucket(origin, n=14, color=BLUEPRINT):
    p = Part(origin)
    rb, rt, h = BUCKET_R * 0.76, BUCKET_R, BUCKET_H
    ang = [2 * math.pi * k / n for k in range(n + 1)]
    for a0, a1 in zip(ang, ang[1:], strict=False):
        am = (a0 + a1) / 2
        p.face(
            [
                (rb * math.cos(a0), rb * math.sin(a0), 0),
                (rb * math.cos(a1), rb * math.sin(a1), 0),
                (rt * math.cos(a1), rt * math.sin(a1), h),
                (rt * math.cos(a0), rt * math.sin(a0), h),
            ],
            color,
            normal=(math.cos(am), math.sin(am), 0),
            op=0.07,
            sw=0,
        )
    ring = [(rt * math.cos(a), rt * math.sin(a), h) for a in ang[:-1]]
    p.face(ring, color, normal=(0, 0, 1), op=0.10, sw=1.8, sop=0.95)
    foot = [(rb * math.cos(a), rb * math.sin(a), 0.01) for a in ang[:-1]]
    p.face(foot, color, op=0.0, sw=1.6, sop=0.8)
    return p


def fence(origin, w, d, h=0.40, color=SG_C, ghost=False):
    """A security group: a low glass wall around what it protects."""
    p = Part(origin)
    hw, hd = w / 2, d / 2
    c = BLUEPRINT if ghost else color
    reach = max(w, d) / 2 + 0.2  # near walls after, far walls before, what is inside
    for n, pick in SIDES:
        (xa, ya), (xb, yb) = pick(hw, hd)
        p.face(
            [(xa, ya, 0), (xb, yb, 0), (xb, yb, h), (xa, ya, h)],
            c,
            normal=n,
            op=0.06 if ghost else 0.20,
            stroke=c,
            sw=1.8 if ghost else 2.4,
            sop=0.95,
            two_sided=True,
            bias=reach,
        )
    p.w, p.d, p.h = w, d, h
    return p


def shadow(origin, w, d, order=5.0, layer=PLATE, op=0.42):
    """A soft contact shadow under a solid."""
    p = Part(origin, layer=layer, order=order)
    n = 18
    pts = [
        (w * 0.62 * math.cos(2 * math.pi * k / n) + 0.10,
         d * 0.62 * math.sin(2 * math.pi * k / n) + 0.06, 0.004)
        for k in range(n)
    ]  # fmt: skip
    p.face(pts, SHADOW, op=op, sw=0, tint_k=0.0)
    return p


class ScanBar(Part):
    """A line of light sweeping the floor from ``x0`` to ``x1``: a plan reading the
    real resources. Animate ``pos`` (0..1) and ``alpha``."""

    def __init__(self, x0, x1, y0, y1, z=0.16, color=BLUEPRINT):
        super().__init__([x0, (y0 + y1) / 2, z], layer=PLATE, order=9)
        self.x0, self.x1, self.pos, self.alpha = x0, x1, 0.0, 0.0
        d = y1 - y0
        for w, op in ((1.3, 0.10), (0.56, 0.20), (0.12, 1.0)):  # two halos, a core
            self.face(_rect(-w / 2, w / 2, -d / 2, d / 2, 0.0), color, op=op, sw=0)

    def refresh(self):
        self.origin[0] = self.x0 + (self.x1 - self.x0) * float(np.clip(self.pos, 0, 1))
        self._sig = None
        return super().refresh()


def floor_text(s, at, fs=20, color=MUTED, weight="MEDIUM", font=None):
    """Text painted on the floor, readable from the front of the stage."""
    t = txt(s, fs=fs, color=color, weight=weight, font=font)
    t.move_to([at[0] + t.width / 2, at[1], at[2] if len(at) > 2 else 0.0])
    return t


# --------------------------------------------------------------------------- #
# the diorama
# --------------------------------------------------------------------------- #
class Resource:
    """One resource on the stage: what is declared (ghost) and what exists (solid)."""

    def __init__(self, key, ghost, solid, shade=None):
        self.key, self.ghost, self.solid, self.shade = key, ghost, solid, shade

    @property
    def parts(self):
        """Draw order: shadow, the real thing, then what is declared (a glass box
        around the solid, or blueprint lines on a solid that outgrew it)."""
        return [p for p in (self.shade, self.solid, self.ghost) if p is not None]


class Diorama(VGroup):
    """The film's small cloud: a region slab, a VPC, a subnet, a security group,
    servers in ``slots`` and a bucket. Nothing is declared or built at first:
    ``declare(key)`` shows a ghost, ``build(key)`` fills it.

    Keys: ``vpc``, ``subnet``, ``sg``, ``bucket``, ``web0`` ... ``webN``.
    """

    PITCH = 1.02  # distance between servers

    def __init__(
        self,
        slots=3,
        cols=None,
        origin=(0, 0, 0),
        label="eu-west-3",
        label_fs=24,
        names=True,
    ):
        super().__init__()
        self.t = 0.0
        cols = cols or slots
        rows = math.ceil(slots / cols)
        P = self.PITCH
        sw_, sd_ = (cols - 1) * P + SERVER_W, (rows - 1) * P * 1.06 + SERVER_D
        sg_w, sg_d = sw_ + 0.50, sd_ + 0.50
        sub_w, sub_d = sg_w + 0.56, sg_d + 0.92
        vpc_w, vpc_d = sub_w + 0.60, sub_d + 0.92
        gap, edge = 0.34, 0.30
        front = (
            0.42 if label else 0.0
        )  # a strip of floor in front, for the region's name
        slab_w = vpc_w + gap + 2 * BUCKET_R + 2 * edge
        slab_d = vpc_d + 2 * edge + front
        o = np.array(origin, dtype=float)
        x_v = (
            o[0] - slab_w / 2 + edge + vpc_w / 2
        )  # the VPC sits left, the bucket right
        vpc_o = np.array([x_v, o[1] + front / 2, o[2]])
        sub_o = vpc_o + np.array([0, 0.19, 0.07])
        sg_o = sub_o + np.array([0, 0.24, 0.07])
        self.size_w, self.size_d = slab_w, slab_d
        self.centre = o

        # the region
        slab = Part(o + np.array([0, 0, -0.26]), layer=FLOOR, order=0)
        add_box(slab, slab_w, slab_d, 0.26, SLAB_C, edge=SLAB_EDGE, sw=1.6)
        grid = VGroup()
        nx, ny = round(slab_w / 0.8), round(slab_d / 0.8)
        for k in range(1, nx):
            x = -slab_w / 2 + slab_w * k / nx
            grid.add(Line([x, -slab_d / 2, 0.003], [x, slab_d / 2, 0.003]))
        for k in range(1, ny):
            y = -slab_d / 2 + slab_d * k / ny
            grid.add(Line([-slab_w / 2, y, 0.003], [slab_w / 2, y, 0.003]))
        grid.set_stroke("#5A6B8C", width=1.0, opacity=0.22).shift(o)
        slab.decal(grid, order=1)
        if label:
            slab.decal(
                floor_text(
                    label,
                    o + np.array([-slab_w / 2 + 0.24, -slab_d / 2 + 0.36, 0.004]),
                    fs=label_fs, color="#8A99B6", font=MONO,
                ),
                order=2,
            )  # fmt: skip
        self.slab = slab

        self.res: dict[str, Resource] = {}
        vpc = ground_plate(vpc_o, vpc_w, vpc_d, VPC_C, order=1)
        if names:  # (too small to read on the islands of the last scene)
            vpc.decal(
                floor_text(
                    "VPC",
                    vpc_o + np.array([-vpc_w / 2 + 0.16, -vpc_d / 2 + 0.24, 0.075]),
                    fs=25, color=mix(VPC_C, WHITE, 0.25), weight="BOLD",
                ),
                order=1.5,
            )  # fmt: skip
        self.res["vpc"] = Resource("vpc", ghost_plate(vpc_o, vpc_w, vpc_d, 0.6), vpc)
        sub = ground_plate(sub_o, sub_w, sub_d, SUBNET_C, order=2, k=0.30)
        if names:
            sub.decal(
                floor_text(
                    "subnet",
                    sub_o + np.array([-sub_w / 2 + 0.16, -sub_d / 2 + 0.22, 0.075]),
                    fs=22, color=mix(SUBNET_C, WHITE, 0.3), weight="BOLD",
                ),
                order=2.5,
            )  # fmt: skip
        self.res["subnet"] = Resource(
            "subnet", ghost_plate(sub_o + [0, 0, -0.06], sub_w, sub_d, 1.6), sub
        )
        self.res["sg"] = Resource(
            "sg", fence(sg_o, sg_w, sg_d, ghost=True), fence(sg_o, sg_w, sg_d)
        )
        self.slots = []
        for i in range(slots):
            r, c = divmod(i, cols)
            so = sg_o + np.array(  # the first row is the one nearest the camera
                [(c - (cols - 1) / 2) * P, (r - (rows - 1) / 2) * P * 1.06, 0.0]
            )
            self.slots.append(so)
            self.res[f"web{i}"] = Resource(
                f"web{i}",
                ghost_box(so, SERVER_W, SERVER_D, SERVER_H),
                server(so),
                shadow(so, SERVER_W, SERVER_D),
            )
        b_o = o + np.array([slab_w / 2 - edge - BUCKET_R, -0.15 + front / 2, 0])
        self.res["bucket"] = Resource(
            "bucket",
            ghost_bucket(b_o),
            bucket(b_o),
            shadow(b_o, 2 * BUCKET_R * 0.8, 2 * BUCKET_R * 0.8),
        )
        self.b_o, self.vpc_o, self.sg_o = b_o, vpc_o, sg_o

        self.add(slab)
        for r in self.res.values():  # nothing is declared, nothing exists
            if r.ghost is not None:
                r.ghost.alpha = 0.0
            r.solid.alpha, r.solid.rise = 0.0, 0.0
            if r.shade is not None:
                r.shade.alpha = 0.0
            self.add(*r.parts)
        self.refresh()
        self.add_updater(Diorama._tick)

    @staticmethod
    def _tick(m, dt):
        m.t += dt
        m.refresh()

    def refresh(self):
        self.slab.refresh()
        for r in self.res.values():
            for p in r.parts:
                p.refresh()
        for i, r in enumerate(self.res.values()):  # status lights: a slow heartbeat
            led = getattr(r.solid, "led", None)
            if led is not None:
                ph = self.t * 1.9 + 1.7 * i
                k = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(ph)) ** 2
                led.set_fill(opacity=k * float(np.clip(r.solid.alpha, 0, 1)))
        return self

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.res[key]
        return super().__getitem__(key)

    # ---- the three verbs ----------------------------------------------------- #
    def declare(self, key, run_time=0.6):
        """The file now asks for ``key``: its ghost appears."""
        return Tween(self.res[key].ghost, run_time=run_time, alpha=1.0)

    def build(self, key, run_time=1.0, keep_ghost=0.0, color=GOOD):
        """``key`` is created: the solid rises inside its ghost, flashing ``color``."""
        r = self.res[key]
        flash = 0.5 if r.solid.layer == PLATE else 1.0  # a wide plate flashes less
        r.solid.alpha, r.solid.rise, r.solid.tint, r.solid.tint_c = (
            1.0,
            0.0,
            flash,
            color,
        )
        r.solid._sig = None
        anims = [
            Tween(r.solid, run_time=run_time, rate_func=rate_functions.ease_out_back, rise=1.0),
            Tween(r.solid, run_time=run_time * 1.5, rate_func=rate_functions.ease_in_quad, tint=0.0),
            Tween(r.ghost, run_time=run_time, alpha=keep_ghost),
        ]  # fmt: skip
        if r.shade is not None:
            anims.append(Tween(r.shade, run_time=run_time, alpha=1.0))
        anims.append(self._ring(r, color, run_time * 1.3))
        return AnimationGroup(*anims)

    def _ring(self, r, color, run_time):
        """A ring that spreads on the floor from a resource being created."""
        w, d = r.solid.w * r.solid.size + 0.16, r.solid.d * r.solid.size + 0.16
        ring = Part(r.solid.origin + np.array([0, 0, 0.012]), layer=PLATE, order=8)
        ring.face(
            _rect(-w / 2, w / 2, -d / 2, d / 2, 0.0), color, op=0.0, sw=3.2, sop=1.0
        )
        ring.alpha = 0.0
        ring.refresh()
        self.add(ring)
        return Succession(
            Tween(ring, run_time=0.05, alpha=0.9),
            Tween(ring, run_time=run_time, rate_func=rate_functions.ease_out_cubic,
                  size=1.0 + 0.9 / max(w, d), alpha=0.0),
        )  # fmt: skip

    def destroy(self, key, run_time=0.9, ghost=0.0):
        """``key`` is destroyed: it flashes red and sinks into the floor."""
        r = self.res[key]
        r.solid.tint_c = BAD
        anims = [
            Succession(
                Tween(r.solid, run_time=run_time * 0.35, tint=0.9),
                Tween(r.solid, run_time=run_time * 0.65, rate_func=rate_functions.ease_in_cubic,
                      rise=0.0, alpha=0.0),
            ),
            Tween(r.ghost, run_time=run_time, alpha=ghost),
        ]  # fmt: skip
        if r.shade is not None:
            anims.append(Tween(r.shade, run_time=run_time, alpha=0.0))
        return AnimationGroup(*anims)

    def pulse(self, key, color=GOLD, run_time=0.6, k=0.6):
        """``key`` lights up in ``color`` and settles back: "this one"."""
        p = self.res[key].solid
        return Succession(
            Do(lambda: setattr(p, "tint_c", color)),
            Tween(p, run_time=run_time * 0.35, tint=k),
            Tween(p, run_time=run_time * 0.65, tint=0.0),
        )

    def here(self, key, lift=0.3):
        """A point above ``key``, clear of its solid and of its ghost (for a tag)."""
        r = self.res[key]
        tops = [p.top(lift) for p in (r.solid, r.ghost) if p.alpha > 0.5]
        return max(tops, key=lambda t: t[2]) if tops else r.solid.top(lift)

    def set_built(self, *keys):
        """Put ``keys`` on the stage as already existing (no animation)."""
        for key in keys:
            r = self.res[key]
            r.solid.alpha, r.solid.rise, r.solid.tint = 1.0, 1.0, 0.0
            r.ghost.alpha = 0.0
            if r.shade is not None:
                r.shade.alpha = 1.0
        return self.refresh()

    def hull(self, grow=1.45):
        """Every corner the stage can reach (servers at their largest), to frame it."""
        pts = [
            f.local + self.slab.origin
            for f in self.slab.submobjects
            if hasattr(f, "local")
        ]
        for key, r in self.res.items():
            k = grow if key.startswith("web") else 1.0
            for part in r.parts:
                pts += [
                    f.local * k + part.origin
                    for f in part.submobjects
                    if hasattr(f, "local")
                ]
        return np.vstack(pts)

    def scan(self, run_time=2.0, color=BLUEPRINT, on_pass=None):
        """A bar of light sweeps the floor; ``on_pass(key)`` returns the animation to
        play as it reaches each existing resource."""
        x0 = self.centre[0] - self.size_w / 2 + 0.1
        x1 = self.centre[0] + self.size_w / 2 - 0.1
        bar = ScanBar(x0, x1, self.centre[1] - self.size_d / 2 + 0.1,
                      self.centre[1] + self.size_d / 2 - 0.1, color=color)  # fmt: skip
        bar.refresh()
        self.add(bar)
        self.scan_bar = bar
        anims = [
            Succession(
                Tween(bar, run_time=0.25, alpha=1.0),
                Tween(
                    bar,
                    run_time=run_time,
                    rate_func=rate_functions.ease_in_out_sine,
                    pos=1.0,
                ),
                Tween(bar, run_time=0.3, alpha=0.0),
            )
        ]
        if on_pass is not None:
            for key, r in self.res.items():
                if r.solid.alpha < 0.5:
                    continue
                frac = float(np.clip((r.solid.origin[0] - x0) / (x1 - x0), 0, 1))
                # the bar eases in and out (0.5 - 0.5 cos(pi a)): invert it for a
                when = 0.25 + run_time * (math.acos(1 - 2 * frac) / math.pi)
                a = on_pass(key)
                if a is not None:
                    anims.append(Succession(Wait(max(0.01, when - 0.1)), a))
        return AnimationGroup(*anims)
