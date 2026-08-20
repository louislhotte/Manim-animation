"""Bake a shaded blue 'planet' PNG from a flat gray-continents globe image.

Reads ``source_globe.png`` (an orthographic globe: opaque disk, land = gray,
ocean = white, outside = transparent) and produces ``planet_blue.png``: a sphere
with blue oceans, light land, diffuse + specular lighting from the upper-left, a
darkened limb and a soft atmospheric rim — so it reads as a real planet instead
of a flat disk. Fully vectorised with numpy; only needs Pillow + numpy (already
in the Manim venv). Re-run after tweaking colours:

    <venv>/bin/python assets/make_planet.py
"""
import numpy as np
from PIL import Image

SRC = "assets/source_globe.png"
OUT = "assets/planet_blue.png"
S = 1500                      # output resolution (square)

# palette (RGB 0-255)
OCEAN = np.array([26, 82, 140], float)      # deep sea blue
LAND = np.array([150, 176, 202], float)     # light steel-blue land
ATMO = np.array([125, 205, 255], float)     # atmospheric limb glow
SPEC = np.array([255, 255, 255], float)     # specular highlight


def main():
    src = np.array(Image.open(SRC).convert("RGBA")).astype(float)
    a = src[..., 3]
    lum = 0.299 * src[..., 0] + 0.587 * src[..., 1] + 0.114 * src[..., 2]
    land_src = (a > 10) & (lum < 235)                 # gray continents

    ys, xs = np.where(a > 10)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    rs = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2

    j, i = np.mgrid[0:S, 0:S]
    nx = (i - S / 2) / (S / 2)
    ny = (j - S / 2) / (S / 2)                         # +down (image space)
    r = np.hypot(nx, ny)
    inside = r <= 1.0
    nz = np.sqrt(np.clip(1 - r * r, 0, 1))            # sphere normal z

    # diffuse lighting, world-up = -ny, light from upper-left-front
    ld = np.array([-0.40, 0.50, 0.90])
    ld /= np.linalg.norm(ld)
    ndotl = np.clip(nx * ld[0] + (-ny) * ld[1] + nz * ld[2], 0, 1)
    # gentle, even sphere shading — no blown-out sub-solar hotspot
    bright = np.clip((0.46 + 0.66 * ndotl) * (0.66 + 0.34 * nz), 0, 1.1)

    # sample continents from the source disk
    sx = np.clip((cx + nx * rs).astype(int), 0, src.shape[1] - 1)
    sy = np.clip((cy + ny * rs).astype(int), 0, src.shape[0] - 1)
    is_land = land_src[sy, sx] & (r < 0.965)

    col = np.where(is_land[..., None], LAND, OCEAN) * bright[..., None]

    # a soft, broad specular sheen (kept low so labels stay readable over it)
    h = np.array([ld[0], ld[1], ld[2] + 1.0])
    h /= np.linalg.norm(h)
    ndoth = np.clip(nx * h[0] + (-ny) * h[1] + nz * h[2], 0, 1)
    col += (ndoth ** 22 * 0.14)[..., None] * SPEC

    # atmospheric rim on the outer few %
    t = (np.clip((r - 0.95) / 0.05, 0, 1) * inside)[..., None]
    col = col * (1 - 0.55 * t) + ATMO * (0.55 * t)

    col = np.clip(col, 0, 255)
    edge = 1.5 / (S / 2)
    alpha = np.clip((1.0 - r) / edge, 0, 1) * 255
    out = np.dstack([col, alpha]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(OUT)
    print(f">> wrote {OUT}  ({S}x{S})  land frac={is_land[inside].mean():.2f}")


if __name__ == "__main__":
    main()
