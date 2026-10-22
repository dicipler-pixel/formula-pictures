# SCRIPT: YEGANEH-METHOD-NEW-02  (layer order as in the original: layer 1 = lowest, nearest ridge; lake mirrors the whole scene)
# Forward test of the method: an original scene ("Two moons over a mountain lake at dusk") written ONLY with the
# grammar read off Yeganeh's formula: soft steps e^{-e^{z}}, AND = sum of inner exponentials, level-set shapes,
# glow bands around a level set, folded ridge lines arccos(cos), an occlusion chain prod(1-J_u)J_s, a fractal
# texture E, colour channels as quadratics in v (v=0,1,2), and F = floor(255 clamp). Same pixel convention.
import numpy as np
from PIL import Image
np.seterr(all='ignore'); ex = np.exp
def scene(W_=2000, H_=1200):
    m = np.arange(1, W_ + 1) * (2000 / W_); n = np.arange(1, H_ + 1) * (1200 / H_)
    X, Y = np.meshgrid((m - 1000) / 500.0, (501 - n) / 500.0)
    def E_at(x, y):
        tot = 0
        for s in range(1, 41):
            k = 1.25 ** s
            tot = tot + 0.9**s * np.cos(k*(np.cos(3*s*s)*x + np.sin(3*s*s)*y) + 3*np.cos(k*(np.cos(5*s*s)*x + np.sin(5*s*s)*y)) + np.cos(4*s))
        return tot
    def sky(v, x, y, e):
        top = (v*v - 7*v + 22) / 40          # R,G,B = 0.55, 0.40, 0.35 -> wait: v=0 0.55, v=1 0.40, v=2 0.35 (deep dusk)
        hor = (-v*v - 3*v + 40) / 40         # v=0 1.00, v=1 0.90, v=2 0.70 (warm horizon)
        t = ex(-ex(-3*(y - 0.15)))           # soft vertical blend
        M1 = (x - 0.7)**2 + (y - 0.55)**2;  M2 = (x + 1.1)**2 + (y - 0.75)**2
        moon1 = ex(-ex(400*(M1 - 0.02)))     # disk of radius ~0.141
        moon2 = ex(-ex(900*(M2 - 0.004)))    # small disk
        glow = ex(-ex(4*(np.sqrt(M1) - 0.35) )) * 0.35 + ex(-ex(8*(np.sqrt(M2) - 0.12))) * 0.2
        craters = 1 - 0.12 * ex(-ex(6*(e/2 + 0.4)))
        moonc = (v*v - 2*v + 39) / 40        # v=0 0.975, v=1 0.95, v=2 0.975 (pale)
        base = (1 - t) * hor + t * top + glow * (1 - (moon1 + moon2))
        return base * (1 - moon1 - moon2) + moonc * craters * (moon1 + moon2)
    E = E_at(X, Y)
    # mountain layers: folded ridge lines; layer 1 is the lowest (nearest) ridge, as in the original chain
    def J(s, x, y, e, k=120):
        ridge = (-0.66 + 0.075*s + 0.20*np.arccos(np.cos(3*x + 0.7*np.cos(2*x + s*s) + s*s))/np.pi
                 + 0.07*np.arccos(np.cos(9*x + np.cos(5*x + 3*s*s) + 2*s*s))/np.pi + e/250)
        return ex(-ex(-k*(ridge - y)))
    def above(v, x, y, e):
        img = 0; run = 1
        for s in range(1, 7):
            Js = J(s, x, y, e)
            shade = (3*v*v - 5*v + 22)/40 * (0.55 + 0.09*s) + e/120   # nearer = darker, farther = paler (haze)
            img = img + run * Js * shade; run = run * (1 - Js)
        return img + run * sky(v, x, y, e)
    lake = ex(-ex(-80*(-0.78 - Y)))          # soft step: below the shoreline y = -0.78
    Ym = -1.56 - Y; Xr = X + 0.006*np.cos(50*Y + E/2); Em = E_at(Xr, Ym)
    def H(v):
        refl = above(v, Xr, Ym, Em) * 0.72 * (1 - 0.08*ex(-ex(4*np.cos(70*Y + E/2))))
        return above(v, X, Y, E) * (1 - lake) + refl * lake
    F = lambda h: np.floor(255*ex(-ex(-1000*h))*np.abs(h)**ex(-ex(1000*(h - 1))))
    return np.nan_to_num(np.stack([F(H(v)) for v in range(3)], -1)).clip(0, 255).astype(np.uint8)
img = scene(); Image.fromarray(img).save('new_scene_two_moons_v2.png'); print('saved', img.shape)
