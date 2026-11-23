"""Generate cached, approved narration without changing the film or its wording."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import wave

for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
    os.environ[key] = "1"

import numpy as np
import mlx.core as mx
from mlx_audio.tts.utils import load_model
from mlx_audio.tts.models.kokoro.pipeline import KokoroPipeline

BASE = Path(__file__).resolve().parent
RATE = 24000
config = json.loads((BASE / "narration.json").read_text())
assert config["approvalStatus"] == "approved-in-conversation"
assert hashlib.sha256(Path(config["sourceVideo"]).read_bytes()).hexdigest() == config["sourceVideoSha256"]
assert importlib.util.find_spec("en_core_web_sm")
assert mx.metal.is_available(), "Local speech generation requires Metal access."
model = load_model(config["model"])
pipeline = KokoroPipeline(lang_code=config["language"], model=model, repo_id=config["model"])
takes = BASE / "takes"
takes.mkdir(exist_ok=True)
rows = []
for cue in config["cues"]:
    settings = {k: config[k] for k in ("model", "voice", "language", "speed")}
    settings["text"] = cue["text"]
    key = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()[:16]
    path = takes / f'{cue["id"]}-{key}.wav'
    meta = path.with_suffix(".json")
    if not path.exists():
        pieces, tokens = [], []
        offset = 0.0
        for result in pipeline(cue["text"], voice=config["voice"], speed=config["speed"]):
            pcm = np.asarray(result.audio, dtype=np.float32).reshape(-1)
            assert np.isfinite(pcm).all() and np.max(np.abs(pcm)) < 1
            pieces.append(pcm)
            for token in result.tokens or []:
                tokens.append({"text": token.text, "phonemes": token.phonemes,
                    "startSec": None if token.start_ts is None else offset + token.start_ts,
                    "endSec": None if token.end_ts is None else offset + token.end_ts})
            offset += len(pcm) / RATE
        pcm = np.concatenate(pieces)
        with wave.open(str(path), "wb") as output:
            output.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
            output.writeframes(np.round(pcm * 32767).astype("<i2").tobytes())
        meta.write_text(json.dumps({"settings": settings, "tokens": tokens}, indent=2) + "\n")
        mx.clear_cache()
    with wave.open(str(path)) as source:
        assert source.getframerate() == RATE
        pcm = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    active = np.flatnonzero(np.abs(pcm.astype(np.int32)) > 32)
    row = {**cue, **json.loads(meta.read_text()), "audioPath": str(path),
        "durationSec": len(pcm) / RATE, "speechFirstSec": float(active[0] / RATE),
        "speechLastSec": float(active[-1] / RATE),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    rows.append(row)
    (BASE / "takes-measured.json").write_text(json.dumps({"durationSec": config["durationSec"], "cues": rows}, indent=2) + "\n")
    print(cue["id"], f'{row["durationSec"]:.3f}s / {cue["latestEndSec"] - cue["startSec"]:.3f}s', flush=True)
print("Completed", len(rows), "approved passages.", flush=True)
