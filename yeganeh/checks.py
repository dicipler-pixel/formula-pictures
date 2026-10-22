# SCRIPT: YEGANEH-CHECKS-01
# (1) Occlusion chain is a complete measurement: sum_s prod_{u<s}(1-J_u) J_s + prod_s (1-J_s) = 1 (telescoping).
# (2) Cloud texture E = sum (9/10)^s D_s with frequencies (5/4)^s: Weierstrass-type, roughness exponent -ln(0.9)/ln(1.25).
import numpy as np
rng = np.random.default_rng(0); J = rng.random((10, 100000))
tot = sum(np.prod(1 - J[:s], axis=0) * J[s] for s in range(10)) + np.prod(1 - J, axis=0)
print('occlusion chain sums to 1, max error', np.abs(tot - 1).max())
print('roughness (Holder) exponent of the cloud sum:', -np.log(0.9) / np.log(1.25))
