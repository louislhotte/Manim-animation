"""Place approved speech at visual anchors using only quiet punctuation pauses."""

import hashlib
import json
from pathlib import Path
import re
import wave

import numpy as np

ROOT = Path(__file__).resolve().parent
RATE = 24000


def isotonic(values, weights):
    blocks = []
    for i, (value, weight) in enumerate(zip(values, weights)):
        blocks.append([i, i + 1, value * weight, weight])
        while len(blocks) > 1 and blocks[-2][2] / blocks[-2][3] > blocks[-1][2] / blocks[-1][3]:
            right = blocks.pop()
            left = blocks.pop()
            blocks.append([left[0], right[1], left[2] + right[2], left[3] + right[3]])
    result = np.zeros(len(values))
    for start, end, total, weight in blocks:
        result[start:end] = total / weight
    return result


def stamp(time):
    value = round(time * 1000)
    return f"{value // 3600000:02}:{value // 60000 % 60:02}:{value // 1000 % 60:02},{value % 1000:03}"


def main():
    takes = json.loads((ROOT / "narration-takes.json").read_text())
    visuals = json.loads((ROOT / "visual-anchors.json").read_text())
    assert len(takes["cues"]) == len(visuals["cues"]) == 26
    duration = takes["durationSec"]
    timeline = np.zeros(round(duration * RATE), dtype=np.int16)
    rows, predictions, boundaries, passages = [], [], [], []
    previous_end = 0
    for take, visual in zip(takes["cues"], visuals["cues"]):
        assert take["text"] == visual["text"] and take["id"] == visual["id"]
        with wave.open(take["audioPath"], "rb") as source:
            assert source.getframerate() == RATE and source.getnchannels() == 1
            audio = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").copy()
        positions, cursor = [], 0
        for token in take["tokens"]:
            pos = take["text"].find(token["text"], cursor)
            if pos < 0:
                raise ValueError(f"Unmapped token {token['text']} in {take['id']}")
            positions.append((pos, token))
            cursor = pos + len(token["text"])
        # Only punctuation with a measured quiet interval can become an insertion point.
        cuts = [(0, 0)]
        floating = audio.astype(np.float64) / 32768
        window = round(0.016 * RATE)
        energy = np.concatenate(([0.0], np.cumsum(floating * floating)))
        for index, (pos, token) in enumerate(positions[:-1]):
            if token["text"] not in (".", "?", ",", ":", ";") or not visual["anchors"]:
                continue
            following = positions[index + 1][1]
            center = (token["startSec"] + following["startSec"]) / 2
            low = max(cuts[-1][0] + round(0.18 * RATE), round((center - 0.12) * RATE))
            high = min(len(audio) - round(0.18 * RATE), round((center + 0.12) * RATE))
            if high <= low + window:
                continue
            candidates = np.arange(low, high - window + 1)
            rms = np.sqrt((energy[candidates + window] - energy[candidates]) / window)
            best = int(np.argmin(rms))
            if rms[best] > 0.002:
                continue
            quiet_start = int(candidates[best])
            # Choose the quietest sample in the centre of the confirmed quiet interval.
            a = quiet_start + window // 4
            b = quiet_start + 3 * window // 4
            sample = a + int(np.argmin(np.abs(audio[a:b]).astype(np.int32)))
            cuts.append((sample, pos + len(token["text"])))
            boundaries.append({
                "passageId": take["id"], "sample": sample,
                "punctuation": token["text"], "rmsDbfs": float(20 * np.log10(max(rms[best], 1e-12))),
                "sampleValue": int(audio[sample]),
            })
        cuts.append((len(audio), len(take["text"])))
        desired, weights, segment_anchors = [], [], []
        for segment, ((start, char_start), (end, char_end)) in enumerate(zip(cuts, cuts[1:])):
            anchors = []
            seen = set()
            for anchor in visual["anchors"]:
                pos = take["text"].index(anchor["phrase"])
                if not char_start <= pos < char_end or pos in seen:
                    continue
                seen.add(pos)
                token = next(t for p, t in positions if p == pos)
                anchors.append((anchor, token))
            segment_anchors.append(anchors)
            if anchors:
                desired.append(float(np.mean([
                    anchor["targetSpokenSec"] - take["startSec"] - token["startSec"]
                    for anchor, token in anchors
                ])))
                weights.append(4 * len(anchors))
            else:
                desired.append(0.10 if segment == 0 else desired[-1])
                weights.append(0.25)
        budget = take["latestEndSec"] - take["startSec"] - len(audio) / RATE
        if budget < 0:
            raise ValueError(f"Speech exceeds visual window: {take['id']}")
        delays = np.clip(isotonic(desired, weights), 0.0, budget)
        restored = []
        paragraph_rows = []
        for segment, ((start, char_start), (end, char_end)) in enumerate(zip(cuts, cuts[1:])):
            placement = round((take["startSec"] + delays[segment]) * RATE) + start
            segment_audio = audio[start:end]
            stop = placement + len(segment_audio)
            assert placement >= previous_end and stop <= len(timeline)
            timeline[placement:stop] = segment_audio
            restored.append(timeline[placement:stop])
            previous_end = stop
            row = {
                "id": f"{take['id']}-{segment+1:02d}", "passageId": take["id"],
                "text": take["text"][char_start:char_end].strip(),
                "startSec": placement / RATE, "endSec": stop / RATE,
                "durationSec": len(segment_audio) / RATE,
                "sourceAudioPath": take["audioPath"],
                "sourceStartSample": start, "sourceEndSample": end,
                "insertedDelaySec": float(delays[segment]),
            }
            rows.append(row)
            paragraph_rows.append(row)
            for anchor, token in segment_anchors[segment]:
                predicted = take["startSec"] + delays[segment] + token["startSec"]
                predictions.append({
                    "passageId": take["id"], "phrase": anchor["phrase"],
                    "targetSec": anchor["targetSpokenSec"], "predictedSec": predicted,
                    "errorSec": predicted - anchor["targetSpokenSec"],
                })
        assert np.array_equal(np.concatenate(restored), audio), "Speech samples changed"
        assert re.sub(r"\s+", " ", " ".join(r["text"] for r in paragraph_rows)) == take["text"]
        passages.append({
            "id": take["id"], "text": take["text"],
            "startSec": paragraph_rows[0]["startSec"], "endSec": paragraph_rows[-1]["endSec"],
            "audioSha256": hashlib.sha256(audio.tobytes()).hexdigest(),
            "allSourceSamplesPreserved": True,
        })
    with wave.open(str(ROOT / "aligned-raw.wav"), "wb") as output:
        output.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        output.writeframes(timeline.astype("<i2").tobytes())
    report = {
        "durationSec": duration, "sampleRate": RATE, "cues": rows, "passages": passages,
        "phraseTimingMethod": "Kokoro predicted token times against animation design anchors; not forced alignment.",
        "phraseAnchors": predictions, "quietSplitBoundaries": boundaries,
        "maxPredictedPhraseErrorSec": max(abs(p["errorSec"]) for p in predictions),
        "allSourceSamplesPreserved": True,
        "outroMusicOnlyStartSec": 275.616666,
    }
    (ROOT / "narration-alignment.json").write_text(json.dumps(report, indent=2) + "\n")
    captions = "\n\n".join(
        f"{i+1}\n{stamp(row['startSec'])} --> {stamp(row['endSec'])}\n{row['text']}"
        for i, row in enumerate(passages)
    ) + "\n"
    (ROOT.parent / "MCP_1080p60-voiced-with-music.srt").write_text(captions)
    print(json.dumps({
        "passages": len(passages), "segments": len(rows), "quietCuts": len(boundaries),
        "maxPredictedPhraseErrorSec": report["maxPredictedPhraseErrorSec"],
        "overHalfSecond": [p for p in predictions if abs(p["errorSec"]) > 0.6],
    }, indent=2))


if __name__ == "__main__":
    main()
