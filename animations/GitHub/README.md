# Git & GitHub, Visually

A short (~2:50), house-style explainer that shows — at a high level, one action
per scene — what Git & GitHub are *for* and how the everyday moves actually work.

No voice-over: everything is on screen, and every hold is timed so you can read
it before it moves on. Uses `Text` (Pango) rather than `Tex`, so it renders
without a LaTeX toolchain.

![five people, five branches, all merging back into main](media/preview.png)

## The idea

One picture carries the whole film — the **commit graph**:

```
   feature ●──●                 a branch: a parallel line of work
          ╱     ╲
   main ●──●──●──●──●           commits are dots, linked into history;
        └ snapshot  └ merge       a merge ties two lines back together
```

- **commit**  → a saved snapshot of your whole project (message, author, time)
- **push**    → send your local commits up to GitHub so the team can see them
- **branch**  → a safe, parallel line of work off `main`
- **merge**   → bring a finished branch back into `main` (on GitHub, via a PR)
- **cherry-pick** → copy just *one* commit from another branch, not the whole thing

Colours are consistent throughout: `main` is **blue**, and each collaborator /
feature branch keeps its own colour (green, amber, purple, pink, teal).

## The film (`GitHubExplained`)

Bookended by the channel's intro card and the "Thank you for watching!" outro,
seven scenes — one action each, in build-up order:

1. **What are Git & GitHub?** — the high-level picture: Git is version control on
   your computer (every change saved as a commit); GitHub is the shared home for
   your code online. `push` up, `pull` down. *Track every change · work in
   parallel · never lose work.*
2. **Commit — save a snapshot** — edit some files, `git commit`, and a commit dot
   lands on the lane with its message and hash. Commits link into your history.
3. **Push — share it on GitHub** — your commits start life only on your laptop;
   `git push` sends them up to `origin/main` so they're backed up and visible.
4. **Branch — work in parallel** — `git checkout -b feature` forks a parallel
   line off `main`; you commit freely while `main` keeps moving, untouched.
5. **Merge — bring it back together** — open a **Pull Request** so teammates can
   review, then `git merge` joins the two histories with a merge commit.
6. **Cherry-pick — grab just one commit** — you want only the *Fix crash* commit
   from `dev`, not its WIP: `git cherry-pick` copies that single commit onto `main`.
7. **Many people, one project** — the finale: five people (Ana, Ben, Chen, Dara,
   Elias) each branch off `main`, work in parallel, then merge back — ending in a
   `v1.0` release. *One project, many contributors — that's collaboration on GitHub.*

## Rendering

```bash
./render.sh commit --quick     # fast sanity check of one scene
./render.sh                    # the whole film, 480p
./render.sh full -q m          # final 720p
./render.sh full -q h          # 1080p
./render.sh --stitch -q m      # render each scene and join into one film
```

`render.sh` reuses the HarnessEngineering / CNN / Fourier series' `.venv` if it
finds one (so Manim isn't reinstalled), otherwise it bootstraps a local `.venv`
from `requirements.txt`.

Individually renderable scenes: `intro` · `overview` · `commit` · `push` ·
`branch` · `merge` · `cherry` · `collab` · `outro` (or `full`, the default).

`GIT_QUICK=1` (or `--quick`) shortens the on-screen holds while iterating. Pacing
(`DELAY`) and the palette live at the top of `git_github.py`. The default `DELAY`
is tuned so the full film lands at about **2:50**.
