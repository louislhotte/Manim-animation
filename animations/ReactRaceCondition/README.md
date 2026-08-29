# Race Conditions in React

A short, house-style explainer (~2.5 min, no voice-over) on the classic React
data-fetching **race condition** — why a component can end up showing the wrong
data — and the one-line fix.

Everything is on screen and every hold is timed so you can read it before it
moves on. Uses `Text` (Pango) rather than `Tex`, so it renders with no LaTeX
toolchain. The JSX is set in Menlo, syntax-coloured, and highlighted line-by-line
as it's explained. Nothing is a screenshot — the app card, the React-atom logo
and the sequence diagram are all Manim mobjects.

## The idea

A `Profile` component fetches a user inside `useEffect` on every `userId` change:

```jsx
useEffect(() => {
  fetchUser(userId).then(user => setUser(user));
}, [userId]);
```

Click **Alice**, then quickly click **Bob**. Two requests are in flight:

```
        click Alice ───GET /user/1───────────────▶  (slow ~900ms)
        click Bob   ────────GET /user/2──▶            (fast ~300ms)

        Bob   ◀──200────────  arrives FIRST → setUser(Bob)     ✓
        Alice ◀──200──────────────────  arrives LAST → setUser(Alice)  ✗
```

Responses come back **out of order**: Bob's is quick and lands first, then
Alice's slow response lands last and *overwrites* it. Selection says Bob; the
screen shows Alice. That's the race.

**The fix** — a cleanup flag. The effect's cleanup runs *before* the next effect
(when `userId` changes), so the stale response is dropped:

```jsx
useEffect(() => {
  let ignore = false;
  fetchUser(userId).then(user => {
    if (!ignore) setUser(user);   // stale response is dropped
  });
  return () => { ignore = true; };  // runs when userId changes
}, [userId]);
```

**Level up** — cancel the request itself with `AbortController`, so there's no
stale response to arrive at all:

```jsx
const c = new AbortController();
fetch(url, { signal: c.signal }).then(res => res.json()).then(setUser);
return () => c.abort();
```

The rule: **every effect that starts async work must clean it up.**

## The film (`RaceConditionsReact`)

Bookended by the channel's intro card (a spinning React-atom logo) and the
"Thanks for watching!" outro.

| # | Scene   | Class   | What it shows |
|---|---------|---------|---------------|
| — | Intro   | `Intro` | Title card + React-atom logo |
| 1 | Setup   | `Setup` | The `Profile` effect; one clean fetch resolves to Alice ✓ |
| 2 | Race    | `Race`  | Sequence diagram: Bob returns first, Alice returns last and wins ✗ |
| 3 | Fix     | `Fix`   | The `ignore` cleanup flag drops the stale response; UI stays Bob ✓ |
| 4 | Recap   | `Recap` | `AbortController` + the takeaway and the rule |
| — | Outro   | `Outro` | "Thanks for watching!" |

Colours are consistent throughout: React **cyan** for the framing, **purple**
for Alice (the slow request), **sky blue** for Bob (the fast one clicked last),
green for the good path and red for the bug.

## Render

```bash
./render.sh race --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                # the whole film, 480p
./render.sh full -q h           # final HD (1080p60) — slow
./render.sh --stitch -q m       # render each scene and stitch to one file
```

`render.sh` reuses an existing Manim venv (HarnessEngineering / Fourier / CNN) if
present, otherwise bootstraps a local `.venv`. Pacing knobs: `RACE_QUICK=1`
collapses every reading hold; `RACE_DELAY` overrides the reading-hold multiplier.
