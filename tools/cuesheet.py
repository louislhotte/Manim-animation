"""Does every cue of a narrated film land on its picture? One frame per cue, to look at.

A film built for narration starts a beat with ``voice(vo)`` / ``tell(caption, vo)``
and places its picture changes with ``cue("phrase")`` (or makes a motion end on a
word with ``span("phrase")``, or hands the phrase to a helper of its own). This tool
reads those lines and phrases from the film's source, in order; takes the start time of every line from the render's trace
(``MX_TRACE_DIR``); and pulls, for each phrase, the frame a moment *after* the
narrator reaches it. Each scene becomes one sheet: thumbnails in film order, the
phrase under each. Read the sheets: a picture that has not changed when its word
has been said, or that changed long before, shows at a glance.

Usage (clips and traces are found from the film's render.sh, like voiceover.py):

    MX_TRACE_DIR=/private/tmp/x-media/trace ./render.sh --stitch          # real pace, not --quick
    python tools/cuesheet.py animations/Protocols                         # every scene
    python tools/cuesheet.py animations/Protocols -q h Stream Sealed      # some, from the HD clips
    python tools/cuesheet.py animations/Protocols --trace DIR --after 1.2

Sheets go to ``<media>/cues/<Scene>.jpg``. Needs ffmpeg on PATH and Pillow (the
Manim venv has it). Works for films whose scene classes call one method that holds
the narration (``def construct(self): self.scene_x()``) or hold it themselves.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import subprocess
from pathlib import Path

from voiceover import RES, render_config

LINE_CALLS = ("voice", "over_card", "narrate")


def _strings(node):
    return [
        a.value
        for a in node.args
        if isinstance(a, ast.Constant) and isinstance(a.value, str)
    ]


def events(body):
    """(position, "line" | "phrase", text) of a method, in source order.

    Lines are what ``voice`` / ``tell`` / ``over_card`` are given (or a variable
    named ``vo``). Every other string of the method is a candidate phrase: it counts
    as a cue when it is part of the line being said (``cue("phrase")``,
    ``span("phrase")``, a film's own helper, or a tuple of phrases a loop walks).
    A phrase is several words, or a single word handed straight to a method of the
    scene (``self.cue("Refused")``, ``self.glide(clock, 338, "eighty")``): a bare
    word anywhere else is more likely a label or a flag than a cue.
    """
    lines, taken, direct = [], set(), set()
    for n in ast.walk(body):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and getattr(n.func.value, "id", "") == "self"
        ):
            direct.update(id(a) for a in n.args if isinstance(a, ast.Constant))
    for n in ast.walk(body):
        if (
            isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and getattr(n.targets[0], "id", None) == "vo"
        ):
            try:
                lines.append(
                    ((n.lineno, n.col_offset), "line", ast.literal_eval(n.value))
                )
                taken.update(id(c) for c in ast.walk(n.value))
            except ValueError:
                pass
        if not isinstance(n, ast.Call):
            continue
        name = getattr(n.func, "attr", "")
        if name in LINE_CALLS and _strings(n):
            lines.append(((n.lineno, n.col_offset), "line", _strings(n)[0]))
            taken.update(id(a) for a in n.args)
        elif name == "tell" and len(_strings(n)) > 1:  # tell("caption", "the line")
            lines.append(((n.lineno, n.col_offset), "line", _strings(n)[1]))
            taken.update(id(a) for a in n.args)
    phrases = [
        ((n.lineno, n.col_offset), "phrase", n.value)
        for n in ast.walk(body)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and id(n) not in taken
        and (
            (len(n.value) >= 6 and " " in n.value.strip())
            or (id(n) in direct and len(n.value.strip()) >= 5)
        )
    ]
    return sorted(lines + phrases)


def narration_method(tree, scene):
    """The function that holds a scene's narration: its ``construct``, or the one
    method ``construct`` calls on ``self``."""
    by_name = {
        n.name: n
        for n in ast.walk(tree)
        if isinstance(n, (ast.ClassDef, ast.FunctionDef))
    }
    klass = by_name.get(scene)
    if not isinstance(klass, ast.ClassDef):
        return None
    construct = next(
        (
            n
            for n in klass.body
            if isinstance(n, ast.FunctionDef) and n.name == "construct"
        ),
        None,
    )
    if construct is None:
        return None
    if any(kind == "line" for _, kind, _ in events(construct)):
        return construct
    for n in ast.walk(construct):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and getattr(n.func.value, "id", "") == "self"
        ):
            target = by_name.get(n.func.attr)
            if isinstance(target, ast.FunctionDef) and any(
                kind == "line" for _, kind, _ in events(target)
            ):
                return target
    return None


def shots(fn, trace, after):
    """(time in the clip, label) for every line start and every cue of the scene."""
    data = json.loads(trace.read_text())
    wps = data.get("wps", 2.5)
    starts = [
        c["t"] for part in data["parts"] for c in part["captions"] if c.get("note")
    ]
    out, k, line, seen = [], -1, None, set()
    for _, kind, text in events(fn):
        if kind == "line":
            k += 1
            if k >= len(starts):
                break
            line = text
            out.append(
                (starts[k] + 0.6, "LINE  " + " ".join(text.split()[:8]) + " ...")
            )
        elif (
            line and text in line and text != line and (k, text) not in seen
        ):  # "maybe" counts when it is in the line
            seen.add((k, text))
            out.append(
                (starts[k] + len(line[: line.index(text)].split()) / wps + after, text)
            )
    return out


def sheet(clip, items, out, cols=5, w=427, h=240):
    from PIL import Image, ImageDraw, ImageFont

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
    except OSError:
        font = ImageFont.load_default()
    rows = -(-len(items) // cols)
    img = Image.new("RGB", (cols * w, rows * (h + 26)), "white")
    draw = ImageDraw.Draw(img)
    for i, (t, label) in enumerate(items):
        grab = subprocess.run(  # one frame, straight from ffmpeg's stdout: no temporary file
            ["ffmpeg", "-loglevel", "error", "-ss", f"{max(0.0, t):.2f}", "-i", str(clip), "-frames:v", "1",
             "-vf", f"scale={w}:{h}", "-f", "image2pipe", "-vcodec", "png", "-"],
            capture_output=True,
        )  # fmt: skip
        x, y = (i % cols) * w, (i // cols) * (h + 26)
        if grab.returncode == 0 and grab.stdout:
            img.paste(Image.open(io.BytesIO(grab.stdout)), (x, y))
        draw.text(
            (x + 4, y + h + 5), f"{t:6.1f} s   {label[:56]}", fill="black", font=font
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=88)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("film", type=Path, help="the film folder (with its render.sh)")
    ap.add_argument(
        "scenes", nargs="*", help="scene classes (default: every scene of render.sh)"
    )
    ap.add_argument(
        "-q",
        default="l",
        choices=RES,
        help="quality of the rendered clips (default: l)",
    )
    ap.add_argument(
        "--trace", type=Path, help="trace directory (default: <media>/trace)"
    )
    ap.add_argument(
        "--after", type=float, default=0.9, help="seconds after the word (default 0.9)"
    )
    args = ap.parse_args()

    film = args.film.resolve()
    cfg = render_config(film)
    tree = ast.parse((film / cfg["file"]).read_text())
    clips = cfg["media"] / "videos" / Path(cfg["file"]).stem / RES[args.q]
    traces = args.trace or cfg["media"] / "trace"
    done = 0
    for entry in cfg["scenes"]:
        name = entry.split(":")[-1]
        if args.scenes and name not in args.scenes:
            continue
        fn, trace, clip = (
            narration_method(tree, name),
            traces / f"{name}.json",
            clips / f"{name}.mp4",
        )
        if fn is None or not trace.exists() or not clip.exists():
            continue
        items = shots(fn, trace, args.after)
        if len(items) < 2:
            continue
        out = cfg["media"] / "cues" / f"{name}.jpg"
        sheet(clip, items, out)
        print(f"{name}: {len(items)} frames -> {out}")
        done += 1
    if not done:
        print(
            "no sheet written: render with MX_TRACE_DIR first (real pace), and check the scene names"
        )
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
