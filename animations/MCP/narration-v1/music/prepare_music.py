"""Arrange the local presentation track to the MCP film's exact duration."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = Path("/Users/lhottelouis/Library/CloudStorage/OneDrive-TheBostonConsultingGroup,Inc/Documents/Demo/Assets/paulyudin-presentation-music-164836.mp3")
VIDEO = ROOT.parents[1] / "MCP_1080p60.mp4"
RATE = 48000
TARGET_LUFS = -29.0
BPM = 107.0
BAR = 4 * 60 / BPM
REPEAT_START = 8 * BAR
SHIFT = 32 * BAR
SEGMENT_END = REPEAT_START + SHIFT + BAR


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def measure(path):
    result = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
                  "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    return json.loads(re.findall(r"\{[^{}]*\}", result.stderr)[-1])


def main():
    duration = float(json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(VIDEO)]).stdout)["format"]["duration"])
    samples = round(duration * RATE)
    final = ROOT / "music-bed.wav"
    if final.exists():
        raise SystemExit(f"Refusing to overwrite {final}")
    copied = ROOT / SOURCE.name
    if not copied.exists():
        shutil.copy2(SOURCE, copied)
    arranged = ROOT / "music-arranged.wav"
    filters = [f"[0:a]aresample={RATE},asplit=4[a][b][c][d]"]
    filters.append(f"[a]atrim=start=0:end={SEGMENT_END:.9f},asetpts=PTS-STARTPTS[s0]")
    for i, name in enumerate("bcd", 1):
        filters.append(f"[{name}]atrim=start={REPEAT_START:.9f}:end={SEGMENT_END:.9f},asetpts=PTS-STARTPTS[s{i}]")
    filters += [f"[s0][s1]acrossfade=d={BAR:.9f}:c1=tri:c2=tri[x1]",
                f"[x1][s2]acrossfade=d={BAR:.9f}:c1=tri:c2=tri[x2]",
                f"[x2][s3]acrossfade=d={BAR:.9f}:c1=tri:c2=tri[x3]",
                f"[x3]atrim=end_sample={samples},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.5,afade=t=out:st={duration-3.2:.9f}:d=3.2[out]"]
    run(["ffmpeg", "-n", "-v", "error", "-i", str(copied), "-filter_complex", ";".join(filters),
         "-map", "[out]", "-c:a", "pcm_f32le", "-ar", str(RATE), "-ac", "2", str(arranged)])
    raw_measurement = measure(arranged)
    gain = TARGET_LUFS - float(raw_measurement["input_i"])
    run(["ffmpeg", "-n", "-v", "error", "-i", str(arranged), "-af", f"volume={gain:.6f}dB",
         "-c:a", "pcm_s24le", "-ar", str(RATE), "-ac", "2", str(final)])
    final_measurement = measure(final)
    output_probe = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,sample_rate,channels,duration", "-of", "json", str(final)]).stdout)
    run(["ffmpeg", "-v", "error", "-i", str(final), "-f", "null", "-"])
    report = {
        "sourceFile": copied.name,
        "sourceSha256": hashlib.sha256(copied.read_bytes()).hexdigest(),
        "durationSec": duration, "sampleRate": RATE, "samples": samples,
        "tempoBpm": BPM,
        "tempoEvidence": "Bass-envelope correlation 0.927 for a 71.776 s shift, corresponding to 32 bars at 107 BPM",
        "arrangement": {"firstSegmentSec": [0, SEGMENT_END], "followingSegmentsSec": [[REPEAT_START, SEGMENT_END]] * 3,
                        "crossfadeDurationSec": BAR, "crossfadeCurve": "triangular", "phraseRepeatBars": 32,
                        "crossfadeStartsSec": [SEGMENT_END - BAR + i * SHIFT for i in range(3)],
                        "trimEndSec": duration, "fadeInSec": 1.5, "fadeOutSec": 3.2},
        "targetLufsBeforeSpeechDucking": TARGET_LUFS,
        "linearGainDb": gain,
        "arrangedMeasurement": raw_measurement,
        "finalMeasurement": final_measurement,
        "outputProbe": output_probe,
        "fullDecodePassed": True,
        "speechDuckingApplied": False,
        "listeningReviewPerformed": False,
        "filterComplex": ";".join(filters),
    }
    (ROOT / "music-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(final), "durationSec": duration, "gainDb": gain, "measurement": final_measurement}))


if __name__ == "__main__":
    main()
