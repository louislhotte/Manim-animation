# The Geometry of (a + b)²

A short (~2-minute), house-style **visual proof** of the perfect-square identity

> **(a + b)²  =  a² + 2ab + b²**

No voice-over — everything is on screen, and every hold is timed so you can read
it before it moves on. Uses `Text` (Pango) rather than `Tex`, so it renders
without a LaTeX toolchain.

![the square of side (a+b), split into a², ab, ab, b²](media/preview.png)

## The idea

Build a square whose side is **a + b**. Its area is **(a + b)²** by definition.
Now split each side into a segment of length `a` and one of length `b`. The two
cuts carve the square into **four quadrant-aligned blocks**:

```
        ┌───────────┬───────┐
        │           │       │
    b   │    ab     │  b²   │      a² : the corner square  (a × a)
        │           │       │      b² : the corner square  (b × b)
        ├───────────┼───────┤      ab : two equal strips   (a × b)
        │           │       │
    a   │    a²     │  ab   │      area of whole = sum of parts
        │           │       │       (a + b)² = a² + 2ab + b²
        └───────────┴───────┘
              a         b
```

The whole area equals the sum of the pieces, so **(a + b)² = a² + 2ab + b²** —
and you can *see* that the middle **2ab** is just the two off-diagonal strips.
Colours are consistent throughout: **a / a²** blue, **b / b²** green, the two
**ab** strips amber.

## The film (`BinomialSquare`)

Bookended by the channel's intro card and the "Thank you for watching!" outro,
four scenes:

1. **Squaring a sum** — the identity, and the classic mistake `(a+b)² ≠ a² + b²`:
   where does the middle **2ab** come from?
2. **Build a square of side (a + b)** — the core proof. Split the square, colour
   the four blocks (**a²**, **ab**, **ab**, **b²**), and assemble the identity
   area-by-area; the two equal strips *are* the `2ab`.
3. **One identity — every split** — with `a + b` fixed at **5**, slide the split
   and watch the live areas. Three examples — **(3, 2) → 9 + 12 + 4**,
   **(4, 1) → 16 + 8 + 1**, **(2, 3) → 4 + 12 + 9** — and every one totals **25 = 5²**.
4. **Count the squares** — a countable unit grid for `a = 2, b = 1`:
   **4 + 2 + 2 + 1 = 9 = 3²**, then the payoff — squaring in your head:
   **21² = (20 + 1)² = 400 + 40 + 1 = 441**.

## Rendering

```bash
./render.sh proof --quick     # fast sanity check of one scene
./render.sh                   # the whole film, 480p
./render.sh full -q m         # final 720p
./render.sh full -q h         # 1080p
./render.sh --stitch -q m     # render each scene and join into one film
```

`render.sh` reuses the HarnessEngineering / CNN / Fourier series' `.venv` if it
finds one (so Manim isn't reinstalled), otherwise it bootstraps a local `.venv`
from `requirements.txt`.

Individually renderable scenes: `intro` · `hook` · `proof` · `vary` · `grid` ·
`outro` (or `full`, the default).

`PS_QUICK=1` (or `--quick`) shortens the on-screen holds while iterating. Pacing
(`DELAY`), the palette, and the master square geometry all live at the top of
`binomial_square.py`. The default `DELAY` is tuned so the full film lands at
almost exactly **2:00**.
