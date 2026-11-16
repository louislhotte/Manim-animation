import hashlib,json,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).parent
data=json.loads((ROOT/'takes.json').read_text())
plan=json.loads((ROOT/'plan.json').read_text())
assert len(data['cues'])==len(plan['cues'])
RATE=24000
out=np.zeros(round(data['durationSec']*RATE),dtype=np.int16)
previous=0.
for cue in data['cues']:
    assert cue['startSec']>=previous, ('overlap',cue['id'])
    with wave.open(cue['audioPath'],'rb') as f:
        assert f.getframerate()==RATE and f.getnchannels()==1
        a=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2')
    start=round(cue['startSec']*RATE)
    assert start+len(a)<=len(out)
    out[start:start+len(a)]=a
    previous=cue['endSec']
with wave.open(str(ROOT/'aligned.wav'),'wb') as f:
    f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes(out.astype('<i2').tobytes())
def stamp(t):
    ms=round(t*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
srt='\n\n'.join(f"{i+1}\n{stamp(c['startSec'])} --> {stamp(c['endSec'])}\n{c['text']}" for i,c in enumerate(data['cues']))+'\n'
(ROOT.parent/'Protocols_1080p60-narrated.srt').write_text(srt)
(ROOT/'script.txt').write_text('\n\n'.join(c['text'] for c in data['cues'])+'\n')
print('Aligned',len(data['cues']),'cues;',round(previous,3),'last spoken end')
