"""Generate every image asset used by Parts 4, 5 and 6 of the CNN series.

The scene files load their images with relative paths (``images/<name>.png``),
so each part keeps its own ``images/`` folder.  This script regenerates all of
them deterministically from the shared MNIST source, which means the animations
render on a clean checkout without any missing-file errors.

Run it from anywhere:

    python generate_assets.py

Dependencies: numpy, scipy, pillow (see requirements.txt).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.signal import convolve2d

ROOT = Path(__file__).resolve().parent

# Canonical MNIST source shipped with Part 1 (a 28x28 "0").
BASE_IMAGE = ROOT / "Part 1_ CNN background and motivation" / "images" / "0_mnist.png"

# Optional real photo used for the Part 6 "large image" example.  If present it
# is used (grayscale, square-cropped); otherwise a synthetic face is drawn.
FACE_SOURCE = ROOT / "assets" / "face_source.png"

# Which files each part needs in its own images/ folder.
PART_DIRS = {
    "Part 4_ About Activations": [
        "0_mnist.png",
        "mnist_relu.png",
        "mnist_sigmoid.png",
        "mnist_tanh.png",
        "mnist_leaky.png",
        "mnist_elu.png",
    ],
    "Part 5_ About pooling": [
        "0_mnist.png",
        "mnist_relu.png",
        "0_mnist_pooled.png",
    ],
    "Part 6_ Conclusion": [
        "0_mnist.png",
        "mnist_relu.png",
        "face.png",
        "face_output.png",
    ],
}

# Deterministic output so re-runs are reproducible.
RNG_SEED = 0


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def to_uint8(arr01: np.ndarray) -> np.ndarray:
    """Clip a float array in [0, 1] and scale to uint8."""
    return (np.clip(arr01, 0.0, 1.0) * 255.0).astype(np.uint8)


def normalise(arr: np.ndarray) -> np.ndarray:
    """Min-max normalise an array into [0, 1] (flat arrays map to zeros)."""
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo < 1e-12:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def save_gray(arr01: np.ndarray, path: Path) -> None:
    Image.fromarray(to_uint8(arr01), mode="L").save(path)


# --------------------------------------------------------------------------- #
# Activation maps (Part 4)
# --------------------------------------------------------------------------- #
def activation_maps(gray: np.ndarray) -> dict[str, np.ndarray]:
    """Convolve the digit with a fixed kernel, then apply each activation.

    The convolution response is standardised (zero mean, unit variance) so the
    different activations produce visibly distinct, clean grayscale maps.
    """
    rng = np.random.default_rng(RNG_SEED)
    kernel = rng.random((3, 3))
    kernel /= kernel.sum()

    response = convolve2d(gray, kernel, mode="same", boundary="symm")
    x = (response - response.mean()) / (response.std() + 1e-8)

    return {
        "mnist_relu.png": normalise(np.maximum(0.0, x)),
        "mnist_leaky.png": normalise(np.where(x > 0, x, 0.1 * x)),
        "mnist_elu.png": normalise(np.where(x > 0, x, np.exp(x) - 1.0)),
        "mnist_sigmoid.png": 1.0 / (1.0 + np.exp(-x)),
        "mnist_tanh.png": (np.tanh(x) + 1.0) / 2.0,
    }


# --------------------------------------------------------------------------- #
# Average pooling (Part 5)
# --------------------------------------------------------------------------- #
def average_pool(gray: np.ndarray, size: int = 2) -> np.ndarray:
    """2x2 average pooling (28x28 -> 14x14) implemented in pure numpy."""
    h, w = gray.shape
    h, w = h - h % size, w - w % size
    pooled = gray[:h, :w].reshape(h // size, size, w // size, size).mean(axis=(1, 3))
    return pooled


# --------------------------------------------------------------------------- #
# Synthetic face + edge detection (Part 6)
# --------------------------------------------------------------------------- #
def load_source_face(path: Path, px: int = 256) -> np.ndarray:
    """Load a real photo as a square grayscale [0, 1] array of side ``px``.

    Center-crops to a square, converts to grayscale and stretches the contrast
    so it reads cleanly at small sizes.
    """
    img = Image.open(path).convert("L")
    w, h = img.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((px, px), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    return np.asarray(img, dtype=float) / 255.0


def make_face(px: int = 256, supersample: int = 4) -> np.ndarray:
    """Grayscale 256x256 "large" input for Part 6.

    Uses the real photo at ``FACE_SOURCE`` when available; otherwise draws a
    clean, anti-aliased synthetic face (rendered high-res then downsampled) as a
    stand-in illustrating that CNNs scale to images bigger than MNIST.
    """
    if FACE_SOURCE.exists():
        return load_source_face(FACE_SOURCE, px)

    s = px * supersample
    img = Image.new("L", (s, s), color=40)
    draw = ImageDraw.Draw(img)

    def box(cx, cy, rx, ry):
        return [cx - rx, cy - ry, cx + rx, cy + ry]

    c = s / 2
    # Head
    draw.ellipse(box(c, c, 0.34 * s, 0.42 * s), fill=170)
    # Eyes (white + pupil)
    for sign in (-1, 1):
        ex = c + sign * 0.14 * s
        ey = c - 0.10 * s
        draw.ellipse(box(ex, ey, 0.075 * s, 0.05 * s), fill=235)
        draw.ellipse(box(ex, ey, 0.03 * s, 0.03 * s), fill=25)
    # Nose
    draw.line([c, c - 0.03 * s, c, c + 0.10 * s], fill=90, width=max(2, s // 120))
    # Mouth
    draw.arc(box(c, c + 0.10 * s, 0.15 * s, 0.11 * s), start=20, end=160,
             fill=25, width=max(3, s // 90))

    img = img.resize((px, px), Image.LANCZOS)
    return np.asarray(img, dtype=float) / 255.0


def sobel_edges(gray: np.ndarray) -> np.ndarray:
    """Sobel gradient magnitude, normalised to [0, 1] for a clean edge map."""
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)
    ky = kx.T
    gx = convolve2d(gray, kx, mode="same", boundary="symm")
    gy = convolve2d(gray, ky, mode="same", boundary="symm")
    return normalise(np.hypot(gx, gy))


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def build_assets() -> dict[str, np.ndarray]:
    if not BASE_IMAGE.exists():
        raise FileNotFoundError(f"Base MNIST image not found: {BASE_IMAGE}")

    gray = np.asarray(Image.open(BASE_IMAGE).convert("L"), dtype=float) / 255.0

    assets = activation_maps(gray)
    assets["0_mnist_pooled.png"] = average_pool(gray, size=2)

    face = make_face()
    assets["face.png"] = face
    assets["face_output.png"] = sobel_edges(face)
    return assets


def main() -> None:
    assets = build_assets()

    for part, filenames in PART_DIRS.items():
        images_dir = ROOT / part / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        for name in filenames:
            dest = images_dir / name
            if name == "0_mnist.png":
                # Keep the original file verbatim (preserves its exact format).
                shutil.copyfile(BASE_IMAGE, dest)
            else:
                save_gray(assets[name], dest)

        print(f"[ok] {part}/images  ({len(filenames)} files)")

    print("\nAll assets generated.")


if __name__ == "__main__":
    main()
