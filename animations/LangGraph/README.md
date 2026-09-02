# LangGraph: Orchestrating a Team of Agents

A no-voiceover Manim explainer on multi-agent orchestration with LangGraph. It
builds the mental model from first principles (a graph you can reason about),
then shows the supervisor pattern coordinating a team of specialist agents, and
finishes with parallel fan-out. On-screen code is real, current LangGraph.

**Measured runtime: 2:49** (169 s, 480p15 at the real cadence).

## What it teaches

- **Why orchestrate.** One agent wired to every tool bloats its context and
  blurs its focus. Split the work, give each specialist one job, and add a
  coordinator.
- **The LangGraph identity.** A graph made of a shared **State** (a message
  list), **nodes** (units of work), **edges** (control flow), a **conditional
  edge** (a router that picks the next node), and **cycles** (the loop that makes
  it an agent, not a DAG).
- **The supervisor pattern.** A supervisor node routes a task to a Researcher,
  an Analyst, and a Writer, looping back until it routes to `END`. The shared
  State visibly accumulates messages as control flows through the graph. Real
  `Command(goto=..., update=...)` handoffs.
- **Parallelism.** `Send()` launches one worker per subtopic, all at the same
  time (map), then the results reduce back into one state and a Synthesize node
  merges them.
- **The takeaway.** Orchestration is just a graph: nodes are agents, a router
  decides the next step, shared state carries the work, loops let it iterate.
  Add specialists, not complexity.

The code panels use the real API: `StateGraph` / `MessagesState`,
`add_conditional_edges`, `Command`, `Send`, and
`ChatAnthropic(model="claude-opus-4-8")`.

## Scenes

| Scene       | Class          | What happens |
|-------------|----------------|--------------|
| Intro       | `Intro`        | House title card. |
| The problem | `Problem`      | One overloaded do-everything agent -> split the work, add a coordinator. |
| The graph   | `Graph`        | State / nodes / edges / conditional edge / cycle, built line-by-line from a `StateGraph` code panel. |
| The supervisor | `Team`      | Supervisor routes to Researcher / Analyst / Writer; the token travels the edges and the shared State grows each hop; loop until `END`. |
| In parallel | `Parallel`     | `Send()` fan-out to four concurrent workers, then reduce + Synthesize. |
| Takeaway    | `Takeaway`     | One-line recap card. |
| Outro       | `Outro`        | House thank-you card. |
| Full film   | `LangGraphFilm`| All of the above, end to end. |

## Rendering

`render.sh` reuses an existing Manim venv in the repo (the HarnessEngineering
series' `.venv`) if present, otherwise it bootstraps a local `.venv` from
`requirements.txt` (just `manim` + `numpy`, no LaTeX).

```bash
./render.sh team --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                # the whole film, 480p15 (real cadence)
./render.sh full -q h           # final 1080p60 render (slow)
./render.sh --stitch -q m       # render each scene and ffmpeg-concat to one file
```

Scenes: `full` (default) | `intro` | `problem` | `graph` | `team` | `parallel`
| `takeaway` | `outro`. Quality `-q l|m|h|k` = 480p15 / 720p30 / 1080p60 /
2160p60. `LG_QUICK=1` (or `--quick`) collapses the on-screen holds for fast
iteration; `LG_DELAY` / `LG_READ` override the pacing.

## Notes

- House style: dark palette, shadowed `Text` for crisp small type, Menlo code
  panels, the "Created by Ptolémé" intro/outro bookends.
- Every scene renders alone and the full film renders end to end; the bundled
  `edgecheck.py` is clean on every scene and on the stitched film.
