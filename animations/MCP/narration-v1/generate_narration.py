"""Synthesize the approved MCP narration locally, preserving the source movie."""

import hashlib
import json
import os
from pathlib import Path
import re
import wave

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import numpy as np
from mlx_audio.tts.models.kokoro.pipeline import KokoroPipeline
from mlx_audio.tts.utils import load_model

ROOT = Path(__file__).resolve().parent
MODEL = "mlx-community/Kokoro-82M-bf16"
VOICE = "af_heart"
SPEED = 0.95
RATE = 24000


def time_sec(value):
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return 3600 * int(hours) + 60 * int(minutes) + float(seconds)


def pronunciation(text):
    replacements = {
        "MCP": "[MCP](/ˌɛm sˌiː pˈiː/)",
        "AI": "[AI](/ˌeɪ ˈaɪ/)",
        "JSON": "[JSON](/dʒˈeɪsən/)",
        "HTTP": "[HTTP](/ˌeɪtʃ tˌiː tˌiː pˈiː/)",
        "id": "[id](/ˌaɪ dˈiː/)",
    }
    for word, spoken in replacements.items():
        text = re.sub(r"\b" + re.escape(word) + r"\b", lambda _: spoken, text)
    return text


def main():
    blocks = (ROOT.parent / "voiceover.srt").read_text().strip().split("\n\n")
    cues = []
    for block in blocks:
        lines = block.splitlines()
        start, end = lines[1].split(" --> ")
        cues.append({
            "id": f"{int(lines[0]):02d}",
            "startSec": time_sec(start),
            "captionEndSec": time_sec(end),
            "text": " ".join(lines[2:]),
        })
    for index, cue in enumerate(cues):
        cue["latestEndSec"] = cues[index + 1]["startSec"] - 0.06 if index + 1 < len(cues) else 275.55
    plan = {
        "title": "MCP narrated explainer",
        "sourceVideo": str(ROOT.parent / "MCP_1080p60.mp4"),
        "durationSec": 287.283333,
        "model": MODEL,
        "voice": VOICE,
        "language": "a",
        "speed": SPEED,
        "cues": cues,
    }
    (ROOT / "narration-plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    (ROOT / "takes").mkdir(exist_ok=True)
    pipeline = None
    rows = []
    for cue in cues:
        text = pronunciation(cue["text"])
        key = hashlib.sha256(json.dumps([text, MODEL, VOICE, SPEED]).encode()).hexdigest()[:16]
        path = ROOT / "takes" / f"{cue['id']}-{key}.wav"
        metadata_path = path.with_suffix(".json")
        if not path.exists() or not metadata_path.exists():
            if pipeline is None:
                model = load_model(MODEL)
                pipeline = KokoroPipeline(lang_code="a", model=model, repo_id=MODEL)
            pieces, tokens, offset = [], [], 0.0
            for result in pipeline(text, voice=VOICE, speed=SPEED):
                audio = np.asarray(result.audio, dtype=np.float32).reshape(-1)
                if not len(audio) or not np.isfinite(audio).all() or np.abs(audio).max() >= 1:
                    raise ValueError(f"Invalid synthesized audio for cue {cue['id']}")
                for token in result.tokens:
                    if token.start_ts is not None and token.end_ts is not None:
                        tokens.append({
                            "text": token.text,
                            "startSec": offset + token.start_ts,
                            "endSec": offset + token.end_ts,
                            "phonemes": token.phonemes,
                        })
                pieces.append(audio)
                offset += len(audio) / RATE
            audio = np.concatenate(pieces)
            # Remove only leading/trailing dead air; retain natural pauses and all speech.
            active = np.flatnonzero(np.abs(audio) > 0.0008)
            if not len(active):
                raise ValueError(f"Silent synthesis for cue {cue['id']}")
            first = max(0, int(active[0]) - 1440)
            last = min(len(audio), int(active[-1]) + 2400)
            audio = audio[first:last]
            for token in tokens:
                token["startSec"] -= first / RATE
                token["endSec"] -= first / RATE
            with wave.open(str(path), "wb") as output:
                output.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
                output.writeframes(np.round(audio * 32767).astype("<i2").tobytes())
            metadata = {
                "text": cue["text"],
                "synthesisText": text,
                "durationSec": len(audio) / RATE,
                "tokens": tokens,
            }
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
        metadata = json.loads(metadata_path.read_text())
        row = {**cue, **metadata, "audioPath": str(path)}
        row["endSec"] = row["startSec"] + row["durationSec"]
        row["remainingSec"] = row["latestEndSec"] - row["endSec"]
        rows.append(row)
        (ROOT / "narration-takes.json").write_text(json.dumps({**plan, "cues": rows}, indent=2) + "\n")
        print(f"Cue {cue['id']}: {row['durationSec']:.2f}s, remaining {row['remainingSec']:+.2f}s", flush=True)
    print(f"Generated {len(rows)} passages", flush=True)


if __name__ == "__main__":
    main()
