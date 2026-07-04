import numpy as np
from demo.bpp import DATASETS, OPT, evaluate

names = list(DATASETS["OR3"].keys())
train = names[:12]
LB = OPT["OR3"]
TRAIN = {n: DATASETS["OR3"][n] for n in train}
FULL = DATASETS["OR3"]

def sc(fn):
    return (evaluate(TRAIN, fn)-LB)/LB*100, (evaluate(FULL, fn)-LB)/LB*100

# Rich piecewise on r with fixed breakpoints, free values. Loose zone is first-fit-ish constant.
BP = np.array([0,2,4,6,8,10,14,20,30])  # score value applies for r in [BP[i], BP[i+1])
def make(vals, cap=30.0, tie=0.0):
    vals = np.asarray(vals, float)
    def p(item, bins):
        r = bins - item
        idx = np.clip(np.searchsorted(BP, r, side='right')-1, 0, len(vals)-1)
        s = vals[idx].copy()
        # loose zone (r>=30) tie-break: add tiny term
        s = s + tie*np.minimum(r, 60.0)
        return s
    return p

rng = np.random.default_rng(0)
# start from a v0-like value vector
base = np.array([3.0, 2.2, 1.4, 0.6, -1.0, 0.02, 0.02, 0.03, 0.03])
best = (base.copy(), *sc(make(base)))
print("base:", sc(make(base)))

pool = []
for it in range(4000):
    v = best[0] + rng.normal(0, [0.6,0.6,0.6,0.6,0.8,0.3,0.3,0.05,0.05])
    fn = make(v)
    t, f = sc(fn)
    pool.append((t, f, v.copy()))
    if t < best[1] or (t == best[1] and f < best[2]):
        best = (v.copy(), t, f)

pool.sort(key=lambda x: (x[0], x[1]))
print("\ntop by train:")
seen = set()
for t, f, v in pool[:40]:
    key = (round(t,3), round(f,3))
    if key in seen: continue
    seen.add(key)
    print(f"train={t:.3f} full={f:.3f}  vals={np.round(v,2).tolist()}")
