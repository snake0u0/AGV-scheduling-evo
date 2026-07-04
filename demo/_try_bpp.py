import numpy as np
from demo.bpp import DATASETS, OPT, evaluate, compile_priority

names = list(DATASETS["OR3"].keys())
train = names[:12]

def exc(code, subset=None):
    fn = compile_priority(code)
    if fn is None:
        return None
    if subset is None:
        avg = evaluate(DATASETS["OR3"], fn)
    else:
        avg = evaluate({n: DATASETS["OR3"][n] for n in subset}, fn)
    return (avg - OPT["OR3"]) / OPT["OR3"] * 100

V0 = '''def priority(item, bins):
    r = bins - item
    s = np.minimum(r, 30.0) * 0.001
    s[r <= 8] = -1.0
    s[r <= 6] = 3.0 - 0.4 * r[r <= 6]
    return s'''

V1 = '''def priority(item, bins):
    r = bins - item
    s = np.full(len(bins), 0.99)
    s[r <= 20] = 0.98
    s[r <= 9] = 0.90
    s[r <= 7] = 1.0
    s[r <= 5] = 2.0
    s[r <= 3] = 3.0
    s[r <= 2] = 4.0
    return s'''

if __name__ == "__main__":
    for n, c in [("v0", V0), ("v1", V1)]:
        print(f"{n}: full={exc(c):.3f}%  train={exc(c, train):.3f}%")
