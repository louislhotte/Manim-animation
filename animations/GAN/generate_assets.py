"""Train a *real* toy GAN (pure NumPy) and bake training snapshots for the film.

Everything the animation shows is computed here, never fabricated:

- The target distribution is the classic **8 Gaussians on a ring** benchmark.
- A generator G: z -> R^2 and a discriminator D: R^2 -> (0,1) are two small MLPs
  trained against each other with the standard non-saturating GAN loss and Adam.
  Both nets' gradients are derived by hand (no autograd, no torch).
- At chosen iterations we snapshot: the generator's samples, the discriminator's
  score over a coarse grid (the 3-D confidence terrain the film orbits) and a fine
  grid (2-D heatmap), and the mean D score on real vs fake batches (which both head
  to 0.5 as the game converges).

Output: ``assets/gan.npz`` (+ optional PNG previews for a human sanity check).

Run directly:  python generate_assets.py            # bake the npz
               python generate_assets.py --preview  # + write preview PNGs
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

SEED = 7
LATENT = 2               # latent dimension (2 keeps the "noise" honest and drawable)
H = 128                  # hidden width of both nets
BATCH = 256
ITERS = 9000
RING_R = 2.0             # radius of the ring of Gaussian modes
MODE_STD = 0.18          # spread of each mode
N_MODES = 8

# Snapshot iterations: a clean blob -> ring progression (indices into training).
SNAP_ITERS = [0, 90, 260, 650, 1600, 4200, 9000]

# Grids over the data plane.
BAR_N = 14               # coarse grid for the 3-D prism terrain (BAR_N^2 prisms)
FINE_N = 56              # fine grid for the 2-D heatmap / previews
EXTENT = 3.3             # half-width of both grids (plane is [-EXTENT, EXTENT]^2)

NS = 700                 # generator samples saved per snapshot
NR = 1400                # real samples saved (the target cloud)
WALK_N = 140             # points along the latent-space walk


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def mode_centers():
    ang = np.linspace(0, 2 * np.pi, N_MODES, endpoint=False)
    return RING_R * np.stack([np.cos(ang), np.sin(ang)], axis=1)


CENTERS = mode_centers()


def sample_real(n, rng):
    idx = rng.integers(0, N_MODES, n)
    return CENTERS[idx] + rng.normal(0.0, MODE_STD, (n, 2))


# --------------------------------------------------------------------------- #
# A tiny 2-hidden-layer MLP with hand-written forward / backward + Adam.
# --------------------------------------------------------------------------- #
def _init(fan_in, fan_out, rng, gain):
    # He-ish init scaled by `gain`.
    return (rng.standard_normal((fan_in, fan_out)) * gain / np.sqrt(fan_in)).astype(np.float64)


class MLP:
    def __init__(self, sizes, rng, leaky=0.0, gain=1.0):
        self.leaky = leaky
        self.W, self.b = [], []
        for a, c in zip(sizes[:-1], sizes[1:]):
            self.W.append(_init(a, c, rng, gain))
            self.b.append(np.zeros(c))
        # Adam state
        self.mW = [np.zeros_like(w) for w in self.W]
        self.vW = [np.zeros_like(w) for w in self.W]
        self.mb = [np.zeros_like(b) for b in self.b]
        self.vb = [np.zeros_like(b) for b in self.b]
        self.t = 0

    def _act(self, z):
        return np.where(z > 0, z, self.leaky * z)

    def _dact(self, z):
        return np.where(z > 0, 1.0, self.leaky)

    def forward(self, x):
        """Return (output, cache). Output of the last layer is linear."""
        zs, as_ = [], [x]
        a = x
        for i in range(len(self.W)):
            z = a @ self.W[i] + self.b[i]
            zs.append(z)
            if i < len(self.W) - 1:
                a = self._act(z)
            else:
                a = z  # linear head
            as_.append(a)
        return a, (zs, as_)

    def backward(self, grad_out, cache):
        """Given dL/d(output), return (dL/d(input), [dW...], [db...])."""
        zs, as_ = cache
        gW = [None] * len(self.W)
        gb = [None] * len(self.W)
        g = grad_out
        for i in reversed(range(len(self.W))):
            if i < len(self.W) - 1:
                g = g * self._dact(zs[i])
            gW[i] = as_[i].T @ g
            gb[i] = g.sum(axis=0)
            g = g @ self.W[i].T
        return g, gW, gb

    def adam(self, gW, gb, lr=1e-3, b1=0.5, b2=0.999, eps=1e-8):
        self.t += 1
        bc1 = 1 - b1 ** self.t
        bc2 = 1 - b2 ** self.t
        for i in range(len(self.W)):
            self.mW[i] = b1 * self.mW[i] + (1 - b1) * gW[i]
            self.vW[i] = b2 * self.vW[i] + (1 - b2) * (gW[i] ** 2)
            self.W[i] -= lr * (self.mW[i] / bc1) / (np.sqrt(self.vW[i] / bc2) + eps)
            self.mb[i] = b1 * self.mb[i] + (1 - b1) * gb[i]
            self.vb[i] = b2 * self.vb[i] + (1 - b2) * (gb[i] ** 2)
            self.b[i] -= lr * (self.mb[i] / bc1) / (np.sqrt(self.vb[i] / bc2) + eps)


def sigmoid(s):
    return 1.0 / (1.0 + np.exp(-np.clip(s, -30, 30)))


# --------------------------------------------------------------------------- #
# Training
# --------------------------------------------------------------------------- #
def bar_grid():
    xs = np.linspace(-EXTENT, EXTENT, BAR_N)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    return X, Y, np.stack([X.ravel(), Y.ravel()], axis=1)


def fine_grid():
    xs = np.linspace(-EXTENT, EXTENT, FINE_N)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    return X, Y, np.stack([X.ravel(), Y.ravel()], axis=1)


def train():
    rng = np.random.default_rng(SEED)
    G = MLP([LATENT, H, H, 2], rng, leaky=0.0, gain=1.0)      # ReLU generator
    D = MLP([2, H, H, 1], rng, leaky=0.2, gain=1.0)           # LeakyReLU discriminator

    _, _, bar_pts = bar_grid()
    _, _, fine_pts = fine_grid()

    # ---- teacher discriminator: train a fresh D *alone* against the frozen
    # initial (blob) generator. It's a real discriminator, trained on real-vs-
    # (initial fakes); it sharply separates the ring from the blob, which is
    # exactly the point Scene "Discriminator" makes. G is untouched here.
    Dt = MLP([2, H, H, 1], rng, leaky=0.2, gain=1.0)
    for _ in range(500):
        xr = sample_real(BATCH, rng)
        xf, _ = G.forward(rng.standard_normal((BATCH, LATENT)))
        sr, cr = Dt.forward(xr)
        sf, cf = Dt.forward(xf)
        pr, pf = sigmoid(sr), sigmoid(sf)
        _, gWr, gbr = Dt.backward((pr - 0.9) / BATCH, cr)
        _, gWf, gbf = Dt.backward((pf - 0.0) / BATCH, cf)
        Dt.adam([a + b for a, b in zip(gWr, gWf)],
                [a + b for a, b in zip(gbr, gbf)], lr=1e-3)
    D_teach_bar = sigmoid(Dt.forward(bar_pts)[0]).reshape(BAR_N, BAR_N)
    D_teach_fine = sigmoid(Dt.forward(fine_pts)[0]).reshape(FINE_N, FINE_N)
    print(f"  teacher D terrain range={D_teach_bar.max() - D_teach_bar.min():.3f}")

    snaps = {k: [] for k in ("iter", "G", "Dbar", "Dfine", "dreal", "dfake")}
    snap_set = set(SNAP_ITERS)
    real_smooth = 0.9  # one-sided label smoothing for stability

    for it in range(ITERS + 1):
        if it in snap_set:
            z = rng.standard_normal((NS, LATENT))
            gs, _ = G.forward(z)
            db, _ = D.forward(bar_pts)
            df, _ = D.forward(fine_pts)
            xr = sample_real(2000, rng)
            xf, _ = G.forward(rng.standard_normal((2000, LATENT)))
            snaps["iter"].append(it)
            snaps["G"].append(gs.copy())
            snaps["Dbar"].append(sigmoid(db).reshape(BAR_N, BAR_N).copy())
            snaps["Dfine"].append(sigmoid(df).reshape(FINE_N, FINE_N).copy())
            snaps["dreal"].append(float(sigmoid(D.forward(xr)[0]).mean()))
            snaps["dfake"].append(float(sigmoid(D.forward(xf)[0]).mean()))
            print(f"  snap it={it:5d}  D(real)={snaps['dreal'][-1]:.3f}  "
                  f"D(fake)={snaps['dfake'][-1]:.3f}")
            if it == ITERS:
                break

        # ---- Discriminator step ---------------------------------------- #
        xr = sample_real(BATCH, rng)
        z = rng.standard_normal((BATCH, LATENT))
        xf, _ = G.forward(z)                        # detached for the D step
        sr, cr = D.forward(xr)
        sf, cf = D.forward(xf)
        pr, pf = sigmoid(sr), sigmoid(sf)
        gr = (pr - real_smooth) / BATCH             # real label 0.9
        gf = (pf - 0.0) / BATCH                     # fake label 0
        _, gWr, gbr = D.backward(gr, cr)
        _, gWf, gbf = D.backward(gf, cf)
        D.adam([a + b for a, b in zip(gWr, gWf)],
               [a + b for a, b in zip(gbr, gbf)], lr=1e-3)

        # ---- Generator step (non-saturating) --------------------------- #
        z = rng.standard_normal((BATCH, LATENT))
        xf, cG = G.forward(z)
        sf, cfD = D.forward(xf)
        pf = sigmoid(sf)
        g_s = (pf - 1.0) / BATCH                    # dL_G/d(logit), L=-log D(G(z))
        dxf, _, _ = D.backward(g_s, cfD)            # grad wrt fake samples (D frozen)
        _, gWG, gbG = G.backward(dxf, cG)
        G.adam(gWG, gbG, lr=1e-3)

    # ---- a smooth latent-space walk through the trained generator ------- #
    tt = np.linspace(0, 2 * np.pi, WALK_N, endpoint=True)
    walk_z = 1.7 * np.stack([np.cos(tt), np.sin(tt)], axis=1)
    walk_xy, _ = G.forward(walk_z)

    real = sample_real(NR, rng)

    out = ASSETS / "gan.npz"
    np.savez_compressed(
        out,
        iters=np.array(snaps["iter"]),
        G_samples=np.stack(snaps["G"]),          # (S, NS, 2)
        D_bars=np.stack(snaps["Dbar"]),          # (S, BAR_N, BAR_N)
        D_fine=np.stack(snaps["Dfine"]),         # (S, FINE_N, FINE_N)
        d_real=np.array(snaps["dreal"]),         # (S,)
        d_fake=np.array(snaps["dfake"]),         # (S,)
        real=real,                               # (NR, 2)
        D_teach_bar=D_teach_bar,                 # (BAR_N, BAR_N) sharp terrain
        D_teach_fine=D_teach_fine,               # (FINE_N, FINE_N)
        centers=CENTERS,                         # (8, 2)
        walk_z=walk_z, walk_xy=walk_xy,          # (WALK_N, .)
        extent=np.array(EXTENT),
        bar_n=np.array(BAR_N), fine_n=np.array(FINE_N),
        ring_r=np.array(RING_R), mode_std=np.array(MODE_STD),
    )
    sz = out.stat().st_size / 1e6
    print(f"\nwrote {out}  ({sz:.2f} MB)  snapshots={len(snaps['iter'])}")
    return out


# --------------------------------------------------------------------------- #
# Optional PNG previews (PIL ships with manim) so a human can verify convergence
# --------------------------------------------------------------------------- #
def previews():
    from PIL import Image
    d = np.load(ASSETS / "gan.npz")
    prev = Path(os.environ.get("GAN_PREVIEW_DIR", "/tmp/gan-preview"))
    prev.mkdir(parents=True, exist_ok=True)
    S = d["D_fine"].shape[0]
    W = 460
    ext = float(d["extent"])

    def to_px(pts):
        u = (pts[:, 0] + ext) / (2 * ext) * (W - 1)
        v = (ext - pts[:, 1]) / (2 * ext) * (W - 1)
        return np.stack([u, v], axis=1).astype(int)

    for k in range(S):
        heat = d["D_fine"][k]                       # (FINE_N, FINE_N), in [0,1]
        img = np.zeros((W, W, 3), np.uint8)
        # bilinear-ish upsample of the heatmap into the background
        fn = heat.shape[0]
        for py in range(W):
            gy = int((ext - (ext - py / (W - 1) * 2 * ext)) / (2 * ext) * (fn - 1))
        # simpler: nearest upsample
        ys = ((np.arange(W) / (W - 1)) * (fn - 1)).astype(int)
        xs = ((np.arange(W) / (W - 1)) * (fn - 1)).astype(int)
        big = heat[np.ix_(xs, ys)].T                # (W,W) note transpose to (row=y)
        # blue (low) -> gold (high)
        img[..., 0] = (40 + big * 200).astype(np.uint8)
        img[..., 1] = (50 + big * 150).astype(np.uint8)
        img[..., 2] = (90 + (1 - big) * 120).astype(np.uint8)
        im = Image.fromarray(img)
        px = im.load()
        for (u, v) in to_px(d["real"]):
            if 0 <= u < W and 0 <= v < W:
                px[u, v] = (245, 245, 240)
        for (u, v) in to_px(d["G_samples"][k]):
            if 0 <= u < W and 0 <= v < W:
                px[u, v] = (67, 198, 232)
        im.save(prev / f"snap_{k}_it{int(d['iters'][k])}.png")
    print(f"previews -> {prev}  (real=white, fake=cyan, D score = blue..gold)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="also write PNG previews")
    args = ap.parse_args()
    train()
    if args.preview:
        previews()
