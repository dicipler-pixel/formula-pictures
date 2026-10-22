# SCRIPT: YEGANEH-ANATOMY-01
# Demonstrable account of how the black-hole formula is built: (1) the primitives are exact identities;
# (2) each visual element is one term (ablation: switch it off, the element disappears, nothing else changes much).
import numpy as np
from PIL import Image, ImageDraw
np.seterr(all='ignore'); ex = np.exp
# ---- (1) primitives
S = lambda z, k=1.0: ex(-ex(-k * z))                    # soft step: ~0 for z<0, ~1 for z>0
z = np.linspace(-3, 3, 100001)
print('soft step  e^{-e^{-1000 z}} vs Heaviside, max error away from |z|<0.01:', np.abs(S(z, 1000) - (z > 0))[np.abs(z) > 0.01].max())
a, b = np.random.default_rng(0).normal(size=(2, 100000))
print('AND rule   e^{-e^a - e^b} = S(-a) * S(-b): max error', np.abs(ex(-ex(a) - ex(b)) - S(-a) * S(-b)).max())
x = np.linspace(-1, 3, 400001)
F = np.floor(255 * ex(-ex(-1000 * x)) * np.abs(x) ** ex(-ex(1000 * (x - 1))))
G = np.floor(255 * np.clip(x, 0, 1))
print('colour map F(x) = floor(255*clamp(x,0,1)): disagreements', int((F != G).sum()), 'of', x.size, '(only within 0.01 of 0 and 1)')
for name, f in (('(v^2+v+14)/20', lambda v: (v*v + v + 14) / 20), ('(3v^2-3v+28)/40', lambda v: (3*v*v - 3*v + 28) / 40)):
    print(f'channel coefficient {name}: R,G,B =', [f(v) for v in (0, 1, 2)], ' (a quadratic in v through three chosen colour values = Lagrange interpolation)')
# ---- (2) ablation renders (half resolution), toggling the named terms
def render(drop=(), W_=1000, H_=600):
    m = np.arange(1, W_ + 1) * (2000 / W_); n = np.arange(1, H_ + 1) * (1200 / H_)
    X, Y = np.meshgrid((m - 1000) / 500.0, (501 - n) / 500.0)
    def D(s):
        k = 1.25 ** s
        return (np.cos(k*(np.cos(2*s*s)*X + np.sin(2*s*s)*Y) + 4*np.cos(k*(np.cos(7*s*s)*X + np.sin(7*s*s)*Y)) + 2*np.cos(5*s))
                * np.cos(k*(np.cos(2*s*s)*Y - np.sin(2*s*s)*X) + 4*np.cos(k*(np.cos(8*s*s)*X + np.sin(8*s*s)*Y)) + 2*np.cos(5*s)))
    E = 0 * X if 'texture E' in drop else sum(0.9**s * D(s) for s in range(1, 51))
    L = (10 - 9*ex(-ex(-10*(Y - X/5)))) * (Y - X/5)**2 + (X + Y/5)**2
    K = ex(-ex(-1.5*(L - 2.5)))
    A = lambda v: ex(-ex(v*(np.abs(L - 0.3) - 0.05)) - ex(-2*(L - 0.3)))
    B = lambda v: ex(-ex(v*(np.abs(10*(Y - X/5)**2 + 0.8*(X + Y/5)**2 - 0.7) - 0.3 + E/7)) - ex(-20*(L - 0.3)))
    def J(v, s):
        arg = (Y + 1 - s/20 + E/200 + 2*np.arccos(np.cos(4*X + np.cos(2*X + 2*s*s) + s*s))/25
               + np.arccos(np.cos(7*X + np.cos(3*X + 4*s*s) + 5*s*s))/25 + np.arccos(np.cos(17*X + np.cos(12*X + 6*s*s) + 7*s*s))/50)
        return ex(-ex(-100*(s - 0.5)) - ex(v*arg))
    W = lambda v: ex(-ex(15*(np.cos(9*Y + X/4)*np.cos(2*X + Y) + 6/5 - (1 + E/3)*K/(1 + v))))
    J150 = {s: (0*X if 'mountains C' in drop else J(150, s)) for s in range(0, 11)}
    P = np.ones_like(X)
    for s in range(1, 11): P = P * (1 - J150[s])
    C = np.zeros_like(X); run = np.ones_like(X)
    for s in range(1, 11):
        run = run * (1 - J150[s-1]); C = C + run * J150[s] * (5/4 + s/7) * J(-0.5, s)
    W0 = 0*X if 'clouds W' in drop else W(0); W1 = W(1)
    glow = 0 if 'glow A' in drop else 1; ring = 0 if 'ring B' in drop else 1
    def H(v):
        sky = ((v*v + v + 14)/20*(21/20 - np.sqrt(L)/18)*(15 - Y)/15 + glow*(A(100) + A(5) + A(0.75)) + ring*(B(5)/8 + B(1)/12))
        return sky*P*(1 - W0) + P*W0*(8 - W1)/8 + ((3*v*v - 3*v + 28)/40 + E/100)*C
    Fm = lambda h: np.floor(255*np.clip(h, 0, 1))
    return np.nan_to_num(np.stack([Fm(H(v)) for v in range(3)], -1)).astype(np.uint8)
panels = [('full formula', ()), ('without glow terms A', ('glow A',)), ('without ring terms B', ('ring B',)),
          ('without cloud term W', ('clouds W',)), ('without mountain layers J, C', ('mountains C',)), ('without texture E', ('texture E',))]
tiles = []
for title, drop in panels:
    im = Image.fromarray(render(drop)).resize((600, 360)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 600, 26], fill=(255, 255, 255)); d.text((8, 6), title, fill=(0, 0, 0)); tiles.append(im)
sheet = Image.new('RGB', (1200, 1080), 'white')
for i, t in enumerate(tiles): sheet.paste(t, ((i % 2) * 600, (i // 2) * 360))
sheet.save('anatomy_ablation.png'); print('saved anatomy_ablation.png')
