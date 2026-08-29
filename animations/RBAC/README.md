# Role-Based Access Control — a short explainer

A ~3-minute, no-voiceover Manim film on **RBAC**: how real systems answer the
question *"what is this user allowed to do?"* without drowning in per-user
permission grants. It's the **authorization** companion to the repo's
**authentication** pieces (`SSO/`, `JWTAuth/`) — *who you are* vs *what you can do*.

## What it teaches

The one idea: **don't grant permissions to people — grant them to roles, then
hand people a role.** That indirection turns an N×M tangle of direct grants into
a tidy N + M, and makes "who can do what" something you can actually manage.

1. **The tangle** — wire each person straight to each permission and the graph
   explodes; every hire, quit, or transfer means re-wiring it by hand — and the
   stale `delete` grant nobody remembered to revoke.
2. **The fix** — put a **Role** in the middle: `Users → Roles → Permissions`.
   Roles bundle the permissions for a job; you assign a role, not a pile of
   grants. Promote someone or off-board them by moving **one** edge.
3. **The check** — a request arrives (`Bob → DELETE /reports/Q3`). RBAC resolves
   the user's role → that role's permissions → *does the set include `delete`?*
   Bob (Editor) is **DENIED**; Alice (Admin) is **ALLOWED**. The check never
   looks at the person — only at what their roles grant.
4. **The rules** — role **hierarchy** (`Viewer ⊂ Editor ⊂ Admin`, senior roles
   inherit junior permissions), **least privilege** by default, and where
   **ABAC** picks up when you need context (time, location, ownership).

Everything is drawn with Manim `Text` (Pango), never `Tex` — no LaTeX toolchain.

## Scenes

| Scene    | Class          | Beat                                            |
|----------|----------------|-------------------------------------------------|
| `intro`  | `Intro`        | Title card                                      |
| `tangle` | `Tangle`       | Direct grants → N×M mess + the stale grant      |
| `roles`  | `Roles`        | The role hub; assign / promote / off-board      |
| `check`  | `Check`        | Access check in action: DENIED vs ALLOWED       |
| `recap`  | `Recap`        | Hierarchy, least privilege, ABAC → takeaway     |
| `outro`  | `Outro`        | Thanks card                                     |
| `full`   | `HowRBACWorks` | The whole film, intro card to outro card        |

## Rendering

```bash
./render.sh roles --quick -q l    # fast layout check of one scene (480p15)
./render.sh                       # whole film, 480p
./render.sh full -q h             # final 1080p60 (slow — run in background)
./render.sh --stitch -q m         # render each scene and ffmpeg-concat (720p)
```

`render.sh` reuses a sibling Manim venv (`HarnessEngineering`, `Fourier`, or
`CNN`) if one exists, otherwise bootstraps a local `.venv`. Output lands under
`media/videos/rbac/<res>/`.

Pacing knobs: `RBAC_QUICK=1` collapses every hold for a fast sanity render;
`RBAC_DELAY` and `RBAC_READ` tune the inter-step rhythm and per-caption reading
hold.

## Runtime

Measured full-film duration (1080p60, `HowRBACWorks`): **3:11** (191 s),
1920×1080 @ 60 fps. Edge-bleed scan clean across the whole film.
