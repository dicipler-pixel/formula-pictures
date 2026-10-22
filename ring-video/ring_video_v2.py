# SCRIPT: RING-VIDEO-02
# Narrated cut of "The ring keeps two books" (Kokoro am_michael). The picture is timed to the voice:
# each narration segment spans one stretch of the simulation. Story captions are left out
# (the voice carries them); the readout, legend, opening DOI notice and credits card stay.
# Usage: python3 narrate.py; python3 ring_video.py simulate; python3 ring_video_v2.py plan | audio | render <worker> <nworkers> [max_frames]
import numpy as np, json, sys, os
import soundfile as sf
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ring_video as rv
OUT = rv.OUT; FPS = 24; GAP = 0.6
DOI = 'CC | https://doi.org/10.5281/zenodo.22803572'
seg = json.load(open(OUT + '/voice/segments.json'))
SIM_HZ = rv.SIM_HZ

def sim_states():
    rng = np.random.default_rng(7); th = 1e-3 * rng.standard_normal(rv.N); dt = 1 / SIM_HZ; st = []
    for i in range(int(20.0 * SIM_HZ) + 1):
        t = i * dt; st.append(th.copy())
        th = th - rv.MU * dt * rv.grad(th, rv.d_of(t)) + rv.NOISE * np.sqrt(dt) * rng.standard_normal(rv.N)
    return np.array(st)

def plan():
    sim = json.load(open(OUT + '/sim.json')); ts_ = sim['t_slip']
    t_pi = next(f['t'] for f in sim['frames'] if f['d'] >= np.pi)
    L = lambda k: seg[k]['sec']
    # (name, sim start, sim end, [voice keys], extra seconds)
    parts = [('intro', 0.0, 1.0, ['s1'], 0.8), ('wind', 1.0, t_pi, ['s2', 's3'], 0.6),
             ('hold', t_pi, ts_ - 0.45, ['s4', 's5'], 0.6), ('slip', ts_ - 0.45, ts_ + 0.35, ['s6'], 0.8),
             ('settle', ts_ + 0.35, 20.0, ['s7'], 0.8), ('credits', 20.0, 20.0, ['s8'], 2.0)]
    tl, cues, v0 = [], [], 0.0
    for name, a, b, keys, extra in parts:
        dur = sum(L(k) for k in keys) + GAP * (len(keys) - 1) + extra
        c = v0 + 0.3
        for k in keys: cues.append({'key': k, 'start': c}); c += L(k) + GAP
        tl.append({'name': name, 'v0': v0, 'v1': v0 + dur, 's0': a, 's1': b, 'slow': (dur / (b - a)) if b > a else None})
        v0 += dur
    nF = int(np.ceil(v0 * FPS))
    json.dump({'parts': tl, 'cues': cues, 'nF': nF, 'T': v0}, open(OUT + '/plan_v2.json', 'w'), indent=1)
    for p in tl: print(p['name'], round(p['v0'], 2), round(p['v1'], 2), 'sim', round(p['s0'], 2), round(p['s1'], 2), 'x%.1f' % p['slow'] if p['slow'] else '')
    print('total %.1f s, %d frames' % (v0, nF))

def frame_info(pl, i, states):
    v = i / FPS
    p = next((q for q in pl['parts'] if q['v0'] <= v < q['v1']), pl['parts'][-1])
    s = p['s0'] + (p['s1'] - p['s0']) * (v - p['v0']) / (p['v1'] - p['v0'])
    th = states[int(round(s * SIM_HZ))]; d = rv.d_of(s)
    E = float(np.sum(4 * (1 - np.cos(rv.xs(th, d)))))
    return {'v': v, 'part': p, 't': s, 'd': float(d), 'th': th.tolist(), 'E': E, 'floor': float(rv.floor(d))}

