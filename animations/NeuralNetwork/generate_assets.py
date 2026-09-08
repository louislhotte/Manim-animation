"""Bake every real number the film shows into ``assets/nn_learn.npz``.

The film "How a Neural Network Learns" is honest: every prediction, loss curve,
accuracy and confusion count on screen is produced *here*, by

    1. generating a real image dataset — procedural 12x12 grayscale pictures of
       cars, planes and ships, with per-sample translation / scale / rotation /
       brightness / noise so the task is genuinely non-linear (a linear model
       can't win, and depth/width earns its keep);
    2. training three real numpy MLPs of increasing width (the same architecture
       family, one hidden layer, He-init ReLU, softmax + cross-entropy, Adam);
    3. running a hyper-parameter *sweep* over the hidden width;
    4. recording, for the film: the three training curves, per-architecture test
       accuracy, a confusion matrix, a one-gradient-step "before/after" demo, a
       handful of showcase images with each net's real prediction, and a
       correctness grid over the whole test set (baked to PNGs for the dezoom).

Deterministic (seeded). ``render.sh`` runs it automatically if the npz is
missing. Run standalone with::

    python generate_assets.py            # regenerate assets/nn_learn.npz
    python generate_assets.py --debug    # + a montage PNG to eyeball the shapes

Dependencies: numpy, pillow (see requirements.txt).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

SEED = 7
IMG = 28                      # network input is a 28x28 = 784-pixel image
DR = 336                      # draw at 336x336, area-downsample to IMG (anti-alias)
CLASSES = ["car", "plane", "ship"]
NC = len(CLASSES)

# palette for the correctness-grid PNGs (matches the film)
BG_RGB = (14, 17, 23)        # #0E1117
GOOD_RGB = (61, 214, 140)    # #3DD68C
BAD_RGB = (255, 92, 92)      # #FF5C5C


# ========================================================================== #
# 1. Procedural image dataset  (PIL, seeded)
# ========================================================================== #
def _draw_car(d: ImageDraw.ImageDraw, cx, cy, s, val):
    """A car: low body + cabin + two wheels (horizontal, wheels = the giveaway)."""
    bw, bh = 0.62 * s, 0.20 * s
    body = [cx - bw, cy - bh, cx + bw, cy + bh + 0.05 * s]
    d.rounded_rectangle(body, radius=0.09 * s, fill=int(val))
    # cabin (a shorter, offset top box)
    cw = 0.34 * s
    d.rounded_rectangle([cx - cw, cy - bh - 0.22 * s, cx + cw * 0.5, cy - bh + 0.02 * s],
                        radius=0.06 * s, fill=int(val))
    # wheels
    wr = 0.14 * s
    for wx in (cx - 0.36 * s, cx + 0.36 * s):
        d.ellipse([wx - wr, cy + bh - 0.04 * s, wx + wr, cy + bh + 2 * wr - 0.04 * s],
                  fill=int(val * 0.55))


def _draw_plane(d: ImageDraw.ImageDraw, cx, cy, s, val):
    """A plane: slim fuselage + swept wings + tail (the diagonal wings give it away)."""
    # fuselage
    fw, fh = 0.66 * s, 0.11 * s
    d.rounded_rectangle([cx - fw, cy - fh, cx + fw, cy + fh], radius=0.07 * s, fill=int(val))
    # nose
    d.polygon([(cx + fw, cy - fh), (cx + fw, cy + fh), (cx + fw + 0.16 * s, cy)], fill=int(val))
    # swept wings (a wide, thin diamond crossing the body)
    d.polygon([(cx - 0.10 * s, cy - 0.02 * s), (cx - 0.46 * s, cy - 0.40 * s),
               (cx - 0.30 * s, cy - 0.40 * s), (cx + 0.18 * s, cy - 0.02 * s)], fill=int(val))
    d.polygon([(cx - 0.10 * s, cy + 0.02 * s), (cx - 0.46 * s, cy + 0.40 * s),
               (cx - 0.30 * s, cy + 0.40 * s), (cx + 0.18 * s, cy + 0.02 * s)], fill=int(val))
    # tail fin
    d.polygon([(cx - fw, cy), (cx - fw - 0.02 * s, cy - 0.26 * s),
               (cx - fw + 0.16 * s, cy)], fill=int(val))


def _draw_ship(d: ImageDraw.ImageDraw, cx, cy, s, val):
    """A ship: broad hull (wider at top) + superstructure + funnel + waterline."""
    # hull: a trapezoid, wide deck on top, narrower keel
    top, bot = cy + 0.10 * s, cy + 0.34 * s
    d.polygon([(cx - 0.60 * s, top), (cx + 0.60 * s, top),
               (cx + 0.42 * s, bot), (cx - 0.42 * s, bot)], fill=int(val))
    # superstructure (cabin) on deck
    d.rectangle([cx - 0.24 * s, cy - 0.16 * s, cx + 0.18 * s, top], fill=int(val))
    # funnel
    d.rectangle([cx + 0.02 * s, cy - 0.34 * s, cx + 0.16 * s, cy - 0.14 * s], fill=int(val))
    # mast
    d.line([(cx - 0.14 * s, cy - 0.16 * s), (cx - 0.14 * s, cy - 0.40 * s)],
           fill=int(val), width=max(1, int(0.03 * s)))


_DRAW = {"car": _draw_car, "plane": _draw_plane, "ship": _draw_ship}


# Difficulty knobs — tuned so a linear/tiny model genuinely can't win but a
# wider net can. Strong pose variation (rotation especially) breaks linear
# separability on raw pixels; heavy noise + clutter close the gap further.
# Nuisance tuned so the SHAPES stay recognisable (28x28, light noise) yet the
# task is still non-linear — rotation/translation/scale defeat a linear/tiny net
# while width earns its keep.
ROT = 43.0        # +/- rotation degrees (main non-linearity driver; a rotated
                  # boat is still a boat, so this stays recognisable)
TRANS = 0.14      # +/- translation (fraction of canvas)
SCALE_LO, SCALE_HI = 0.63, 1.16
NOISE = 0.05      # gaussian pixel noise sigma (light — keep shapes readable)
CLUTTER = (0, 2)  # random bright specks per image


def render_sample(cls: str, rng: np.random.Generator) -> np.ndarray:
    """One 12x12 float image in [0,1] with random pose / brightness / noise."""
    canvas = Image.new("L", (DR, DR), color=0)
    d = ImageDraw.Draw(canvas)
    # random pose
    scale = rng.uniform(SCALE_LO, SCALE_HI) * DR
    cx = DR / 2 + rng.uniform(-TRANS, TRANS) * DR
    cy = DR / 2 + rng.uniform(-TRANS, TRANS) * DR
    val = rng.uniform(130, 255)
    _DRAW[cls](d, cx, cy, scale / 2.0, val)  # s in ~half-canvas units
    # random rotation (this is what defeats a linear model on raw pixels)
    ang = rng.uniform(-ROT, ROT)
    canvas = canvas.rotate(ang, resample=Image.BICUBIC, fillcolor=0)

    a = np.asarray(canvas, dtype=np.float32) / 255.0
    # area downsample 48 -> 12
    a = a.reshape(IMG, DR // IMG, IMG, DR // IMG).mean(axis=(1, 3))
    # nuisance: contrast jitter, faint gradient, random clutter, sensor noise
    a = np.clip((a - 0.5) * rng.uniform(0.7, 1.3) + 0.5, 0, 1)
    gy = np.linspace(rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), IMG)[:, None]
    a = a + gy
    for _ in range(rng.integers(*CLUTTER)):
        r, c = rng.integers(0, IMG), rng.integers(0, IMG)
        a[r, c] = min(1.0, a[r, c] + rng.uniform(0.3, 0.7))
    a = a + rng.normal(0, NOISE, a.shape)
    return np.clip(a, 0.0, 1.0).astype(np.float32)


def make_dataset(n_per_class: int, rng: np.random.Generator):
    X, y = [], []
    for ci, cls in enumerate(CLASSES):
        for _ in range(n_per_class):
            X.append(render_sample(cls, rng).ravel())
            y.append(ci)
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int64)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


# ========================================================================== #
# 2. A real numpy MLP  (He init, ReLU, softmax + cross-entropy, Adam)
# ========================================================================== #
def _onehot(y, k=NC):
    o = np.zeros((y.size, k), np.float32)
    o[np.arange(y.size), y] = 1.0
    return o


class MLP:
    def __init__(self, sizes, seed=0):
        self.sizes = list(sizes)
        g = np.random.default_rng(seed)
        self.W, self.b = [], []
        for a, c in zip(sizes[:-1], sizes[1:]):
            self.W.append((g.standard_normal((a, c)) * np.sqrt(2.0 / a)).astype(np.float32))
            self.b.append(np.zeros((1, c), np.float32))
        self._init_adam()

    def _init_adam(self):
        self.mW = [np.zeros_like(w) for w in self.W]
        self.vW = [np.zeros_like(w) for w in self.W]
        self.mb = [np.zeros_like(b) for b in self.b]
        self.vb = [np.zeros_like(b) for b in self.b]
        self.t = 0

    def forward(self, X, cache=False):
        a = X
        acts, zs = [X], []
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            z = a @ W + b
            zs.append(z)
            a = np.maximum(0, z) if i < len(self.W) - 1 else z  # ReLU except last
            acts.append(a)
        z = acts[-1]
        z = z - z.max(1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(1, keepdims=True)
        return (p, acts, zs) if cache else p

    def loss(self, X, y):
        p = self.forward(X)
        return float(-np.mean(np.log(p[np.arange(y.size), y] + 1e-9)))

    def accuracy(self, X, y):
        return float(np.mean(self.forward(X).argmax(1) == y))

    def grads(self, X, y):
        p, acts, zs = self.forward(X, cache=True)
        N = X.shape[0]
        gW = [None] * len(self.W)
        gb = [None] * len(self.b)
        delta = (p - _onehot(y)) / N
        for i in reversed(range(len(self.W))):
            gW[i] = acts[i].T @ delta
            gb[i] = delta.sum(0, keepdims=True)
            if i > 0:
                delta = (delta @ self.W[i].T) * (zs[i - 1] > 0)
        return gW, gb

    def adam_step(self, gW, gb, lr=2e-3, b1=0.9, b2=0.999, eps=1e-8):
        self.t += 1
        for i in range(len(self.W)):
            for m, v, g, p in ((self.mW, self.vW, gW, self.W), (self.mb, self.vb, gb, self.b)):
                m[i] = b1 * m[i] + (1 - b1) * g[i]
                v[i] = b2 * v[i] + (1 - b2) * (g[i] ** 2)
                mhat = m[i] / (1 - b1 ** self.t)
                vhat = v[i] / (1 - b2 ** self.t)
                p[i] -= lr * mhat / (np.sqrt(vhat) + eps)

    def fit(self, Xtr, ytr, Xva, yva, epochs=90, bs=64, lr=2e-3, rng=None, log=True):
        rng = rng or np.random.default_rng(0)
        hist = {"epoch": [], "train_loss": [], "train_acc": [], "val_acc": [], "val_loss": []}
        n = len(ytr)
        for ep in range(epochs + 1):
            if log:
                hist["epoch"].append(ep)
                hist["train_loss"].append(self.loss(Xtr, ytr))
                hist["train_acc"].append(self.accuracy(Xtr, ytr))
                hist["val_acc"].append(self.accuracy(Xva, yva))
                hist["val_loss"].append(self.loss(Xva, yva))
            if ep == epochs:
                break
            order = rng.permutation(n)
            for s in range(0, n, bs):
                b = order[s:s + bs]
                gW, gb = self.grads(Xtr[b], ytr[b])
                self.adam_step(gW, gb, lr=lr)
        return {k: np.asarray(v) for k, v in hist.items()}


# ========================================================================== #
# 3. Orchestration — build data, train, record everything
# ========================================================================== #
def _confusion(net, X, y):
    pred = net.forward(X).argmax(1)
    M = np.zeros((NC, NC), np.int64)
    for t, p in zip(y, pred):
        M[t, p] += 1
    return M


def _mosaic_png(imgs01: np.ndarray, mask: np.ndarray, path: Path, cols=60, cell=14, gap=1):
    """Bake a 'wall of images': every test image as a small grayscale thumbnail,
    tinted GREEN if the net got it right and RED if it got it wrong. You can see
    the shapes AND the correctness at a glance (the green area == the accuracy)."""
    n = len(imgs01)
    rows = int(np.ceil(n / cols))
    H = imgs01.shape[1]
    factor = max(1, H // cell)
    tgt = H // factor
    step = tgt + gap
    canvas = np.zeros((rows * step + gap, cols * step + gap, 3), np.float32)
    canvas[:] = np.array(BG_RGB, np.float32) / 255.0
    good = np.array(GOOD_RGB, np.float32) / 255.0
    bad = np.array(BAD_RGB, np.float32) / 255.0
    for i in range(n):
        r, c = divmod(i, cols)
        g = imgs01[i].reshape(tgt, factor, tgt, factor).mean(axis=(1, 3))
        g = np.clip((g - 0.14) * 1.7, 0.0, 1.0)                 # boost so silhouette reads
        tint = good if mask[i] else bad
        cellimg = tint[None, None, :] * (0.16 + 0.84 * g[..., None])
        y, x = gap + r * step, gap + c * step
        canvas[y:y + tgt, x:x + tgt] = cellimg
    Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8), "RGB").save(path)
    return rows, cols


def main(debug=False):
    rng = np.random.default_rng(SEED)

    # ---- dataset ---------------------------------------------------------- #
    Xtr, ytr = make_dataset(500, rng)      # 1500 train
    Xva, yva = make_dataset(150, rng)      # 450 validation
    Xte, yte = make_dataset(800, rng)      # 2400 test (=> 60x40 grid)
    print(f"data: train {Xtr.shape}  val {Xva.shape}  test {Xte.shape}")

    # ---- one HPO sweep over hidden width; the three headline nets ARE three
    #      points on it, so scene-4's curve and scene-5's models are identical.
    sweep_w = [1, 2, 4, 8, 16, 32, 64, 128]
    CHOSEN = {"Tiny": 2, "Medium": 8, "Large": 64}    # width is the one knob
    EPOCHS = 90
    sweep_val, sweep_tr = [], []
    nets, curves, test_acc, val_acc_final, params = {}, {}, {}, {}, {}
    name_of = {w: n for n, w in CHOSEN.items()}
    for w in sweep_w:
        net = MLP([IMG * IMG, w, NC], seed=1)
        h = net.fit(Xtr, ytr, Xva, yva, epochs=EPOCHS, bs=64, lr=2e-3,
                    rng=np.random.default_rng(2))
        sweep_val.append(float(h["val_acc"][-1]))
        sweep_tr.append(float(h["train_acc"][-1]))
        tag = ""
        if w in name_of:
            name = name_of[w]
            nets[name] = net
            curves[name] = h
            test_acc[name] = net.accuracy(Xte, yte)
            val_acc_final[name] = float(h["val_acc"][-1])
            params[name] = int(sum(x.size for x in net.W) + sum(x.size for x in net.b))
            tag = f"  <-- {name} ({params[name]} params, test {test_acc[name]*100:.1f}%)"
        print(f"  sweep width={w:4d}  val={sweep_val[-1]*100:5.1f}%  train={sweep_tr[-1]*100:5.1f}%{tag}")
    ARCHES = [("Tiny", [IMG * IMG, CHOSEN["Tiny"], NC]),
              ("Medium", [IMG * IMG, CHOSEN["Medium"], NC]),
              ("Large", [IMG * IMG, CHOSEN["Large"], NC])]
    for name, _ in ARCHES:
        print(f"{name:7s} width={CHOSEN[name]:3d}  params={params[name]:5d}  "
              f"test_acc={test_acc[name]*100:5.1f}%  val={val_acc_final[name]*100:5.1f}%")

    # ---- one-training-step demo on a single car (scene 3) ---------------- #
    # Find a fresh (untrained) net + car image where the net is confidently
    # WRONG, so the story "predicts ship -> corrected to car" is genuine.
    car = CLASSES.index("car")
    car_idxs = np.where(ytr == car)[0]
    demo = None
    for seed in range(40):
        cand = MLP([IMG * IMG, 16, NC], seed=seed)
        for ci in car_idxs[:60]:
            p = cand.forward(Xtr[ci:ci + 1]).ravel()
            if p.argmax() != car and p.max() > 0.45:  # confidently wrong
                demo, car_idx = cand, int(ci)
                break
        if demo is not None:
            break
    if demo is None:                       # fallback: any misclassified car
        demo = MLP([IMG * IMG, 16, NC], seed=0)
        car_idx = int(car_idxs[int(np.argmin(demo.forward(Xtr[car_idxs])[:, car]))])
    dx, dy = Xtr[car_idx:car_idx + 1], ytr[car_idx:car_idx + 1]
    demo_before = demo.forward(dx).ravel().astype(np.float32)
    demo_loss_before = demo.loss(dx, dy)
    for _ in range(6):                     # a handful of steps -> improved, not perfect
        gW, gb = demo.grads(dx, dy)
        demo.adam_step(gW, gb, lr=2.2e-3)
    demo_after = demo.forward(dx).ravel().astype(np.float32)
    demo_loss_after = demo.loss(dx, dy)
    print(f"demo car: before={demo_before.round(2)} (loss {demo_loss_before:.2f}) "
          f"-> after={demo_after.round(2)} (loss {demo_loss_after:.2f})")

    # untrained near-uniform output (scene 2), from a fresh medium net
    untrained = MLP([IMG * IMG, 16, NC], seed=4).forward(dx).ravel().astype(np.float32)

    # ---- showcase images + each net's real prediction (scene 5) ---------- #
    # Curate a 3-per-class showcase (real predictions, illustrative picks) so the
    # tiny<medium<large gradient reads clearly: one image all three get right,
    # one only medium+large get, one only large gets. Honest full-set numbers
    # come from the dezoom grids, not this handful.
    pt = nets["Tiny"].forward(Xte).argmax(1) == yte
    pm = nets["Medium"].forward(Xte).argmax(1) == yte
    pl = nets["Large"].forward(Xte).argmax(1) == yte
    show_idx = []
    for ci in range(NC):
        pool = np.where(yte == ci)[0]
        A = [i for i in pool if pt[i] and pm[i] and pl[i]]        # all right
        B = [i for i in pool if (not pt[i]) and pm[i] and pl[i]]  # medium catches it
        C = [i for i in pool if (not pt[i]) and (not pm[i]) and pl[i]]  # only large
        chosen = [int(cat[0]) for cat in (A, B, C) if len(cat)]
        for i in pool:                                            # pad if a cat empty
            if len(chosen) >= 3:
                break
            if int(i) not in chosen:
                chosen.append(int(i))
        show_idx.extend(chosen[:3])
    show_idx = np.asarray(show_idx)
    show_imgs = Xte[show_idx].reshape(-1, IMG, IMG)
    show_true = yte[show_idx]
    show_pred = {name: nets[name].forward(Xte[show_idx]).argmax(1) for name, _ in ARCHES}
    for name, _ in ARCHES:
        print(f"  showcase {name:7s} correct {int((show_pred[name]==show_true).sum())}/9")

    # ---- correctness grids over the whole test set (baked PNGs) ---------- #
    Xte_imgs = Xte.reshape(-1, IMG, IMG)
    grid_shape = None
    for name, _ in ARCHES:
        mask = nets[name].forward(Xte).argmax(1) == yte
        grid_shape = _mosaic_png(Xte_imgs, mask, ASSETS / f"grid_{name.lower()}.png", cols=60)

    confusion_large = _confusion(nets["Large"], Xte, yte)

    # a couple of sample pixel images for scene 1/2 (one per class, clean-ish)
    gallery = {}
    grng = np.random.default_rng(99)
    for ci, cls in enumerate(CLASSES):
        gallery[cls] = np.stack([render_sample(cls, grng) for _ in range(6)])  # (6,12,12)

    # ---- save ------------------------------------------------------------- #
    out = ASSETS / "nn_learn.npz"
    np.savez_compressed(
        out,
        classes=np.array(CLASSES),
        img=IMG, n_train=len(ytr), n_val=len(yva), n_test=len(yte),
        # per-arch scalars
        arch_names=np.array([a[0] for a in ARCHES]),
        arch_sizes=np.array([a[1] for a in ARCHES], dtype=object),
        params=np.array([params[a[0]] for a in ARCHES]),
        test_acc=np.array([test_acc[a[0]] for a in ARCHES], np.float32),
        val_acc=np.array([val_acc_final[a[0]] for a in ARCHES], np.float32),
        # curves (medium is the "the training" hero curve; keep all three)
        cur_epoch=curves["Medium"]["epoch"],
        tiny_train_loss=curves["Tiny"]["train_loss"], tiny_train_acc=curves["Tiny"]["train_acc"],
        tiny_val_acc=curves["Tiny"]["val_acc"],
        med_train_loss=curves["Medium"]["train_loss"], med_train_acc=curves["Medium"]["train_acc"],
        med_val_acc=curves["Medium"]["val_acc"], med_val_loss=curves["Medium"]["val_loss"],
        large_train_loss=curves["Large"]["train_loss"], large_train_acc=curves["Large"]["train_acc"],
        large_val_acc=curves["Large"]["val_acc"],
        # HPO sweep
        sweep_w=np.array(sweep_w), sweep_val=np.array(sweep_val, np.float32),
        sweep_tr=np.array(sweep_tr, np.float32),
        # scene 3 demo
        demo_before=demo_before, demo_after=demo_after,
        demo_loss_before=np.float32(demo_loss_before), demo_loss_after=np.float32(demo_loss_after),
        demo_img=Xtr[car_idx].reshape(IMG, IMG), demo_true=CLASSES.index("car"),
        untrained_probs=untrained,
        # scene 2 pixel demo (a plane, mid-recognizable)
        pixel_img=gallery["plane"][0],
        # scene 5 showcase
        show_imgs=show_imgs, show_true=show_true,
        show_pred_tiny=show_pred["Tiny"], show_pred_med=show_pred["Medium"],
        show_pred_large=show_pred["Large"],
        # confusion (large)
        confusion_large=confusion_large,
        grid_rows=grid_shape[0], grid_cols=grid_shape[1],
        # small galleries per class for scene 1
        gal_car=gallery["car"], gal_plane=gallery["plane"], gal_ship=gallery["ship"],
    )
    print(f"\n[ok] wrote {out}  ({out.stat().st_size//1024} KB)")
    print(f"[ok] grids: {grid_shape[0]}x{grid_shape[1]} cells each")

    if debug:
        # montage: 3 rows (classes) x 8 samples, upscaled, to eyeball readability
        drng = np.random.default_rng(123)
        tiles = []
        for cls in CLASSES:
            row = [render_sample(cls, drng) for _ in range(8)]
            tiles.append(np.concatenate(row, axis=1))
        mont = np.concatenate(tiles, axis=0)
        big = np.repeat(np.repeat((mont * 255).astype(np.uint8), 16, 0), 16, 1)
        Image.fromarray(big, "L").save(ASSETS / "debug_montage.png")
        print(f"[ok] wrote {ASSETS/'debug_montage.png'} (rows: car / plane / ship)")


if __name__ == "__main__":
    main(debug="--debug" in sys.argv)
