# The Story of Gravity

A short (~3-minute), house-style explainer that tells the story of gravity in
four beats — no voice-over, everything is on screen. Built from shapes, motion
and small captions; it uses `Text` (Pango), so it renders without LaTeX.

![Newton's cannonball: fast enough sideways, and the fall becomes an orbit](media/preview.png)

## The idea

The free-fall motion is physically honest: objects drop with position ∝ t²
(constant acceleration), so the light and heavy balls really do land together,
and the strobe of velocity arrows really does grow linearly. The rest is the
classic narrative arc — from an apple on the ground to the law that moves the
planets.

## The film (`Gravity`)

Bookended by the channel's intro card and the "Thank you for watching!" outro,
four scenes:

1. **Why things fall** — everything drops, always down. Aristotle's 2000-year
   hunch ("heavier falls faster") is crossed out; Galileo drops two balls that
   land together. The punchline: one acceleration for all, **g ≈ 9.8 m/s²**,
   with velocity growing every second.
2. **Newton's leap · 1666** — the apple, and the bigger question: how far up
   does the pull reach? The same force that drops the apple holds the **Moon**.
   Why doesn't the Moon fall? *It does* — it just moves sideways fast enough to
   keep missing. Newton's **cannonball**: fire it faster and faster until the
   fall closes into an **orbit**.
3. **The universal law** — every mass attracts every other mass:
   **F = G · m₁·m₂ / r²**. More mass → stronger pull; twice as far → a *quarter*
   of the force (the inverse-square, shown concretely). **G = 6.674 × 10⁻¹¹** is
   tiny — gravity is the weakest force — but mass piles up and planets are huge.
4. **From an apple to the cosmos** — a little solar system turns while one
   equation ticks off the apple, the Moon, the planets, the tides, and the
   galaxies. A closing nod: two centuries later Einstein recast gravity as
   curved spacetime, but for apples and planets Newton still rules.

## Rendering

```bash
./render.sh newton --quick     # fast sanity check of one scene
./render.sh                    # the whole film, 480p
./render.sh full -q m          # final 720p
./render.sh full -q h          # 1080p
./render.sh --stitch -q m      # render each scene and join into one film
```

`render.sh` reuses the HarnessEngineering / CNN / Fourier series' `.venv` if it
finds one (so Manim isn't reinstalled), otherwise it bootstraps a local `.venv`
from `requirements.txt`.

Individually renderable scenes: `intro` · `falling` · `newton` · `law` ·
`cosmos` · `outro` (or `full`, the default).

`GRAV_QUICK=1` (or `--quick`) shortens the on-screen holds while iterating. The
palette and pacing knob (`DELAY`) live at the top of `gravity.py`.
