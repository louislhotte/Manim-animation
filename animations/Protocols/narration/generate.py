import os
os.environ['HF_HUB_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import hashlib,json,re,wave
from pathlib import Path
import numpy as np
from mlx_audio.tts.utils import load_model
from mlx_audio.tts.models.kokoro.pipeline import KokoroPipeline
ROOT=Path(__file__).parent
plan=json.loads((ROOT/'plan.json').read_text())
(ROOT/'takes').mkdir(exist_ok=True)
model=None
rows=[]
for cue in plan['cues']:
    text=cue['text']
    for word,rep in {'SYN':'[SYN](/sˈɪn/)', 'ACK':'[ACK](/ˈæk/)', 'Léa':'[Léa](/lˈeɪə/)', 'JSON':'[JSON](/ʤˈeɪsən/)'}.items():
        text=re.sub(r'\b'+word+r'\b',lambda m:rep,text)
    speed=cue.get('speed',.95)
    key=hashlib.sha256(json.dumps([text,speed,'af_heart','Kokoro-82M-bf16']).encode()).hexdigest()[:16]
    path=ROOT/'takes'/f"{cue['id']}-{key}.wav"
    meta=path.with_suffix('.json')
    if not path.exists():
        if model is None:
            model=load_model('mlx-community/Kokoro-82M-bf16')
            pipeline=KokoroPipeline(lang_code='a',model=model,repo_id='mlx-community/Kokoro-82M-bf16')
        pieces=[]; tokens=[]; offset=0.
        for result in pipeline(text,voice='af_heart',speed=speed):
            a=np.asarray(result.audio,dtype=np.float32).reshape(-1)
            assert np.isfinite(a).all() and abs(a).max()<1
            for t in result.tokens:
                if t.start_ts is not None:
                    tokens.append({'text':t.text,'start':offset+t.start_ts,'end':offset+t.end_ts,'phonemes':t.phonemes})
            pieces.append(a); offset+=len(a)/24000
        a=np.concatenate(pieces)
        active=np.flatnonzero(abs(a)>.0008)
        first=max(0,int(active[0])-1440); last=min(len(a),int(active[-1])+2400)
        a=a[first:last]
        for t in tokens: t['start']-=first/24000; t['end']-=first/24000
        with wave.open(str(path),'wb') as f:
            f.setparams((1,2,24000,0,'NONE','not compressed'))
            f.writeframes(np.round(a*32767).astype('<i2').tobytes())
        meta.write_text(json.dumps({'tokens':tokens,'text':cue['text'],'spokenText':text,'speed':speed,'durationSec':len(a)/24000},indent=2))
    data=json.loads(meta.read_text())
    row={**cue,**data,'audioPath':str(path)}
    row['endSec']=cue['startSec']+data['durationSec']
    row['roomSec']=cue['latestEndSec']-cue['startSec']
    row['gapSec']=cue['latestEndSec']-row['endSec']
    rows.append(row)
    (ROOT/'takes.json').write_text(json.dumps({'durationSec':plan['durationSec'],'cues':rows},indent=2))
    print(f"{cue['id']} {data['durationSec']:.2f}s / {row['roomSec']:.2f}s, gap {row['gapSec']:+.2f}s",flush=True)
print('COMPLETE',len(rows),flush=True)
