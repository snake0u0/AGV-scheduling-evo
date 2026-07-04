import numpy as np, time
from demo.bpp import DATASETS, OPT, evaluate

names = list(DATASETS["OR3"].keys()); LB = OPT["OR3"]
TR = {n: DATASETS["OR3"][n] for n in names[:12]}
VA = {n: DATASETS["OR3"][n] for n in names[12:16]}
TE = {n: DATASETS["OR3"][n] for n in names[16:20]}
FULL = DATASETS["OR3"]; WEIB = DATASETS["Weibull 5k"]; WLB = OPT["Weibull 5k"]
def ex(sub, fn): return (evaluate(sub, fn) - LB) / LB * 100
def exW(fn): return (evaluate(WEIB, fn) - WLB) / WLB * 100

# v0-generalized: closing reward [0,gclose], NARROW penalty band (gclose,gpen], worst-fit tail r>gpen
def make(p):
    A, B, gclose, gpen, pen, slope, off, cap = p
    def pr(item, bins):
        r = bins - item
        s = off + slope * np.minimum(r, cap)
        s[r <= gpen] = pen
        m = r <= gclose; s[m] = A - B * r[m]
        return s
    return pr

lo = np.array([2.0, 0.10, 3.0, 5.0, -2.0, -0.006, -0.5, 20.0])
hi = np.array([8.0, 0.60, 8.0, 13.0, 0.2, 0.012, 1.0, 60.0])
def clip(p): return np.minimum(np.maximum(p, lo), hi)

v0p = np.array([3.0, 0.4, 6.0, 8.0, -1.0, 0.001, 0.0, 30.0])
print("v0 sanity: train=%.3f FULL=%.3f" % (ex(TR, make(v0p)), ex(FULL, make(v0p))), flush=True)

rng = np.random.default_rng(1)
pool = [(ex(TR, make(v0p)), v0p.copy())]
t0 = time.time()
for it in range(500):
    p = lo + rng.random(8) * (hi - lo)
    pool.append((ex(TR, make(p)), p))
pool.sort(key=lambda x: x[0])
print("after random: best train=%.3f (%.1fs)" % (pool[0][0], time.time()-t0), flush=True)

seeds = [v0p.copy()] + [p for _, p in pool[:10]]
scale = (hi - lo) * 0.05
for si, seed in enumerate(seeds):
    cur = seed.copy(); ct = ex(TR, make(cur))
    for it in range(300):
        v = clip(cur + rng.normal(0, scale))
        t = ex(TR, make(v))
        pool.append((t, v))
        if t < ct: cur, ct = v, t
    print("  hc %d -> train=%.3f (%.1fs)" % (si, ct, time.time()-t0), flush=True)

pool.sort(key=lambda x: x[0])
seen = set(); best = []
for t, p in pool:
    k = round(t, 3)
    if k in seen: continue
    seen.add(k); best.append((t, p));
    if len(best) >= 30: break

print("\n== top distinct by train (train/FULL/valid/test/weib), * beats v0 ==")
for t, p in best:
    fn = make(p); f = ex(FULL, fn)
    star = "  <== beats v0" if (f < 2.957 and t < 3.545) else ("  (FULL<v0)" if f < 2.957 else "")
    print("train=%.3f FULL=%.3f valid=%.3f test=%.3f weib=%.3f%s\n   p=%s"
          % (t, f, ex(VA, fn), ex(TE, fn), exW(fn), star, np.round(p, 4).tolist()))
