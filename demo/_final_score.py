import numpy as np
from demo.bpp import DATASETS, OPT, evaluate, compile_priority

names = list(DATASETS["OR3"].keys())
train, valid, test = names[:12], names[12:16], names[16:20]
LB = OPT["OR3"]

def exc(fn, subset):
    sub = {n: DATASETS["OR3"][n] for n in subset}
    return (evaluate(sub, fn) - LB) / LB * 100

def score(code, label=""):
    fn = compile_priority(code)
    if fn is None:
        print(f"{label:6s}: COMPILE/SMOKE FAIL"); return
    t = exc(fn, train); v = exc(fn, valid); te = exc(fn, test); f = exc(fn, names)
    w = (evaluate(DATASETS["Weibull 5k"], fn) - OPT["Weibull 5k"]) / OPT["Weibull 5k"] * 100
    star = "  <-- beats v0" if (f < 2.957 and t < 3.545) else ""
    print(f"{label:6s} train={t:6.3f} valid={v:6.3f} test={te:6.3f} FULL={f:6.3f} Weib={w:6.3f}{star}")

if __name__ == "__main__":
    from demo._final_cands import CANDS
    print("baseline v0: FULL=2.957 train=3.545 (want train<3.545 AND FULL<2.957)")
    for label, code in CANDS:
        score(code, label)
