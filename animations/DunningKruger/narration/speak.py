"""speak.py: say every line of the film with a local voice.

Kokoro (82M), run on this machine by mlx-audio: nothing is sent anywhere, and the
model must already be in the Hugging Face cache (the script runs offline). The
same voice as the other narrated films of this repository.

Each line of ``cues.json`` becomes one take, said in one go so that the sentences of
a line keep a common melody. Next to the sound, the model's own timing of every
word is kept: Kokoro decides how long each sound lasts before it draws the wave, so
these are the durations the wave was built from, not an estimate made afterwards.
(Said twice, a line gets the same timing to the millisecond; the wave itself differs
by the vocoder's noise, which nobody hears.)

    <python with mlx-audio> narration/speak.py     # -> media/narration/takes/, voice.json

Takes are cached by text, voice and speed: a changed line is the only one said again.
The sound itself is not kept in git (``media/`` is ignored); it is rebuilt from here.
What is kept is ``voice.json``, the rhythm of the voice: for every line, when each
word starts and how long the line takes. The film reads it and follows: its cues
land on the words as they are really said, and each beat lasts as long as its line
(``_Common.tell`` / ``until`` in ``dunning_kruger.py``; ``DK_VOICE=0`` ignores it).

After a change to the script: cue_times.py (the new lines), speak.py, cue_times.py
(the film, cut again), render, place.py, listen.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import wave
from pathlib import Path

for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
    os.environ.setdefault(key, "1")

import numpy as np  # noqa: E402
from common import LEAD_IN, MIN_PAUSE, QUIET, RATE, flow, load  # noqa: E402

HERE = Path(__file__).resolve().parent
MODEL = "mlx-community/Kokoro-82M-bf16"
VOICE = "af_heart"
SPEED = 0.9  # Kokoro's own pace is brisk; this film is a story


def spoken(text):
    """Text as it is handed to the voice (the script itself is never changed)."""
    return text


def words_of(text, tokens):
    """The model's tokens, regrouped as the words of ``text.split()``: for each, when
    its sound starts and ends, and the pause its punctuation takes afterwards."""
    out, cur = [], None
    for tok in tokens:
        if cur is None:
            cur = {"text": "", "start": None, "end": None, "pause": None}
        cur["text"] += tok["text"]
        if tok["start"] is not None:
            if any(c.isalnum() for c in tok["text"]):
                cur["start"] = tok["start"] if cur["start"] is None else cur["start"]
                cur["end"] = tok["end"]
            elif cur["end"] is not None:  # punctuation after the word: a pause
                first = cur["pause"][0] if cur["pause"] else tok["start"]
                cur["pause"] = [first, tok["end"]]
        if tok["space"]:
            out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    assert [w["text"] for w in out] == text.split(), (text, [w["text"] for w in out])
    assert all(w["start"] is not None for w in out), text
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--speed", type=float, default=SPEED)
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--out", type=Path, default=HERE.parent / "media" / "narration")
    args = ap.parse_args()

    cues = json.loads((HERE / "cues.json").read_text())
    texts = [ln["text"] for sc in cues["scenes"] for ln in sc["lines"]]
    takes = args.out / "takes"
    takes.mkdir(parents=True, exist_ok=True)

    pipeline, rows = None, []
    for n, text in enumerate(texts, 1):
        say = spoken(text)
        key = hashlib.sha256(json.dumps([say, MODEL, args.voice, args.speed]).encode()).hexdigest()[:12]
        path = takes / f"{n:02d}-{key}.wav"
        meta = path.with_suffix(".json")
        if not (path.exists() and meta.exists()):
            if pipeline is None:
                import mlx.core as mx
                from mlx_audio.tts.models.kokoro.pipeline import KokoroPipeline
                from mlx_audio.tts.utils import load_model

                assert mx.metal.is_available(), "Kokoro on mlx needs the GPU (Metal)"
                pipeline = KokoroPipeline(lang_code="a", model=load_model(MODEL), repo_id=MODEL)
            pieces, tokens, offset = [], [], 0.0
            for result in pipeline(say, voice=args.voice, speed=args.speed):
                pcm = np.asarray(result.audio, dtype=np.float32).reshape(-1)
                assert len(pcm) and np.isfinite(pcm).all() and np.abs(pcm).max() < 1, text
                for tok in result.tokens:
                    timed = tok.start_ts is not None and tok.end_ts is not None
                    tokens.append(
                        {
                            "text": tok.text,
                            "space": bool(tok.whitespace),
                            "start": offset + tok.start_ts if timed else None,
                            "end": offset + tok.end_ts if timed else None,
                            "phonemes": tok.phonemes,
                        }
                    )
                pieces.append(pcm)
                offset += len(pcm) / RATE
            pcm = np.concatenate(pieces)
            with wave.open(str(path), "wb") as f:
                f.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
                f.writeframes(np.round(pcm * 32767).astype("<i2").tobytes())
            loud = np.flatnonzero(np.abs(pcm) > QUIET)
            meta.write_text(
                json.dumps(
                    {
                        "text": text,
                        "voice": args.voice,
                        "speed": args.speed,
                        "duration": len(pcm) / RATE,
                        "speech": [float(loud[0] / RATE), float(loud[-1] / RATE)],
                        "words": words_of(text, tokens),
                        "phonemes": " ".join(t["phonemes"] or "" for t in tokens),
                    },
                    indent=1,
                )
                + "\n"
            )
        row = {"n": n, "wav": path.name, **json.loads(meta.read_text())}
        rows.append(row)
        said = row["speech"][1] - row["speech"][0]
        print(f"{n:02d}  {said:5.2f} s  {len(text.split()):2d} words  {len(text.split()) / said:4.2f} w/s  {text[:60]}", flush=True)
    (args.out / "takes.json").write_text(
        json.dumps({"model": MODEL, "voice": args.voice, "speed": args.speed, "rate": RATE, "takes": rows}, indent=1) + "\n"
    )
    total = sum(r["speech"][1] - r["speech"][0] for r in rows)
    n_words = sum(len(r["text"].split()) for r in rows)
    print(f"{len(rows)} lines, {n_words} words, {total:.1f} s of speech: {n_words / total * 60:.0f} words a minute")

    # the rhythm of the voice, for the film to follow
    lines = {}
    for r in rows:
        starts, length = flow(r, load(takes / r["wav"]))
        lines[r["text"]] = {"length": length, "words": starts}
    spoken_s = sum(v["length"] for v in lines.values())
    voice = {
        "model": MODEL,
        "voice": args.voice,
        "speed": args.speed,
        "lead_in": LEAD_IN,  # a line starts this long after its caption
        "min_pause": MIN_PAUSE,  # already counted in the times below
        "words_a_second": round(n_words / spoken_s, 2),
        "lines": lines,  # line -> seconds it takes, and when each word starts
    }
    if args.out == HERE.parent / "media" / "narration":
        (HERE / "voice.json").write_text(json.dumps(voice, indent=1) + "\n")
        print(f"voice.json: {spoken_s:.1f} s with a narrator's pauses, {voice['words_a_second']} words a second")


if __name__ == "__main__":
    main()
