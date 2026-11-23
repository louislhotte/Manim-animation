"""Recover the existing film's phrase schedule without rendering or editing it."""
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
WPS = 2.6

def seconds(value):
    h, m, s = value.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

rows = []
for block in (HERE.parent / 'voiceover.srt').read_text().strip().split('\n\n'):
    number, window, *spoken = block.splitlines()
    start, end = map(seconds, window.split(' --> '))
    rows.append(dict(id=f'{int(number):02}', text=' '.join(spoken), startSec=start,
                     originalSubtitleEndSec=end, anchors=[]))

class Schedule:
    def __init__(self, n):
        self.row = rows[n-1]
        self.now = 0.

    def offset(self, phrase):
        return len(self.row['text'][:self.row['text'].index(phrase)].split()) / WPS

    def play(self, duration):
        self.now += duration

    def anchor(self, phrase, kind, begin, end, notes=''):
        target = self.offset(phrase)
        self.row['anchors'].append(dict(
            phrase=phrase, kind=kind,
            spokenTargetSec=round(self.row['startSec']+target,6),
            visualStartSec=round(self.row['startSec']+begin,6),
            visualEndSec=round(self.row['startSec']+end,6),
            sourceScheduledLeadSec=.3,
            delayPastRequestedCueSec=round(max(0,begin-(target-.3)),6) if kind=='cue' else 0.,
            notes=notes,
        ))

    def cue(self, phrase, duration=0., notes=''):
        # cue() does nothing when a preceding animation has reached/passed it.
        self.now = max(self.now, self.offset(phrase)-.3)
        self.anchor(phrase, 'cue', self.now, self.now+duration, notes)
        self.play(duration)

    def span(self, phrase, floor, cap, notes=''):
        duration=min(cap,max(floor,self.offset(phrase)-.3-self.now))
        self.anchor(phrase,'span',self.now,self.now+duration,notes)
        self.play(duration)

s=Schedule(2);s.play(.8)
s.cue('a server answers',.7,'Server, key and link appear; key then travels to browser.')
s.span('But anyone',.9,1.6,'Shop key reaches browser by this transition.')
s.cue('anyone can make a key',.6,'Second server and key appear.')
s.cue('claim a name',1.5,'Duplicate name appears, then the second key travels.')
s=Schedule(3);s.play(.6);s.cue('the same claim',1.,'Both server name tags glow.')
s=Schedule(4);s.play(.6)
s.cue('this key belongs',1.,'Key and name fly into the certificate.')
s.cue('signed by someone',1.25,'Signature appears over 0.45 s, then glows for 0.8 s.')
s.cue('already trusts',1.4,'Certificate travels into browser, then the lock closes.')
s=Schedule(5);s.play(.8)
for phrase in ('the name','the public key','the dates','who issued'):
    s.cue(phrase,.45,'Corresponding certificate field appears and is highlighted.')
s=Schedule(6);s.play(.7)
s.cue('controls the name',.9,'Domain field receives the authority check mark.')
s.cue('it hashes those fields',.9,'Fields flow toward the fingerprint.')
s.span('and signs',.9,1.6,'Fingerprint cells finish appearing before signing starts.')
s.cue('signs the fingerprint',1.8,'Private key moves to the fingerprint; both collapse into the signature.')
s.cue('That signature',1.,'Completed signature glows.')
s=Schedule(7);s.play(.6)
s.cue('check the seal',1.4,'Public key moves to the seal, then signed fingerprint unfolds.')
s.cue('against the fingerprint',1.4,'Recomputed fields/fingerprint appear over two 0.7 s animations.')
s.cue('They agree',1.55,'Comparison scan begins; success check appears 1.15 s later.')
s=Schedule(8)
s.cue('a single letter',2.5,'Letter changes; fingerprint recolours; mismatch appears.')
s.cue('nobody can make',1.6,'Forgery key appears and fails against the signature.')
s=Schedule(9);s.play(1.2)
s.cue('Another certificate',.8,'Intermediate authority certificate appears.')
s.cue('a root authority',.8,'Root certificate appears.')
s.cue('signs itself',1.,'Root self-signature arrow is drawn.')
s=Schedule(10)
s.cue('The root is already',0.,'Root-store grid begins appearing.')
s.span('more than a hundred',1.2,2.2,'Grid finishes early because span is capped at 2.2 s; count appears next.')
s.play(.4);s.play(.8)
s=Schedule(11)
s.cue('Each seal',1.2,'Intermediate key checks leaf certificate; check appears after 0.9 s.')
s.cue('the certificate above',1.2,'Root key checks intermediate; check appears after 0.9 s.')
s.cue('a root it already holds',1.7,'Root is linked to the device store; final check appears.')
s=Schedule(12);s.play(.6)
s.span('The chain reaches',1.5,3.4,'The three check gates finish entering.')
for phrase in ('a root it trusts','the validity dates','The name matches'):
    s.cue(phrase,1.2,'Certificate reaches the gate after 0.6 s; green status then appears.')
s=Schedule(13);s.play(.5)
for phrase in ('an issuer it does not','a date that has passed','a name that does not'):
    s.cue(phrase,1.,'Failed certificate arrives over 0.45 s; red error then appears over 0.55 s.')
s=Schedule(14);s.play(1.3)
s.cue('anyone can copy it',.9,'Certificate is copied to the impersonating server.')
s.cue('fresh random numbers',1.5,'Challenge appears over 0.6 s, then travels to both servers over 0.9 s.')
s.cue('with the private key',2.9,'Private key/signature highlight; response and success/failure results follow.')
s=Schedule(15);s.play(.5)
s.span('two hundred',1.2,2.6,'398-day and 200-day rows finish early because span is capped at 2.6 s.')
s.cue('forty-seven',1.,'100-day and 47-day future rows appear.')
s.cue('So renewal',.4,'Renewal loop appears.')
s.cue('collects a fresh',.7,'Fresh certificate appears beside the renewal loop.')

payload=dict(durationSec=181.533333,wps=WPS,
             timingBasis='Original SRT caption starts plus source cue/span scheduling. Float schedule excludes frame quantization; allow roughly one to two video frames.',
             cues=rows)
(HERE/'visual-anchors.json').write_text(json.dumps(payload,indent=2)+'\n')
for row in rows:
    print(row['id'],[(a['phrase'],a['spokenTargetSec'],a['visualStartSec'],a['delayPastRequestedCueSec']) for a in row['anchors']])
