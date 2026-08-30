# Lockfiles — a short explainer

A no-voiceover, house-style Manim film on **`package.json` vs `package-lock.json`,
and why committing the lockfile is what makes a build reproducible** across a team.
It anchors on the *real files* — the manifest you write, the lockfile the tool
computes — and closes by showing the same manifest-plus-lockfile pattern in
Python's Poetry (`pyproject.toml` + `poetry.lock`) and beyond.

## What it teaches

1. **The manifest** — `package.json` is what *you* declare: a few direct
   dependencies, each pinned to a version **range** (`"express": "^4.18.2"`), not a
   single version.
2. **A range, not a version** — semver is `MAJOR.MINOR.PATCH`, and the caret `^`
   accepts any newer minor or patch below the next major (`^4.18.2` → `>=4.18.2
   <5.0.0`). So `npm install` today and next month can resolve *different*
   versions: the install isn't deterministic. *"...but it works on my machine."*
3. **The lockfile** — `package-lock.json` records the answer install resolved: the
   **whole tree** (two named deps can pull in dozens), every package pinned to an
   exact `version`, with a `resolved` URL and an `integrity` hash. `npm ci` replays
   it verbatim.
4. **Same tree, everywhere** — without a lock, two devs, CI and prod each resolve
   their own tree and drift apart (the bug nobody else can reproduce). Commit the
   lock and every environment gets the **identical** tree, bit for bit — and the
   integrity hashes mean nobody swapped a package underneath you.
5. **The same pattern** — `pyproject.toml` + `poetry.lock` is the same split (a
   manifest you write, a lockfile the tool computes, `poetry install` to replay).
   So is Cargo, Bundler, Go, Composer. **Declare loose. Lock exact. Commit both.**

Closes on a one-line recap: *package.json says what you want; package-lock.json
pins what you got — so every machine builds the same thing.*

## Scenes

`Intro · Manifest · Ranges · Lockfile · Repro · Pattern · Recap · Outro`

Each renders on its own; `LockfilesFilm` renders the whole thing end to end.

## Render

```bash
./render.sh ranges --quick      # fast layout check of one scene (480p15)
./render.sh                     # whole film, 480p
./render.sh full -q h           # final 1080p60 (HQ)
./render.sh --stitch -q m       # render each scene and concat (720p30)
```

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN) if present, otherwise bootstraps a local `.venv`. No LaTeX — all
text is Pango `Text`; the JSON/TOML is set in Menlo with a quote-precise syntax
highlighter.

Pacing knobs: `PL_QUICK=1` collapses the reading holds for fast iteration;
`PL_DELAY` / `PL_READ` fine-tune the cadence.

## Runtime

Measured full-film duration (`LockfilesFilm`, 720p30): **3:02** (182.6 s),
1280×720 @ 30 fps. Edge-bleed scan clean across every scene and the full film.
