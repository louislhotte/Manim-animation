#!/usr/bin/env python3
"""Turn a photo into a single closed path for a Fourier / epicycle drawing.

The pipeline is dependency-light on purpose (numpy + scipy + Pillow only, all of
which the Manim env already ships) so it runs offline:

    1. load  -> grayscale, downscale, gentle blur
    2. Otsu  -> pick the light/dark level that isolates the ink
    3. marching squares (pure numpy) -> ordered iso-contour loops, which capture
       *internal* features (eyes, nose, mouth), not just the silhouette
    4. keep the longest loops, then stitch them into ONE path with a greedy
       nearest-neighbour tour (the pen travels in short straight hops)
    5. resample by arc length, center + scale into Manim units, save as complex

Outputs (next to this file):
    data/louis_path.npy   complex128, shape (N,) -- the drawing, in Manim units
    data/preview.png      sanity check: target path (grey) vs the M-vector
                          Fourier reconstruction (black)

Run directly (uses assets/louis.png) or pass a path:  python generate_path.py [img]
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
DEFAULT_IMG = HERE / "assets" / "louis.png"
OUT_NPY = HERE / "data" / "louis_path.npy"
OUT_PREVIEW = HERE / "data" / "preview.png"

# --- tunables --------------------------------------------------------------- #
MAX_DIM = 360          # downscale the long edge to this before tracing
BLUR_SIGMA = 1.1       # smooths the staircase edges -> fewer tiny contours
KEEP_LOOPS = 24        # keep only the N longest iso-contour loops
MIN_LOOP_PTS = 30      # drop contours shorter than this (noise)
N_SAMPLES = 2600       # points in the final resampled path (Fourier period)
PREVIEW_VECTORS = 220  # how many epicycles the preview reconstruction uses
FIT_HALF_H = 3.3       # target half-height in Manim units
FIT_HALF_W = 6.2       # target half-width in Manim units


def otsu_level(gray_u8: np.ndarray) -> float:
    """Classic Otsu threshold on a uint8 image -> the level maximising between
    class variance (separates the dark ink from the lighter paint)."""
    hist = np.bincount(gray_u8.ravel(), minlength=256).astype(float)
    total = gray_u8.size
    sum_total = np.dot(np.arange(256), hist)
    w_b = 0.0
    sum_b = 0.0
    best_var = -1.0
    best_t = 127
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best_var:
            best_var = var
            best_t = t
    return float(best_t)


def _cross(a: float, b: float, level: float) -> float:
    """Fraction along an edge (corner a -> corner b) where the field hits level."""
    d = b - a
    if d == 0:
        return 0.5
    return min(1.0, max(0.0, (level - a) / d))


def marching_squares(field: np.ndarray, level: float) -> list[np.ndarray]:
    """Pure-numpy marching squares.

    Returns a list of polylines (each an (n, 2) float array of x=col, y=row) that
    trace the ``field == level`` iso-contours. Crossing points on a shared cell
    edge are computed identically from both neighbouring cells, so endpoints
    match exactly and link into clean loops.
    """
    h, w = field.shape
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []

    for r in range(h - 1):
        g_tl_row = field[r]
        g_bl_row = field[r + 1]
        for c in range(w - 1):
            tl = g_tl_row[c]
            tr = g_tl_row[c + 1]
            br = g_bl_row[c + 1]
            bl = g_bl_row[c]

            a_tl = tl >= level
            a_tr = tr >= level
            a_br = br >= level
            a_bl = bl >= level
            n_above = a_tl + a_tr + a_br + a_bl
            if n_above == 0 or n_above == 4:
                continue

            # crossing points on the four edges (only where signs differ)
            pts = {}
            if a_tl != a_tr:  # top edge
                pts["T"] = (c + _cross(tl, tr, level), float(r))
            if a_tr != a_br:  # right edge
                pts["R"] = (float(c + 1), r + _cross(tr, br, level))
            if a_bl != a_br:  # bottom edge
                pts["B"] = (c + _cross(bl, br, level), float(r + 1))
            if a_tl != a_bl:  # left edge
                pts["L"] = (float(c), r + _cross(tl, bl, level))

            keys = list(pts)
            if len(keys) == 2:
                segments.append((pts[keys[0]], pts[keys[1]]))
            elif len(keys) == 4:  # saddle: disambiguate with the cell centre
                center = 0.25 * (tl + tr + br + bl)
                if center >= level:
                    segments.append((pts["T"], pts["R"]))
                    segments.append((pts["B"], pts["L"]))
                else:
                    segments.append((pts["T"], pts["L"]))
                    segments.append((pts["B"], pts["R"]))

    return _link_segments(segments)


def _link_segments(segments) -> list[np.ndarray]:
    """Stitch an unordered segment soup into ordered polylines by walking shared
    endpoints. Interior crossing points have degree 2 -> clean loops/chains."""
    def key(p):
        return (round(p[0], 4), round(p[1], 4))

    adj: dict = defaultdict(list)  # key -> list of (neighbour_key, seg_id)
    for sid, (p0, p1) in enumerate(segments):
        k0, k1 = key(p0), key(p1)
        adj[k0].append((k1, sid))
        adj[k1].append((k0, sid))

    used: set[int] = set()

    def walk(start):
        path = [start]
        cur = start
        while True:
            nxt = next(((nb, sid) for nb, sid in adj[cur] if sid not in used), None)
            if nxt is None:
                break
            nb, sid = nxt
            used.add(sid)
            path.append(nb)
            cur = nb
        return np.array(path, dtype=float)

    polylines = []
    # open chains first (contours that run into the image border)
    for k, nbrs in adj.items():
        if len(nbrs) == 1 and any(sid not in used for _, sid in nbrs):
            polylines.append(walk(k))
    # then the remaining closed loops
    for k, nbrs in adj.items():
        if any(sid not in used for _, sid in nbrs):
            polylines.append(walk(k))
    return polylines


def stitch(loops: list[np.ndarray]) -> np.ndarray:
    """Greedy nearest-neighbour tour over the loops, flipping each so the pen
    makes the shortest hop. Returns one concatenated (M, 2) path."""
    loops = sorted(loops, key=lambda p: len(p), reverse=True)
    order_result = [loops[0]]
    used = {0}
    cur_end = loops[0][-1]
    while len(used) < len(loops):
        best = None  # (dist, index, flip)
        for i, lp in enumerate(loops):
            if i in used:
                continue
            d_start = float(np.hypot(*(lp[0] - cur_end)))
            d_end = float(np.hypot(*(lp[-1] - cur_end)))
            flip = d_end < d_start
            d = min(d_start, d_end)
            if best is None or d < best[0]:
                best = (d, i, flip)
        _, i, flip = best
        used.add(i)
        seg = loops[i][::-1] if flip else loops[i]
        order_result.append(seg)
        cur_end = seg[-1]
    return np.concatenate(order_result, axis=0)


def resample_closed(path_xy: np.ndarray, n: int) -> np.ndarray:
    """Uniform arc-length resample of a closed path -> n points (no duplicate
    closing point; the sequence is treated as periodic)."""
    closed = np.vstack([path_xy, path_xy[:1]])
    seg = np.diff(closed, axis=0)
    seglen = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(seglen)])
    total = cum[-1]
    s = np.linspace(0.0, total, n, endpoint=False)
    x = np.interp(s, cum, closed[:, 0])
    y = np.interp(s, cum, closed[:, 1])
    return np.stack([x, y], axis=1)


def to_manim_complex(path_xy: np.ndarray) -> np.ndarray:
    """Pixel coords (x right, y down) -> centered complex points (y up), scaled
    to fit inside the target box while keeping aspect ratio."""
    z = path_xy[:, 0] - 1j * path_xy[:, 1]  # flip y so 'up' is positive
    z = z - z.mean()
    scale = min(FIT_HALF_H / np.abs(z.imag).max(), FIT_HALF_W / np.abs(z.real).max())
    return z * scale


def fourier_coeffs(z: np.ndarray):
    """DFT of the path -> integer frequencies and complex coefficients c_k such
    that z(t) = sum_k c_k * exp(2*pi*i*k*t), t in [0, 1)."""
    n = len(z)
    coeffs = np.fft.fft(z) / n
    freqs = np.round(np.fft.fftfreq(n, d=1.0 / n)).astype(int)
    return freqs, coeffs


def save_preview(z: np.ndarray, freqs, coeffs, m: int) -> None:
    """Draw the target path (grey) and its m-vector reconstruction (black)."""
    order = np.argsort(np.abs(freqs))[:m]
    t = np.linspace(0.0, 1.0, 3000, endpoint=False)
    recon = np.zeros_like(t, dtype=complex)
    for i in order:
        recon += coeffs[i] * np.exp(2j * np.pi * freqs[i] * t)

    size = 720
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    span = max(np.abs(z.real).max(), np.abs(z.imag).max()) * 1.08

    def to_px(cz):
        px = (cz.real / span * 0.5 + 0.5) * size
        py = (0.5 - cz.imag / span * 0.5) * size
        return list(zip(px, py, strict=False))

    draw.line(to_px(z) + to_px(z[:1]), fill=(180, 180, 180), width=1)
    draw.line(to_px(recon) + to_px(recon[:1]), fill=(15, 15, 15), width=2)
    img.save(OUT_PREVIEW)


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IMG
    print(f">> loading {src}")
    im = Image.open(src).convert("L")
    scale = MAX_DIM / max(im.size)
    im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))))
    gray = np.asarray(im, dtype=float)

    level = otsu_level(np.asarray(im, dtype=np.uint8))
    print(f">> otsu level = {level:.0f}")
    field = gaussian_filter(gray, BLUR_SIGMA)

    loops = marching_squares(field, level)
    loops = [lp for lp in loops if len(lp) >= MIN_LOOP_PTS]
    loops.sort(key=lambda p: len(p), reverse=True)
    loops = loops[:KEEP_LOOPS]
    print(f">> kept {len(loops)} loops, sizes: {[len(lp) for lp in loops[:8]]}...")

    path_xy = stitch(loops)
    path_xy = resample_closed(path_xy, N_SAMPLES)
    z = to_manim_complex(path_xy)

    OUT_NPY.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUT_NPY, z)
    print(f">> saved {OUT_NPY}  ({len(z)} points)")

    freqs, coeffs = fourier_coeffs(z)
    save_preview(z, freqs, coeffs, PREVIEW_VECTORS)
    print(f">> saved {OUT_PREVIEW}  (reconstruction with {PREVIEW_VECTORS} vectors)")


if __name__ == "__main__":
    main()
