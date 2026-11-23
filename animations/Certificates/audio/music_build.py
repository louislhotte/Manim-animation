#!/usr/bin/env python3
"""Arrange and linearly level the music bed without changing its source."""

from array import array
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def probe(path):
    return json.loads(run([
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(path),
    ]).stdout)


def loudness(path):
    result = run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-",
    ])
    data, _ = json.JSONDecoder().raw_decode(result.stderr[result.stderr.rfind("{"):])
    return {key: float(data[key]) for key in ("input_i", "input_tp", "input_lra")}


def window_stats(path, start, duration):
    result = subprocess.run([
        "ffmpeg", "-v", "error", "-ss", str(start), "-i", str(path),
        "-t", str(duration), "-f", "f32le", "-acodec", "pcm_f32le", "-",
    ], check=True, capture_output=True)
    samples = array("f")
    samples.frombytes(result.stdout)
    assert samples
    rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    peak = max(abs(value) for value in samples)
    assert rms > 0 and peak > 0
    return {
        "startSec": start,
        "durationSec": duration,
        "rmsDbFS": 20 * math.log10(rms),
        "peakDbFS": 20 * math.log10(peak),
    }


def main():
    config = json.loads((ROOT / "music_config.json").read_text())
    source = Path(config["source"])
    local_source = ROOT / "music-source.mp3"
    arranged = ROOT / "music-arranged.wav"
    final = ROOT / "music.wav"
    report_path = ROOT / "music-report.json"
    for destination in (local_source, arranged, final, report_path):
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite {destination}")
    source_hash = sha256(source)
    shutil.copyfile(source, local_source)
    assert sha256(local_source) == source_hash

    rate = config["sampleRate"]
    samples = round(config["durationSec"] * rate)
    duration = samples / rate
    first_start, first_end = config["firstSegment"]
    repeat_start, repeat_end = config["repeatSegment"]
    crossfade = config["crossfadeSec"]
    expected = (first_end - first_start) + (repeat_end - repeat_start) - crossfade
    assert abs(expected - duration) < 1 / rate
    fade_out_start = duration - config["fadeOutSec"]
    graph = (
        f"[0:a]aresample={rate},aformat=channel_layouts=stereo,asplit=2[a][b];"
        f"[a]atrim=start={first_start}:end={first_end},asetpts=PTS-STARTPTS[a1];"
        f"[b]atrim=start={repeat_start}:end={repeat_end},asetpts=PTS-STARTPTS[b1];"
        f"[a1][b1]acrossfade=d={crossfade}:c1=tri:c2=tri,"
        f"afade=t=in:st=0:d={config['fadeInSec']},"
        f"afade=t=out:st={fade_out_start}:d={config['fadeOutSec']},"
        f"atrim=end_sample={samples},asetpts=PTS-STARTPTS[out]"
    )
    run([
        "ffmpeg", "-n", "-v", "error", "-i", str(local_source),
        "-filter_complex", graph, "-map", "[out]", "-ar", str(rate),
        "-ac", "2", "-c:a", "pcm_f32le", str(arranged),
    ])
    before = loudness(arranged)
    gain_db = config["integratedLoudnessLUFS"] - before["input_i"]
    run([
        "ffmpeg", "-n", "-v", "error", "-i", str(arranged),
        "-af", f"volume={gain_db:.8f}dB", "-ar", str(rate),
        "-ac", "2", "-c:a", "pcm_s24le", str(final),
    ])
    final_probe = probe(final)
    stream = final_probe["streams"][0]
    actual_duration = float(final_probe["format"]["duration"])
    assert abs(actual_duration - duration) <= 1 / rate
    assert stream["codec_name"] == "pcm_s24le"
    assert int(stream["sample_rate"]) == rate and stream["channels"] == 2
    after = loudness(final)
    assert abs(after["input_i"] - config["integratedLoudnessLUFS"]) < 0.2
    assert after["input_tp"] < -1.5
    run(["ffmpeg", "-v", "error", "-xerror", "-i", str(final), "-f", "null", "-"])
    windows = {
        "opening": window_stats(final, 0, 3),
        "middle": window_stats(final, duration / 2 - 2, 4),
        "repeat": window_stats(final, first_end - crossfade - 1, crossfade + 2),
        "ending": window_stats(final, duration - config["fadeOutSec"], config["fadeOutSec"]),
    }
    assert all(window["rmsDbFS"] > -80 for window in windows.values())
    assert sha256(source) == source_hash
    report = {
        "musicFile": str(final),
        "sourceCopy": str(local_source),
        "durationSec": actual_duration,
        "sampleRate": rate,
        "channels": 2,
        "codec": stream["codec_name"],
        "arrangedLoudness": before,
        "linearGainDb": gain_db,
        "musicLoudness": after,
        "speechDuckingApplied": False,
        "signalChecks": windows,
        "fullDecodePassed": True,
        "sourceUnchanged": True,
        "sourceSha256": source_hash,
        "musicSha256": sha256(final),
        "listeningReviewVerified": False,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