def overlay(im, fr, pl):
    dr = ImageDraw.Draw(im, 'RGBA'); v = fr['v']; T = pl['T']; W, H = rv.W, rv.H
    P = (238, 230, 216); DIM = (183, 178, 196); AM = (240, 166, 74); CY = (134, 212, 228)
    fs, fl, fb = rv.font('texgyreheros-regular.otf', 19), rv.font('texgyreheros-regular.otf', 17), rv.font('texgyrepagella-regular.otf', 40)
    def fade(t0, t1, ramp=0.5): return max(0.0, min(1.0, (v - t0) / ramp, (t1 - v) / ramp))
    intro = pl['parts'][0]
    a = fade(-1, intro['v1'] - 0.2)
    if a > 0:
        al = int(255 * a)
        dr.text((40, 26), 'The ring keeps two books', font=fb, fill=P + (al,))
        dr.text((40, 76), 'Five sites, a twist wound in,', font=fs, fill=DIM + (al,))
        dr.text((40, 100), 'one budget shared by two books', font=fs, fill=DIM + (al,))
        dr.text((W - 40, H - 40), DOI, font=fl, fill=DIM + (al,), anchor='rs')
    dr.text((40, 150), 'twist d = ' + rv.pi_str(fr['d']), font=fs, fill=P)
    dr.text((40, 180), 'connection book  %5.1f' % fr['E'], font=fs, fill=AM)
    dr.text((40, 208), 'opposite book     %5.1f' % (8 * rv.N - fr['E']), font=fs, fill=CY)
    dr.text((40, 236), 'budget              %d' % (8 * rv.N), font=fs, fill=DIM)
    if fr['part']['name'] == 'slip':
        dr.text((40, 272), 'slowed %d×' % round(fr['part']['slow']), font=fs, fill=P)
    y0 = H - 118
    dr.rectangle((40, y0 + 4, 62, y0 + 18), fill=AM); dr.text((74, y0), 'connection book  4(1 − cos x) per edge', font=fl, fill=P)
    dr.rectangle((40, y0 + 34, 62, y0 + 48), fill=CY); dr.text((74, y0 + 30), 'opposite book  4(1 + cos x) per edge', font=fl, fill=P)
    dr.rectangle((49, y0 + 60, 53, y0 + 80), fill=P); dr.text((74, y0 + 60), 'lowest connection book any field can reach', font=fl, fill=P)
    dr.text((74, y0 + 86), 'each edge always holds 8: the band width never changes', font=fl, fill=DIM)
    cr = pl['parts'][-1]; a = fade(cr['v0'] - 0.2, T + 10, 0.8)
    if a > 0:
        al = int(255 * a)
        dr.rectangle((0, 0, W, H), fill=(17, 21, 43, int(222 * a)))
        rows = [('The ring keeps two books', fb, P), ('Jeromie Beasley', fs, P), ('', fs, P),
                ('Books, budget and floor: Non-normality is connection energy (v15), Section 7', fs, DIM),
                ('Motion: downhill flow of the connection energy in the ring family, with a small noise', fs, DIM),
                ('Drawn from equations in the grammar of Hamid Naderi Yeganeh’s formula images', fs, DIM),
                ('Narration: Kokoro, voice am_michael · made with AI assistance', fs, DIM),
                ('Lean proofs: github.com/dicipler-pixel/nonnormality-connection-energy-lean', fs, DIM), ('', fs, P),
                ('Atlas Memoriae · Ex memoria lux, ex luce materia.', fs, P), (DOI, fs, P)]
        y = 150
        for s, f, c in rows:
            if s: dr.text((W / 2, y), s, font=f, fill=c + (al,), anchor='mm')
            y += 52 if f is fb else 34
    return im

def render(worker, nw, limit=None):
    pl = json.load(open(OUT + '/plan_v2.json')); states = sim_states(); rv.BG = rv.background()
    os.makedirs(OUT + '/frames_v2', exist_ok=True); cache = {}
    # the intro light: a soft brightening that travels once around the ring while the voice introduces it
    for i in range(worker, pl['nF'] if limit is None else min(limit, pl['nF']), nw):
        p = OUT + '/frames_v2/f%04d.png' % i
        if os.path.exists(p): continue
        fr = frame_info(pl, i, states)
        key = tuple(np.round(fr['th'], 6)) + (round(fr['d'], 6),)
        if fr['part']['name'] == 'credits' and key in cache: base = cache[key].copy()
        else:
            base = rv.draw(fr)
            if fr['part']['name'] == 'intro':
                u = (fr['v'] - 1.0) / max(fr['part']['v1'] - 2.0, 1e-6)
                if 0 <= u <= 1:
                    ang = (np.pi / 2 - 2 * np.pi * u) % (2 * np.pi)
                    da = np.angle(np.exp(1j * (rv.A - ang)))
                    lam = np.exp(-(da / 0.35) ** 2) * np.exp(-((rv.r - rv.R) / 0.07) ** 2)
                    arr = np.asarray(base).astype(float) / 255
                    arr = np.clip(arr + 0.35 * lam[..., None] * rv.paper, 0, 1)
                    base = Image.fromarray((arr * 255).astype(np.uint8))
            if fr['part']['name'] == 'credits': cache[key] = base.copy()
        overlay(base, fr, pl).save(p)

def audio():
    pl = json.load(open(OUT + '/plan_v2.json')); sr = seg['s1']['sr']
    track = np.zeros(int(np.ceil(pl['nF'] / FPS * sr)) + sr)
    for c in pl['cues']:
        a, _ = sf.read(OUT + '/voice/%s.wav' % c['key']); s = int(c['start'] * sr)
        track[s:s + len(a)] += a
    track = track[:int(pl['nF'] / FPS * sr)]
    sf.write(OUT + '/voice/narration_v2.wav', track, sr); print('audio %.2f s, peak %.3f' % (len(track) / sr, np.abs(track).max()))

if __name__ == '__main__':
    {'plan': lambda: plan(), 'render': lambda: render(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else None), 'audio': lambda: audio()}[sys.argv[1]]()
