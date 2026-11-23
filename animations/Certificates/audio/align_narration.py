"""Place unchanged speech at visual anchors, splitting only at quiet punctuation."""
import hashlib
import json
from pathlib import Path
import re
import wave
import numpy as np

BASE = Path(__file__).resolve().parent
RATE = 24000

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, audio):
    with wave.open(str(path), "wb") as target:
        target.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        target.writeframes(audio.astype("<i2").tobytes())

def norm(text):
    return re.sub(r"[^a-z0-9\s']", "", text.lower())

def monotonic(values, weights):
    blocks = []
    for i, (value, weight) in enumerate(zip(values, weights)):
        blocks.append([i, i, value * weight, weight])
        while len(blocks) > 1 and blocks[-2][2] / blocks[-2][3] > blocks[-1][2] / blocks[-1][3]:
            right, left = blocks.pop(), blocks.pop()
            blocks.append([left[0], right[1], left[2] + right[2], left[3] + right[3]])
    result = np.empty(len(values))
    for first, last, total, weight in blocks:
        result[first:last + 1] = total / weight
    return result

config = json.loads((BASE / "narration.json").read_text())
measured = json.loads((BASE / "takes-measured.json").read_text())
visuals = json.loads((BASE / "visual-anchors.json").read_text())
by_id = {row["id"]: row for row in visuals["cues"]}
assert len(measured["cues"]) == len(config["cues"])
clips = BASE / "aligned-clips"
clips.mkdir(exist_ok=True)
entries, audit, passages = [], [], []
for cue in measured["cues"]:
    assert sha(cue["audioPath"]) == cue["sha256"]
    with wave.open(cue["audioPath"]) as source:
        audio = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").copy()
    active = np.flatnonzero(np.abs(audio.astype(np.int32)) > 18)
    low = max(0, int(active[0]) - 2400)
    high = min(len(audio), int(active[-1]) + 2401)
    tokens = cue["tokens"]
    joined, positions = "", []
    for index, token in enumerate(tokens):
        word = norm(token["text"]).strip()
        if word:
            positions.append((len(joined), index))
            joined += word + " "
    anchors = []
    for anchor in by_id[cue["id"]]["anchors"]:
        phrase = norm(anchor["phrase"])
        at = joined.find(phrase)
        assert at >= 0, (cue["id"], phrase, joined)
        token_index = max(i for position, i in positions if position <= at)
        token = tokens[token_index]
        assert token["startSec"] is not None
        target = anchor.get("recommendedSpokenSec", max(anchor["spokenTargetSec"], anchor["visualStartSec"] + 0.1))
        anchors.append({**anchor, "sourceSec": token["startSec"], "targetSec": target})
    cuts = [low]
    for token in tokens[:-1]:
        if token["text"] not in (".", ",", ":", ";", "!", "?") or token["startSec"] is None:
            continue
        left = max(low + 1200, int((token["startSec"] - .08) * RATE))
        right = min(high - 1200, int((token["endSec"] + .18) * RATE))
        if right - left < 480:
            continue
        loud = (np.abs(audio[left:right].astype(np.int32)) > 60).astype(np.int64)
        counts = np.concatenate(([0], np.cumsum(loud)))
        quiet = np.flatnonzero((counts[480:] - counts[:-480]) == 0)
        if not len(quiet):
            continue
        centers = quiet + left + 240
        desired = round((token["startSec"] + token["endSec"]) / 2 * RATE)
        cut = int(centers[np.argmin(np.abs(centers - desired))])
        if cut - cuts[-1] >= .25 * RATE:
            cuts.append(cut)
    cuts.append(high)
    sections = [{"left": left, "right": right,
        "anchors": [a for a in anchors if left / RATE <= a["sourceSec"] < right / RATE]}
        for left, right in zip(cuts, cuts[1:])]
    known = [(i, float(np.mean([a["targetSec"] - a["sourceSec"] for a in section["anchors"]])))
        for i, section in enumerate(sections) if section["anchors"]]
    values, weights = [], []
    for i, section in enumerate(sections):
        value = float(np.interp(i, [x[0] for x in known], [x[1] for x in known])) if known else cue["startSec"] + .15
        values.append(value)
        weights.append(max(1, len(section["anchors"])))
    minimum = cue["startSec"] + .04 - low / RATE
    maximum = cue["latestEndSec"] - .08 - high / RATE
    assert minimum <= maximum, (cue["id"], "speech exceeds available visual window")
    shifts = np.clip(monotonic(values, weights), minimum, maximum)
    if cue["id"] == "01":
        # The opening has three successive cards: title, question, then tagline.
        # Retain the takes and place their sentence pauses at those transitions.
        assert len(sections) == 5
        shifts[1] = 4.0 - sections[1]["left"] / RATE
        shifts[2:] += 4.70
    cue_entries = []
    reconstructed = []
    for i, (section, shift) in enumerate(zip(sections, shifts)):
        left, right = section["left"], section["right"]
        piece = audio[left:right]
        start = round((left / RATE + float(shift)) * RATE) / RATE
        path = clips / f'{cue["id"]}-{i + 1:02}.wav'
        save(path, piece)
        reconstructed.append(piece)
        active_piece = np.flatnonzero(np.abs(piece.astype(np.int32)) > 100)
        entry = {"id": path.stem, "parentId": cue["id"], "startSec": start,
            "endSec": start + len(piece) / RATE, "durationSec": len(piece) / RATE,
            "audioPath": str(path), "sha256": sha(path), "sourceSampleStart": left,
            "sourceSampleEnd": right, "sourceAudioPath": cue["audioPath"],
            "speechStartSec": start + float(active_piece[0] / RATE) if len(active_piece) else start,
            "speechEndSec": start + float(active_piece[-1] / RATE) if len(active_piece) else start}
        entries.append(entry)
        cue_entries.append(entry)
        for anchor in section["anchors"]:
            actual = float(shift) + anchor["sourceSec"]
            audit.append({"cue": cue["id"], "phrase": anchor["phrase"], "targetSec": anchor["targetSec"],
                "predictedSpokenSec": actual, "errorSec": actual - anchor["targetSec"],
                "visualStartSec": anchor["visualStartSec"]})
    assert np.array_equal(np.concatenate(reconstructed), audio[low:high])
    passages.append({"id": cue["id"], "text": cue["text"], "startSec": cue_entries[0]["startSec"], "endSec": cue_entries[-1]["endSec"]})
    errors = [abs(a["errorSec"]) for a in audit if a["cue"] == cue["id"]]
    print(cue["id"], "clips", len(sections), "ends", round(cue_entries[-1]["endSec"], 3), "max predicted anchor error", round(max(errors or [0]), 3))

timeline = np.zeros(round(config["durationSec"] * RATE), dtype="<i2")
previous = 0
for cue in entries:
    with wave.open(cue["audioPath"]) as source:
        audio = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    start = round(cue["startSec"] * RATE)
    assert start >= previous and start + len(audio) <= len(timeline)
    timeline[start:start + len(audio)] = audio
    previous = start + len(audio)
save(BASE / "narration-raw.wav", timeline)
report = {"durationSec": config["durationSec"], "sourceVideoSha256": config["sourceVideoSha256"],
    "sampleRate": RATE, "rawSha256": sha(BASE / "narration-raw.wav"), "cues": entries,
    "passages": passages, "phraseAnchors": audit, "timingMethod": "model token predictions checked against visual events; not forced alignment"}
(BASE / "narration-alignment.json").write_text(json.dumps(report, indent=2) + "\n")
def stamp(time):
    ms = round(time * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'
(BASE.parent / "Certificates_1080p60-narrated.srt").write_text("\n\n".join(
    f'{i + 1}\n{stamp(c["startSec"])} --> {stamp(c["endSec"])}\n{c["text"]}' for i, c in enumerate(passages)) + "\n")
print("Preserved all spoken samples in", len(entries), "aligned clips.")
