"""Mona Tesla v5: exact coefficient animation and narrated layer build.
Run: python make_video.py [--prepare-only]
Requires numpy scipy pillow matplotlib; ffmpeg must be on PATH.
To regenerate voice: python narrate.py --model MODEL.onnx --voices VOICES.bin
"""
from pathlib import Path
import json, math, subprocess, sys
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
AS=ROOT/'assets'; AS.mkdir(exist_ok=True)
D=json.loads((ROOT/'mona_tesla_formula_v5.json').read_text())
W,H=948,1270; VW,VH=1920,1080; FPS=24
BG=(10,17,25); INK=(231,237,239); MUT=(152,172,186); CYAN=(88,215,227); GOLD=(233,191,113)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
def ft(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
def rgb(s,pi=None):
 s=np.clip(s,0,1)
 if pi is None:return np.repeat(np.floor(s[...,None]*255).astype('uint8'),3,axis=2)
 pi=np.array(pi);return np.floor(255*np.clip(pi*s[...,None]+(1-pi)*s[...,None]**3,0,1)).astype('uint8')
def sigmoid(t):return (1+np.tanh(t/2))/2

def prepare():
 if (AS/'math_cache.npz').exists():return
 t=np.arange(2048)/2048
 lam=np.log(np.array(D['band_tones'])/(1-np.array(D['band_tones'])))
 tau=np.full((H,W),lam[0]);layers=[tau.copy()]
 polygons=[];counts=[]
 for level_i,level in enumerate(D['levels']):
  outlines=[o for o in D['outlines'] if o['level']==level];counts.append(len(outlines))
  for o in outlines:
   c=np.array(o['circles']);z=(c[:,0,None]*np.exp(1j*(2*np.pi*c[:,1,None]*t+c[:,2,None]))).sum(axis=0)
   polygons.append(z)
   x,y=z.real,z.imag;x1,y1=np.roll(x,-1),np.roll(y,-1)
   inc=o['sigma']*(lam[level_i+1]-lam[level_i])
   for row in range(max(0,int(np.ceil(y.min()))),min(H,int(np.floor(y.max()))+1)):
    active=((y<=row)&(y1>row))|((y1<=row)&(y>row))
    xx=x[active]+(row-y[active])*(x1[active]-x[active])/(y1[active]-y[active])
    direction=np.where(y1[active]>y[active],1,-1);order=np.argsort(xx);xx=xx[order];direction=direction[order]
    winding=0
    for k in range(len(xx)-1):
     winding+=direction[k]
     if winding:
      left=max(0,int(np.ceil(xx[k])));right=min(W,int(np.ceil(xx[k+1])))
      if right>left:tau[row,left:right]+=inc
  layers.append(tau.copy())
  print('Prepared tone layer',level_i+1,flush=True)
 light=np.zeros((H,W));boltpaths=[];u=np.arange(901)/900
 for b in D['bolts']:
  p0,p1=np.array(b['p0']),np.array(b['p1']);delta=p1-p0;normal=np.array([-delta[1],delta[0]])/np.linalg.norm(delta)
  offset=np.sin(np.pi*u)*sum(b['amp']*.62**j*np.sin(2**j*np.pi*u+D['bolt_phases'][j]) for j in range(8))
  pts=p0+u[:,None]*delta+offset[:,None]*normal;boltpaths.append(pts)
  v=6*(b['start']+b['span']*u);kap=b['kappa'];gkap=max(kap,3);q=np.sqrt(gkap*gkap-4)
  beta=np.exp(-v/kap)*(np.sqrt(4+v*v)+v)/2/(.5*np.exp(-q/gkap)*(gkap+q))
  xmin=max(0,int(np.floor(pts[:,0].min()-60)));xmax=min(W,int(np.ceil(pts[:,0].max()+60))+1)
  ymin=max(0,int(np.floor(pts[:,1].min()-60)));ymax=min(H,int(np.ceil(pts[:,1].max()+60))+1)
  yy,xx=np.mgrid[ymin:ymax,xmin:xmax];rho,idx=cKDTree(pts).query(np.column_stack((xx.ravel(),yy.ravel())))
  val=beta[idx]*(np.exp(-rho*rho/(2*b['w']**2))+.6*np.exp(-rho*rho/32)+.4*np.exp(-rho*rho/288));val[rho>60]=0
  light[ymin:ymax,xmin:xmax]=np.maximum(light[ymin:ymax,xmin:xmax],val.reshape(yy.shape))
 n,m=np.mgrid[:H,:W];X=(m-474)/300;Y=(n-635)/300
 E=sum(.9**j*np.cos(1.25**j*(np.cos(3*j*j)*X+np.sin(3*j*j)*Y)+np.cos(4*j)) for j in range(1,30))
 np.savez_compressed(AS/'math_cache.npz',layers=np.array(layers),polygons=np.array(polygons),light=light,grain=E/140,boltpaths=np.array(boltpaths),counts=counts)
 final=rgb(sigmoid(tau+5*np.minimum(light,1.6))+E/140,D['perron'])
 Image.fromarray(final).save(AS/'reconstructed.png')
 original=ROOT/'Mona_Tesla_v5.png'
 if original.exists():
  a=np.array(Image.open(original));assert np.array_equal(a,final),'Final image must match exact corrected renderer'
 print('Exact final render verified',flush=True)

# Narration is segmented so the visual explanation tracks what the voice says.
def script():
 scenes=[
 dict(kind='single',min=12,title='The circles are the drawing',kicker='01 / FOURIER ORBITS',body=['A circle supplies one rotating vector.','Its radius, frequency and phase come','directly from the coefficient file.'],formula='orbit',narration='This picture begins with rotating circles. Each circle supplies a vector with a measured radius, a rotation frequency, and a starting phase. Add those vectors, and the final tip becomes the drawing pen.'),
 dict(kind='detail',min=12,title='Every small circle matters',kicker='02 / ONE COMPLETE CHAIN',body=['64 terms in each outline.','1 fixed offset places the chain.','63 rotating circles shape its contour.'],formula='orbit',narration='Here is one smaller contour, enlarged. Its sixty four terms include one fixed offset and sixty three rotating circles. Large circles establish the shape. Small circles refine the detail. Negative frequencies rotate in the opposite direction.'),
 dict(kind='all',min=16,title='All 651 chains at work',kicker='03 / THE WHOLE COEFFICIENT SET',body=['41,013 rotating circles.','651 fixed offsets.','Every tip traces one closed outline.'],formula='orbit',narration='Now all six hundred fifty one chains run together. You are seeing all forty one thousand thirteen rotating circles. Their tips trace the stored contours at two thousand forty eight samples per orbit. These outlines will define the portrait.'),
 dict(kind='winding',min=11,title='A contour becomes a region',kicker='04 / NONZERO WINDING',body=['Trace the closed polygon.','Test whether each pixel lies inside.','The stored sign adds or subtracts tone.'],formula='winding',narration='A closed outline tells us which pixels lie inside it. The nonzero winding test creates that region. Each stored sign then adds or subtracts its tone increment. Subtracting regions preserves holes and interior details.'),
 ]
 descriptions=[
 ('The first tone layer establishes the broad silhouette and its darkest structure.',['Broad silhouette','Dark structure']),
 ('The second layer begins separating the figure from the surrounding field.',['Figure and surrounding field','Cumulative tone']),
 ('The third layer adds another increment wherever its signed regions apply.',['Signed regions','Another tone increment']),
 ('The fourth layer continues the build. Every earlier contribution remains in place.',['Keep earlier contributions','Add layer four']),
 ('The fifth layer brings in more intermediate tones across the portrait.',['Intermediate tones','Add layer five']),
 ('The sixth layer adds the next set of closed contours to the accumulated field.',['More closed contours','Add layer six']),
 ('The seventh layer continues the tonal separation around the face and clothing.',['Tonal separation','Add layer seven']),
 ('The eighth layer adds finer regions while retaining the larger shapes underneath.',['Finer regions','Larger shapes remain']),
 ('The ninth layer contributes eighty nine signed outlines, the largest group in this build.',['89 signed outlines','Largest contour group']),
 ('The tenth layer adds another set of regions to the same scalar tone field.',['One accumulated field','Add layer ten']),
 ('The eleventh layer brings the build closer to its brightest tone bands.',['Brighter tone bands','Add layer eleven']),
 ('The twelfth layer adds the next highlight regions without replacing the earlier layers.',['Highlight regions','Add layer twelve']),
 ('The thirteenth layer completes the contour based tone field. The portrait is now assembled.',['Contour tone field complete','651 outlines assembled'])]
 for i,(n,b) in enumerate(descriptions):
  scenes.append(dict(kind='layer',layer=i+1,min=5.1,title=f'Tone layer {i+1:02d} / 13',kicker=f'05 / CONTOUR BUILD · LEVEL {D["levels"][i]}',body=b+[f'{sum(o["level"]==D["levels"][i] for o in D["outlines"])} outlines in this layer'],formula='tone',narration=n))
 scenes +=[
 dict(kind='bolt',min=13,title='Lightning is another field',kicker='06 / FRACTURE ENVELOPE',body=['15 paths from the supplied bolt data.','Oscillating offsets shape each branch.','Distance and envelope control the glow.'],formula='bolt',narration='The lightning is calculated separately. Fifteen paths use oscillating offsets to form the branches. Distance from each sampled path sets the glow, and the fracture envelope controls its strength. That light field is added to the portrait tone.'),
 dict(kind='grain',min=9,title='Grain from 29 cosine waves',kicker='07 / SHADE AND GRAIN',body=['Map tone through the sigmoid.','Add the prescribed cosine sum / 140.','Clamp the result between zero and one.'],formula=None,narration='The tone passes through a sigmoid. Twenty nine cosine waves then add the specified grain. This texture is deterministic too. The same equations produce the same pattern every time.'),
 dict(kind='colour',min=10,title='One field becomes three colours',kicker='08 / PERRON COLOUR MAP',body=['Use the supplied Perron vector.','Blend linear and cubic shade per channel.','Quantize each RGB value to an integer.'],formula='colour',narration='Finally, the supplied Perron vector controls the red, green, and blue channels. Each channel blends the shade with its cube. That turns the single brightness field into this warm gold palette.'),
 dict(kind='final',min=8,title='The equations are the picture',kicker='MONA TESLA V5',body=['Circles → contours → signed tone','Lightning → grain → RGB','Every visible pixel is computed.'],formula=None,narration='Circles become contours. Contours build tone. Lightning, grain, and colour complete the image. The equations are the picture.'),
 dict(kind='credits',min=7,title='Mona Tesla v5',kicker='CREDITS',body=['Formula artwork and coefficient set','Jeromie Beasley','Fourier epicycles · winding numbers','Kokoro-82M / hexgrad · am_michael','Code animation and rendering: ChatGPT'],formula=None,narration='Mona Tesla, version five. Formula artwork and coefficients by Jeromie Beasley. Narration generated with Kokoro.')]
 return scenes

def formula_images():
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 forms={
 'orbit':r'$z_j(t)=\sum_k a_{jk}\,e^{i(2\pi f_{jk}t+p_{jk})}$',
 'winding':r'$W_j(w)=\mathbf{1}\!\left[\mathrm{wind}(z_j,w)\ne0\right]$',
 'tone':r'$\tau_0=\lambda(s_0)+\sum_j\sigma_j\,\Delta\lambda_j\,W_j$',
 'bolt':r'$\tau=\tau_0+5\,\min(\mathcal{L},1.6)$',
 'colour':r'$c_v=\pi_v\,s^{\prime}+(1-\pi_v)(s^{\prime})^3$'}
 out={}
 for key,expr in forms.items():
  path=AS/f'eq_{key}.png'
  if not path.exists():
   fig=plt.figure(figsize=(7.7,1.1),dpi=130);fig.patch.set_alpha(0)
   fig.text(.02,.4,expr,fontsize=24,color='#e9bf71',va='center');fig.savefig(path,transparent=True,bbox_inches='tight',pad_inches=.08);plt.close(fig)
  im=Image.open(path).convert('RGBA');im.thumbnail((800,110),Image.Resampling.LANCZOS);out[key]=im
 return out

def smooth(v):v=np.clip(v,0,1);return float(v*v*(3-2*v))
def video():
 prepare();cache=np.load(AS/'math_cache.npz');layers=cache['layers'];polys=cache['polygons'];light=cache['light'];grain=cache['grain'];bolts=cache['boltpaths']
 scenes=json.loads((ROOT/'timeline.json').read_text());eqs=formula_images()
 scale=.713;PX,PY=1136,68;PW,PH=round(W*scale),round(H*scale)
 def tx(z,origin=None,sc=None):
  if origin is None:origin=complex(PX,PY)
  if sc is None:sc=scale
  q=origin+z*sc;return np.column_stack((q.real,q.imag))
 def portrait(arr):return Image.fromarray(arr).resize((PW,PH),Image.Resampling.LANCZOS)
 toneims=[portrait(rgb(sigmoid(a))) for a in layers]
 lit=rgb(sigmoid(layers[-1]+5*np.minimum(light,1.6)))
 litim=portrait(lit);grayshade=np.clip(sigmoid(layers[-1]+5*np.minimum(light,1.6))+grain,0,1)
 grayim=portrait(rgb(grayshade));finalim=portrait(rgb(grayshade,D['perron']))
 coeff=np.array([o['circles'] for o in D['outlines']]);amp=coeff[:,:,0];freq=coeff[:,:,1];phase=coeff[:,:,2]
 # Positions are sums of actual complex coefficients, never fitted visual paths.
 pxy=np.array([tx(z) for z in polys]);pathlists=[[(float(x),float(y)) for x,y in a] for a in pxy]
 stationary=np.zeros((H,W),dtype='uint8')
 basebg=Image.new('RGB',(VW,VH),BG)
 bd=ImageDraw.Draw(basebg)
 for x in range(0,VW,80):bd.line((x,0,x,VH),fill=(14,23,32))
 for y in range(0,VH,80):bd.line((0,y,VW,y),fill=(14,23,32))
 bd.line((72,996,1848,996),fill=(41,57,69),width=1)
 bd.text((72,1019),'JEROMIE BEASLEY  /  MONA TESLA v5',font=ft(17),fill=MUT)
 out=ROOT/'Mona_Tesla_v5_Explainer_Kokoro.mp4'
 out.parent.mkdir(exist_ok=True)
 silent=AS/'silent.mp4'
 cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{VW}x{VH}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','4',str(silent)]
 preview='--preview' in sys.argv
 enc=None if preview else subprocess.Popen(cmd,stdin=subprocess.PIPE)
 selected=0;detail=299;total_frames=sum(s['frames'] for s in scenes);frame_i=0
 # Static all-outline layer highlights, rasterized once per tone group.
 highlights=[]
 for lvl in D['levels']:
  im=Image.new('RGBA',(VW,VH));dr=ImageDraw.Draw(im)
  for j,o in enumerate(D['outlines']):
   if o['level']==lvl:dr.line(pathlists[j]+pathlists[j][:1],fill=(*CYAN,200),width=1)
  highlights.append(im)
 def wrapped(dr,text,xy,font,fill,maxw=910,lineheight=42):
  x,y=xy;words=text.split();line=''
  for word in words:
   trial=(line+' '+word).strip()
   if dr.textlength(trial,font=font)>maxw and line:dr.text((x,y),line,font=font,fill=fill);y+=lineheight;line=word
   else:line=trial
  if line:dr.text((x,y),line,font=font,fill=fill)
  return y+lineheight
 def chain(dr,j,t,origin=None,sc=None,progress=1,full=False):
  c=coeff[j];vec=c[:,0]*np.exp(1j*(2*np.pi*c[:,1]*t+c[:,2]));end=np.cumsum(vec);centers=np.r_[0+0j,end[:-1]]
  a=scale if sc is None else sc
  ctr=tx(centers,origin,sc);ep=tx(end,origin,sc)
  limit=min(64,int(progress*64)+1)
  for k in range(1,limit):
   xx,yy=ctr[k];r=c[k,0]*a
   dr.ellipse((xx-r,yy-r,xx+r,yy+r),outline=(51,107,124) if full else (55,137,157),width=1)
   if not full:dr.line((xx,yy,*ep[k]),fill=(90,172,188),width=1)
  if not full:
   for k in range(1,limit):
    xx,yy=ep[k];dr.ellipse((xx-2,yy-2,xx+2,yy+2),fill=GOLD)
  xx,yy=ep[-1];dr.ellipse((xx-4,yy-4,xx+4,yy+4),fill=(255,226,164))
 for scene_idx,s in enumerate(scenes):
  print('Rendering',scene_idx+1,len(scenes),s['title'],s['frames']/FPS,'seconds',flush=True)
  for f in ([s['frames']//2] if preview else range(s['frames'])):
   p=f/max(s['frames']-1,1);kind=s['kind'];im=basebg.copy();dr=ImageDraw.Draw(im)
   if kind in ['single','detail']:
    j=selected if kind=='single' else detail
    if kind=='single':origin=complex(PX,PY);sc=scale
    else:
     z=polys[j];sc=min(650/(z.real.max()-z.real.min()),720/(z.imag.max()-z.imag.min()));origin=complex(PX+PW/2,PY+PH/2)-np.mean(z)*sc
    # A full slow lap, then hold the finished outline.
    lap=min(p/0.88,1);idx=max(2,min(2048,int(lap*2048)))
    points=tx(polys[j][:idx],origin,sc)
    dr.line([tuple(q) for q in points],fill=GOLD,width=3)
    chain(dr,j,lap,origin,sc,progress=1)
    dr.text((PX,PY+PH+12),'ACTUAL COEFFICIENTS · ONE COMPLETE ORBIT',font=ft(16),fill=MUT)
   elif kind=='all':
    lap=min(p/.92,1);idx=max(2,min(2048,int(lap*2048)))
    # All 41,013 rotating circles are evaluated and drawn; tiny radii remain tiny.
    vec=amp*np.exp(1j*(2*np.pi*freq*lap+phase));end=np.cumsum(vec,axis=1);centers=np.concatenate([np.zeros((651,1),complex),end[:,:-1]],axis=1)
    for j in range(651):
     ctr=tx(centers[j]);rads=amp[j]*scale
     for k in range(1,64):
      xx,yy=ctr[k];r=rads[k];dr.ellipse((xx-r,yy-r,xx+r,yy+r),outline=(30,71,85),width=1)
    for j in range(651):
     dr.line(pathlists[j][:idx],fill=(165,150,113),width=1)
     q=tx(end[j,-1:])[0];dr.ellipse((q[0]-1.3,q[1]-1.3,q[0]+1.3,q[1]+1.3),fill=CYAN)
    dr.text((PX,PY+PH+12),'ALL CIRCLES · ALL 651 OUTLINE TIPS',font=ft(16),fill=MUT)
   elif kind=='winding':
    im.paste(toneims[1],(PX,PY));dr=ImageDraw.Draw(im)
    for j in range(31):dr.line(pathlists[j],fill=CYAN if D['outlines'][j]['sigma']==1 else GOLD,width=2)
    dr.text((PX,PY+PH+12),'CYAN: ADD REGION   GOLD: SUBTRACT REGION',font=ft(16),fill=MUT)
   elif kind=='layer':
    j=s['layer'];a=smooth(min(p/.65,1));im.paste(Image.blend(toneims[j-1],toneims[j],a),(PX,PY))
    if p<.75:
     ov=highlights[j-1].copy();ov.putalpha(ov.getchannel('A').point(lambda x:int(x*(1-smooth(p/.75)))));im.paste(ov,(0,0),ov)
    dr=ImageDraw.Draw(im)
    for k in range(13):
     x=PX+k*52;dr.rectangle((x,PH+PY+18,x+39,PH+PY+24),fill=GOLD if k<j else (46,57,65))
   elif kind=='bolt':
    a=smooth(min(p/.8,1));im.paste(portrait(rgb(sigmoid(layers[-1]+a*5*np.minimum(light,1.6)))),(PX,PY))
   elif kind=='grain':im.paste(Image.blend(litim,grayim,smooth(min(p/.7,1))),(PX,PY))
   elif kind=='colour':im.paste(Image.blend(grayim,finalim,smooth(min(p/.8,1))),(PX,PY))
   else:im.paste(finalim,(PX,PY))
   dr=ImageDraw.Draw(im)
   dr.text((72,78),s['kicker'],font=ft(20,True),fill=CYAN)
   y=wrapped(dr,s['title'],(68,138),ft(53,True),INK,maxw=980,lineheight=66)
   y=max(y+45,320)
   for line in s['body']:
    y=wrapped(dr,line,(72,y),ft(29),MUT,maxw=935,lineheight=42)+12
   if s.get('formula'):
    eq=eqs[s['formula']];im.paste(eq,(68,660),eq)
   if kind=='single':
    dr.text((72,804),'radius = a     speed / direction = f     start = p',font=ft(24),fill=GOLD)
    dr.text((72,850),'The last tip traces z(t).',font=ft(27),fill=INK)
   elif kind=='detail':
    dr.text((72,804),'DETAIL VIEW · OUTLINE 300',font=ft(21),fill=GOLD)
    dr.text((72,850),'Same coefficients. Enlarged view.',font=ft(27),fill=INK)
   elif kind=='layer':
    dr.text((72,800),f'{sum(cache["counts"][:s["layer"]])} / 651 outlines accumulated',font=ft(26),fill=GOLD)
   # Short timed verbatim captions, grouped by punctuation / phrase, clear of artwork.
   elapsed=f/FPS
   for cap in s.get('captions',[]):
    if cap['start']<=elapsed<cap['end']:
     yy=889
     for line in cap['lines']:dr.text((72,yy),line,font=ft(27),fill=INK);yy+=37
     break
   dr.rectangle((72,995,72+int(1776*frame_i/total_frames),997),fill=GOLD)
   if not preview:enc.stdin.write(im.tobytes())
   frame_i+=1
  if preview or scene_idx in [0,1,2,3,4,10,16,17,18,19,20,21]:im.save(AS/f'qa_{scene_idx:02d}.jpg',quality=90)
 if preview:return
 enc.stdin.close();assert enc.wait()==0
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',str(ROOT/'narration.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart','-metadata','title=Mona Tesla v5 — The Equations Are the Picture','-metadata','artist=Jeromie Beasley','-metadata','comment=Exact Fourier coefficient animation; Kokoro am_michael narration.',str(out)],check=True)
 print('VIDEO COMPLETE',out,flush=True)

if __name__=='__main__':
 if '--prepare-only' in sys.argv:prepare()
 elif '--script-only' in sys.argv:(ROOT/'script.json').write_text(json.dumps(script(),indent=2))
 else:video()
