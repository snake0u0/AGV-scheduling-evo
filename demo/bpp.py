"""DEMO — FunSearch-style LLM program search on Online Bin Packing (OBP).

Faithful (simplified) reproduction of the bin-packing experiment in FunSearch
(Romera-Paredes et al., Nature 2024, "Mathematical discoveries from program search with LLMs"):
the LLM evolves a Python PROGRAM (a `heuristic(item, bins)` numpy function), not a single-line
expression. Items are packed online into the bin with the highest heuristic score among bins that
still fit; objective = fraction of EXCESS bins over the lower bound (lower is better). Evolution
starts from Best-Fit, exactly as in the paper.

Simplifications vs the paper (see docs/reports report for the full comparison):
  - simple elite pool + best-shot prompt, NOT the island model / programs database
  - ~10 LLM samples, NOT ~1e6; single instance size for evolution
  - model = logged-in `claude` CLI (Haiku by default here), NOT Codey/PaLM2

Run:  python -m demo.bpp            (uses claude if available, else a mock proposer)
      DEMO_LLM=0 python -m demo.bpp (force mock, free)
"""
import os, sys, re, math, random, statistics
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ahd.llm import ClaudeCliLLM, cli_available

CAP = 1.0
MODEL = os.environ.get("DEMO_MODEL", "haiku")     # FunSearch used Codey; here Haiku via the CLI
N_TRAIN_ITEMS = 200
N_TEST_ITEMS = 500                                 # larger -> tests generalization (FunSearch-style)
TRAIN = list(range(0, 12))
VALID = list(range(12, 16))
TEST = list(range(20, 24))

# FunSearch starts from Best-Fit. Baselines expressed as heuristic programs (with docstrings, as in the paper).
BEST_FIT = ('def heuristic(item, bins):\n'
            '    """Best-Fit: prefer the bin with the least remaining capacity that still fits."""\n'
            '    return -(bins - item)')
WORST_FIT = ('def heuristic(item, bins):\n'
             '    """Worst-Fit: prefer the bin with the most remaining capacity."""\n'
             '    return bins')

_SYSTEM = """You improve a Python heuristic for ONLINE BIN PACKING (bin capacity = 1.0).

The packing skeleton (FIXED, you do not change it) is:
    for item in items:
        cand = [remaining capacity of each open bin that still fits item] + [1.0]  # last = a FRESH empty bin
        scores = heuristic(item, np.array(cand))
        place item in cand[argmax(scores)]      # if that is the last (fresh) entry, a NEW bin is opened

So `bins` passed to your heuristic is a numpy array of candidate remaining-capacities whose LAST element
is always a fresh empty bin (capacity 1.0). Your heuristic can therefore CHOOSE to open a new bin (leaving
more space) instead of squeezing the item into a tight existing bin.

def heuristic(item, bins):  -> return a numpy array of scores (same length as bins); highest score wins.
Goal: MINIMIZE the total number of bins used.
You may use numpy as np and the builtins min, max, abs, len, range, sum. No imports, no I/O.
Explore NON-OBVIOUS scoring (nonlinear in bins and item) — the best heuristics do NOT always pick the
tightest bin; sometimes leaving a bin's residual capacity un-tiny (or opening a fresh bin) packs better."""


def gen_items(n, seed):
    """Weibull-distributed items (FunSearch benchmark family): skewed, many small + few large."""
    rng = random.Random(seed)
    items = []
    while len(items) < n:
        v = rng.weibullvariate(0.28, 3.0)
        if 0.02 < v <= 1.0:
            items.append(round(v, 3))
    return items


def compile_heuristic(code):
    """Safely exec an LLM `heuristic` program; return the callable or None if invalid."""
    g = {"__builtins__": {}, "np": np, "min": min, "max": max, "abs": abs,
         "len": len, "range": range, "sum": sum}
    try:
        exec(code, g)
        fn = g["heuristic"]
        s = np.asarray(fn(0.3, np.array([0.4, 0.9, 0.55])), dtype=float)   # smoke-test
        if s.shape != (3,) or not np.all(np.isfinite(s)):
            return None
        return fn
    except Exception:
        return None


def pack(items, fn):
    """Online packing (FunSearch skeleton). Candidates for each item = the open bins that still fit
    PLUS one fresh empty bin (capacity CAP) as the LAST element, so the heuristic may CHOOSE to open
    a new bin. Item -> highest-scoring candidate. Returns #bins used."""
    bins = []
    for it in items:
        idxs = [i for i, r in enumerate(bins) if r + 1e-9 >= it]
        caps = np.array([bins[i] for i in idxs] + [CAP])     # last entry = a fresh empty bin
        try:
            scores = np.asarray(fn(it, caps), dtype=float)
            if scores.shape != caps.shape:
                raise ValueError
            j = int(np.argmax(scores))
        except Exception:
            j = int(np.argmin(caps[:-1])) if idxs else len(caps) - 1   # fallback: best-fit / open new
        if j == len(caps) - 1:
            bins.append(CAP - it)            # heuristic chose to open a new bin
        else:
            bins[idxs[j]] -= it
    return len(bins)


