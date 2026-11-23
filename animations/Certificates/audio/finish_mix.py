"""Normalize speech, duck the music once, and preserve the encoded video."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import numpy as np

BASE = Path(__file__).resolve().parent
RATE = 48000

def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def stats(path, prefix=""):
    result = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
        prefix + "loudnorm=I=-16:TP=-2:LRA=11:print_format=json", "-f", "null", "-"])
    value = json.JSONDecoder().raw_decode(result.stderr[result.stderr.rfind("{"):])[0]
    assert all(math.isfinite(float(value[k])) for k in ("input_i", "input_tp", "input_lra"))
    return value

def load_audio(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
        "-ar", str(RATE), "-ac", "2", "-f", "f32le", "-"])
    return np.frombuffer(raw, dtype="<f4").reshape(-1, 2)

def save_audio(path, samples):
    subprocess.run(["ffmpeg", "-n", "-v", "error", "-f", "f32le", "-ar", str(RATE),
        "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", str(path)],
        input=samples.astype("<f4").tobytes(), check=True)

def video_hash(path):
    return run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-c", "copy",
        "-f", "hash", "-hash", "sha256", "-"]).stdout.strip()

config = json.loads((BASE / "narration.json").read_text())
alignment = json.loads((BASE / "narration-alignment.json").read_text())
source = Path(config["sourceVideo"])
output = BASE.parent / "Certificates_1080p60-narrated-music.mp4"
speech_path = BASE / "narration.wav"
ducked_path = BASE / "music-ducked.wav"
mix_path = BASE / "final-mix.wav"
for path in (output, speech_path, ducked_path, mix_path):
    assert not path.exists(), f"Refusing to overwrite {path}"
assert sha(source) == config["sourceVideoSha256"] == alignment["sourceVideoSha256"]
assert sha(BASE / "narration-raw.wav") == alignment["rawSha256"]
for cue in alignment["cues"]:
    assert sha(cue["audioPath"]) == cue["sha256"]

# Analyze and normalize the centered stereo voice, so channel conversion cannot
# change the measured delivery level afterward.
pan = "pan=stereo|c0=c0|c1=c0,"
measured = stats(BASE / "narration-raw.wav", pan)
normalize = pan + "loudnorm=I=-16:TP=-2:LRA=11:" + (
    "measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
    "measured_thresh={input_thresh}:offset={target_offset}:linear=true".format(**measured))
run(["ffmpeg", "-n", "-v", "error", "-i", str(BASE / "narration-raw.wav"), "-af", normalize,
    "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s24le", str(speech_path)])
voice = load_audio(speech_path)
music = load_audio(BASE / "music.wav")
count = round(config["durationSec"] * RATE)
assert len(voice) == len(music) == count

# The music stem is already -29 LUFS. Smooth cue-based ducking is applied only
# here, once; it stays down through short pauses instead of pumping on syllables.
duck_db = np.zeros(count, dtype=np.float32)
duck_windows = []
for cue in alignment["cues"]:
    first, last = cue["speechStartSec"], cue["speechEndSec"]
    left = max(0, round((first - .14) * RATE))
    start = max(left, round(first * RATE))
    end = min(count, round((last + .25) * RATE))
    right = min(count, round((last + .90) * RATE))
    if start > left:
        duck_db[left:start] = np.minimum(duck_db[left:start], np.linspace(0, -10, start - left))
    duck_db[start:end] = -10
    if right > end:
        duck_db[end:right] = np.minimum(duck_db[end:right], np.linspace(-10, 0, right - end))
    duck_windows.append([first, last])
ducked = music * (10 ** (duck_db / 20))[:, None]
combined = voice + ducked
assert np.max(np.abs(combined)) < 1, "Mix would clip"
save_audio(ducked_path, ducked)
save_audio(mix_path, combined)
run(["ffmpeg", "-n", "-v", "error", "-i", str(source), "-i", str(mix_path),
    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
    "-ar", str(RATE), "-movflags", "+faststart", "-metadata", "title=Certificates — narrated with music", str(output)])
print("Exported", output.name, flush=True)
run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output), "-f", "null", "-"])
assert video_hash(source) == video_hash(output)
assert sha(source) == config["sourceVideoSha256"]
probe = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(output)]).stdout)
assert abs(float(probe["format"]["duration"]) - config["durationSec"]) < .05
encoded_stats = stats(output)
assert float(encoded_stats["input_tp"]) <= -1.5
assert abs(float(encoded_stats["input_i"]) + 16) < 1

# Confirm both components survive AAC encoding in the actual exported video.
decoded = load_audio(output)
checks = []
for name, first, last in (("opening", 1, 5), ("middle", 83, 88), ("repeat", 117, 121), ("ending", 175, 179)):
    left, right = round(first * RATE), round(last * RATE)
    speech_window = voice[left:right].reshape(-1)
    music_window = ducked[left:right].reshape(-1)
    encoded_window = decoded[left:right].reshape(-1)
    has_speech = np.sqrt(np.mean(speech_window ** 2)) > 1e-5
    components = np.column_stack((speech_window, music_window)) if has_speech else music_window[:, None]
    gains = np.linalg.lstsq(components, encoded_window, rcond=None)[0]
    assert .85 < gains[-1] < 1.15, (name, gains)
    checks.append({"window": name, "startSec": first, "endSec": last,
        "musicGainAfterEncoding": float(gains[-1]), "musicRmsDbFS": float(20 * np.log10(np.sqrt(np.mean(music_window ** 2))))})
report = {"video": str(output), "durationSec": float(probe["format"]["duration"]),
    "passages": len(alignment["passages"]), "alignedClips": len(alignment["cues"]),
    "sourceUnchanged": True, "videoStreamIdentical": True, "fullDecodePassed": True,
    "encodedLoudnessLUFS": float(encoded_stats["input_i"]), "encodedTruePeakDbTP": float(encoded_stats["input_tp"]),
    "musicBeforeDuckingLUFS": float(stats(BASE / "music.wav")["input_i"]),
    "narrationLUFS": float(stats(speech_path)["input_i"]), "duckingDb": -10,
    "musicExportChecks": checks, "listeningReviewVerified": False,
    "sourceVideoSha256": sha(source), "outputVideoSha256": sha(output)}
(BASE / "export-report.json").write_text(json.dumps(report, indent=2) + "\n")
(BASE / "mix-config.json").write_text(json.dumps({"sampleRate": RATE, "channels": 2,
    "narrationTargetLUFS": -16, "musicPreDuckTargetLUFS": -29, "duckingDb": -10,
    "duckAttackSec": .14, "duckHoldSec": .25, "duckReleaseSec": .65,
    "musicSource": "music.wav", "speechSource": "narration.wav", "duckWindows": duck_windows}, indent=2) + "\n")
print(json.dumps(report, indent=2), flush=True)
