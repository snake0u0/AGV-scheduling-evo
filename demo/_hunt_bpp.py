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


# residual r = bins-item. min item=20 => r in (0,20) is DEAD (unfillable), r==0 perfect, r>=20 usable.
BP = np.array([0, 1, 2, 4, 6, 8, 10, 13, 16, 20, 24, 28, 34, 42, 55, 75])
N = len(BP)


def make(vals):
    vals = np.asarray(vals, float)
    def p(item, bins):
        r = bins - item
        idx = np.clip(np.searchsorted(BP, r, side="right") - 1, 0, N - 1)
        return vals[idx]
    return p


def run(seed, base, step, iters, w):
    rng = np.random.default_rng(seed)
    cur = base.copy()
    ct, cf = sc(make(cur))
    obj = lambda t, f: w * t + f
    pool = []
    for it in range(iters):
        v = cur + rng.normal(0, step)
        t, f = sc(make(v))
        pool.append((t, f, v.copy()))
        if obj(t, f) < obj(ct, cf):
            cur, ct, cf = v.copy(), t, f
        if it % 500 == 0:
            pool.sort(key=lambda x: obj(x[0], x[1]))
            cur, ct, cf = pool[0][2].copy(), pool[0][0], pool[0][1]
    return pool


# best-fit-ish descending base; usable zone slightly above dead zone
base = np.array([5, 3.5, 3.0, 2.5, 2.0, 1.6, 1.2, 0.8, 0.4,
                 1.10, 1.05, 1.02, 1.00, 0.98, 0.96, 0.94])
step = np.array([0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.35, 0.35,
                 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04])

allpool = []
for seed, w in [(0, 1.0), (1, 1.0), (2, 0.5), (3, 2.0), (4, 1.0)]:
    allpool += run(seed, base, step, 2000, w)

# rank by full, and separately by train
def show(pool, key, label, k=12):
    pool = sorted(pool, key=key)
    seen = set()
    print(label)
    n = 0
    for t, f, v in pool:
        kk = (round(t, 3), round(f, 3))
        if kk in seen:
            continue
        seen.add(kk)
        print("  train=%.3f full=%.3f  %s" % (t, f, np.round(v, 3).tolist()))
        n += 1
        if n >= k:
            break


show(allpool, lambda x: (x[1], x[0]), "== best by FULL ==")
show(allpool, lambda x: (x[0], x[1]), "== best by TRAIN ==")
print("BP =", BP.tolist())
