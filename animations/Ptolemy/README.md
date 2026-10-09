# Ptolemy's Theorem

A short, no-voice-over explainer for the most beautiful fact linking the sides
and the diagonals of a quadrilateral drawn inside a circle:

```
AC · BD  =  AB · CD  +  BC · DA
```

For a cyclic quadrilateral `ABCD` (four points on a circle, taken in order), the
product of the two diagonals equals the sum of the products of the two pairs of
opposite sides. It is named for Claudius Ptolemy (~150 AD), who used it to build
the first table of chords, the ancestor of the sine table.

## What it teaches

- The statement itself, colour-coded so the geometry and the algebra line up:
  the diagonals are violet, one pair of opposite sides is blue, the other green.
- That it is *true numerically*: with real coordinates, all six lengths and both
  products are computed and shown to match, and they stay matched as a point is
  dragged around the circle.
- *Why* it is true: the classical proof by two pairs of similar triangles.
- That it is more general than it looks: a rectangle turns it into the
  Pythagorean theorem.
- That the circle is essential: lift one point out of the plane and equality
  breaks, `AC · BD < AB · CD + BC · DA`. Equality is the knife-edge that holds
  exactly when the four points are concyclic (Ptolemy's inequality).

Every number on screen is a real distance between real point coordinates,
computed and asserted at import time (there is no hand-typed "answer").

## Scenes

1. **Intro** — title card with an inscribed-quadrilateral emblem.
2. **Setup** — a circle, four points, the quadrilateral, the two diagonals, and
   the colour-coded statement.
3. **Check** — a concrete cyclic quadrilateral: the six real lengths, the two
   products, and a live drag of point `D` around the circle with both sides
   staying exactly equal.
4. **Proof** — place `K` on diagonal `AC` so that `∠ABK = ∠DBC`; two pairs of
   similar triangles give `AK·BD = AB·CD` and `KC·BD = BC·DA`; adding them (with
   `AK + KC = AC`) finishes it.
5. **Pythagoras** — the special case: inscribe a rectangle. Both diagonals are a
   diameter, so Ptolemy collapses to `d² = a² + b²`.
6. **Space** — *3D*. Keep `A B C` on the circle and lift `D` up out of the
   plane. The diagonal product falls short of the sum; equality snaps back the
   moment `D` returns to the circle. The camera orbits so you can see the point
   leave the plane. This is the only scene with camera movement (a genuine 3D
   object earns it).
7. **Recap** — one card: the statement and the four things we saw.
8. **Outro** — thank-you card.

## Rendering

```bash
./render.sh setup --quick -q l     # fast layout check of one scene (480p15)
./render.sh space --quick -q l     # check the 3D scene
./render.sh full                   # whole film, 480p (stitched)
./render.sh full -q h              # final 1080p60 (slow; run in background)
```

The film mixes 2D `Scene` classes and one 3D `ThreeDScene` (`Space`), so `full`
always renders each scene and stitches them with ffmpeg (there is no single
all-in-one class). `render.sh` reuses an existing Manim venv
(`HarnessEngineering` / `Fourier` / `CNN`) if present, else bootstraps a local
`.venv`. The 3D scene's partial-movie writes stall on the OneDrive mount, so the
media dir defaults to `/private/tmp/ptol-media` (override with `PTOL_MEDIA_DIR`).

Env knobs: `PTOL_QUICK=1` collapses the reading holds; `PTOL_DELAY=x` overrides
the reading-hold multiplier.

## Runtime

Measured full film (1080p60): **3:46** (226.7 s). Per scene: Intro 9.5s, Setup
32.2s, Check 41.6s, Proof 46.1s, Pythagoras 31.7s, Space 34.6s, Recap 22.3s,
Outro 8.8s.

## Notes

- No LaTeX: all text is Pango `Text`, with super/subscripts (`d²`, `a²`, `b²`)
  built from scaled `Text` pieces so they stay crisp and in the body font.
- No real-world dataset applies (this is pure planar geometry); the "real data"
  is the point coordinates, from which every length and product is computed.
