"""Pack 17 unit squares into the smallest square we can find, and record the search.

This implements the formulation Gensane & Ryckelynck used for congruent square
packings ("Improved Dense Packings of Congruent Squares in a Square", Discrete
Comput. Geom. 34, 2005): optimise the MAXIMAL INFLATION FUNCTION.  The state is
(x, y, theta) for every square with centers in the unit container [0,1]^2.  For
a pair of squares the clearance is the largest common side a they could have
without overlapping (computed exactly from the separating-axis theorem: the
best of the 4 face-normal axes); for a wall it is the largest side that stays
inside.  The inflation limit

    lambda(config) = min over all 136 pairs and 17 walls of the clearance

is the true square size this configuration supports, so the equivalent
container side for UNIT squares is s = 1 / lambda.  There is no feasibility
knife-edge: every configuration is a valid packing at its own lambda, and the
search just pushes lambda up.  A simulated annealer maximises a soft-min
version of lambda (so every near-bottleneck contact contributes), then an exact
hill-climb polish squeezes the last fractions.

The naive 5x5 grid start has lambda = 1/5 exactly; the Bidwell record
corresponds to lambda = 1/4.67553 = 0.21388.

Outputs (assets/):
    packing_run.npz   trajectory snapshots in unit-square view (for the film),
                      milestones, the best configuration, the naive grid.  The
                      best packing is re-verified strictly (SAT, tol 1e-9) at
                      save time and again at manim import time.
    preview_*.jpg     meme-style stills (white box, gray squares).

Env knobs:
    SP_BUDGET  wall-clock seconds for the search (default 480)
    SP_SEED    RNG seed (default 7)
"""
from __future__ import annotations

import os
import time

import numpy as np

N = 17
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
BUDGET = float(os.environ.get("SP_BUDGET", "480"))
SEED = int(os.environ.get("SP_SEED", "7"))
RECORD_LAMBDA = 1.0 / 4.67553009360455          # Bidwell 1998

rng = np.random.default_rng(SEED)
PAIR_I, PAIR_J = np.triu_indices(N, 1)          # 136 unordered pairs
IDX = np.arange(N)


# --------------------------------------------------------------------------- #
# clearances (all exact SAT face-normal computations)
# --------------------------------------------------------------------------- #
def pair_clear(ci, thi, cJ, thJ):
    """Largest common square side such that square i and each square in J do
    not overlap: max over the 4 candidate separating axes of |d.a| / (ri+rj),
    where ri, rj are the per-unit-side support radii along axis a."""
    cJ = np.atleast_2d(cJ)
    thJ = np.atleast_1d(thJ)
    m = len(thJ)
    ui = np.array([np.cos(thi), np.sin(thi)])
    vi = np.array([-np.sin(thi), np.cos(thi)])
    uJ = np.stack([np.cos(thJ), np.sin(thJ)], axis=1)
    vJ = np.stack([-np.sin(thJ), np.cos(thJ)], axis=1)
    axes = np.empty((m, 4, 2))
    axes[:, 0, :] = ui
    axes[:, 1, :] = vi
    axes[:, 2, :] = uJ
    axes[:, 3, :] = vJ
    d = cJ - ci
    dist = np.abs(np.einsum("mae,me->ma", axes, d))            # (m,4)
    ri = 0.5 * (np.abs(axes @ ui) + np.abs(axes @ vi))
    rj = 0.5 * (np.abs(np.einsum("mae,me->ma", axes, uJ))
                + np.abs(np.einsum("mae,me->ma", axes, vJ)))
    return np.max(dist / (ri + rj), axis=1)                    # (m,)


def wall_clear(c, th):
    """Largest square side keeping each square inside the unit container."""
    c = np.atleast_2d(c)
    th = np.atleast_1d(th)
    r = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    gap = np.minimum(np.minimum(c[:, 0], 1 - c[:, 0]),
                     np.minimum(c[:, 1], 1 - c[:, 1]))
    return gap / r


def all_pair_clear(c, th):
    """Clearances for all 136 pairs at once."""
    ci, cj = c[PAIR_I], c[PAIR_J]
    u = np.stack([np.cos(th), np.sin(th)], axis=1)
    v = np.stack([-np.sin(th), np.cos(th)], axis=1)
    axes = np.stack([u[PAIR_I], v[PAIR_I], u[PAIR_J], v[PAIR_J]], axis=1)
    d = cj - ci
    dist = np.abs(np.einsum("pae,pe->pa", axes, d))
    ri = 0.5 * (np.abs(np.einsum("pae,pe->pa", axes, u[PAIR_I]))
                + np.abs(np.einsum("pae,pe->pa", axes, v[PAIR_I])))
    rj = 0.5 * (np.abs(np.einsum("pae,pe->pa", axes, u[PAIR_J]))
                + np.abs(np.einsum("pae,pe->pa", axes, v[PAIR_J])))
    return np.max(dist / (ri + rj), axis=1)                    # (136,)


