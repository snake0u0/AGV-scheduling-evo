import sys, numpy as np
from demo.bpp import DATASETS, OPT, evaluate

names = list(DATASETS["OR3"].keys())
LB = OPT["OR3"]
FULL = DATASETS["OR3"]
TRAIN = {n: FULL[n] for n in names[:12]}


def excf(fn):
    return (evaluate(FULL, fn) - LB) / LB * 100


def exct(fn):
    return (evaluate(TRAIN, fn) - LB) / LB * 100


# residual r = bins-item; C=150, item in [20,100]; r in (0,20) is DEAD.
BP = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 18, 20, 24, 30, 40, 60], float)
N = len(BP)


def make(vals):
    vals = np.asarray(vals, float)

    def p(item, bins):
        r = bins - item
        idx = np.clip(np.searchsorted(BP, r, side="right") - 1, 0, N - 1)
        return vals[idx]
    return p


base = np.array([6, 3.2, 2.8, 2.4, 2.0, 1.6, 1.2, -1, -1, -0.8, -0.6, -0.4, -0.2,
                 1.10, 1.06, 1.03, 1.00, 0.97], float)
step = np.array([0.6, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.35, 0.35, 0.3, 0.3,
                 0.05, 0.05, 0.04, 0.04, 0.04], float)

best = []  # (full, vec)


def run(seed, iters):
    rng = np.random.default_rng(seed)
    cur = base.copy()
    cf = excf(make(cur))
    for it in range(iters):
        v = cur + rng.normal(0, step)
        f = excf(make(v))
        best.append((f, v.copy()))
        if f < cf:
            cur, cf = v.copy(), f
    print(f"seed {seed} done, best full so far={min(b[0] for b in best):.3f}", flush=True)


for seed in [0, 1, 2, 3, 5, 7]:
    run(seed, 700)

# dedup + rank by full; report train for the top few
best.sort(key=lambda x: x[0])
seen = set()
print("== top by FULL (with train) ==")
shown = 0
for f, v in best:
    k = round(f, 3)
    if k in seen:
        continue
    seen.add(k)
    t = exct(make(v))
    print("  full=%.3f train=%.3f  %s" % (f, t, np.round(v, 2).tolist()))
    shown += 1
    if shown >= 12:
        break
