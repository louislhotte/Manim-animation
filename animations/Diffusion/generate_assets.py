"""Bake the noise<->image trajectories the Diffusion film plays.

Everything shown "emerging from noise" is produced here, once, so the morph is
smooth and reproducible:

  * the hero image is the real ComfyUI output (``src_screens/foxgirl_sq.png``) --
    the very image the screenshot's "Save Image" node shows;
  * a second, procedural "mountain sunset" target for the prompt-conditioning
    scene -- same starting noise, a different result;
  * for each target: a trajectory of RES x RES frames that blends the clean image
    into ONE fixed field of gaussian static (the signal fades, the noise grows).
    Play it forwards to add noise; play it backwards to denoise. Both targets
    share the SAME static field, so "same noise, different prompt" reads true;
  * a heavily-blurred hero ("one big leap" = the blurry average) for the
    why-small-steps beat.

Saved to ``assets/diffusion.npz`` as uint8 RGBA arrays that drop straight into a
manim ``ImageMobject.pixel_array``. Deterministic (seeded). ``render.sh`` runs it
automatically if the npz is missing.

    python generate_assets.py           # regenerate assets/diffusion.npz
    python generate_assets.py --debug   # + montage PNGs to eyeball the frames
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
SRC = ROOT / "src_screens" / "foxgirl_sq.png"

SEED = 7
RES = 224          # working / display resolution (native fox-crop size)
N = 48             # frames per trajectory
P = 1.5            # signal-ramp exponent: structure lingers in noise, then snaps in
rng = np.random.default_rng(SEED)


# -------------------------------------------------------------------------- #
def _rgba(img_float: np.ndarray) -> np.ndarray:
    """HxWx3 float in [0,1] -> HxWx4 uint8 (opaque)."""
    a = np.clip(img_float, 0.0, 1.0)
    h, w = a.shape[:2]
    out = np.empty((h, w, 4), np.uint8)
    out[..., :3] = (a * 255.0 + 0.5).astype(np.uint8)
    out[..., 3] = 255
    return out


def load_fox() -> np.ndarray:
    im = Image.open(SRC).convert("RGB").resize((RES, RES), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255.0


def gray_static() -> np.ndarray:
    """One fixed field of gaussian static, centred on mid-grey."""
    g = 0.5 + 0.30 * rng.standard_normal((RES, RES, 1)).astype(np.float32)
    return np.repeat(np.clip(g, 0.0, 1.0), 3, axis=2)


def make_landscape() -> np.ndarray:
    """A procedural 'mountain lake at sunset' -- gradient sky, soft sun, two
    ridgelines and a mirrored water half with a reflection column."""
    H = W = RES
    yy = np.linspace(0.0, 1.0, H)[:, None]              # 0 top -> 1 bottom
    xx = np.linspace(0.0, 1.0, W)[None, :]
    hy = 0.58                                           # horizon line (fraction)

    top = np.array([0.15, 0.12, 0.34])                 # deep indigo
    mid = np.array([0.98, 0.52, 0.28])                 # warm orange
    pink = np.array([0.99, 0.72, 0.52])                # pink horizon band

    # --- sky: indigo -> orange, with a pink glow near the horizon ---------- #
    t = np.clip(yy / hy, 0.0, 1.0)                      # 0 top -> 1 horizon
    sky = (1 - t)[..., None] * top + t[..., None] * mid
    glow = np.exp(-((yy - hy) / 0.16) ** 2)            # band hugging horizon
    sky = sky + glow[..., None] * (pink - mid) * 0.6
    sky = np.broadcast_to(sky, (H, W, 3)).copy()

    # --- sun: soft disc + halo sitting on the horizon ---------------------- #
    sx, sy, r = 0.5, hy - 0.02, 0.075
    d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    disc = np.clip(1.0 - (d / r) ** 8, 0.0, 1.0)        # crisp-ish sun
    halo = np.exp(-((d / (r * 3.2)) ** 2)) * 0.55       # warm halo
    sun_col = np.array([1.0, 0.96, 0.80])
    sky = sky * (1 - disc)[..., None] + disc[..., None] * sun_col
    sky = sky + halo[..., None] * (np.array([1.0, 0.85, 0.55]) - 0.5) * 0.7

    img = np.clip(sky, 0.0, 1.0)

    # --- mountains: two layered silhouettes -------------------------------- #
    xs = np.linspace(0, 1, W)

    def ridge(base, amp, k, phase, col):
        prof = base - amp * (0.5 + 0.5 * np.sin(2 * np.pi * k * xs + phase)) \
            - 0.4 * amp * (0.5 + 0.5 * np.sin(2 * np.pi * (k * 1.9) * xs + phase * 2.1))
        for j in range(W):
            mask = yy[:, 0] >= prof[j]
            img[mask, j, :] = col
    # far range (lighter, higher), then near range (darker, lower)
    ridge(hy - 0.02, 0.11, 2.3, 0.7, np.array([0.30, 0.22, 0.40]))
    ridge(hy + 0.03, 0.10, 3.1, 2.0, np.array([0.14, 0.10, 0.22]))

    # --- water: mirror the sky below the horizon, darker, + a sun column --- #
    for i in range(H):
        if yy[i, 0] <= hy:
            continue
        src = int(round((2 * hy - yy[i, 0]) * (H - 1)))
        src = min(max(src, 0), H - 1)
        img[i, :, :] = img[src, :, :] * 0.72 + np.array([0.02, 0.02, 0.05])
    # bright reflection streak under the sun, broken by horizontal ripples
    col_dist = np.abs(xx - sx)
    refl = np.exp(-((col_dist / 0.06) ** 2))
    ripple = 0.5 + 0.5 * np.sin(2 * np.pi * 22 * yy)
    below = (yy > hy).astype(np.float32)
    add = below * refl * (0.35 + 0.4 * ripple)
    img = img + add[..., None] * (np.array([1.0, 0.82, 0.5]) - 0.3)

    return np.clip(img, 0.0, 1.0)


def trajectory(x0: np.ndarray, G: np.ndarray) -> np.ndarray:
    """[N,H,W,4] uint8: frame i blends signal level s_i of x0 with (1-s_i) static.

    i = 0    -> pure static (s=0);  i = N-1 -> clean image (s=1).
    Play forwards = denoise;  play backwards = add noise.
    """
    frames = np.empty((N, RES, RES, 4), np.uint8)
    for i in range(N):
        s = (i / (N - 1)) ** P
        frames[i] = _rgba(s * x0 + (1.0 - s) * G)
    return frames


def blurred(x0: np.ndarray) -> np.ndarray:
    """The 'one big leap' guess: a strong blur pulled toward its mean (mush)."""
    im = Image.fromarray((np.clip(x0, 0, 1) * 255).astype(np.uint8))
    im = im.filter(ImageFilter.GaussianBlur(radius=RES * 0.05))
    a = np.asarray(im, np.float32) / 255.0
    mean = a.mean(axis=(0, 1), keepdims=True)
    return a * 0.72 + mean * 0.28            # desaturate toward the average


# ========================================================================== #
# Gallery — illustrative examples of the kinds of things diffusion makes.
# (Procedural, so they are self-contained; the anime hero is the real one.)
# ========================================================================== #
def _grid():
    yy = np.linspace(-1.0, 1.0, RES)[:, None]
    xx = np.linspace(-1.0, 1.0, RES)[None, :]
    return xx, yy


def make_art(seed: int = 3) -> np.ndarray:
    """Domain-warped plasma through a vibrant palette -> abstract digital art."""
    x = np.linspace(-3, 3, RES)[None, :]
    y = np.linspace(-3, 3, RES)[:, None]
    warp = np.sin(1.5 * x + np.cos(1.1 * y)) + np.cos(1.7 * y + np.sin(0.9 * x))
    f = (np.sin(2.2 * x + 1.6 * warp) + np.cos(2.6 * y - 1.3 * warp)
         + 0.5 * np.sin(4.0 * warp))
    f = (f - f.min()) / (f.max() - f.min() + 1e-9)
    stops = np.array([[0.09, 0.03, 0.26], [0.42, 0.09, 0.55], [0.95, 0.24, 0.45],
                      [1.0, 0.62, 0.26], [1.0, 0.95, 0.62]])
    idx = f * (len(stops) - 1)
    lo = np.floor(idx).astype(int)
    hi = np.clip(lo + 1, 0, len(stops) - 1)
    t = (idx - lo)[..., None]
    img = stops[lo] * (1 - t) + stops[hi] * t
    return np.clip(img, 0, 1).astype(np.float32)


def make_sphere3d() -> np.ndarray:
    """A shaded sphere with specular + soft contact shadow -> looks like a render."""
    xx, yy = _grid()
    bg = ((1 - (yy + 1) / 2)[..., None] * np.array([0.10, 0.12, 0.16])
          + ((yy + 1) / 2)[..., None] * np.array([0.20, 0.22, 0.28]))
    img = np.broadcast_to(bg, (RES, RES, 3)).copy()
    R, cx, cy = 0.62, 0.0, -0.04
    nx = np.broadcast_to((xx - cx) / R, (RES, RES))
    ny = np.broadcast_to((yy - cy) / R, (RES, RES))
    r2 = nx ** 2 + ny ** 2
    mask = r2 <= 1.0
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    N = np.stack([nx, ny, nz], -1)
    L = np.array([-0.5, 0.7, 0.6]); L = L / np.linalg.norm(L)
    diff = np.clip(N @ L, 0, 1)
    Rr = 2 * (N @ L)[..., None] * N - L
    spec = np.clip(Rr @ np.array([0.0, 0.0, 1.0]), 0, 1) ** 32
    base = np.array([0.87, 0.30, 0.36])
    col = base * (0.14 + 0.86 * diff[..., None]) + spec[..., None] * 0.9
    sh = np.exp(-(((xx - cx) / (R * 1.15)) ** 2
                  + ((yy - (cy + R * 0.98)) / (R * 0.22)) ** 2))
    img = img * (1 - 0.55 * sh[..., None])
    img = np.where(mask[..., None], col, img)
    return np.clip(img, 0, 1)


def make_planet(seed: int = 5) -> np.ndarray:
    """A ringed, banded planet over a starfield -> sci-fi concept art."""
    rs = np.random.default_rng(seed)
    img = np.empty((RES, RES, 3), np.float32)
    img[:] = np.array([0.02, 0.02, 0.06])
    ys = rs.integers(0, RES, 240); xs = rs.integers(0, RES, 240)
    br = rs.uniform(0.3, 1.0, 240)
    img[ys, xs] = br[:, None] * np.array([1.0, 1.0, 1.0])
    xx, yy = _grid()
    R, cx, cy = 0.5, -0.08, 0.06
    nx = np.broadcast_to((xx - cx) / R, (RES, RES))
    ny = np.broadcast_to((yy - cy) / R, (RES, RES))
    r2 = nx ** 2 + ny ** 2
    mask = r2 <= 1.0
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    N = np.stack([nx, ny, nz], -1)
    L = np.array([-0.6, 0.4, 0.7]); L = L / np.linalg.norm(L)
    diff = np.clip(N @ L, 0, 1)
    band = 0.5 + 0.5 * np.sin(8 * ny + 2 * nx)
    base = (np.array([0.86, 0.56, 0.30]) * band[..., None]
            + np.array([0.55, 0.30, 0.50]) * (1 - band)[..., None])
    col = base * (0.12 + 0.9 * diff[..., None])
    img = np.where(mask[..., None], col, img)
    rr = np.sqrt((xx - cx) ** 2 + ((yy - cy) / 0.30) ** 2)
    ring = (rr > 0.72) & (rr < 0.98)
    draw = ring & (~mask | (yy > cy))            # ring passes in front below centre
    ringcol = np.array([0.92, 0.82, 0.62])
    img = np.where(draw[..., None], 0.55 * img + 0.45 * ringcol, img)
    return np.clip(img, 0, 1)


def make_cinematic() -> np.ndarray:
    """An aurora night over mountains -> a cinematic frame (base for the video tile)."""
    yy = np.linspace(0.0, 1.0, RES)[:, None]
    xx = np.linspace(0.0, 1.0, RES)[None, :]
    sky = ((1 - yy)[..., None] * np.array([0.03, 0.04, 0.13])
           + yy[..., None] * np.array([0.05, 0.10, 0.20]))
    img = np.broadcast_to(sky, (RES, RES, 3)).copy()
    for k, (cyy, amp, col) in enumerate([(0.30, 0.05, [0.12, 0.9, 0.5]),
                                         (0.37, 0.04, [0.22, 0.7, 0.92])]):
        centre = cyy + amp * np.sin(2 * np.pi * 2 * xx + k)
        band = np.exp(-((yy - centre) / 0.055) ** 2)
        img = img + band[..., None] * np.array(col) * 0.5
    d = np.sqrt((xx - 0.76) ** 2 + (yy - 0.20) ** 2)
    moon = np.clip(1 - (d / 0.045) ** 8, 0, 1)
    img = img * (1 - moon[..., None]) + moon[..., None] * np.array([1.0, 1.0, 0.95])
    xs = np.linspace(0, 1, RES)
    prof = (0.64 - 0.12 * (0.5 + 0.5 * np.sin(2 * np.pi * 2.2 * xs + 0.5))
            - 0.05 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.3 * xs)))
    mtn = np.array([0.03, 0.05, 0.09])
    for j in range(RES):
        img[yy[:, 0] >= prof[j], j, :] = mtn
    return np.clip(img, 0, 1)


def film_frame(base: np.ndarray) -> np.ndarray:
    """Wrap a scene in a filmstrip (sprocket bars) + a translucent play button."""
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    bar = int(RES * 0.11)
    d.rectangle([0, 0, RES, bar], fill=(6, 6, 8))
    d.rectangle([0, RES - bar, RES, RES], fill=(6, 6, 8))
    hw, step, pad = int(RES * 0.045), int(RES * 0.12), int(bar * 0.30)
    for cx in range(step // 2, RES, step):
        d.rounded_rectangle([cx - hw // 2, pad, cx + hw // 2, bar - pad],
                            radius=2, fill=(225, 225, 225))
        d.rounded_rectangle([cx - hw // 2, RES - bar + pad, cx + hw // 2, RES - pad],
                            radius=2, fill=(225, 225, 225))
    r = int(RES * 0.15)
    cx, cy = RES // 2, RES // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, 120))
    t = int(r * 0.55)
    d.polygon([(cx - t // 2, cy - t), (cx - t // 2, cy + t), (cx + t, cy)],
              fill=(255, 255, 255, 235))
    return np.asarray(im, np.float32) / 255.0


# -------------------------------------------------------------------------- #
def main() -> None:
    x0_fox = load_fox()
    x0_land = make_landscape()
    G = gray_static()

    fox = trajectory(x0_fox, G)
    land = trajectory(x0_land, G)

    np.savez_compressed(
        ASSETS / "diffusion.npz",
        fox=fox,
        land=land,
        x0_fox=_rgba(x0_fox),
        x0_land=_rgba(x0_land),
        noise=_rgba(G),
        fox_blur=_rgba(blurred(x0_fox)),
        res=np.array(RES),
        n=np.array(N),
    )
    print(f">> wrote {ASSETS/'diffusion.npz'}  (RES={RES}, N={N})")

    # --- gallery: what diffusion can make (PNGs the film loads directly) ---- #
    gdir = ASSETS / "gallery"
    gdir.mkdir(exist_ok=True)
    gallery = {
        "anime": x0_fox,                 # the real ComfyUI generation
        "photo": x0_land,                # the procedural sunset
        "art": make_art(),
        "render3d": make_sphere3d(),
        "concept": make_planet(),
        "video": film_frame(make_cinematic()),
    }
    for name, arr in gallery.items():
        Image.fromarray(_rgba(arr)[..., :3]).save(gdir / f"{name}.png")
    print(f">> wrote {len(gallery)} gallery PNGs to {gdir}")

    if "--debug" in sys.argv:
        def strip(frames, path, k=8):
            idx = np.linspace(0, len(frames) - 1, k).round().astype(int)
            row = np.concatenate([frames[i][..., :3] for i in idx], axis=1)
            Image.fromarray(row).save(path)
            print(f">> {path}")
        strip(fox, ASSETS / "debug_fox.png")
        strip(land, ASSETS / "debug_land.png")
        Image.fromarray(_rgba(x0_land)[..., :3]).save(ASSETS / "debug_land_clean.png")
        Image.fromarray(_rgba(blurred(x0_fox))[..., :3]).save(ASSETS / "debug_blur.png")
        Image.fromarray(_rgba(G)[..., :3]).save(ASSETS / "debug_noise.png")
        order = ["anime", "photo", "art", "render3d", "concept", "video"]
        row = np.concatenate([_rgba(gallery[k])[..., :3] for k in order], axis=1)
        Image.fromarray(row).save(ASSETS / "debug_gallery.png")
        print(f">> {ASSETS/'debug_gallery.png'}")


if __name__ == "__main__":
    main()