def lam_of(c, th):
    """The exact inflation limit lambda for a configuration."""
    return min(all_pair_clear(c, th).min(), wall_clear(c, th).min())


def sq_min_clear(c, th):
    """Per-square minimum clearance (its tightest pair or wall)."""
    A = all_pair_clear(c, th)
    m = np.full(N, np.inf)
    np.minimum.at(m, PAIR_I, A)
    np.minimum.at(m, PAIR_J, A)
    return np.minimum(m, wall_clear(c, th))


# --------------------------------------------------------------------------- #
# soft-min objective:  F = -tau * log sum exp(-a / tau)  (maximise)
# --------------------------------------------------------------------------- #
def soft_F(vals, tau):
    a0 = vals.min()
    return a0 - tau * np.log(np.sum(np.exp(-(vals - a0) / tau)))


# --------------------------------------------------------------------------- #
# trajectory recording (unit-square view: container side 1/lam, centers c/lam)
# --------------------------------------------------------------------------- #
REC_EVERY = 900
_rec = {"c": [], "th": [], "s": [], "pen": [], "it": []}
_props = 0
_last_rec = -10**9


def record(c, th, force=False):
    global _last_rec
    if not force and _props - _last_rec < REC_EVERY:
        return
    _last_rec = _props
    lam = lam_of(c, th)
    s = 1.0 / lam
    mins = sq_min_clear(c, th)
    # contact pressure in [0,1]: 1 = this square sits on the bottleneck
    margin = 0.004 * lam
    press = np.clip((lam + margin - mins) / margin, 0.0, 1.0)
    _rec["c"].append(c * s)
    _rec["th"].append(th.copy())
    _rec["s"].append(s)
    _rec["pen"].append(press)
    _rec["it"].append(_props)


# --------------------------------------------------------------------------- #
# annealer on the soft-min objective
# --------------------------------------------------------------------------- #
def anneal(c, th, t_end, sched, T0=6e-3, T1=1e-5, tau0=1.5e-3, tau1=1e-4,
           sig0=0.014, sig1=0.0012, rot0=0.45, rot1=0.02):
    """Metropolis on -F. Incremental: only square i's 16 pairs + wall change.

    ``t_end`` is when this call returns; ``sched=(t0, t1)`` is the GLOBAL
    annealing window that the temperature / move-size schedules are pinned to
    (so calling this in short slices does not collapse the schedule).
    """
    global _props
    A = all_pair_clear(c, th)                      # (136,)
    Wc = wall_clear(c, th)                         # (17,)
    pair_rows = [np.where((PAIR_I == i) | (PAIR_J == i))[0] for i in range(N)]
    pair_other = [np.where(PAIR_I == i, PAIR_J, PAIR_I)[pair_rows[i]]
                  for i in range(N)]
    sched_t0, sched_t1 = sched
    span = max(sched_t1 - sched_t0, 1.0)
    T, tau, sig, rot = T0, tau0, sig0, rot0
    F = soft_F(np.concatenate([A, Wc]), tau)
    n_acc = 0
    while time.time() < t_end:
        for _ in range(4000):
            _props += 1
            if _props % 512 == 0:
                f = min(max((time.time() - sched_t0) / span, 0.0), 1.0)
                T = T0 * (T1 / T0) ** f
                tau = tau0 * (tau1 / tau0) ** f
                sig = sig0 * (sig1 / sig0) ** f
                rot = rot0 * (rot1 / rot0) ** f
                F = soft_F(np.concatenate([A, Wc]), tau)
            i = int(rng.integers(N))
            kind = rng.random()
            nc, nth = c[i].copy(), th[i]
            if kind < 0.62:
                nc = nc + rng.normal(0, sig, 2)
                nth = nth + rng.normal(0, rot * 0.30)
            elif kind < 0.82:
                if rng.random() < 0.5:
                    nth = nth + rng.normal(0, rot)
                else:
                    base = np.round(nth / (np.pi / 4)) * (np.pi / 4)
                    nth = base + rng.normal(0, 0.015)
            elif kind < 0.92:
                d = np.array([0.5, 0.5]) - nc
                nc = nc + d * rng.uniform(0, 0.08) + rng.normal(0, sig * 0.5, 2)
            else:
                nth = rng.uniform(0, np.pi / 2)
                nc = rng.uniform(0.18, 0.82, 2)
            rows = pair_rows[i]
            oth = pair_other[i]
            newA = pair_clear(nc, nth, c[oth], th[oth])
            newW = wall_clear(nc, nth)[0]
            oldA_rows = A[rows].copy()
            oldW_i = Wc[i]
            A[rows] = newA
            Wc[i] = newW
            F_new = soft_F(np.concatenate([A, Wc]), tau)
            dF = F_new - F
            if dF >= 0 or rng.random() < np.exp(dF / T):
                c[i], th[i] = nc, nth
                F = F_new
                n_acc += 1
                record(c, th)
            else:
                A[rows] = oldA_rows
                Wc[i] = oldW_i
    return n_acc