def fitness(code, seeds, n_items):
    """Mean fraction of EXCESS bins over the lower bound (sum/cap); lower is better."""
    fn = compile_heuristic(code)
    if fn is None:
        return 9.99
    exs = []
    for s in seeds:
        items = gen_items(n_items, s)
        lb = sum(items) / CAP
        exs.append(pack(items, fn) / lb - 1.0)
    return statistics.mean(exs)


class MockBPP:
    def __init__(self, seed=0):
        self.rng = random.Random(seed)
    def vary(self, elites, k):
        out = []
        for _ in range(k):
            base = self.rng.choice([c for c, _ in elites])
            # trivial structural tweak (mock only): scale the score
            out.append(base.replace("return ", "return (1.0 + 0.01*item) * (", 1) + ")"
                       if "return (" not in base else base)
        return out


class LLMBPP:
    def __init__(self):
        self.cli = ClaudeCliLLM(model=MODEL, timeout=300)   # Sonnet verbose replies can exceed 180s
    def vary(self, elites, k):
        shown = "\n\n".join(f"# version v{i}  (excess over LB = {fit*100:.2f}%)\n{code}"
                            for i, (code, fit) in enumerate(elites[:2]))
        prompt = (f"{shown}\n\n# The versions above are prior heuristics (lower excess is better).\n"
                  f"Write {k} IMPROVED, DIFFERENT versions of `heuristic` that use FEWER bins.\n"
                  f"Output ONLY the {k} complete functions, each starting with a line "
                  f"'def heuristic(item, bins):', separated by a line '===NEXT==='. No prose, no markdown.")
        text = self.cli._complete(_SYSTEM + "\n\n" + prompt)
        return self._parse(text)
    def _parse(self, text):
        text = re.sub(r"```(?:python)?", "", text)
        out = []
        for block in text.split("===NEXT==="):
            i = block.find("def heuristic")
            if i >= 0:
                out.append(block[i:].strip())
        return out
    def usage(self):
        return self.cli.usage()


def evolve_bpp(proposer, seeds, gens, pop=8, elite=3, n_items=N_TRAIN_ITEMS, verbose=True):
    pool = [BEST_FIT]                                  # start from Best-Fit (as in FunSearch)
    scored = [(c, fitness(c, seeds, n_items)) for c in pool]
    for g in range(gens):
        scored.sort(key=lambda x: x[1])
        elites = scored[:elite] if len(scored) >= 1 else scored
        kids = [c for c in proposer.vary(elites, pop) if compile_heuristic(c) is not None]
        scored = elites + [(c, fitness(c, seeds, n_items)) for c in kids]
        if verbose:
            b = min(scored, key=lambda x: x[1])
            print(f"gen {g:>2}: best excess = {b[1]*100:.3f}%   ({len(kids)} valid kids)")
    scored.sort(key=lambda x: x[1])
    return [c for c, _ in scored[:elite]]


def main():
    use_llm = cli_available() and os.environ.get("DEMO_LLM") != "0"
    proposer = LLMBPP() if use_llm else MockBPP()
    tag = f"CLAUDE-CLI/{MODEL}" if use_llm else "MOCK"
    print(f"OBP (FunSearch-style program search) | proposer={tag} | "
          f"train {len(TRAIN)}x{N_TRAIN_ITEMS} items / test {len(TEST)}x{N_TEST_ITEMS} items\n")

    bf = fitness(BEST_FIT, TEST, N_TEST_ITEMS)
    wf = fitness(WORST_FIT, TEST, N_TEST_ITEMS)
    print(f"baseline Best-Fit  excess(test) = {bf*100:.3f}%")
    print(f"baseline Worst-Fit excess(test) = {wf*100:.3f}%\n")

    elites = evolve_bpp(proposer, TRAIN, gens=int(os.environ.get("DEMO_GEN", "10")))
    sel = min(elites, key=lambda c: fitness(c, VALID, N_TRAIN_ITEMS))    # select on valid
    ev = fitness(sel, TEST, N_TEST_ITEMS)                                # report on test (larger size)
    print(f"\nevolved heuristic (best on valid) | excess(test) = {ev*100:.3f}%  "
          f"({(bf - ev) / bf * 100:+.1f}% relative to Best-Fit)")
    print("--- program ---\n" + sel + "\n---------------")
    if use_llm:
        print(proposer.usage())


if __name__ == "__main__":
    main()
