"""place.py: lay the voice under the pictures, and make the narrated film.

The film is already cut to the voice (``voice.json``), so most takes go down as
they were said. Two things still move, and only ever by letting a pause grow: a
take is cut where it is already silent (at its punctuation, never inside a phrase),
no syllable is stretched, squeezed or said again, and no pause shrinks.

  * A narrator's pauses. The voice's own full stop lasts 0.3 to 0.65 s and some
    have none; each is brought to ``MIN_PAUSE`` (the film was told so: the same
    floors are in ``voice.json``).
  * A late picture. A cue can land after its word is due, when the motion before it
    is not over (``cues.json`` has the real times). Then the words wait: how long
    each pause grows is a small least-squares problem per line, in which every cue
    wants its word a third of a second after its picture and every extra pause
    costs something, a comma more than a full stop (``PAUSE_COST``, ``GAP_COST``).

    ~/.cache/manimx/venv/bin/python narration/place.py

writes ``media/narration/narration.wav`` (the voice alone, as long as the film),
``media/DunningKruger_1080p60-narrated.mp4`` (the film's own video stream, copied,
with the voice at -16 LUFS), the subtitles of what is really said and when
(``DunningKruger_1080p60-narrated.srt``) and ``narration/placement.json``: every
piece, every pause that grew, and how far each word lands from its picture.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from common import LEAD_IN, cuts_of, floors, load, save
from scipy.optimize import nnls

HERE = Path(__file__).resolve().parent
FILM = HERE.parent
MEDIA = FILM / "media"
CLIPS = MEDIA / "videos" / "dunning_kruger" / "1080p60"
VIDEO = MEDIA / "DunningKruger_1080p60.mp4"
NAME = "DunningKruger_1080p60-narrated"

AFTER = 0.3  # a word is wanted this long after its picture starts (the film's own lead)
CARD_START = {"Intro": 1.8}  # over the title card: once the title is written
TAIL = 0.15  # a line is over this long before the next one starts
FADE = 0.006  # every piece fades in and out, so that no cut can click
PAUSE_COST = 0.05  # what a second of extra pause costs, against a second of drift
GAP_COST = {"start": 2.0, ".": 1.0, "!": 1.0, "?": 1.0, ":": 1.5, ";": 1.5, ",": 4.0}
CUE_WEIGHT = {"cue": 1.0, "span": 0.7}
OK = (-0.2, 0.9)  # word after picture, in seconds: inside this, the two read as one
SUB_CHARS = 84  # a subtitle holds about this many characters
LUFS, PEAK = -16.0, -2.0


def run(args, **kw):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True, text=True, **kw)


def seconds(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout)


def place_line(line, take, pcm, rate, start, limit):
    """Cut one take at its silences and decide when each piece is said.

    ``start``: when its first word may begin; ``limit``: when it must be over.
    Times are seconds from the start of the scene. Returns the pieces and the cues."""
    words = take["words"]
    cuts = cuts_of(words, pcm, rate)  # (time in the take, first word after it, mark, silence)
    first_word = [0] + [c[1] for c in cuts]
    edges = [max(0.0, words[0]["start"] - 0.06), *[c[0] for c in cuts]]
    # the end is where the sound has died away: the model's slot for a last word runs on
    edges.append(min(take["duration"], take["speech"][1] + 0.12))
    n = len(first_word)
    piece_of = lambda k: max(j for j in range(n) if first_word[j] <= k)  # noqa: E731

    natural = start - words[0]["start"]  # take time + natural = scene time, said in one go
    room = limit - (edges[-1] + natural)  # how much later the last piece may be said
    assert room > -1e-6, (line["text"], "does not fit even when said in one go", room)
    floor = np.array([0.0, *floors(cuts)])  # a narrator's pauses, as the film was told
    if floor.sum() > room:
        floor *= room / floor.sum()
    rows, rhs = [], []
    for a in line["anchors"]:
        row = np.zeros(n)
        row[: piece_of(a["word"]) + 1] = 1.0  # every pause before the word delays it
        w = math.sqrt(CUE_WEIGHT[a["kind"]])
        rows.append(row * w)
        rhs.append((a["t"] + AFTER - words[a["word"]]["start"] - natural - row @ floor) * w)
    costs = [GAP_COST["start"]] + [GAP_COST.get(c[2], 4.0) for c in cuts]
    for j, cost in enumerate(costs):
        row = np.zeros(n)
        row[j] = math.sqrt(PAUSE_COST * cost)
        rows.append(row)
        rhs.append(0.0)
    more = nnls(np.array(rows), np.array(rhs))[0]  # beyond the floor, for the pictures
    squeezed = floor.sum() + more.sum() > room + 1e-9
    if squeezed:
        more *= (room - floor.sum()) / more.sum()
    extra = floor + more
    shift = natural + np.cumsum(extra)

    pieces = []
    for j in range(n):
        a, b = edges[j], edges[j + 1]
        last = (first_word[j + 1] if j + 1 < n else len(words)) - 1
        pieces.append(
            {
                "text": " ".join(w["text"] for w in words[first_word[j] : last + 1]),
                "take": [round(a, 4), round(b, 4)],
                "start": round(a + shift[j], 4),
                "end": round(b + shift[j], 4),
                "extra_pause": round(float(extra[j]), 3),
                "silence_before": round(cuts[j - 1][3], 3) if j else 0.0,
            }
        )
    cues = []
    for a in line["anchors"]:
        said = words[a["word"]]["start"] + shift[piece_of(a["word"])]
        cues.append({"phrase": a["phrase"], "kind": a["kind"], "picture": a["t"], "word": round(float(said), 3),
                     "after_picture": round(float(said - a["t"]), 3)})  # fmt: skip
    when = [(w["start"] + shift[piece_of(k)], w["end"] + shift[piece_of(k)]) for k, w in enumerate(words)]
    return pieces, cues, when, squeezed


def subtitles(words, when, offset):
    """What is said, in readable portions: sentences, cut at a comma when long."""
    bits, cur = [], []
    for k, w in enumerate(words):
        cur.append(k)
        if w["text"][-1] in ".!?,:;":
            bits.append(cur)
            cur = []
    if cur:
        bits.append(cur)
    out, cur = [], []
    for bit in bits:
        text = " ".join(words[k]["text"] for k in cur + bit)
        if cur and (len(text) > SUB_CHARS or words[cur[-1]]["text"][-1] in ".!?"):
            out.append(cur)
            cur = []
        cur = cur + bit
    out.append(cur)
    return [
        {"start": offset + when[ks[0]][0], "end": offset + when[ks[-1]][1] + 0.3, "text": " ".join(words[k]["text"] for k in ks)}
        for ks in out
    ]


def srt_time(t):
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def loudness(path, prefix=""):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af",
               f"{prefix}loudnorm=I={LUFS}:TP={PEAK}:LRA=11:print_format=json", "-f", "null", "-"]).stderr  # fmt: skip
    return json.JSONDecoder().raw_decode(err[err.rfind("{") :])[0]


def stream_hash(path):
    return run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:v:0", "-c", "copy", "-f", "hash", "-hash", "sha256", "-"]).stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--takes", type=Path, default=MEDIA / "narration", help="where speak.py wrote")
    ap.add_argument("--no-video", action="store_true", help="place and report only")
    args = ap.parse_args()

    cues = json.loads((HERE / "cues.json").read_text())
    spoken = json.loads((args.takes / "takes.json").read_text())
    rate, takes = spoken["rate"], iter(spoken["takes"])

    film, offset = [], 0.0
    for sc in cues["scenes"]:
        clip = CLIPS / f"{sc['scene']}.mp4"
        if not args.no_video:  # the pictures in cues.json must be the pictures of the video
            assert abs(seconds(clip) - sc["length"]) < 0.02, (sc["scene"], "cues.json and the rendered clip disagree")
        for i, line in enumerate(sc["lines"]):
            take = next(takes)
            assert take["text"] == line["text"], "re-run speak.py: the script has changed"
            pcm = load(args.takes / "takes" / take["wav"], rate)
            start = line["t0"] + CARD_START.get(sc["scene"], LEAD_IN)
            limit = (sc["lines"][i + 1]["t0"] - TAIL) if i + 1 < len(sc["lines"]) else sc["length"] - 0.4
            pieces, where, when, squeezed = place_line(line, take, pcm, rate, start, limit)
            film.append({"scene": sc["scene"], "offset": offset, "t0": line["t0"], "limit": limit, "take": take,
                         "pcm": pcm, "pieces": pieces, "cues": where, "when": when, "squeezed": squeezed})  # fmt: skip
        offset += sc["length"]
    total = offset

    # ---- the report --------------------------------------------------------------- #
    drift, grown = [], []
    for n, ln in enumerate(film, 1):
        print(f"\n{n:02d} {ln['scene']:8s} said {ln['pieces'][0]['start'] - ln['t0']:+.2f} s after its caption, "
              f"over {ln['limit'] - ln['pieces'][-1]['end'] + TAIL:.2f} s before the next" + ("  SQUEEZED" if ln["squeezed"] else ""))  # fmt: skip
        for j, p in enumerate(ln["pieces"]):
            was, now = p["silence_before"], p["silence_before"] + p["extra_pause"]
            more = "" if p["extra_pause"] < 0.02 else f"  (pause {was:.2f} -> {now:.2f} s)" if j else f"  (starts {now:.2f} s later)"
            print(f"     {p['start']:6.2f}  {p['text']}{more}")
            if j and p["extra_pause"] > 0.02:
                grown.append(now)
        for c in ln["cues"]:
            drift.append(c["after_picture"])
            flag = "" if OK[0] <= c["after_picture"] <= OK[1] else "   <-- look"
            print(f"       {c['kind']:4s} {c['phrase']!r}: word {c['after_picture']:+.2f} s after its picture{flag}")
    drift = np.array(drift)
    print(f"\n{len(drift)} cues: the word comes {np.median(drift):.2f} s after its picture (median), "
          f"from {drift.min():+.2f} to {drift.max():+.2f} s; {int(((drift < OK[0]) | (drift > OK[1])).sum())} outside {OK[0]} to {OK[1]} s")  # fmt: skip
    print(f"{len(grown)} pauses grew; the longest pause is now {max(grown):.2f} s")

    # ---- the voice track ---------------------------------------------------------- #
    track = np.zeros(int(round(total * rate)), dtype=np.float32)
    ramp = np.linspace(0.0, 1.0, int(FADE * rate), dtype=np.float32)
    busy = 0
    for ln in film:
        for p in ln["pieces"]:
            a, b = (int(round(t * rate)) for t in p["take"])
            piece = ln["pcm"][a:b].copy()
            piece[: len(ramp)] *= ramp
            piece[-len(ramp) :] *= ramp[::-1]
            at = int(round((ln["offset"] + p["start"]) * rate))
            assert at >= busy and at + len(piece) <= len(track), ("pieces overlap", p)
            track[at : at + len(piece)] = piece
            busy = at + len(piece)
    voice = args.takes / "narration.wav"
    save(voice, track, rate)

    said = [{"text": w["text"], "start": round(ln["offset"] + a, 3), "end": round(ln["offset"] + b, 3)}
            for ln in film for w, (a, b) in zip(ln["take"]["words"], ln["when"], strict=True)]  # fmt: skip
    (args.takes / "words.json").write_text(json.dumps(said) + "\n")  # for listen.py

    subs = [s for ln in film for s in subtitles(ln["take"]["words"], ln["when"], ln["offset"])]
    for s, nxt in zip(subs, subs[1:] + [{"start": total}], strict=True):
        s["end"] = min(s["end"], nxt["start"] - 0.04)
    srt = "\n".join(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n" for i, s in enumerate(subs, 1))
    (FILM / f"{NAME}.srt").write_text(srt)

    report = {
        "voice": {k: spoken[k] for k in ("model", "voice", "speed")},
        "film_seconds": round(total, 3),
        "speech_seconds": round(sum(p["take"][1] - p["take"][0] for ln in film for p in ln["pieces"]), 1),
        "settings": {"lead_in": LEAD_IN, "card_start": CARD_START, "pause_cost": PAUSE_COST, "gap_cost": GAP_COST},
        "lines": [
            {"scene": ln["scene"], "text": ln["take"]["text"], "at": round(ln["offset"] + ln["pieces"][0]["start"], 3),
             "pieces": [{k: (round(ln["offset"] + p[k], 3) if k in ("start", "end") else p[k]) for k in ("start", "end", "text", "extra_pause")} for p in ln["pieces"]],
             "cues": [{**c, "picture": round(ln["offset"] + c["picture"], 3), "word": round(ln["offset"] + c["word"], 3)} for c in ln["cues"]]}
            for ln in film
        ],
    }  # fmt: skip

    # ---- the film with its voice ---------------------------------------------------- #
    if not args.no_video:
        assert abs(seconds(VIDEO) - total) < 0.05, "stitch the film again: its clips have changed"
        pan = "pan=stereo|c0=c0|c1=c0,"
        m = loudness(voice, pan)
        norm = (f"{pan}loudnorm=I={LUFS}:TP={PEAK}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")  # fmt: skip
        out = MEDIA / f"{NAME}.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-i", VIDEO, "-i", voice, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
             "-af", norm, "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
             "-metadata", "title=The Dunning-Kruger Effect (narrated)", out])  # fmt: skip
        run(["ffmpeg", "-v", "error", "-xerror", "-i", out, "-f", "null", "-"])  # it decodes to the end
        assert stream_hash(out) == stream_hash(VIDEO), "the video stream changed"
        heard = loudness(out)
        shutil.copyfile(FILM / f"{NAME}.srt", MEDIA / f"{NAME}.srt")  # players load it with the video
        report["video"] = {"file": f"media/{NAME}.mp4", "seconds": round(seconds(out), 3), "video_stream_unchanged": True,
                           "loudness_lufs": float(heard["input_i"]), "true_peak_db": float(heard["input_tp"])}  # fmt: skip
        print(f"\n{out.relative_to(FILM)}: {seconds(out):.1f} s, {heard['input_i']} LUFS, peak {heard['input_tp']} dBTP, video stream unchanged")
    (HERE / "placement.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"{len(subs)} subtitles -> {NAME}.srt; placement.json written")


if __name__ == "__main__":
    main()
