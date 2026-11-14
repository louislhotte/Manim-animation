"""stage.py: Paris as the ground of a 3D scene.

Cairo cannot texture a tilted plane (an ``ImageMobject`` is only ever scaled and
rotated), and fifty thousand street segments are too many vector paths per frame.
So the map is a texture on the GPU: ``MapPlane`` is a ``manimx.Painter`` that draws
the ground with exactly the camera's projection, through an offscreen OpenGL
context (``moderngl``, which Manim already depends on), and hands the pixels to the
frame. Everything else (courses, couriers, labels, HUD) is ordinary Manim on top.

Why it stays sharp at every distance: each texture carries its own mip levels,
*drawn* at each scale (``city.texture`` with the street widths of that scale), not
averaged down from the largest one. The GPU blends the levels per pixel
(trilinear + anisotropic filtering), the way a map renderer changes style with
zoom, so thin streets neither shimmer nor fade when the camera pulls back.

World coordinates: kilometres east / north of the stage's centre, ``z`` up.
"""

from __future__ import annotations

import numpy as np
from manimx import BG, Painter

import city

_GL = {}


def _context():
    if "ctx" not in _GL:
        import moderngl

        ctx = moderngl.create_standalone_context()
        prog = ctx.program(
            vertex_shader="""
            #version 330
            uniform mat3 rot;         // world -> camera
            uniform vec3 centre;      // what the camera looks at (world)
            uniform float focal;
            uniform float zoom;
            uniform vec2 shift;       // screen shift, frame units
            uniform vec2 half_frame;  // half the frame, frame units
            in vec2 in_pos;           // a corner of the ground rectangle (world x, y)
            in vec2 in_uv;
            out vec2 uv;
            out float depth;
            void main() {
                vec3 r = rot * (vec3(in_pos, 0.0) - centre);
                float w = focal - r.z;   // Manim: x' = zoom * focal * x / (focal - z)
                gl_Position = vec4((zoom * focal * r.x + shift.x * w) / half_frame.x,
                                   (zoom * focal * r.y + shift.y * w) / half_frame.y,
                                   0.0, w);
                uv = in_uv;
                depth = w;
            }
            """,
            fragment_shader="""
            #version 330
            uniform sampler2D tex;
            uniform float feather;    // soft edge, in texture units
            uniform float opacity;
            uniform vec3 fog;         // (start, end, strength): depth where the ground fades
            uniform vec3 tint;        // what it fades to
            in vec2 uv;
            in float depth;
            out vec4 color;
            void main() {
                vec3 c = texture(tex, uv).rgb;
                vec2 d = min(uv, 1.0 - uv);
                float a = feather > 0.0 ? smoothstep(0.0, feather, min(d.x, d.y)) : 1.0;
                float f = fog.z * smoothstep(fog.x, fog.y, depth);
                color = vec4(mix(c, tint, f), a * opacity);
            }
            """,
        )
        _GL.update(ctx=ctx, prog=prog, moderngl=moderngl, fbo={})
    return _GL


