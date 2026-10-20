"""Bake the real numbers behind the Backpropagation film into assets/backprop.npz.

Everything the animation shows is computed here, once, with plain numpy so the
manim scene never fabricates a value:

  * A real, NON-CONVEX loss surface  L(w1, w2)  for the model
        f(x) = w2 * tanh(w1 * x)
    fitted (MSE) to data drawn from a true tanh.  The model is nonlinear in its
    parameters, so the loss genuinely curves into valleys.  The sign symmetry
    f(-w1, -w2) == f(w1, w2) puts TWO mirror-image global valleys on the
    surface, separated by a raised ridge through the origin.

  * A real gradient-descent trajectory (momentum GD, real backprop on the two
    parameters) that starts up on the hillside and rolls down into one valley.

  * The exact forward values AND backward gradients of a tiny
        x -> [linear w1,b1] -> tanh -> [linear w2,b2] -> loss
    network, so the "chain rule, run backward" scene shows honest arithmetic.

Run `python generate_assets.py` to (re)bake, or `--preview` to also dump
matplotlib PNGs (surface + contour + trajectory, and the fit) for eyeballing.
"""

from __future__ import annotations

import argparse
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
NPZ = os.path.join(ASSETS, "backprop.npz")

# --------------------------------------------------------------------------- #
#  The 2-parameter model and its loss surface                                 #
# --------------------------------------------------------------------------- #
# Target ("truth") the model is trying to match:  y = A_true * tanh(B_true * x)
A_TRUE = 0.90
B_TRUE = 1.60

# Deterministic dataset.  A little Gaussian noise keeps it honest (real data is
# noisy) but not so much that the global minimum loss stops being small.
RNG = np.random.default_rng(7)
XS = np.linspace(-2.5, 2.5, 40)
YS = A_TRUE * np.tanh(B_TRUE * XS) + RNG.normal(0.0, 0.03, size=XS.shape)


def model(w1: float, w2: float, x: np.ndarray) -> np.ndarray:
    """f(x) = w2 * tanh(w1 * x)."""
    return w2 * np.tanh(w1 * x)


def loss(w1: float, w2: float) -> float:
    """Mean-squared error of the 2-parameter model over the dataset."""
    r = model(w1, w2, XS) - YS
    return float(np.mean(r * r))


def loss_grad(w1: float, w2: float) -> np.ndarray:
    """Analytic gradient [dL/dw1, dL/dw2] (this IS backprop for two params)."""
    t = np.tanh(w1 * XS)               # forward: hidden activation
    r = w2 * t - YS                    # forward: residual
    # dL/dpred = 2 r / N ; pred = w2 * t
    dpred = 2.0 * r / XS.size
    dw2 = float(np.sum(dpred * t))                       # d pred / d w2 = t
    dw1 = float(np.sum(dpred * w2 * (1.0 - t * t) * XS))  # chain thru tanh'
    return np.array([dw1, dw2])


# --------------------------------------------------------------------------- #
#  Surface grid (for range-picking / preview / asserts)                       #
# --------------------------------------------------------------------------- #
# Ranges chosen (and verified in --preview) so the two valleys and the central
# ridge frame nicely, and the corners don't tower over everything.
W1_MIN, W1_MAX = -2.6, 2.6
W2_MIN, W2_MAX = -1.8, 1.8
GN = 81
W1_AXIS = np.linspace(W1_MIN, W1_MAX, GN)
W2_AXIS = np.linspace(W2_MIN, W2_MAX, GN)
# LOSS_GRID[i, j] = loss at (w1=W1_AXIS[i], w2=W2_AXIS[j])
LOSS_GRID = np.empty((GN, GN))
for i, a in enumerate(W1_AXIS):
    for j, b in enumerate(W2_AXIS):
        LOSS_GRID[i, j] = loss(a, b)

# The two mirror global minima live at (+/-B_TRUE, +/-A_TRUE).  Confirm on grid.
MIN_A = np.array([B_TRUE, A_TRUE])          # target valley the ball rolls into
MIN_B = np.array([-B_TRUE, -A_TRUE])        # its mirror
MIN_LOSS = loss(*MIN_A)


# --------------------------------------------------------------------------- #
#  Real gradient-descent trajectory (momentum GD = real backprop, 2 params)   #
# --------------------------------------------------------------------------- #
def descend(start, lr=0.08, momentum=0.80, steps=140):
    """Run momentum gradient descent; return an (steps+1, 3) array of
    [w1, w2, loss] so the manim ball can ride the real path."""
    w = np.array(start, dtype=float)
    v = np.zeros(2)
    path = [[w[0], w[1], loss(*w)]]
    for _ in range(steps):
        g = loss_grad(*w)
        v = momentum * v - lr * g
        w = w + v
        path.append([w[0], w[1], loss(*w)])
    return np.array(path)


