"""Generate the real Kokoro voice, then make a frame-accurate scene timeline."""
from pathlib import Path
import json,re,math,argparse
import numpy as np
import soundfile as sf
import onnxruntime as ort
import kokoro_onnx
from kokoro_onnx import Kokoro
from make_video import FPS,script
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--voices',required=True);a=p.parse_args()
opts=ort.SessionOptions();opts.intra_op_num_threads=4;opts.inter_op_num_threads=1
# Keep CPU execution bounded and reproducible on large hosts.
kokoro_onnx.create_session=lambda path:ort.InferenceSession(path,sess_options=opts,providers=['CPUExecutionProvider'])
k=Kokoro(a.model,a.voices)
scenes=script();audio=[];clock=0;sr=24000;entries=[]
for i,s in enumerate(scenes):
 path=ROOT/'assets'/f'voice_{i:02d}.wav'
 if path.exists():samples,sr=sf.read(path,dtype='float32')
 else:
  samples,sr=k.create(s['narration'],voice='af_heart',speed=.98,lang='en-us')
  sf.write(path,samples,sr)
 speechdur=len(samples)/sr
 duration=max(s['min'],speechdur+1.7);frames=math.ceil(duration*FPS);duration=frames/FPS
 lead=.5;pad=np.zeros(int(round(duration*sr)),dtype='float32');start=int(lead*sr);pad[start:start+len(samples)]=samples
 audio.append(pad);s.update(frames=frames,start=clock,duration=duration,speech_duration=speechdur,voice='af_heart',captions=[])
 # Short phrase captions are proportional within each scene; narration remains unaltered.
 phrases=re.split(r'(?<=[.!?])\s+',s['narration']);weights=[len(x.split()) for x in phrases];pos=lead
 for phrase,weight in zip(phrases,weights):
  dur=speechdur*weight/sum(weights);words=phrase.split();lines=[];line=''
  for word in words:
   if len(line+' '+word)>57 and line:lines.append(line);line=word
   else:line=(line+' '+word).strip()
  if line:lines.append(line)
  s['captions'].append(dict(start=pos,end=pos+dur,lines=lines));pos+=dur
 entries.append((clock+lead,clock+lead+speechdur,s['narration']))
 clock+=duration
 print('Kokoro',i+1,len(scenes),round(speechdur,1),'s; scene',round(duration,1),'s',flush=True)
sf.write(ROOT/'narration.wav',np.concatenate(audio),sr,subtype='PCM_16')
(ROOT/'timeline.json').write_text(json.dumps(scenes,indent=2))
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(ROOT/'narration.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(st)} --> {stamp(en)}\n{txt}' for i,(st,en,txt) in enumerate(entries))+'\n')
print('Narration duration',clock,flush=True)
