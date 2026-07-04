import numpy as np
from demo.bpp import DATASETS, OPT, evaluate

names = list(DATASETS["OR3"].keys())
train = names[:12]
LB = OPT["OR3"]
TRAIN = {n: DATASETS["OR3"][n] for n in train}
FULL = DATASETS["OR3"]

def score_fn(fn):
    t = (evaluate(TRAIN, fn) - LB) / LB * 100
    f = (evaluate(FULL, fn) - LB) / LB * 100
    return t, f

# v0-family parametric: near-full reward window, dead-gap valley, tiny loose preference
def mk(cap, scale, dead, pen, nf, A, B):
    def p(item, bins):
        r = bins - item
        s = np.minimum(r, cap) * scale
        s[r <= dead] = pen
        m = r <= nf
        s[m] = A - B * r[m]
        return s
    return p

rng = np.random.default_rng(0)
# start = v0
base = dict(cap=30.0, scale=0.001, dead=8.0, pen=-1.0, nf=6.0, A=3.0, B=0.4)
best = base.copy()
bt, bf = score_fn(mk(**base))
print("v0-family base:", round(bt,3), round(bf,3))

pool = []
cur = base.copy(); ct, cf = bt, bf
steps = dict(cap=6.0, scale=0.0008, dead=1.5, pen=0.6, nf=1.2, A=0.6, B=0.12)
for it in range(6000):
    c = cur.copy()
    for k in c:
        c[k] = cur[k] + rng.normal(0, steps[k])
    c["nf"] = min(c["nf"], c["dead"] - 0.5)   # keep nf < dead
    c["cap"] = max(c["cap"], 15.0)
    try:
        t, f = score_fn(mk(**c))
    except Exception:
        continue
    pool.append((f, t, c.copy()))
    if (t, f) < (ct, cf):
        cur, ct, cf = c.copy(), t, f
    if it % 1200 == 0:
        pool.sort(key=lambda x: (x[1], x[0]))
        cur = pool[0][2].copy(); ct, cf = pool[0][1], pool[0][0]

pool.sort(key=lambda x: (x[1], x[0]))   # by train then full
print("\ntop distinct (by train,full), beating or matching v0:")
seen = set(); shown = 0
for f, t, c in pool:
    key = (round(t, 3), round(f, 3))
    if key in seen:
        continue
    seen.add(key)
    print(f"train={t:.3f} full={f:.3f}  "
          f"cap={c['cap']:.1f} scale={c['scale']:.4f} dead={c['dead']:.1f} "
          f"pen={c['pen']:.2f} nf={c['nf']:.1f} A={c['A']:.2f} B={c['B']:.2f}")
    shown += 1
    if shown >= 20:
        break
