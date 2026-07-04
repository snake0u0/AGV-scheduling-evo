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
        print(f"{label}: COMPILE FAIL")
        return None
    t = exc(fn, train)
    v = exc(fn, valid)
    te = exc(fn, test)
    f = exc(fn, names)
    w = (evaluate(DATASETS["Weibull 5k"], fn) - OPT["Weibull 5k"]) / OPT["Weibull 5k"] * 100
    print(f"{label:14s} train={t:6.3f}  valid={v:6.3f}  test={te:6.3f}  FULL={f:6.3f}  Weib={w:6.3f}")
    return f


if __name__ == "__main__":
    import sys, json
    # candidates provided as a python file exposing CANDS = [(label, code), ...]
    from demo._cands_bpp import CANDS
    print("baseline v0 full=2.957 train=3.545 | goal: beat these")
    for label, code in CANDS:
        score(code, label)
