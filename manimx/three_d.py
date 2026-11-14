"""3D scenes with a HUD: a camera that keeps panels on screen, sits off-centre, and
lets a mobject paint itself; and the scene helpers that go with it.

Use ``ExplainerStageScene`` when a 3D scene has a fixed column of panels beside a
3D subject (Terraform's diorama, MIP's map of Paris)::

    class _Base3D(_Common, ExplainerStageScene):
        def scene_x(self):
            panel = self.hud_root(make_panel())          # stays on screen, even if
            self.sway(theta=-60, amp=8, period=18)       # its updaters rebuild it
            tag = self.billboard(label, lambda: part.top())

``Painter`` is the escape hatch for what Cairo's vector path cannot do well: a
textured ground plane, ten thousand dots, a glow. The mobject receives the camera
and the frame's pixel array and draws by itself (NumPy, Cairo, a GPU buffer).
"""

from __future__ import annotations

import itertools as it

import numpy as np
from manim import DEGREES, TAU, Mobject, ThreeDCamera
from manim.camera.camera import Camera

from .scene import Explainer3DScene


class Painter(Mobject):
    """A mobject that draws itself: override ``paint(camera, pixels)``.

    ``pixels`` is the frame being built, RGBA uint8, row 0 at the top. Mobjects are
    painted in scene order (``z_index`` first), so a painter can sit under or over
    ordinary mobjects. ``camera.project_points`` maps world points to frame units and
    ``camera.to_pixels`` maps those to pixels.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = np.zeros((1, 3))  # a mobject without points is never displayed

    def paint(self, camera, pixels):
        raise NotImplementedError


class PainterCameraMixin:
    """Adds ``Painter`` mobjects to a Cairo camera."""

    def type_or_raise(self, mobject):
        if isinstance(mobject, Painter):
            return Painter
        return super().type_or_raise(mobject)

    def _capture(self, mobjects, **kwargs):
        mobjects = self.get_mobjects_to_display(mobjects, **kwargs)
        # a painter that is the ground goes first, whatever Manim's depth sort says
        mobjects.sort(key=lambda m: not getattr(m, "underlay", False))
        for kind, group in it.groupby(mobjects, self.type_or_raise):
            if kind is Painter:
                for m in group:
                    m.paint(self, self.pixel_array)
            else:
                self.display_funcs[kind](list(group), self.pixel_array)

    def to_pixels(self, pts):
        """Frame units (x right, y up, centre 0) -> pixel coordinates (x, y)."""
        pts = np.asarray(pts, dtype=float)
        sx = self.pixel_width / self.frame_width
        sy = self.pixel_height / self.frame_height
        return np.column_stack(
            [
                self.pixel_width / 2 + pts[:, 0] * sx,
                self.pixel_height / 2 - pts[:, 1] * sy,
            ]
        )


class PainterCamera(PainterCameraMixin, Camera):
    """The flat camera, with painters."""

    def capture_mobjects(self, mobjects, **kwargs):
        self._capture(mobjects, **kwargs)


class HudCamera(PainterCameraMixin, ThreeDCamera):
    """A 3D camera for scenes with a HUD.

    * ``screen_shift``: added to every projected point, so the 3D subject can live
      beside a column of panels while the camera still turns around *it*;
    * ``hud_roots``: groups whose whole *current* family is fixed in the frame on
      every capture, so panels whose updaters add or rebuild children stay put;
    * ``Painter`` mobjects draw themselves.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.screen_shift = np.zeros(3)
        self.hud_roots = []

    def capture_mobjects(self, mobjects, **kwargs):
        for root in self.hud_roots:
            self.fixed_in_frame_mobjects.update(root.get_family())
        self.reset_rotation_matrix()
        self._capture(mobjects, **kwargs)

    def project_points(self, points):
        return super().project_points(points) + self.screen_shift

    def get_cairo_context(self, pixel_array):
        """Manim's canvas matrix, without the frame centre.

        ``ThreeDCamera`` already subtracts ``frame_center`` when it projects; the
        flat camera's canvas subtracts it a second time (and from the HUD too, and
        only if it was set before the first frame, since the context is cached).
        Here ``frame_center`` is only the world point the camera looks at: it lands
        on the middle of the screen, plus ``screen_shift``."""
        import cairo

        ctx = self.get_cached_cairo_context(pixel_array)
        if ctx:
            return ctx
        pw, ph = self.pixel_width, self.pixel_height
        fw, fh = self.frame_width, self.frame_height
        surface = cairo.ImageSurface.create_for_data(
            pixel_array.data, cairo.FORMAT_ARGB32, pw, ph
        )
        ctx = cairo.Context(surface)
        ctx.scale(pw, ph)
        ctx.set_matrix(cairo.Matrix(pw / fw, 0, 0, -(ph / fh), pw / 2, ph / 2))
        self.cache_cairo_context(pixel_array, ctx)
        return ctx


class ExplainerStageScene(Explainer3DScene):
    """A 3D explainer scene on a ``HudCamera`` (or a subclass of it)."""

    CAMERA = HudCamera

    def __init__(self, **kw):
        kw.setdefault("camera_class", self.CAMERA)
        super().__init__(**kw)

    def hud_root(self, *mobs, z=10):
        """Groups that live on the screen, not in the scene (panels with updaters)."""
        for m in mobs:
            m.set_z_index(z)
            self.camera.hud_roots.append(m)
        return mobs[0] if len(mobs) == 1 else mobs

    def billboard(self, mob, point, z=5):
        """A label that floats at ``point()`` (a world position), facing the camera."""
        mob.anchor_fn = point
        mob.move_to(point())
        mob.add_updater(lambda m: m.move_to(m.anchor_fn()))
        self.camera.add_fixed_orientation_mobjects(mob)
        mob.set_z_index(z)
        return mob

    def sway(self, theta, amp=8.0, period=17.0):
        """Let the camera swing slowly around ``theta`` (degrees): the set keeps a
        front, the HUD stays readable. ``amp=0`` stops it."""
        tr = self.camera.theta_tracker
        tr.clear_updaters()
        tr.sway = (theta, amp, period, 0.0)

        def swing(m, dt):
            th, a, per, t = m.sway
            t += dt
            m.sway = (th, a, per, t)
            m.set_value((th + a * np.sin(TAU * t / per)) * DEGREES)

        if amp:
            tr.add_updater(swing)
            self.add(tr)
        else:
            self.remove(tr)

    def wipe(self, rt=None):
        tr = self.camera.theta_tracker
        tr.clear_updaters()
        self.remove(tr)
        super().wipe(rt)
