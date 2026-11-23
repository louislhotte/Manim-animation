"""Normalize narration, duck the music, and copy the original MCP picture."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parent
RATE = 48000
VOICE_TARGET = -16.0
VOICE_PEAK = -2.0
DUCK_DB = -10.0
ATTACK = 0.100
RELEASE = 0.350
MERGE_GAP = 0.500


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def probe(path: Path) -> dict:
    return json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]).stdout)


def measure(path: Path, prefix: str = "") -> dict:
    filters = prefix + f"loudnorm=I={VOICE_TARGET}:TP={VOICE_PEAK}:LRA=11:print_format=json"
    result = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", filters, "-f", "null", "-"])
    return json.loads(re.findall(r"\{[^{}]*\}", result.stderr)[-1])


def decode(path: Path) -> np.ndarray:
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ac", "2", "-ar", str(RATE), "-f", "f32le", "-"])
    return np.frombuffer(raw, dtype="<f4").reshape(-1, 2)


def save(path: Path, samples: np.ndarray) -> None:
    subprocess.run(["ffmpeg", "-n", "-v", "error", "-f", "f32le", "-ar", str(RATE), "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", str(path)],
                   input=samples.astype("<f4", copy=False).tobytes(), check=True, capture_output=True)


def video_hash(path: Path) -> str:
    return run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-c", "copy", "-f", "hash", "-hash", "sha256", "-"]).stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def speech_intervals(cues: list[dict], duration: float) -> list[list[float]]:
    merged: list[list[float]] = []
    previous_end = 0.0
    for cue in cues:
        start, end = float(cue["startSec"]), float(cue["endSec"])
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration):
            raise ValueError(f"Invalid speech interval: {start}, {end}")
        if start < previous_end - 1 / RATE:
            raise ValueError("Speech intervals overlap or are unsorted")
        if merged and start - merged[-1][1] <= MERGE_GAP:
            merged[-1][1] = end
        else:
            merged.append([start, end])
        previous_end = end
    return merged


def duck_envelope(count: int, intervals: list[list[float]]) -> np.ndarray:
    gain = np.ones(count, dtype=np.float32)
    floor = 10 ** (DUCK_DB / 20)
    for start, end in intervals:
        speech_start, speech_end = round(start * RATE), round(end * RATE)
        attack_start = max(0, speech_start - round(ATTACK * RATE))
        release_end = min(count, speech_end + round(RELEASE * RATE))
        gain[speech_start:speech_end] = floor
        if speech_start > attack_start:
            phase = np.linspace(0, np.pi, speech_start - attack_start, endpoint=False, dtype=np.float32)
            curve = floor + (1 - floor) * (0.5 + 0.5 * np.cos(phase))
            gain[attack_start:speech_start] = np.minimum(gain[attack_start:speech_start], curve)
        if release_end > speech_end:
            phase = np.linspace(0, np.pi, release_end - speech_end, endpoint=False, dtype=np.float32)
            curve = floor + (1 - floor) * (0.5 - 0.5 * np.cos(phase))
            gain[speech_end:release_end] = np.minimum(gain[speech_end:release_end], curve)
    return gain


def db(value: float) -> float:
    return 20 * math.log10(max(value, 1e-12))


def main() -> None:
    source = ROOT.parent / "MCP_1080p60.mp4"
    raw_voice = ROOT / "aligned-raw.wav"
    alignment_path = ROOT / "narration-alignment.json"
    music_path = ROOT / "music/music-bed.wav"
    voice_path = ROOT.parent / "MCP_1080p60-narration.wav"
    ducked_path = ROOT / "ducked-music.wav"
    mixed_path = ROOT / "mixed.wav"
    output_path = ROOT.parent / "MCP_1080p60-voiced-with-music.mp4"
    report_path = ROOT / "audio-validation.json"
    for path in (voice_path, ducked_path, mixed_path, output_path, report_path):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    alignment = json.loads(alignment_path.read_text())
    duration = float(alignment["durationSec"])
    expected_samples = round(duration * RATE)
    source_probe = probe(source)
    if any(stream["codec_type"] == "audio" for stream in source_probe["streams"]):
        raise ValueError("Source already has audio; an explicit existing-audio mix is required")
    if abs(float(source_probe["format"]["duration"]) - duration) > 1 / RATE:
        raise ValueError("Source duration differs from the alignment")
    intervals = speech_intervals(alignment["cues"], duration)
    stereo_prefix = f"aresample={RATE},pan=stereo|c0=c0|c1=c0,"
    initial_voice = measure(raw_voice, stereo_prefix)
    norm = (f"loudnorm=I={VOICE_TARGET}:TP={VOICE_PEAK}:LRA=11:"
            f"measured_I={initial_voice['input_i']}:measured_TP={initial_voice['input_tp']}:"
            f"measured_LRA={initial_voice['input_lra']}:measured_thresh={initial_voice['input_thresh']}:"
            f"offset={initial_voice['target_offset']}:linear=true:print_format=json")
    print("Normalizing stereo narration", flush=True)
    normalize_result = run(["ffmpeg", "-n", "-hide_banner", "-nostats", "-i", str(raw_voice),
                           "-af", stereo_prefix + norm + f",aresample={RATE},apad=whole_len={expected_samples},atrim=end_sample={expected_samples}",
                           "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_s24le", str(voice_path)])
    normalization = json.loads(re.findall(r"\{[^{}]*\}", normalize_result.stderr)[-1])
    voice = decode(voice_path)
    music = decode(music_path)
    if len(voice) != expected_samples or len(music) != expected_samples:
        raise ValueError("A stem does not match the exact timeline length")
    if not np.isfinite(voice).all() or not np.isfinite(music).all():
        raise ValueError("A stem contains nonfinite samples")
    gain = duck_envelope(expected_samples, intervals)
    ducked = music * gain[:, None]
    save(ducked_path, ducked)
    mixed = voice + ducked
    if float(np.max(np.abs(mixed))) >= 1:
        raise ValueError("Unnormalized mix clips")
    save(mixed_path, mixed)
    print("Copying original video and encoding mixed audio", flush=True)
    run(["ffmpeg", "-n", "-v", "error", "-i", str(source), "-i", str(mixed_path),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", str(RATE),
         "-movflags", "+faststart", str(output_path)])
    print("Verifying full decode, picture equality, loudness, and music contribution", flush=True)
    run(["ffmpeg", "-v", "error", "-i", str(output_path), "-f", "null", "-"])
    source_hash, output_hash = video_hash(source), video_hash(output_path)
    if source_hash != output_hash:
        raise ValueError("Encoded picture changed")
    output_probe = probe(output_path)
    audio_stream = next(s for s in output_probe["streams"] if s["codec_type"] == "audio")
    if abs(float(audio_stream["duration"]) - duration) > 0.002:
        raise ValueError("Encoded audio duration differs from the video")
    final_measure = measure(output_path)
    if float(final_measure["input_tp"]) > -1.5:
        raise ValueError(f"Final true peak lacks target headroom: {final_measure['input_tp']} dBTP")
    voice_measure = measure(voice_path)
    music_measure = measure(ducked_path)
    # Compare independently decoded AAC to the known voice and music components.
    encoded = decode(output_path)
    if len(encoded) < expected_samples:
        raise ValueError("Decoded AAC does not span the whole timeline")
    windows = [("opening", 1.5, 6), ("middle", 140, 145), ("outro", 279, 283)]
    music_report = json.loads((ROOT / "music/music-report.json").read_text())
    for index, start in enumerate(music_report["arrangement"]["crossfadeStartsSec"], 1):
        windows.append((f"repeat_{index}", start - 0.5, start + music_report["arrangement"]["crossfadeDurationSec"] + 0.5))
    contribution = []
    for label, start, end in windows:
        bounds = slice(round(start * RATE), round(end * RATE))
        m = ducked[bounds].astype(np.float64).ravel()
        v = voice[bounds].astype(np.float64).ravel()
        y = encoded[bounds].astype(np.float64).ravel()
        predictors = np.column_stack((v, m))
        fitted_gain, *_ = np.linalg.lstsq(predictors, y, rcond=None)
        residual = y - predictors @ fitted_gain
        if not 0.90 < fitted_gain[1] < 1.10:
            raise ValueError(f"Encoded music contribution differs from intended mix at {label}: {fitted_gain[1]}")
        contribution.append({"window": label, "startSec": start, "endSec": end,
                             "musicRmsDbfs": db(float(np.sqrt(np.mean(m*m)))),
                             "meanMusicGainDb": db(float(np.sqrt(np.mean(gain[bounds]**2)))),
                             "encodedVoiceGain": float(fitted_gain[0]), "encodedMusicGain": float(fitted_gain[1]),
                             "aacResidualRmsDbfs": db(float(np.sqrt(np.mean(residual*residual))))})
    report = {"durationSec": duration, "sampleRate": RATE, "samples": expected_samples,
              "cueCount": len(alignment["cues"]), "mergedSpeechIntervalCount": len(intervals),
              "speechIntervals": intervals, "musicDuckingDb": DUCK_DB, "attackSec": ATTACK,
              "releaseSec": RELEASE, "mergeGapSec": MERGE_GAP,
              "voiceStereoInputMeasurement": initial_voice, "normalization": normalization,
              "voiceMeasurement": voice_measure, "duckedMusicMeasurement": music_measure,
              "finalEncodedMeasurement": final_measure, "musicContributionWindows": contribution,
              "mixSamplePeakDbfs": db(float(np.max(np.abs(mixed)))),
              "fullDecodePassed": True, "sourceVideoHash": source_hash, "outputVideoHash": output_hash,
              "sourceVideoUnchanged": True, "audioDurationSec": float(audio_stream["duration"]),
              "outputProbe": output_probe, "listeningReviewPerformed": False,
              "sourceSha256": sha256(source), "alignmentSha256": sha256(alignment_path),
              "rawVoiceSha256": sha256(raw_voice), "musicSha256": sha256(music_path),
              "outputVideo": str(output_path), "voiceWav": str(voice_path)}
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(output_path), "voiceLufs": voice_measure["input_i"],
                      "finalLufs": final_measure["input_i"], "truePeak": final_measure["input_tp"],
                      "videoUnchanged": True, "durationSec": float(audio_stream["duration"])}), flush=True)


if __name__ == "__main__":
    main()
