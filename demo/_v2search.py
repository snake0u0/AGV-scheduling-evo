import numpy as np, time
from demo.bpp import DATASETS, OPT, evaluate

names = list(DATASETS["OR3"].keys()); LB = OPT["OR3"]
TR = {n: DATASETS["OR3"][n] for n in names[:12]}
VA = {n: DATASETS["OR3"][n] for n in names[12:16]}
TE = {n: DATASETS["OR3"][n] for n in names[16:20]}
FULL = DATASETS["OR3"]; WEIB = DATASETS["Weibull 5k"]; WLB = OPT["Weibull 5k"]
def ex(sub, fn): return (evaluate(sub, fn) - LB) / LB * 100
def exW(fn): return (evaluate(WEIB, fn) - WLB) / WLB * 100

# master family: closing reward [0,gclose], dead valley (gclose,gdead], tail for r>gdead
def make(p):
    A, B, gclose, pen, gdead, slope, off, exact = p
    def pr(item, bins):
        r = bins - item
        s = off + slope * np.minimum(r, 60.0)
        m = r <= gdead; s[m] = pen
        m = r <= gclose; s[m] = A - B * r[m]
        s[r == 0] = exact
        return s
    return pr

# search bounds
lo = np.array([2.0, 0.05, 3.0, -3.0, 8.0, -0.02, 0.0, 4.0])
hi = np.array([9.0, 0.60, 9.0,  0.5, 22.0, 0.02, 1.0, 60.0])

def clip(p): return np.minimum(np.maximum(p, lo), hi)

rng = np.random.default_rng(0)
pool = []
t0 = time.time()
# random search
for it in range(400):
    p = lo + rng.random(8) * (hi - lo)
    t = ex(TR, make(p))
    pool.append((t, p))
pool.sort(key=lambda x: x[0])
print("after random: best train=%.3f  (%.1fs)" % (pool[0][0], time.time()-t0), flush=True)

# hill-climb from top 8 seeds
seeds = [p for _, p in pool[:8]]
scale = (hi - lo) * 0.06
for si, seed in enumerate(seeds):
    cur = seed.copy(); ct = ex(TR, make(cur))
    for it in range(250):
        v = clip(cur + rng.normal(0, scale))
        t = ex(TR, make(v))
        pool.append((t, v))
        if t < ct: cur, ct = v, t
    print("  hc seed %d -> train=%.3f  (%.1fs)" % (si, ct, time.time()-t0), flush=True)

pool.sort(key=lambda x: x[0])
seen = set(); best = []
for t, p in pool:
    k = round(t, 3)
    if k in seen: continue
    seen.add(k); best.append((t, p))
    if len(best) >= 25: break

print("\n== top distinct by train (train/FULL/valid/test/weib) ==")
for t, p in best:
    fn = make(p)
    f = ex(FULL, fn)
    star = "  <== beats v0" if (f < 2.957 and t < 3.545) else ""
    print("train=%.3f FULL=%.3f valid=%.3f test=%.3f weib=%.3f%s\n   p=%s"
          % (t, f, ex(VA, fn), ex(TE, fn), exW(fn), star, np.round(p, 3).tolist()))
