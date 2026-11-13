"""Turn a narrated film's caption trace into a timed voice-over script.

A film built for narration starts every beat with ``cap(caption, need=..., note=vo)``
(see ``manimx.scene``; the Terraform film wraps it as ``tell(caption, vo)``): ``note``
is the line to say, ``need`` the time it takes to say it. Rendering with
``MX_TRACE_DIR=<dir>`` saves, per scene, when each line started and how long the
picture gives it. This tool adds the scenes' offsets in the stitched film and writes:

  * ``VOICEOVER.md``   the script: timecode, room, words, caption, narration;
  * ``voiceover.srt``  the same lines as subtitles (a teleprompter while recording,
                       or captions for the finished video).

Usage (from anywhere; clips and traces are found from the film's render.sh):

    MX_TRACE_DIR=/private/tmp/x-media/trace ./render.sh --stitch -q h
    python tools/voiceover.py animations/Terraform -q h

Lines whose narration does not fit before the next one starts are flagged
``TIGHT``: shorten the line or give the beat more to do. Needs ffprobe on PATH.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

RES = {"l": "480p15", "m": "720p30", "h": "1080p60", "k": "2160p60"}


def render_config(film_dir: Path) -> dict:
    """FILE, SCENES and the media directory declared in the film's render.sh."""
    text = (film_dir / "render.sh").read_text()

    def var(name, default=""):
        m = re.search(rf"^{name}=(.*)$", text, re.M)
        return m.group(1).split("#")[0].strip().strip("\"'") if m else default

    scenes = re.search(r"^SCENES=\(([^)]*)\)", text, re.M)
    media = os.environ.get("MX_MEDIA_DIR") or os.environ.get(var("MEDIA_ENV") or "-")
    return {
        "file": var("FILE"),
        "scenes": scenes.group(1).split() if scenes else [],
        "media": Path(media or var("MEDIA_DEFAULT") or film_dir / "media"),
    }


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0",
         str(path)],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    return float(out.stdout.strip())


def clock(t: float, tenths: bool = True) -> str:
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m)}:{s:04.1f}" if tenths else f"{int(m)}:{int(s):02d}"


def srt_time(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def collect(
    cfg: dict, quality: str, trace_dir: Path | None
) -> tuple[list[dict], float]:
    """Every narrated line of the film with its absolute start time."""
    clips = cfg["media"] / "videos" / Path(cfg["file"]).stem / RES[quality]
    trace_dir = trace_dir or cfg["media"] / "trace"
    lines, offset = [], 0.0
    for entry in cfg["scenes"]:
        name = entry.split(":")[-1]
        clip = clips / f"{name}.mp4"
        if not clip.exists():
            raise SystemExit(
                f"missing clip {clip}: render the film first (--stitch -q {quality})"
            )
        length = duration(clip)
        trace = trace_dir / f"{name}.json"
        rows = []
        if trace.exists():
            data = json.loads(trace.read_text())
            cfg["wps"] = data.get("wps", cfg.get("wps"))
            for part in data["parts"]:
                rows += part["captions"]
        for i, row in enumerate(rows):
            nxt = rows[i + 1]["t"] if i + 1 < len(rows) else length
            lines.append(
                {
                    "scene": name,
                    "start": offset + row["t"],
                    "room": nxt - row["t"],
                    "caption": row["text"],
                    "say": (row.get("note") or "").strip(),
                    "first": i == 0,
                    "scene_start": offset,
                    "scene_end": offset + length,
                }
            )
        if not rows:
            lines.append({"scene": name, "start": offset, "room": length, "caption": "",
                          "say": "", "first": True, "scene_start": offset,
                          "scene_end": offset + length})  # fmt: skip
        offset += length
    return lines, offset


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("film", type=Path, help="the film folder (with its render.sh)")
    ap.add_argument(
        "-q", default="h", choices=RES, help="quality of the rendered clips"
    )
    ap.add_argument(
        "--trace", type=Path, help="trace directory (default: <media>/trace)"
    )
    ap.add_argument(
        "--wps",
        type=float,
        help="speaking rate, words per second (default: the film's)",
    )
    ap.add_argument("--title", help="title of the script (default: the folder name)")
    args = ap.parse_args()

    film = args.film.resolve()
    cfg = render_config(film)
    lines, total = collect(cfg, args.q, args.trace)
    args.wps = args.wps or cfg.get("wps") or 2.5
    title = args.title or film.name
    spoken = [ln for ln in lines if ln["say"]]
    words = sum(len(ln["say"].split()) for ln in spoken)

    md = [
        f"# Voice-over script: {title}",
        "",
        f"Film length **{clock(total, False)}** ({total:.1f} s), {len(spoken)} lines, "
        f"{words} words. Timecodes are from the {RES[args.q]} render; every line starts "
        "when its caption appears.",
        "",
        f"*Room* is the time until the next line starts. The pacing assumes "
        f"{args.wps * 60:.0f} words a minute, so a line of *n* words wants about "
        f"n / {args.wps:g} seconds. A line marked **TIGHT** has less than that.",
        "",
        "`voiceover.srt` holds the same lines as subtitles: load it next to the video "
        "to read along while recording.",
    ]
    srt, tight, scene = [], 0, None
    for ln in lines:
        if ln["scene"] != scene:
            scene = ln["scene"]
            md += [
                "",
                f"## {scene}  ({clock(ln['scene_start'], False)} to "
                f"{clock(ln['scene_end'], False)})",
            ]
        if not ln["say"]:
            md += ["", f"**{clock(ln['start'])}**  no narration ({ln['room']:.1f} s)."]
            continue
        n = len(ln["say"].split())
        want = n / args.wps
        flag = ""
        if want > ln["room"] - 0.1:
            flag, tight = "  **TIGHT**", tight + 1
        md += [
            "",
            f"**{clock(ln['start'])}**  room {ln['room']:.1f} s, {n} words "
            f"(about {want:.1f} s){flag}",
        ]
        if ln["caption"]:
            md.append(f"*On screen: {ln['caption']}*")
        md += ["", f"> {ln['say']}"]
        end = min(ln["start"] + want + 0.6, ln["start"] + ln["room"] - 0.05)
        srt.append(
            f"{len(srt) + 1}\n{srt_time(ln['start'])} --> {srt_time(end)}\n{ln['say']}\n"
        )
    (film / "VOICEOVER.md").write_text("\n".join(md) + "\n")
    (film / "voiceover.srt").write_text("\n".join(srt))
    print(f"{film.name}: {clock(total, False)}, {len(spoken)} lines, {words} words, "
          f"{tight} tight -> VOICEOVER.md, voiceover.srt")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
