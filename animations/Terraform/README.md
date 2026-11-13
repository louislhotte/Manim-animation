# Terraform

How a text file becomes real infrastructure. A house-style Manim film built on
`manimx`, **made to be narrated**: **5:58** (358.2 s, measured on the 1080p60
render, `Terraform_1080p60.mp4`), with flat scenes and scenes on a 3D stage.

It follows one small example from end to end (a VPC, a subnet, a security group,
two servers and a bucket, declared in `demo/main.tf`) and uses it to explain what
Terraform is for an engineer who has never used it: declaring resources, providers,
the dependency graph, `plan` and `apply`, the state, changes in place and
replacements, drift, remote state and locking, modules and environments.

## Scenes (`render.sh` name, class)

| # | name | class | what it shows |
|---|------|-------|---------------|
| 0 | `intro` | `Intro` | house title card |
| 1 | `apply` | `Apply` (3D) | the file, five folded blocks, beside an empty region; each block declares a ghost on the stage; `terraform apply` (and `yes`) fills them in dependency order |
| 2 | `blocks` | `Blocks` | one block opens: keyword, type, name, arguments (`count = 2` declares `web[0]` and `web[1]`), and the picture it declares; the script you no longer write; the provider turns blocks into API calls |
| 3 | `graph` | `Graph` | a reference (`aws_vpc.main.id`) and its arc; the blocks change places, the arcs follow; the file becomes a dependency graph; apply walks it in parallel, destroy walks it backwards |
| 4 | `plan` | `Plan` | one table, three windows: code, state, cloud. `init`, `plan` (six `+`), `apply` (the cloud fills, the ids are recorded), `apply` again: no changes |
| 5 | `change` | `Change` (3D) | edit the file: 2 becomes 3 (one `+`), a bigger instance type (three `~`, updated in place), a new image (three `-/+`, replaced) |
| 6 | `drift` | `Drift` (3D) | someone resizes a server in the console; it outgrows its blueprint; `plan` reads the real resources and finds it; `apply` puts it back |
| 7 | `team` | `Team` | the state moves from a laptop to a shared bucket (`backend.tf`); with `use_lockfile`, Ada and Bob apply at once: one holds the lock, the other is refused |
| 8 | `envs` | `Envs` (3D) | the file becomes a module with one input (`servers`); three calls build dev, staging and prod from the same code, each with its own state file |
| 9 | `outro` | `Outro` | house thank-you card |

The film is a stitch (`FILM=""` in `render.sh`): one class cannot be both a 2D and
a 3D scene.

**The picture.** On the 3D stage a *ghost* (a glass block in blueprint blue) is
what the file declares, and a *solid* is what really exists. `apply` fills ghosts
with solids; a manual change makes a solid outgrow its ghost; a plan is the
difference between the two. The five resources keep one colour each, as blocks of
code, graph nodes, table rows and objects on the stage.

## Narration

The film is paced for a voice: every beat lasts at least as long as its line takes
to say, and the picture changes when the narrator reaches the word it illustrates
(`cue("phrase")` in the code).

- **`VOICEOVER.md`** is the timed script (27 lines, 690 words): for each line its
  timecode, the room before the next line, its word count, and the caption on
  screen. Every line has at least a second more than it takes to say.
- **`voiceover.srt`** holds the same lines as subtitles: open it with the video to
  read along while recording.
- The pace is `TF_WPS` words per second (default 2.3, about 138 words a minute),
  with a breath of 1.1 s after each line. For a slower voice, re-render with
  `TF_WPS=2.0` and regenerate the script.

Captions are deliberately few (one short sentence per beat, on screen for the
whole beat). Nothing has to be read while it moves.

## What is real, and what is a model

**No Terraform binary and no cloud account were used.** Nothing was downloaded to
make this film, so nothing on screen is a recorded run. Instead `sim.py` computes
everything from the real configuration:

- it parses the `resource` blocks of `demo/main.tf` and the references between
  them, and derives the dependency graph from those references;
- it keeps the three things Terraform reconciles (configuration, state, a pretend
  cloud) and implements `plan` (refresh, diff, classify: create, update in place,
  replace, destroy) and `apply` (walk the graph, run what is ready in parallel,
  record ids in the state);
- it prints the results in the Terraform CLI's wording
  (`# aws_instance.web[2] will be created`, `Plan: 1 to add, 0 to change, 0 to
  destroy.`, `Apply complete! ...`, `No changes. Your infrastructure matches the
  configuration.`).