# --------------------------------------------------------------------------- #
# exact hill-climb polish on true lambda
# --------------------------------------------------------------------------- #
def polish(c, th, t_end, step0=2.5e-3, rot_mult=6.0, floor=2e-6):
    global _props
    step = step0
    lam = lam_of(c, th)
    while step > floor and time.time() < t_end:
        improved = False
        for i in range(N):
            base_c, base_th = c[i].copy(), th[i]
            cands = [(step, 0, 0), (-step, 0, 0), (0, step, 0), (0, -step, 0),
                     (0, 0, step * rot_mult), (0, 0, -step * rot_mult),
                     (step, step, 0), (-step, step, 0),
                     (step, -step, 0), (-step, -step, 0)]
            for dx, dy, dth in cands:
                _props += 4
                c[i] = base_c + np.array([dx, dy])
                th[i] = base_th + dth
                l2 = lam_of(c, th)
                if l2 > lam + 1e-14:
                    lam = l2
                    base_c, base_th = c[i].copy(), th[i]
                    improved = True
                else:
                    c[i], th[i] = base_c, base_th
            record(c, th)
        if not improved:
            step *= 0.55
    return lam


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def naive_start():
    """The naive packing: 4x4 block + 1, side 5  ->  lambda = 0.2 exactly."""
    c = []
    for j in range(4):
        for i in range(4):
            c.append([(i + 0.5) / 5, (j + 0.5) / 5])
    c.append([4.5 / 5, 0.5 / 5])
    return np.array(c, dtype=float), np.zeros(N)


def main():
    t0 = time.time()
    c, th = naive_start()
    lam = lam_of(c, th)
    assert abs(lam - 0.2) < 1e-12, f"grid start should have lambda=0.2, got {lam}"
    record(c, th, force=True)
    best = dict(lam=lam, c=c.copy(), th=th.copy())
    milestones = [(lam, c.copy(), th.copy())]
    print(f"start: lambda={lam:.6f} (side {1/lam:.4f}), budget {BUDGET:.0f}s, "
          f"seed {SEED}")

    # ---- basin-hopping cycles: anneal (cooling per cycle) + exact polish -- #
    def adopt(lam, tag):
        nonlocal best
        if lam > best["lam"] + 1e-9:
            best = dict(lam=lam, c=c.copy(), th=th.copy())
            milestones.append((lam, c.copy(), th.copy()))
            record(c, th, force=True)
            print(f"  t={time.time()-t0:6.1f}s  props={_props/1e6:5.2f}M  "
                  f"{tag}  side={1/lam:.6f}")

    t_final = t0 + BUDGET
    k = 0
    while time.time() < t_final - 0.10 * BUDGET:
        T0k = max(6e-3 * (0.62 ** k), 7e-4)
        cyc_start = time.time()
        cyc_end = min(cyc_start + 0.24 * BUDGET, t_final - 0.06 * BUDGET)
        if cyc_end - cyc_start < 8:
            break
        while time.time() < cyc_end:
            anneal(c, th, min(time.time() + 6.0, cyc_end),
                   sched=(cyc_start, cyc_end), T0=T0k)
            adopt(lam_of(c, th), f"anneal[{k}]")
        adopt(polish(c, th, min(time.time() + 0.08 * BUDGET, t_final)),
              f"polish[{k}]")
        c, th = best["c"].copy(), best["th"].copy()
        k += 1
    adopt(polish(c, th, t_final), "polish[final]")
    print(f"search done: side={1/best['lam']:.6f} after {k} cycles")

    # ---- verify strictly in unit-square view ------------------------------ #
    lam_b = best["lam"]
    sb = 1.0 / lam_b
    cb = best["c"] * sb                    # centers for UNIT squares in [0,sb]^2
    thb = best["th"].copy()
    A = all_pair_clear(best["c"], best["th"])
    Wc = wall_clear(best["c"], best["th"])
    assert A.min() >= lam_b - 1e-12 and Wc.min() >= lam_b - 1e-12
    # independent overlap check at unit scale: penetration must be ~0
    worst = sat_worst_pen(cb, thb, sb)
    assert worst <= 1e-9, f"unit-view overlap {worst}"
    print(f"done: best side = {sb:.6f}  (record 4.675530)  "
          f"props={_props/1e6:.2f}M  wall={time.time()-t0:.0f}s  "
          f"frames={len(_rec['s'])}")

    F = len(_rec["s"])
    keep = np.unique(np.linspace(0, F - 1, min(F, 3600)).round().astype(int))
    mile_lam = np.array([m[0] for m in milestones])
    np.savez_compressed(
        os.path.join(ASSETS, "packing_run.npz"),
        traj_c=np.array(_rec["c"])[keep],
        traj_th=np.array(_rec["th"])[keep],
        traj_s=np.array(_rec["s"])[keep],
        traj_pen=np.array(_rec["pen"])[keep],
        traj_it=np.array(_rec["it"])[keep],
        best_s=sb, best_c=cb, best_th=thb,
        mile_s=1.0 / mile_lam,
        mile_c=np.array([m[1] for m in milestones]) / mile_lam[:, None, None],
        mile_th=np.array([m[2] for m in milestones]),
        naive_c=naive_start()[0] * 5.0, naive_th=naive_start()[1],
        seed=SEED, props=_props,
    )
    print(f"saved assets/packing_run.npz  ({len(keep)} trajectory frames, "
          f"{len(milestones)} milestones)")
    previews(milestones, sb, cb, thb)


