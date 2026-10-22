# SCRIPT: RING-VIDEO-01
# "The ring keeps two books": a 5-site twisted ring (v15, Section 7) drawn with Yeganeh's grammar.
# Simulation: downhill flow of the connection energy within the ring family, small noise,
# twist wound in slowly. Rendering: soft steps, level sets, glow bands, painter's layering.
# Usage: python3 ring_video.py simulate | render <worker> <nworkers> [max_frames]
import numpy as np, json, sys, os
from PIL import Image, ImageDraw, ImageFont
OUT = os.path.dirname(os.path.abspath(__file__))
N = 5; FPS = 24; MU = 4.0; NOISE = 2e-3; SIM_HZ = 960
W, H = 1280, 720
def d_of(t):
    s = np.clip((t - 1.0) / 16.0, 0, 1)
    return 2.9 * np.pi * (s - np.sin(2 * np.pi * s) / (2 * np.pi))
def xs(th, d): return th - np.roll(th, -1) - d / N
def grad(th, d):
    g = 4 * np.sin(xs(th, d)); return g - np.roll(g, 1)
def floor(d): return min(4 * N * (1 - np.cos((d - 2 * np.pi * w) / N)) for w in range(-3, 4))
def winding(th):
    dth = (th - np.roll(th, -1) + np.pi) % (2 * np.pi) - np.pi
    return int(round(dth.sum() / (2 * np.pi)))

def simulate():
    rng = np.random.default_rng(7); th = 1e-3 * rng.standard_normal(N)
    dt = 1 / SIM_HZ; T = 20.0; states = []
    for i in range(int(T * SIM_HZ) + 1):
        t = i * dt; states.append(th.copy())
        th = th - MU * dt * grad(th, d_of(t)) + NOISE * np.sqrt(dt) * rng.standard_normal(N)
    states = np.array(states)
    w = np.array([winding(s) for s in states]); i_slip = int(np.argmax(w != w[0]))
    t_slip = i_slip * dt
    # frame schedule: real time, except 0.45 s before to 0.35 s after the slip, shown 6x slower
    a, b, slow = t_slip - 0.45, t_slip + 0.35, 6.0
    times, t = [], 0.0
    while t <= T:
        times.append(t); t += (1 / FPS) / (slow if a <= t < b else 1.0)
    frames = []
    for t in times:
        th = states[int(round(t * SIM_HZ))]; d = d_of(t)
        E = float(np.sum(4 * (1 - np.cos(xs(th, d)))))
        frames.append({'t': t, 'd': float(d), 'th': th.tolist(), 'E': E, 'floor': float(floor(d)), 'slow': bool(a <= t < b)})
    json.dump({'t_slip': t_slip, 'd_slip': float(d_of(t_slip)), 'frames': frames}, open(OUT + '/sim.json', 'w'))
    print('slip at t=%.3f s, d=%.3f pi; %d frames (%.1f s of video)' % (t_slip, d_of(t_slip) / np.pi, len(frames), len(frames) / FPS))

def S(z, k): return np.exp(-np.exp(np.clip(-k * z, -60, 60)))
xs_ = (np.arange(W) - W / 2) / (H / 2); ys_ = (H / 2 - np.arange(H)) / (H / 2)
X, Y = np.meshgrid(xs_, ys_); r = np.hypot(X, Y); A = np.arctan2(Y, X) % (2 * np.pi)
amber = np.array([240, 166, 74]) / 255; cyan = np.array([134, 212, 228]) / 255
paper = np.array([238, 230, 216]) / 255; night = np.array([17, 21, 43]) / 255; raised = np.array([30, 36, 72]) / 255
R = 0.60; WB = 0.075; RG = 0.86

def background():
    E = np.zeros_like(X)
    for s in range(1, 26):
        E += 0.9 ** s * np.cos(1.25 ** s * (np.cos(3 * s * s) * X + np.sin(3 * s * s) * Y) + np.cos(4 * s))
    t = S(0.95 - r, 2.0)
    return night * (1 - t[..., None]) + raised * t[..., None] + 0.012 * E[..., None]
BG = None