The scenes and `sim.py` assert what they state (six resources on the first apply,
nothing to do on the second, one to add when 2 becomes 3, three updates for the
instance type, three replacements for the image, one change after the drift, 1 / 2
/ 4 servers and three distinct state keys for dev / staging / prod).

What is illustrative, and labelled so on screen:

- resource ids are random (seeded), shaped like real AWS ids;
- durations are typical orders of magnitude, not measurements;
- terminal output is abridged: plan excerpts drop attribute padding and mark
  omitted lines with `…`, the apply log shows one `Creation complete` line per
  wave, the approval prompt is reduced to its last line, the state-lock error
  shows a subset of its fields, and long lines are wrapped to the narrow terminal;
- the example is deliberately minimal, to keep five blocks on screen: there is no
  internet gateway, no route table and no security-group rule, so the two servers
  would start but would not be reachable. It is a teaching file, not a template;
- `ami-0f3a91c2` (short, in the pre-2018 id format, so that the line fits the
  editor) and the bucket names are placeholders: to apply `demo/` for real, use an
  AMI id valid in your region and globally unique bucket names.

`python sim.py` prints the whole story.

## The example (`demo/`)

- `main.tf`: the five resources (the file shown in the film, parsed by `sim.py`).
- `providers.tf`, `backend.tf`: the AWS provider and the S3 backend with
  `use_lockfile` (scene 7).
- `modules/web/` and `envs/{dev,staging,prod}/`: the same five resources as a module
  with one input, `servers`, called three times (scene 8). The module's bucket uses
  `bucket_prefix`, so the three environments do not fight over one bucket name, and
  every environment has its own `backend.tf` with its own state key (`dev.tfstate`,
  `staging.tfstate`, `prod.tfstate`).

## Sources (where each fact is documented)

The CLI wording and behaviour were written from Terraform's documentation, without
running it. If a detail differs in your version, the CLI is the authority.

- Terraform documentation, <https://developer.hashicorp.com/terraform>: the
  `init`, `plan`, `apply` and `destroy` commands (including `-parallelism`, 10 by
  default), resource blocks and references, the dependency graph, state, the S3
  backend and `use_lockfile` (Terraform 1.10 and later), modules.
- Terraform Registry, <https://registry.terraform.io>: providers.
- AWS API action names (`CreateVpc`, `CreateSubnet`, `CreateSecurityGroup`,
  `RunInstances`, `CreateBucket`) and the AWS CLI commands of the hand-written
  script in scene 2: the Amazon EC2 and Amazon S3 API references.

## Colour

Four resources carry a hue of their own and sit side by side, so the hues were
checked with the `dataviz` skill's validator rather than picked by eye:
`#C170BB` (VPC), `#508FF9` (subnet), `#E26E1A` (security group), `#30A46E`
(bucket) pass every check on the film's surface for all pairs (worst pair dE 9.8
under colour-vision-deficiency simulation, 17.9 in normal vision). Servers are
neutral steel. Green, yellow and red are reserved for the plan's `+`, `~` and `-`;
the drift of scene 6 is drawn in red (the scene's own colour), never in the
yellow of an update.

## Render

```bash
./render.sh graph --quick --check     # one scene: layout pass, edge scan, contact sheet
./render.sh                           # whole film, 480p (stitched)
MX_TRACE_DIR=/private/tmp/terraform-media/trace ./render.sh --stitch -q h --no-cache
python ../../tools/voiceover.py . -q h --title Terraform    # VOICEOVER.md, voiceover.srt
python ../../tools/motioncheck.py /private/tmp/terraform-media/videos/terraform/480p15/*.mp4
```

Media goes to `/private/tmp/terraform-media` (override with `TF_MEDIA_DIR`); the
final film is copied here as `Terraform_1080p60.mp4` (git-ignored). Use
`--no-cache` after changing `kit.py` or `stage.py`: Manim's partial-movie cache does
not see changes inside updaters. `TF_QUICK=1` (or `--quick`) collapses the holds.

## Files

- `terraform.py`: storyboard, the eight scenes, the narration.
- `sim.py`: the model of Terraform (parser, graph, plan, apply, CLI wording) and
  the film's story with its assertions.
- `kit.py`: the 2D building blocks (`TextPanel`: an editor / terminal that folds,
  types, scrolls and draws dependency arcs; `ResCard`; icons).
- `stage.py`: the 3D stage (`StageCamera` with its own draw order, `Part`,
  `Diorama`, ghosts and solids).
- `demo/`: the Terraform example.
