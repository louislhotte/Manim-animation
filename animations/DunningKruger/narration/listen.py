"""listen.py: a second machine listens to the finished film.

Nothing here was heard by a person, so the finished film is played to a speech
recogniser (Whisper large-v3-turbo, local, through mlx-audio) that knows nothing of
the script, and three things are compared:

  * the words it hears against the words of the script (a slurred or swallowed word
    shows up here);
  * when it hears each word against when ``place.py`` meant it to be said (this
    checks the voice's own timing of its words, the cutting, and the final file);
  * when it hears the word of every cue against when the picture lands.

    <python with mlx-audio> narration/listen.py     # -> narration/heard.json

Whisper times a word to about a tenth of a second, with two known blind spots that
this script steps around. It starts the first word after a silence too early (it
gives the silence to the word): such a word is judged by its end. And the voice's
own clock gives the last word of a sentence a long slot in which the sound has
already died away: such a word is judged by its start.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import tempfile
import wave
from pathlib import Path

for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
    os.environ.setdefault(key, "1")

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
MEDIA = HERE.parent / "media"
VIDEO = MEDIA / "DunningKruger_1080p60-narrated.mp4"
MODEL = "mlx-community/whisper-large-v3-turbo-asr-fp16"
NUMBERS = {"22": "twenty two", "29": "twenty nine", "400": "four hundred"}


def plain(text):
    """Words as a recogniser may write them: no case, no punctuation, numbers spelled."""
    text = text.lower().replace("-", " ")
    text = re.sub(r"[^a-z0-9' ]", "", text)
    return [w for word in text.split() for w in NUMBERS.get(word, word).split()]


def main():
    from mlx_audio.stt.utils import load_model

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "film.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(VIDEO), "-map", "0:a:0", "-ac", "1", "-ar", "16000", str(wav)], check=True)
        with wave.open(str(wav)) as f:
            sound = np.abs(np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32)) / 32768
        out = load_model(MODEL).generate(str(wav), language="en", word_timestamps=True, condition_on_previous_text=False,
                                         temperature=0.0, verbose=False)  # fmt: skip
    heard = []  # (plain word, start, end)
    for seg in out.segments:
        for w in seg.get("words", []):
            for bit in plain(w["word"]):
                heard.append((bit, float(w["start"]), float(w["end"])))

    said = json.loads((MEDIA / "narration" / "words.json").read_text())
    script = []  # (plain word, start, end, index of the script word)
    for k, w in enumerate(said):
        for bit in plain(w["text"]):
            script.append((bit, w["start"], w["end"], k))

    match = difflib.SequenceMatcher(None, [w[0] for w in script], [w[0] for w in heard], autojunk=False)
    wrong, invented, late, at = [], [], [], {}
    for tag, i1, i2, j1, j2 in match.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2), strict=True):
                k = script[i][3]
                after_silence = k == 0 or said[k]["start"] - said[k - 1]["end"] > 0.2 or said[k - 1]["text"][-1] in ".!?:,"
                off = heard[j][2] - script[i][2] if after_silence else heard[j][1] - script[i][1]
                late.append(off)
                at.setdefault(k, script[i][1] + off)  # when the word is heard to start
        elif i1 == i2 and sound[int(heard[j1][1] * 16000) : int(heard[j2 - 1][2] * 16000) + 1].max(initial=0.0) < 1e-3:
            # words "heard" where the track is silent: a recogniser fills a long silence
            # with what films usually say there ("Thank you."). Kept apart, and shown.
            invented.append({"heard": " ".join(w[0] for w in heard[j1:j2]), "at": round(heard[j1][1], 2)})
        else:
            wrong.append({"script": " ".join(w[0] for w in script[i1:i2]), "heard": " ".join(w[0] for w in heard[j1:j2]),
                          "at": round(script[min(i1, len(script) - 1)][1], 2)})  # fmt: skip
    late = np.array(late)
    print(f"script: {len(script)} words; heard: {len(heard)}; {len(wrong)} places differ")
    for w in wrong:
        print(f"   at {w['at']:7.2f} s  script {w['script']!r}  heard {w['heard']!r}")
    for w in invented:
        print(f"   at {w['at']:7.2f} s  the recogniser wrote {w['heard']!r} where the track is silent")
    spread = np.abs(late - np.median(late))
    print(f"each word is heard {np.median(late):+.3f} s from where it was placed (median); half within "
          f"{np.percentile(spread, 50):.3f} s, 95 % within {np.percentile(spread, 95):.3f} s, all within {spread.max():.3f} s")  # fmt: skip

    placement = json.loads((HERE / "placement.json").read_text())
    starts = np.array([w["start"] for w in said])
    cues, off = [], []
    for ln in placement["lines"]:
        for c in ln["cues"]:
            k = int(np.argmin(np.abs(starts - c["word"])))  # the script word placed at that time
            if k in at:
                cues.append({"phrase": c["phrase"], "picture": c["picture"], "placed": c["word"], "heard": round(at[k], 3)})
                off.append(at[k] - c["picture"])
    off = np.array(off)
    print(f"{len(cues)} cue words heard: {np.median(off):+.2f} s after their picture (median), from {off.min():+.2f} to {off.max():+.2f} s")
    (HERE / "heard.json").write_text(
        json.dumps(
            {
                "recogniser": MODEL,
                "video": VIDEO.name,
                "script_words": len(script),
                "heard_words": len(heard),
                "differences": wrong,
                "written_over_silence": invented,
                "word_median_offset": round(float(np.median(late)), 3),
                "word_95pct_spread": round(float(np.percentile(spread, 95)), 3),
                "word_max_spread": round(float(spread.max()), 3),
                "cues": cues,
                "text": out.text.strip(),
            },
            indent=1,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
