# The Jacobian Conjecture — a short explainer

A ~2.5-minute, house-style Manim film on a famous 87-year-old problem in
algebraic geometry — **what it claims, why everyone believed it, and how an
explicit counterexample was found in July 2026 with an AI in the loop.**

> **The Jacobian Conjecture** (O.-H. Keller, 1939). Let *F* : ℂⁿ → ℂⁿ be a
> polynomial map whose Jacobian determinant `det(DF)` is a nonzero constant.
> Then *F* is invertible, with a polynomial inverse.

True for *n* = 1, open for *n* = 2, and believed true for all *n* — experts
guessed the smallest counterexample, if any, would need a very high degree.
Then **Levent Alpöge, with Anthropic's Claude Fable 5**, produced an explicit
**degree-7** map `F : ℂ³ → ℂ³` with `det(DF) = -2` that is **not injective**:

```python
F1 = (1+z1*z2)**3*z3 + z2**2*(1+z1*z2)*(4+3*z1*z2)
F2 = z2 + 3*z1*(1+z1*z2)**2*z3 + 3*z1*z2**2*(4+3*z1*z2)
F3 = 2*z1 - 3*z1**2*z2 - z1**3*z3

F(0, 0, -1/4) == F(1, -3/2, 13/2) == F(-1, 3/2, 13/2) == (-1/4, 0, 0)
```

Three distinct inputs land on one image ⇒ *F* is not one-to-one ⇒ not
invertible. **The conjecture is false for every dimension *n* ≥ 3.** (*n* = 2
remains open.) Terence Tao published a "digestion" explaining *why* the
construction works.

Everything the film asserts is machine-checked first — run `python3 verify.py`
(pure Python, no dependencies): it confirms `det(DF)` is *exactly* `-2` with
exact rational arithmetic, and that the three points collide.

## What it teaches

1. **The conjecture** — a polynomial map ℂⁿ → ℂⁿ, its Jacobian matrix `DF`, the
   determinant, and the claim *constant Jacobian ⇒ globally invertible*.
2. **Why everyone believed it** — in one variable a constant derivative forces a
   straight line (obviously invertible); in higher dimensions `det(DF)` can stay
   constant while the entries twist — the room where a counterexample could hide.
   The 87-year wall.
3. **The counterexample** — the explicit degree-7 map as runnable `sympy`, and
   the check that `det(DF) = -2` (the hypothesis holds).
4. **One image, three preimages** — the real geometry (Tao's picture): two 3-D
   panels. Left, a *source curve* `b → a → c` through the three preimages; right,
   its *image* under *F* — a loop that passes through **one** point three times.
   Three different inputs, one image ⇒ not injective ⇒ not invertible ⇒
   **false for n ≥ 3**. The curves are the real *F* sampled on the real curve
   (see `verify.py` / `scene_collision`), not an illustration.
5. **How it was found** — Alpöge × Claude Fable 5 (Anthropic), the casual
   announcement (a stylised tweet card), machine-verifiability, Tao's digestion,
   and where the problem stands now (n=1 true · n=2 open · n≥3 false).

Opens on a cold-open **hook** (a grid that *F* swirls/folds onto itself, with
`det J = −2`) and is bookended by the channel's intro / outro cards.

## Scenes

`Hook · Intro · Conjecture · Intuition · Counterexample · Collision · Significance · Outro`

Each renders alone; `JacobianConjecture` is the whole film.

## Render

```bash
./render.sh collision --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                     # whole film, 480p
./render.sh full -q h                # final 1080p60 master (slow)
./render.sh --stitch -q m            # render each scene and concat (720p)
```

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN) or bootstraps a local `.venv` from `requirements.txt`
(Manim 0.21, no LaTeX — all "formulas" are built from `Text`).

Pacing: `JC_QUICK=1` (or `--quick`) collapses the reading holds; `JC_DELAY=<s>`
overrides the reading rhythm (default `2.4` — generous, so formula screens have
time to read).

**Measured runtime:** 3:45 at 480p (full film, default pacing).

## Credits & sources

- Counterexample: **Levent Alpöge with Claude Fable 5 (Anthropic)**, 2026 —
  pending peer review (tracked at openconjectures.org).
- Terence Tao, *"A digestion of the Jacobian conjecture counterexample"* (2026).
- Original conjecture: Ott-Heinrich Keller, 1939.
