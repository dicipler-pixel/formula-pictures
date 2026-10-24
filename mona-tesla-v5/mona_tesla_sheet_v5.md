# Mona Tesla v5 — Jeromie Beasley — the complete formula

The picture is a 948 × 1270 image. Pixel (m, n), with m = 0..947 (column) and n = 0..1269 (row), sits at w = m + i n.
All numbers below come from the data file mona_tesla_formula_v5.json (keys named in brackets). Angles are in radians.

## 1. Orbits
For each outline j (list [outlines]), with circles (a_jk, f_jk, p_jk) [circles] (at most 64):
  z_j(t) = Σ_k a_jk · exp(i(2π f_jk t + p_jk)),   evaluated at t_r = r/2048, r = 0..2047.

## 2. Inside an outline
W_j(w) = 1 if w lies inside the closed 2048-vertex polygon z_j(t_0), z_j(t_1), …, z_j(t_2047) (non-zero winding), else 0.
(This is the winding integral (1/2π)∮ d arg(z_j(t) − w) taken over the 2048 vertices.)

## 3. Tone (offset peel lengths)
Levels [levels] ℓ_0..ℓ_12; band tones [band_tones] s_0..s_13. Each outline has a level [level] (= ℓ_i for some i) and a sign σ_j [sigma].
  λ(s) = 2 artanh(2s − 1)
  τ_0(w) = λ(s_0) + Σ_j σ_j · (λ(s_{i_j+1}) − λ(s_{i_j})) · W_j(w)

## 4. Lightning (fracture envelope)
  M_κ(u) = exp(−u/κ) · (√(4 + u²) + u) / 2,    G(κ) = ½ exp(−√(κ² − 4)/κ) (κ + √(κ² − 4))
Phases φ_0..φ_7 [bolt_phases]. For each bolt b [bolts] with p0, p1 (in picture pixels), amp A, kappa κ, start σ0, span Δ, w (stroke width):
  d = p1 − p0, unit normal ν = (−d_y, d_x)/|d|,
  for q = 0..900, u_q = q/900:
    offset_q = sin(π u_q) · Σ_{j=0..7} A · 0.62^j · sin(2^j π u_q + φ_j)
    P_q = p0 + u_q d + offset_q ν            (a point in the plane, x right, y down)
    β_q = M_κ(6 (σ0 + Δ u_q)) / G(max(κ, 3))
  For a pixel w: let ρ = distance from w to the nearest P_q, and β = β_q of that nearest point.
  If ρ > 60 the bolt contributes 0. Otherwise its value is
    ℒ_b(w) = β · ( exp(−ρ²/(2 w²)) + 0.6 exp(−ρ²/32) + 0.4 exp(−ρ²/288) ).
  ℒ(w) = max over all bolts of ℒ_b(w)   (0 if none).
  τ(w) = τ_0(w) + 5 · min(ℒ(w), 1.6)

## 5. Shade and grain
  s = (1 + tanh(τ/2)) / 2
  X = (m − 474)/300,  Y = (n − 635)/300
  E = Σ_{j=1..29} 0.9^j · cos( 1.25^j (cos(3j²) X + sin(3j²) Y) + cos(4j) )
  s' = clamp(s + E/140, 0, 1)

## 6. Colour (Perron leader)
π = [perron] (the Perron eigenvector of [A], scaled to max 1). For channel v = 0, 1, 2 (R, G, B):
  c_v = π_v s' + (1 − π_v) s'³,    value = floor(255 · clamp(c_v, 0, 1)).