def bar(img, cx, cy, ang, length, width, alpha, halo=True):
    u = (X - cx) * np.cos(ang) + (Y - cy) * np.sin(ang); v = -(X - cx) * np.sin(ang) + (Y - cy) * np.cos(ang)
    L = (u / length) ** 2 + (v / width) ** 2
    if halo:
        Lh = (u / (length * 1.35)) ** 2 + (v / (width * 3.2)) ** 2
        img += 0.10 * alpha * np.exp(-np.exp(3 * (np.sqrt(Lh) - 1.0)))[..., None] * paper
    m = alpha * S(1 - L, 6)
    return img * (1 - m[..., None]) + m[..., None] * paper

def draw(fr):
    th = np.array(fr['th']); d = fr['d']; phi = d / N
    x = xs(th, d); con = 4 * (1 - np.cos(x)); cs = con / 8
    img = BG.copy()
    k_e = np.floor(A / (2 * np.pi) * N).astype(int) % N
    share = cs[k_e]; rin, rout = R - WB / 2, R + WB / 2; split = rin + (1 - share) * WB
    band = S(r - rin, 420) * S(rout - r, 420)
    am = band * S(r - split, 420); cym = band - am
    gl = np.exp(-np.exp(14 * (np.abs(r - R) - 0.02)))
    img += (0.24 * gl * share)[..., None] * amber + (0.16 * gl * (1 - share))[..., None] * cyan
    img = img * (1 - band[..., None]) + 0.95 * (am[..., None] * amber + cym[..., None] * cyan)
    # transport marks: where site k's field would sit if carried a fraction s along its edge
    for k in range(N):
        for s in (0.25, 0.5, 0.75):
            ak = 2 * np.pi * (k + s) / N; cx, cy = (R - 0.12) * np.cos(ak), (R - 0.12) * np.sin(ak)
            img = bar(img, cx, cy, (th[k] - s * phi) / 2, 0.045, 0.006, 0.45, halo=False)
    for k in range(N):
        ak = 2 * np.pi * k / N; vx, vy = R * np.cos(ak), R * np.sin(ak)
        img = bar(img, vx, vy, th[k] / 2, 0.13, 0.017, 1.0)
        dot = S(0.026 - np.hypot(X - vx, Y - vy), 320)
        img = img * (1 - dot[..., None]) + dot[..., None] * night
    # the budget circle: connection share clockwise from the top, the floor as a white tick
    gb = S(r - (RG - 0.006), 900) * S(RG + 0.006 - r, 900)
    ga = ((np.pi / 2 - np.arctan2(Y, X)) % (2 * np.pi)) / (2 * np.pi)
    gfrac = fr['E'] / (8 * N); gam = S(gfrac - ga, 3000)
    img = img * (1 - gb[..., None]) + gb[..., None] * (gam[..., None] * amber + (1 - gam[..., None]) * cyan)
    fa = np.pi / 2 - 2 * np.pi * fr['floor'] / (8 * N)
    tick = S(0.004 - np.abs(-np.sin(fa) * X + np.cos(fa) * Y), 900) * S(r - (RG - 0.035), 900) * S(RG + 0.035 - r, 900) \
        * S(np.cos(fa) * X + np.sin(fa) * Y, 50)
    img = img * (1 - tick[..., None]) + tick[..., None] * paper
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

FONT_DIRS = ['/usr/share/texmf/fonts/opentype/public/tex-gyre/', '/usr/share/fonts/opentype/tex-gyre/',
             os.path.join(OUT, 'fonts')]
FALLBACK = {'texgyrepagella-regular.otf': 'DejaVuSerif.ttf', 'texgyreheros-regular.otf': 'DejaVuSans.ttf'}
def font(name, size):  # TeX Gyre Pagella / Heros if installed, else DejaVu, else Pillow's default
    for d in FONT_DIRS:
        if os.path.exists(os.path.join(d, name)): return ImageFont.truetype(os.path.join(d, name), size)
    try: return ImageFont.truetype(FALLBACK.get(name, 'DejaVuSans.ttf'), size)
    except OSError: return ImageFont.load_default(size)
def pi_str(v):
    return '0' if abs(v) < 5e-4 else ('%.2fπ' % (v / np.pi))
