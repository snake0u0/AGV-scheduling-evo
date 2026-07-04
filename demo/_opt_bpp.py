import numpy as np
from demo.bpp import DATASETS, OPT, evaluate

names = list(DATASETS["OR3"].keys())
train = names[:12]
LB = OPT["OR3"]
TRAIN = {n: DATASETS["OR3"][n] for n in train}
FULL = DATASETS["OR3"]

def sc(fn):
    t = (evaluate(TRAIN, fn) - LB) / LB * 100
    f = (evaluate(FULL, fn) - LB) / LB * 100
    return t, f

# General piecewise-on-r evaluator with configurable breakpoints/values.
def make_pw(bp, vals, slope=0.0):
    bp = np.asarray(bp, float)
    vals = np.asarray(vals, float)
    def p(item, bins):
        r = bins - item
        idx = np.clip(np.searchsorted(bp, r, side="right") - 1, 0, len(vals) - 1)
        return vals[idx] + slope * np.minimum(r, 60.0)
    return p

# Breakpoints chosen around the dead-space threshold (min item = 20).
BP = np.array([0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 30, 50])
# value per interval [BP[i], BP[i+1]); last covers r>=50
base = np.array([5.0, 4.0, 3.0, 2.0, 1.2, 0.5, -0.5, -0.8, -0.6, 0.95, 0.97, 0.99])

rng = np.random.default_rng(1)
best = (base.copy(), *sc(make_pw(BP, base)))
print("base:", best[1:])

pool = []
cur = base.copy()
curscore = sc(make_pw(BP, cur))
step = np.array([0.8,0.8,0.8,0.8,0.6,0.5,0.5,0.4,0.4,0.05,0.03,0.02])
for it in range(9000):
    v = cur + rng.normal(0, step)
    t, f = sc(make_pw(BP, v))
    pool.append((t, f, v.copy()))
    if (t, f) < curscore:
        cur, curscore = v.copy(), (t, f)
    if it % 1500 == 0:
        # occasional restart from global best
        pool.sort(key=lambda x: (x[0], x[1]))
        cur = pool[0][2].copy(); curscore = (pool[0][0], pool[0][1])

pool.sort(key=lambda x: (x[0], x[1]))
print("\ntop distinct by (train,full):")
seen = set(); shown = 0
for t, f, v in pool:
    key = (round(t, 3), round(f, 3))
    if key in seen: continue
    seen.add(key)
    print(f"train={t:.3f} full={f:.3f}  vals={np.round(v,2).tolist()}")
    shown += 1
    if shown >= 25: break
