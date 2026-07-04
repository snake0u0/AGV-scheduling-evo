import numpy as np
from demo.bpp import DATASETS, OPT, evaluate

names = list(DATASETS["OR3"].keys())
LB = OPT["OR3"]
FULL = DATASETS["OR3"]
TRAIN = {n: FULL[n] for n in names[:12]}
VALID = {n: FULL[n] for n in names[12:16]}
TEST  = {n: FULL[n] for n in names[16:20]}
WEIB = DATASETS["Weibull 5k"]; WLB = OPT["Weibull 5k"]

def ex(sub, fn): return (evaluate(sub, fn) - LB) / LB * 100
def exW(fn): return (evaluate(WEIB, fn) - WLB) / WLB * 100

BP = np.array([0,1,2,3,4,5,6,7,8,9,11,13,16,20,24,30,40,55,80], float)
N = len(BP)
def make(vals):
    vals = np.asarray(vals, float)
    def p(item, bins):
        r = bins - item
        idx = np.clip(np.searchsorted(BP, r, side="right") - 1, 0, N - 1)
        return vals[idx]
    return p

base = np.array([6,4,3.4,3.0,2.6,2.2,1.8,1.4,-1,-1,-1,-0.9,-0.7,
                 0.90,0.93,0.96,0.98,0.99,1.00], float)
step = np.array([0.5,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.3,0.3,0.3,0.3,0.3,
                 0.03,0.03,0.03,0.03,0.03,0.03], float)

pool = []
def run(seed, iters=700):
    rng = np.random.default_rng(seed)
    cur = base.copy()
    ct = ex(TRAIN, make(cur))
    for it in range(iters):
        v = cur + rng.normal(0, step)
        t = ex(TRAIN, make(v))
        pool.append((t, v.copy()))
        if t < ct:
            cur, ct = v.copy(), t
        if it % 300 == 0:
            pool.sort(key=lambda x: x[0])
            cur, ct = pool[0][1].copy(), pool[0][0]

for seed in [0,1,2,3,5,7]:
    run(seed)
    print("seed", seed, "done, best train so far=%.3f"%min(p[0] for p in pool), flush=True)

pool.sort(key=lambda x: x[0])
seen=set(); cand=[]
for t,v in pool:
    k=round(t,3)
    if k in seen: continue
    seen.add(k); cand.append((t,v))
    if len(cand)>=40: break

print("BP =", BP.tolist())
print("== top distinct by TRAIN (with full/valid/test/weib), sorted by train+full ==")
rows=[]
for t,v in cand:
    fn=make(v)
    rows.append((t, ex(FULL,fn), ex(VALID,fn), ex(TEST,fn), exW(fn), v))
for t,f,va,te,w,v in sorted(rows, key=lambda r:(r[0]+r[1])):
    print("  train=%.3f full=%.3f valid=%.3f test=%.3f weib=%.3f  %s"%(t,f,va,te,w,np.round(v,2).tolist()))
