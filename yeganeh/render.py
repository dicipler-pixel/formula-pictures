# SCRIPT: YEGANEH-BH-01
# Render Hamid Naderi Yeganeh's "View of a Black Hole from a Planet" exactly from the printed formula,
# to check the formula reproduces his picture. Pixel (row n, column m): x=(m-1000)/500, y=(501-n)/500.
import numpy as np
from PIL import Image
np.seterr(all='ignore')
ex = np.exp
m = np.arange(1, 2001); n = np.arange(1, 1201)
X, Y = np.meshgrid((m - 1000) / 500.0, (501 - n) / 500.0)
def D(s, x, y):
    k = (5 / 4) ** s
    a = np.cos(k * (np.cos(2*s*s)*x + np.sin(2*s*s)*y) + 4*np.cos(k*(np.cos(7*s*s)*x + np.sin(7*s*s)*y)) + 2*np.cos(5*s))
    b = np.cos(k * (np.cos(2*s*s)*y - np.sin(2*s*s)*x) + 4*np.cos(k*(np.cos(8*s*s)*x + np.sin(8*s*s)*y)) + 2*np.cos(5*s))
    return a * b
E = sum((9/10)**s * D(s, X, Y) for s in range(1, 51))
L = (10 - 9*ex(-ex(-10*(Y - X/5)))) * (Y - X/5)**2 + (X + Y/5)**2
K = ex(-ex(-1.5*(L - 2.5)))
def A(v): return ex(-ex(v*(np.abs(L - 0.3) - 0.05)) - ex(-2*(L - 0.3)))
def B(v): return ex(-ex(v*(np.abs(10*(Y - X/5)**2 + 0.8*(X + Y/5)**2 - 0.7) - 0.3 + E/7)) - ex(-20*(L - 0.3)))
def J(v, s):
    arg = (Y + 1 - s/20 + E/200 + 2*np.arccos(np.cos(4*X + np.cos(2*X + 2*s*s) + s*s))/25
           + np.arccos(np.cos(7*X + np.cos(3*X + 4*s*s) + 5*s*s))/25 + np.arccos(np.cos(17*X + np.cos(12*X + 6*s*s) + 7*s*s))/50)
    return ex(-ex(-100*(s - 0.5)) - ex(v*arg))
def W(v): return ex(-ex(15*(np.cos(9*Y + X/4)*np.cos(2*X + Y) + 6/5 - (1 + E/3)*K/(1 + v))))
J150 = {s: J(150, s) for s in range(0, 11)}
P = np.ones_like(X)
for s in range(1, 11): P *= (1 - J150[s])
C = np.zeros_like(X); run = np.ones_like(X)
for s in range(1, 11):
    run = run * (1 - J150[s-1])            # prod_{u=0}^{s-1} (1 - J_{150,u})
    C += run * J150[s] * (5/4 + s/7) * J(-0.5, s)
W0, W1 = W(0), W(1)
def H(v):
    sky = ((v*v + v + 14)/20*(21/20 - np.sqrt(L)/18)*(15 - Y)/15 + A(100) + A(5) + A(0.75) + B(5)/8 + B(1)/12)
    return sky*P*(1 - W0) + P*W0*(8 - W1)/8 + ((3*v*v - 3*v + 28)/40 + E/100)*C
def F(x):
    return np.floor(255*ex(-ex(-1000*x))*np.abs(x)**ex(-ex(1000*(x - 1))))
rgb = np.stack([F(H(v)) for v in range(3)], axis=-1)
rgb = np.nan_to_num(rgb, nan=0).clip(0, 255).astype(np.uint8)
Image.fromarray(rgb).save('yeganeh_bh_render.png')
print('rendered', rgb.shape, 'mean rgb', rgb.reshape(-1,3).mean(0).round(1))