def sat_worst_pen(c, th, s):
    """Worst SAT penetration of unit squares (pairs) or wall protrusion."""
    u = np.stack([np.cos(th), np.sin(th)], axis=1)
    v = np.stack([-np.sin(th), np.cos(th)], axis=1)
    axes = np.stack([u[PAIR_I], v[PAIR_I], u[PAIR_J], v[PAIR_J]], axis=1)
    d = c[PAIR_J] - c[PAIR_I]
    dist = np.abs(np.einsum("pae,pe->pa", axes, d))
    ri = 0.5 * (np.abs(np.einsum("pae,pe->pa", axes, u[PAIR_I]))
                + np.abs(np.einsum("pae,pe->pa", axes, v[PAIR_I])))
    rj = 0.5 * (np.abs(np.einsum("pae,pe->pa", axes, u[PAIR_J]))
                + np.abs(np.einsum("pae,pe->pa", axes, v[PAIR_J])))
    pen = np.maximum(np.min(ri + rj - dist, axis=1), 0.0)
    r = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    lo = np.maximum(0.0, r[:, None] - c)
    hi = np.maximum(0.0, c + r[:, None] - s)
    return max(pen.max(initial=0.0), lo.max(initial=0.0), hi.max(initial=0.0))


# --------------------------------------------------------------------------- #
# meme-style JPG previews (white box, gray squares)
# --------------------------------------------------------------------------- #
def previews(milestones, sb, cb, thb):
    from PIL import Image, ImageDraw

    def draw(s, c, th, path, px=900):
        pad = 40
        scale = (px - 2 * pad) / s
        im = Image.new("RGB", (px, px), "#ffffff")
        dr = ImageDraw.Draw(im)
        dr.rectangle([pad - 3, pad - 3, pad + s * scale + 3, pad + s * scale + 3],
                     outline="#222222", width=3)
        for k in range(N):
            u = np.array([np.cos(th[k]), np.sin(th[k])])
            v = np.array([-np.sin(th[k]), np.cos(th[k])])
            pts = [c[k] + 0.5 * (sx * u + sy * v)
                   for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
            pix = [(pad + p[0] * scale, pad + (s - p[1]) * scale) for p in pts]
            dr.polygon(pix, fill="#5a5f63", outline="#ffffff")
        im.save(path, quality=92)
        print(f"  wrote {os.path.basename(path)}  (s={s:.4f})")

    lam0, c0, th0 = milestones[0]
    draw(1 / lam0, c0 / lam0, th0, os.path.join(ASSETS, "preview_start.jpg"))
    lamm, cm, thm = milestones[len(milestones) // 2]
    draw(1 / lamm, cm / lamm, thm, os.path.join(ASSETS, "preview_mid.jpg"))
    draw(sb, cb, thb, os.path.join(ASSETS, "preview_best.jpg"))


if __name__ == "__main__":
    main()