# Start high on the hillside, off to one side of the ridge, so the descent is a
# long, readable roll down into the right-hand valley (MIN_A).
PATH = descend(start=(0.35, 1.65), lr=0.08, momentum=0.80, steps=140)
# A second, fainter ball started at the mirror-image point: by the model's sign
# symmetry it rolls into the OTHER valley (MIN_B), the same distance down. Shows
# there are two equally-good answers and the start decides which you reach.
PATH2 = descend(start=(-0.35, -1.65), lr=0.08, momentum=0.80, steps=140)


# --------------------------------------------------------------------------- #
#  Tiny network for the "chain rule, backward" scene (one example, real grads) #
# --------------------------------------------------------------------------- #
# x --(w1,b1)--> z1 --tanh--> a1 --(w2,b2)--> z2 = pred ;  L = 1/2 (pred - y)^2
# Chosen so the two weight gradients come out clearly different (0.61 vs 0.33),
# which is the whole point of the scene: each weight gets its own gradient.
BW = {
    "x": 1.00, "y": 0.20,
    "w1": 1.10, "b1": 0.00,
    "w2": 1.20, "b2": 0.00,
}
_x, _y = BW["x"], BW["y"]
z1 = BW["w1"] * _x + BW["b1"]
a1 = np.tanh(z1)
z2 = BW["w2"] * a1 + BW["b2"]
pred = z2
L = 0.5 * (pred - _y) ** 2
# backward pass (reverse-mode: multiply the local derivative at each step)
dpred = pred - _y                      # dL/dpred
dw2 = dpred * a1                       # dL/dw2  = dL/dpred * a1
db2 = dpred                            # dL/db2
da1 = dpred * BW["w2"]                 # dL/da1  = dL/dpred * w2
dz1 = da1 * (1.0 - a1 * a1)            # dL/dz1  = dL/da1 * tanh'(z1)
dw1 = dz1 * _x                         # dL/dw1  = dL/dz1 * x
db1 = dz1                              # dL/db1
BW.update(dict(z1=z1, a1=a1, z2=z2, pred=pred, L=L,
               dpred=dpred, dw2=dw2, db2=db2, da1=da1, dz1=dz1, dw1=dw1, db1=db1))

# --------------------------------------------------------------------------- #
#  "Why it scales" cost contrast (illustrative but arithmetically real)        #
# --------------------------------------------------------------------------- #
# Finite differences need one forward pass PER parameter (plus one baseline);
# backprop needs one forward + one backward ~= two forward passes, for ANY P.
DEMO_PARAMS = 1_000_000            # a deliberately modest "small" network
FD_PASSES = DEMO_PARAMS + 1       # nudge each weight, re-evaluate
BP_PASSES = 2                     # one forward, one backward
SPEEDUP = FD_PASSES / BP_PASSES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true",
                    help="also write matplotlib PNGs to assets/ for eyeballing")
    args = ap.parse_args()

    os.makedirs(ASSETS, exist_ok=True)

    # sanity asserts (single source of truth; catch drift early)
    assert LOSS_GRID.shape == (GN, GN)
    assert MIN_LOSS < 0.01, f"global min loss too big: {MIN_LOSS:.4f}"
    assert loss(0.0, 0.0) > 0.3, "origin should be a raised plateau/ridge"
    assert PATH[-1, 2] < 0.01, f"trajectory did not reach a valley: L={PATH[-1,2]:.4f}"
    # the trajectory should end near MIN_A (the right-hand valley)
    assert np.linalg.norm(PATH[-1, :2] - MIN_A) < 0.25, PATH[-1, :2]
    assert PATH2[-1, 2] < 0.02, f"path2 did not settle: L={PATH2[-1,2]:.4f}"
    assert np.linalg.norm(PATH2[-1, :2] - MIN_B) < 0.25, PATH2[-1, :2]
    # chain-rule numbers (kept clearly distinct so the scene can show that each
    # weight gets its own gradient)
    assert abs(BW["dw1"] - 0.3279) < 1e-3, BW["dw1"]
    assert abs(BW["dw2"] - 0.6088) < 1e-3, BW["dw2"]
    assert abs(BW["dpred"] - 0.7606) < 1e-3, BW["dpred"]

    np.savez(
        NPZ,
        XS=XS, YS=YS,
        W1_AXIS=W1_AXIS, W2_AXIS=W2_AXIS, LOSS_GRID=LOSS_GRID,
        W1_MIN=W1_MIN, W1_MAX=W1_MAX, W2_MIN=W2_MIN, W2_MAX=W2_MAX,
        MIN_A=MIN_A, MIN_B=MIN_B, MIN_LOSS=MIN_LOSS,
        A_TRUE=A_TRUE, B_TRUE=B_TRUE,
        PATH=PATH, PATH2=PATH2,
        BW_KEYS=np.array(list(BW.keys())),
        BW_VALS=np.array([BW[k] for k in BW.keys()], dtype=float),
        DEMO_PARAMS=DEMO_PARAMS, FD_PASSES=FD_PASSES, BP_PASSES=BP_PASSES,
        SPEEDUP=SPEEDUP,
    )
    print(f"wrote {NPZ}")
    print(f"  global min loss   = {MIN_LOSS:.5f} at {MIN_A}")
    print(f"  origin (ridge) L  = {loss(0,0):.4f}")
    print(f"  loss range        = [{LOSS_GRID.min():.3f}, {LOSS_GRID.max():.3f}]")
    print(f"  PATH end          = {PATH[-1]}")
    print(f"  chain rule dw1={BW['dw1']:.4f} dw2={BW['dw2']:.4f} "
          f"pred={BW['pred']:.4f} L={BW['L']:.5f}")
    print(f"  scale contrast    = {FD_PASSES:,} vs {BP_PASSES} passes "
          f"({SPEEDUP:,.0f}x)")

    if args.preview:
        _preview()


