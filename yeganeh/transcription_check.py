# SCRIPT: YEGANEH-TRANSCRIPTION-01
# Re-implement the two-moons formula from its written transcription (fractions as printed) and diff against the
# image produced by YEGANEH-METHOD-NEW-02. Kill: any pixel channel differing by more than 1.
import numpy as np
from PIL import Image
np.seterr(all='ignore'); ex = np.exp; pi = np.pi
m = np.arange(1, 2001); n = np.arange(1, 1201)
x, y = np.meshgrid((m - 1000) / 500, (501 - n) / 500)
def E(x, y): return sum((9/10)**s * np.cos((5/4)**s*(np.cos(3*s*s)*x + np.sin(3*s*s)*y) + 3*np.cos((5/4)**s*(np.cos(5*s*s)*x + np.sin(5*s*s)*y)) + np.cos(4*s)) for s in range(1, 41))
def Sky(v, x, y, e):
    T = (v*v - 7*v + 22)/40; Z = (-v*v - 3*v + 40)/40; t = ex(-ex(-3*(y - 3/20)))
    M1 = (x - 7/10)**2 + (y - 11/20)**2; M2 = (x + 11/10)**2 + (y - 3/4)**2
    mu1 = ex(-ex(400*(M1 - 1/50))); mu2 = ex(-ex(900*(M2 - 1/250)))
    G = 7/20*ex(-ex(4*(np.sqrt(M1) - 7/20))) + 1/5*ex(-ex(8*(np.sqrt(M2) - 3/25)))
    c = (v*v - 2*v + 39)/40; R = 1 - 3/25*ex(-ex(6*(e/2 + 2/5)))
    return ((1 - t)*Z + t*T + G*(1 - mu1 - mu2))*(1 - mu1 - mu2) + c*R*(mu1 + mu2)
def J(s, x, y, e):
    r = (-33/50 + 3*s/40 + 1/(5*pi)*np.arccos(np.cos(3*x + 7/10*np.cos(2*x + s*s) + s*s))
         + 7/(100*pi)*np.arccos(np.cos(9*x + np.cos(5*x + 3*s*s) + 2*s*s)) + e/250)
    return ex(-ex(-120*(r - y)))
def Above(v, x, y, e):
    tot = 0; run = 1
    for s in range(1, 7):
        j = J(s, x, y, e); tot = tot + run*j*((3*v*v - 5*v + 22)/40*(11/20 + 9*s/100) + e/120); run = run*(1 - j)
    return tot + run*Sky(v, x, y, e)
e = E(x, y); lam = ex(-ex(-80*(-39/50 - y)))
xt = x + 3/500*np.cos(50*y + e/2); yt = -39/25 - y; et = E(xt, yt)
H = lambda v: (1 - lam)*Above(v, x, y, e) + lam*18/25*(1 - 2/25*ex(-ex(4*np.cos(70*y + e/2))))*Above(v, xt, yt, et)
F = lambda h: np.floor(255*ex(-ex(-1000*h))*np.abs(h)**ex(-ex(1000*(h - 1))))
img = np.nan_to_num(np.stack([F(H(v)) for v in range(3)], -1)).clip(0, 255).astype(np.uint8)
ref = np.asarray(Image.open('new_scene_two_moons_v2.png'))
d = np.abs(img.astype(int) - ref.astype(int))
print('pixels compared', d.shape[0]*d.shape[1], ' max channel difference', d.max(), ' channels differing at all', int((d > 0).sum()))