def captions(im, fr, meta, i, n):
    dr = ImageDraw.Draw(im, 'RGBA'); t = fr['t']
    P = (238, 230, 216); DIM = (183, 178, 196); AM = (240, 166, 74); CY = (134, 212, 228)
    fs, fl, fb = font('texgyreheros-regular.otf', 19), font('texgyreheros-regular.otf', 17), font('texgyrepagella-regular.otf', 40)
    def fade(t0, t1, ramp=0.4):
        return max(0.0, min(1.0, (t - t0) / ramp, (t1 - t) / ramp))
    a = fade(-1, 3.2)
    if a > 0:
        dr.text((40, 26), 'The ring keeps two books', font=fb, fill=P + (int(255 * a),))
        dr.text((40, 76), 'Five sites, a twist wound in,', font=fs, fill=DIM + (int(255 * a),))
        dr.text((40, 100), 'one budget shared by two books', font=fs, fill=DIM + (int(255 * a),))
    # readout
    dr.text((40, 150), 'twist d = ' + pi_str(fr['d']), font=fs, fill=P)
    dr.text((40, 180), 'connection book  %5.1f' % fr['E'], font=fs, fill=AM)
    dr.text((40, 208), 'opposite book     %5.1f' % (8 * N - fr['E']), font=fs, fill=CY)
    dr.text((40, 236), 'budget              %d' % (8 * N), font=fs, fill=DIM)
    if fr['slow']: dr.text((40, 272), 'slowed 6×', font=fs, fill=P)
    # legend
    y0 = H - 118
    dr.rectangle((40, y0 + 4, 62, y0 + 18), fill=AM); dr.text((74, y0), 'connection book  4(1 − cos x) per edge', font=fl, fill=P)
    dr.rectangle((40, y0 + 34, 62, y0 + 48), fill=CY); dr.text((74, y0 + 30), 'opposite book  4(1 + cos x) per edge', font=fl, fill=P)
    dr.rectangle((49, y0 + 60, 53, y0 + 80), fill=P); dr.text((74, y0 + 60), 'lowest connection book any field can reach', font=fl, fill=P)
    dr.text((74, y0 + 86), 'each edge always holds 8: the band width never changes', font=fl, fill=DIM)
    # story captions (bottom right column)
    tpi = meta['t_pi']; ts = meta['t_slip']
    lines = [(tpi - 0.2, tpi + 3.4, ['d = π: the two windings tie.', 'From here the floor is on the other winding.']),
             (tpi + 3.6, ts - 0.5, ['The field keeps its winding.', 'Its book climbs away from the floor.']),
             (ts - 0.45, ts + 0.9, ['The field slips one winding.']),
             (ts + 1.0, meta['t_end'] - 3.6, ['Back on the floor.', 'The slip is kept in the winding.'])]
    for t0, t1, txt in lines:
        a = fade(t0, t1)
        if a > 0:
            for j, s in enumerate(txt):
                dr.text((W - 40, H - 100 + 30 * j), s, font=fs, fill=P + (int(255 * a),), anchor='ra')
    a = fade(meta['t_end'] - 3.4, meta['t_end'] + 10)
    if a > 0:
        dr.rectangle((0, 0, W, H), fill=(17, 21, 43, int(215 * a)))
        L = ['The ring keeps two books', '',
             'Books, budget and floor: Jeromie Beasley, Non-normality is connection energy (v15), Section 7.',
             'Motion: downhill flow of the connection energy, kept to the ring family, with a small noise.',
             'Drawn entirely from equations, in the grammar of Hamid Naderi Yeganeh’s formula images.',
             '', 'Jeromie Beasley · Atlas Memoriae · made with AI assistance']
        for j, s in enumerate(L):
            f = fb if j == 0 else fs
            dr.text((W / 2, 230 + 38 * j + (20 if j else 0)), s, font=f, fill=(P if j in (0, 6) else DIM) + (int(255 * a),), anchor='mm')
    return im

def render(worker, nw, limit=None):
    global BG
    sim = json.load(open(OUT + '/sim.json')); fr = sim['frames']
    ts = [f['t'] for f in fr]
    meta = {'t_slip': sim['t_slip'], 't_pi': next(f['t'] for f in fr if f['d'] >= np.pi), 't_end': ts[-1]}
    BG = background(); os.makedirs(OUT + '/frames', exist_ok=True)
    for i in range(worker, len(fr) if limit is None else min(limit, len(fr)), nw):
        p = OUT + '/frames/f%04d.png' % i
        if os.path.exists(p): continue
        captions(draw(fr[i]), fr[i], meta, i, len(fr)).save(p)

if __name__ == '__main__':
    if sys.argv[1] == 'simulate': simulate()
    elif sys.argv[1] == 'render': render(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else None)