class _Shared:
    """Held by reference when Manim deep-copies a mobject (a fade copies it)."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __deepcopy__(self, memo):
        return self


class MapPlane(Painter):
    """The ground: one or more map textures laid on ``z = 0``.

    ``add(cx, cy, width_m, px, ...)`` lays the window of the real map centred on
    (cx, cy) metres, ``width_m`` wide, drawn ``px`` pixels wide at its finest
    level. Later layers are drawn over earlier ones with a soft edge, so a detailed
    close-up can sit inside a coarser overview.
    """

    def __init__(self, origin, scale=0.001, bg=BG):
        """``origin``: the map point (metres) at the world's (0, 0); ``scale``:
        world units per metre (0.001: kilometres)."""
        super().__init__()
        self.origin = np.array(origin, dtype=float)
        self.unit = scale  # (not ``scale``: that is a Mobject method)
        self.bg = bg
        self.opacity = 1.0
        self.fog = (0.0, 0.0, 0.0)
        self.res = _Shared(layers=[], last=None)
        self.underlay = True  # drawn before everything else
        self.set_z_index(-100)

    # ---- coordinates -------------------------------------------------------- #
    def w(self, xy, z=0.0):
        """Map metres -> world point(s)."""
        xy = np.asarray(xy, dtype=float)
        out = np.zeros((*xy.shape[:-1], 3))
        out[..., :2] = (xy[..., :2] - self.origin) * self.unit
        out[..., 2] = z
        return out

    # ---- layers --------------------------------------------------------------- #
    def add_layer(
        self, cx, cy, width_m, px, aspect=None, levels=4, feather=0.04, **style
    ):
        """``aspect`` = height / width of the window (default: the frame's)."""
        px = int(px) // 2**levels * 2**levels
        h = int(round(px * (aspect or 9 / 16))) // 2**levels * 2**levels
        imgs = [
            city.texture(cx, cy, width_m, px >> k, h >> k, min_scale=1.0, **style)
            for k in range(levels + 1)
        ]
        height_m = width_m * h / px
        lo = (np.array([cx - width_m / 2, cy - height_m / 2]) - self.origin) * self.unit
        hi = (np.array([cx + width_m / 2, cy + height_m / 2]) - self.origin) * self.unit
        self.res.layers.append({"imgs": imgs, "rect": (*lo, *hi), "feather": feather})
        return self

    # ---- fading (Manim animates a copy toward a faded copy) -------------------- #
    def fade(self, darkness=0.5, family=True):
        self.opacity = self.opacity * (1 - darkness)
        return self

    def interpolate_color(self, m1, m2, alpha):
        self.opacity = (1 - alpha) * m1.opacity + alpha * m2.opacity
        self.fog = tuple(
            (1 - alpha) * a + alpha * b for a, b in zip(m1.fog, m2.fog, strict=True)
        )

    # ---- drawing -------------------------------------------------------------- #
    def _upload(self, gl):
        ctx, mgl = gl["ctx"], gl["moderngl"]
        for layer in self.res.layers:
            if "tex" in layer:
                continue
            base = layer["imgs"][0]
            tex = ctx.texture((base.shape[1], base.shape[0]), 4, base.tobytes())
            tex.build_mipmaps()
            for k, img in enumerate(layer["imgs"][1:], 1):  # our own, drawn levels
                tex.write(img.tobytes(), level=k)
            tex.filter = (mgl.LINEAR_MIPMAP_LINEAR, mgl.LINEAR)
            tex.anisotropy = 16.0
            tex.repeat_x = tex.repeat_y = False
            x0, y0, x1, y1 = layer["rect"]
            quad = np.array(
                [[x0, y0, 0, 1], [x1, y0, 1, 1], [x0, y1, 0, 0], [x1, y1, 1, 0]],
                dtype="f4",
            )
            layer["tex"] = tex
            layer["vao"] = ctx.vertex_array(
                gl["prog"], [(ctx.buffer(quad.tobytes()), "2f 2f", "in_pos", "in_uv")]
            )
            del layer["imgs"]

    def paint(self, camera, pixels):
        if self.opacity <= 0.002:
            return
        gl = _context()
        ctx, prog, mgl = gl["ctx"], gl["prog"], gl["moderngl"]
        self._upload(gl)
        h, w = pixels.shape[:2]
        if (w, h) not in gl["fbo"]:
            ms = ctx.framebuffer(
                color_attachments=[ctx.renderbuffer((w, h), 4, samples=4)]
            )
            gl["fbo"][w, h] = (
                ms,
                ctx.framebuffer(color_attachments=[ctx.texture((w, h), 4)]),
            )
        ms, flat = gl["fbo"][w, h]

        flat_cam = not hasattr(camera, "get_rotation_matrix")
        rot = np.identity(3) if flat_cam else np.array(camera.get_rotation_matrix())
        focal = 1e6 if flat_cam else float(camera.get_focal_distance())
        zoom = 1.0 if flat_cam else float(camera.get_zoom())
        shift = np.array(getattr(camera, "screen_shift", np.zeros(3)), dtype=float)
        centre = np.array(camera.frame_center, dtype=float)
        key = (
            rot.tobytes(), centre.tobytes(), focal, zoom, shift.tobytes(),
            round(self.opacity, 4), tuple(round(v, 4) for v in self.fog), w, h,
        )  # fmt: skip
        if self.res.last is None or self.res.last[0] != key:
            from manim import ManimColor

            bg = ManimColor(self.bg).to_rgb()
            ms.use()
            ctx.clear(*bg, 1.0)
            ctx.enable(mgl.BLEND)
            ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
            prog["rot"].write(rot.T.astype("f4").tobytes())
            prog["centre"].value = tuple(centre)
            prog["focal"].value = focal
            prog["zoom"].value = zoom
            prog["shift"].value = (float(shift[0]), float(shift[1]))
            prog["half_frame"].value = (camera.frame_width / 2, camera.frame_height / 2)
            prog["opacity"].value = float(self.opacity)
            prog["fog"].value = tuple(float(v) for v in self.fog)
            prog["tint"].value = tuple(bg)
            for layer in self.res.layers:
                prog["feather"].value = float(layer["feather"])
                layer["tex"].use(0)
                layer["vao"].render(mgl.TRIANGLE_STRIP)
            ctx.copy_framebuffer(flat, ms)
            img = np.frombuffer(flat.read(components=4), dtype=np.uint8).reshape(
                h, w, 4
            )
            self.res.last = (key, img[::-1])
        pixels[:] = self.res.last[1]


# --------------------------------------------------------------------------- #
# what moves on the map: many small things, drawn straight onto the frame
# --------------------------------------------------------------------------- #
def _bgr(color, a=1.0):
    """Manim's pixel array is RGBA, the Cairo surface on it reads BGRA: swap."""
    from manim import ManimColor

    r, g, b = ManimColor(color).to_rgb()
    return (b, g, r, a)


class Layer(Painter):
    """A painter with an ``alpha`` that Manim's fades understand."""

    def __init__(self):
        super().__init__()
        self.alpha = 1.0
        self.add_updater(
            lambda m: None
        )  # always repainted (its attributes are tweened)

    def fade(self, darkness=0.5, family=True):
        self.alpha = self.alpha * (1 - darkness)
        return self

    def interpolate_color(self, m1, m2, alpha):
        self.alpha = (1 - alpha) * m1.alpha + alpha * m2.alpha


class Swarm(Layer):
    """Couriers and the trails of their courses.

    ``now`` (minutes) is the time of day: every courier sits where its course puts
    it at that minute, with the trail of what it has ridden. ``pop`` (0..1) brings
    the couriers in one after another; ``lift`` (0..1) raises every trail in time
    (height = minutes), turning the plan into threads above the city."""

    def __init__(self, plane, timelines, color, zt=0.03, seed=3, r=0.05, width=0.022):
        super().__init__()
        self.T = [np.asarray(v, dtype=float)[:, 0] for v in timelines]
        self.P = [plane.w(np.asarray(v, dtype=float)[:, 1:3]) for v in timelines]
        self.color, self.zt, self.r, self.lw = (
            color,
            zt,
            r,
            width,
        )  # (``width`` is Manim's)
        self.now, self.pop, self.lift, self.trail = 0.0, 1.0, 0.0, 1.0
        self.old, self.tail = (
            0.42,
            6.0,
        )  # how bright an old trail is; minutes that count as recent
        self.delay = np.random.default_rng(seed).random(len(self.T)) * 0.75
        self.hero = None  # index of a courier drawn in ``hero_color``
        self.hero_color = color
        self.set_z_index(5)

    def paint(self, camera, pixels):
        if self.alpha <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        import cairo

        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        heads, paths, times = [], [], []
        for T, P in zip(self.T, self.P, strict=True):
            k = int(np.searchsorted(T, self.now, side="right"))
            if k >= len(T):
                pts, tt = P, T
            else:
                a = (self.now - T[k - 1]) / max(T[k] - T[k - 1], 1e-9) if k > 0 else 0.0
                head = (
                    P[max(k - 1, 0)] + (P[k] - P[max(k - 1, 0)]) * a if k > 0 else P[0]
                )
                pts = np.vstack([P[:k], head[None, :]])
                tt = np.append(T[:k], self.now)
            if self.lift:
                pts = pts.copy()
                pts[:, 2] = tt * self.zt * self.lift
            paths.append(pts)
            times.append(tt)
        flat = camera.project_points(np.vstack(paths))
        k0 = 0
        for i, pts in enumerate(paths):
            q = flat[k0 : k0 + len(pts)]
            k0 += len(pts)
            a = (
                float(np.clip((self.pop * 1.75 - self.delay[i]) / 0.25, 0, 1))
                * self.alpha
            )
            if a <= 0:
                continue
            color = self.hero_color if i == self.hero else self.color
            if len(q) > 1 and self.trail > 0:
                # the whole course so far, quietly; the last few minutes, brightly
                ctx.new_path()
                ctx.move_to(q[0][0], q[0][1])
                for x, y, _ in q[1:]:
                    ctx.line_to(x, y)
                ctx.set_source_rgba(*_bgr(color, self.old * a * self.trail))
                ctx.set_line_width(self.lw)
                ctx.stroke()
                tt = times[i]
                recent = int(np.searchsorted(tt, tt[-1] - self.tail))
                if recent < len(q) - 1:
                    ctx.new_path()
                    ctx.move_to(q[recent][0], q[recent][1])
                    for x, y, _ in q[recent + 1 :]:
                        ctx.line_to(x, y)
                    ctx.set_source_rgba(*_bgr(color, 0.18 * a * self.trail))
                    ctx.set_line_width(self.lw * 3.4)
                    ctx.stroke_preserve()
                    ctx.set_source_rgba(*_bgr(color, 0.95 * a * self.trail))
                    ctx.set_line_width(self.lw * 1.25)
                    ctx.stroke()
            heads.append((q[-1], a, color, i == self.hero))
        for (x, y, _), a, color, big in heads:
            r = self.r * (1.7 if big else 1.0)
            ctx.new_path()
            ctx.arc(x, y, r * 2.1, 0, 6.2832)
            ctx.set_source_rgba(*_bgr(color, 0.20 * a))
            ctx.fill()
            ctx.arc(x, y, r, 0, 6.2832)
            ctx.set_source_rgba(*_bgr(color, a))
            ctx.fill()


class Orders(Layer):
    """Every order of the city: a short link from its restaurant to its customer.

    ``show`` (0..1) lets them appear one after another; with ``now`` (minutes) an
    order turns ``done`` colour when it is delivered, with a ring that spreads and
    fades for ``ring`` minutes."""

    def __init__(self, plane, orders, color, done, seed=5, ring=2.5):
        super().__init__()
        self.R = plane.w(np.array([o["R"] for o in orders], dtype=float))
        self.C = plane.w(np.array([o["C"] for o in orders], dtype=float))
        self.t = np.array([np.inf if o.get("t") is None else o["t"] for o in orders])
        self.color, self.done, self.ring = color, done, ring
        self.show, self.now = 1.0, -1.0
        self.delay = np.random.default_rng(seed).random(len(orders)) * 0.8
        self.set_z_index(4)

    def paint(self, camera, pixels):
        if self.alpha <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        r = camera.project_points(self.R.copy())
        c = camera.project_points(self.C.copy())
        vis = np.clip((self.show * 1.8 - self.delay) / 0.2, 0, 1) * self.alpha
        got = self.t <= self.now
        for i in np.flatnonzero(vis > 0):
            a = float(vis[i])
            col = self.done if got[i] else self.color
            ctx.new_path()
            ctx.move_to(r[i][0], r[i][1])
            ctx.line_to(c[i][0], c[i][1])
            ctx.set_source_rgba(*_bgr(col, (0.55 if got[i] else 0.42) * a))
            ctx.set_line_width(0.014)
            ctx.stroke()
            ctx.rectangle(r[i][0] - 0.028, r[i][1] - 0.028, 0.056, 0.056)
            ctx.set_source_rgba(*_bgr(col, 0.9 * a))
            ctx.fill()
            ctx.arc(c[i][0], c[i][1], 0.03, 0, 6.2832)
            ctx.fill()
            age = self.now - self.t[i]
            if 0 <= age < self.ring:
                k = age / self.ring
                ctx.new_path()
                ctx.arc(c[i][0], c[i][1], 0.05 + 0.22 * k, 0, 6.2832)
                ctx.set_source_rgba(*_bgr(self.done, (1 - k) * 0.9 * a))
                ctx.set_line_width(0.022)
                ctx.stroke()


class Guess(Layer):
    """ "Who delivers what?": every order tied to one courier of its zone, at random,
    and a new draw every time ``k`` passes an integer."""

    def __init__(self, plane, zones, color, draws=24, seed=11):
        super().__init__()
        rng = np.random.default_rng(seed)
        a, b = [], []
        for z in zones:
            starts = plane.w(np.array([c["start"] for c in z["couriers"]], dtype=float))
            rest = plane.w(np.array([o["R"] for o in z["orders"]], dtype=float))
            pick = rng.integers(0, len(starts), size=(draws, len(rest)))
            a.append(np.stack([starts[p] for p in pick]))
            b.append(np.broadcast_to(rest, (draws, *rest.shape)))
        self.A, self.B = np.concatenate(a, axis=1), np.concatenate(b, axis=1)
        self.color, self.k, self.alpha = color, 0.0, 0.0
        self.set_z_index(3)

    def paint(self, camera, pixels):
        if self.alpha <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        d = int(self.k) % len(self.A)
        frac = self.k - int(self.k)
        a = float(np.clip(min(frac, 1 - frac) * 6, 0, 1)) * self.alpha
        p = camera.project_points(self.A[d].copy())
        q = camera.project_points(self.B[d].copy())
        ctx.new_path()
        for (x0, y0, _), (x1, y1, _) in zip(p, q, strict=True):
            ctx.move_to(x0, y0)
            ctx.line_to(x1, y1)
        ctx.set_source_rgba(*_bgr(self.color, 0.55 * a))
        ctx.set_line_width(0.016)
        ctx.stroke()