def _preview():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import cm

    W1, W2 = np.meshgrid(W1_AXIS, W2_AXIS, indexing="ij")

    # (1) 3D surface + both trajectories
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(W1, W2, LOSS_GRID, cmap=cm.viridis, alpha=0.9,
                    linewidth=0, antialiased=True, rcount=81, ccount=81)
    for p, c in ((PATH, "red"), (PATH2, "orange")):
        ax.plot(p[:, 0], p[:, 1], p[:, 2] + 0.02, color=c, lw=2.5)
        ax.scatter(p[0, 0], p[0, 1], p[0, 2] + 0.02, color=c, s=40)
    ax.set_xlabel("w1"); ax.set_ylabel("w2"); ax.set_zlabel("loss")
    ax.view_init(elev=42, azim=-52)
    ax.set_title("Loss surface  L(w1,w2)  of  f(x)=w2*tanh(w1*x)")
    fig.savefig(os.path.join(ASSETS, "preview_surface.png"), dpi=110,
                bbox_inches="tight")
    plt.close(fig)

    # (2) contour + trajectories (top-down, to judge the valley shape)
    fig, ax = plt.subplots(figsize=(9, 7))
    cs = ax.contourf(W1, W2, LOSS_GRID, levels=30, cmap=cm.viridis)
    ax.contour(W1, W2, LOSS_GRID, levels=15, colors="white",
               linewidths=0.4, alpha=0.5)
    fig.colorbar(cs, ax=ax, label="loss")
    for p, c in ((PATH, "red"), (PATH2, "orange")):
        ax.plot(p[:, 0], p[:, 1], color=c, lw=2.5)
        ax.scatter(*p[0, :2], color=c, s=45, zorder=5)
    for m, lab in ((MIN_A, "min A"), (MIN_B, "min B")):
        ax.scatter(*m, marker="*", color="gold", edgecolor="k", s=260, zorder=6)
        ax.annotate(lab, m, textcoords="offset points", xytext=(6, 6))
    ax.set_xlabel("w1"); ax.set_ylabel("w2")
    ax.set_title("Two valleys (sign symmetry) + real GD paths")
    fig.savefig(os.path.join(ASSETS, "preview_contour.png"), dpi=110,
                bbox_inches="tight")
    plt.close(fig)

    # (3) the actual fit at the end of PATH (does the model match the data?)
    fig, ax = plt.subplots(figsize=(8, 5))
    w1e, w2e = PATH[-1, 0], PATH[-1, 1]
    xf = np.linspace(XS.min(), XS.max(), 200)
    ax.scatter(XS, YS, s=18, color="#4C78A8", label="data")
    ax.plot(xf, model(w1e, w2e, xf), color="red", lw=2.2,
            label=f"fit: {w2e:.2f}*tanh({w1e:.2f}x)")
    ax.plot(xf, A_TRUE * np.tanh(B_TRUE * xf), color="green", lw=1.2,
            ls="--", label="truth")
    ax.legend(); ax.set_title(f"Fit after descent  (loss={PATH[-1,2]:.4f})")
    fig.savefig(os.path.join(ASSETS, "preview_fit.png"), dpi=110,
                bbox_inches="tight")
    plt.close(fig)
    print("wrote preview_surface.png, preview_contour.png, preview_fit.png")


if __name__ == "__main__":
    main()
