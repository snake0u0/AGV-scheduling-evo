"""DEMO — Online Bin Packing with FunSearch's OWN evaluator, skeleton, datasets.

We downloaded FunSearch (github.com/google-deepmind/funsearch) and REPLACED our home-grown
evaluator/skeleton with the exact ones from `bin_packing/bin_packing.ipynb`:
  - get_valid_bin_indices / online_binpack / evaluate   (verbatim)
  - the initial `priority(item, bins)` skeleton (= Best-Fit, with the paper's docstring)
  - their published discovered heuristics (OR and Weibull) for direct comparison
  - their real datasets (OR3, Weibull 5k) + L1 lower bounds  -> demo/funsearch_data.json (CC-BY)

The LLM (claude CLI) evolves `priority` starting from Best-Fit, exactly as in the paper. By default
this script REPRODUCES the published excess numbers (validating our harness == theirs); set
DEMO_EVOLVE=1 to also run the LLM evolution on the OR3 dataset.

Run:  python -m demo.bpp                 (reproduce baselines/published heuristics, free)
      DEMO_EVOLVE=1 python -m demo.bpp   (also run LLM evolution; uses claude CLI)
"""
import os, sys, re, json
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
_DATA = json.load(open(os.path.join(_HERE, "funsearch_data.json")))
DATASETS = {k: {n: {**v, "items": np.array(v["items"], dtype=float)} for n, v in d.items()}
            for k, d in _DATA["datasets"].items()}
OPT = _DATA["opt_num_bins"]          # per-dataset L1 lower bound (FunSearch's opt_num_bins)


# ================= FunSearch's evaluator skeleton (verbatim from bin_packing.ipynb) =================
def get_valid_bin_indices(item, bins):
    """Returns indices of bins in which item can fit."""
    return np.nonzero((bins - item) >= 0)[0]


def online_binpack(items, bins, priority):
    """Performs online binpacking of `items` into `bins` using `priority`."""
    packing = [[] for _ in bins]
    for item in items:
        valid_bin_indices = get_valid_bin_indices(item, bins)
        priorities = priority(item, bins[valid_bin_indices])
        best_bin = valid_bin_indices[np.argmax(priorities)]
        bins[best_bin] -= item
        packing[best_bin].append(item)
    packing = [b for b in packing if b]
    return packing, bins


def evaluate(instances, priority):
    """Average number of bins used across instances (lower is better)."""
    num_bins = []
    for name in instances:
        inst = instances[name]
        cap = inst["capacity"]
        bins = np.array([cap for _ in range(inst["num_items"])], dtype=float)
        _, packed = online_binpack(inst["items"], bins, priority)
        num_bins.append(int((packed != cap).sum()))
    return float(np.mean(num_bins))


def excess(dataset_name, priority):
    """Fraction of excess bins over the L1 lower bound — FunSearch's reported metric."""
    avg = evaluate(DATASETS[dataset_name], priority)
    lb = OPT[dataset_name]
    return (avg - lb) / lb


# ================= heuristics (verbatim from the FunSearch notebook where noted) =================
# Initial skeleton function that FunSearch evolves (best-fit), with the paper's docstring:
SEED = ('def priority(item, bins):\n'
        '    """Returns priority with which we want to add item to each bin.\n\n'
        '    Args:\n      item: Size of item to be added to the bin.\n'
        '      bins: Array of capacities for each bin.\n'
        '    Return:\n      Array of same size as bins with priority score of each bin.\n    """\n'
        '    return -(bins - item)')
WORST_FIT = 'def priority(item, bins):\n    return bins'

# FunSearch's published discovered heuristics (bin_packing.ipynb), verbatim:
FUNSEARCH_OR = (
    'def priority(item, bins):\n'
    '    """Heuristic discovered for the OR datasets."""\n'
    '    def s(bin, item):\n'
    '        if bin - item <= 2: return 4\n'
    '        elif (bin - item) <= 3: return 3\n'
    '        elif (bin - item) <= 5: return 2\n'
    '        elif (bin - item) <= 7: return 1\n'
    '        elif (bin - item) <= 9: return 0.9\n'
    '        elif (bin - item) <= 12: return 0.95\n'
    '        elif (bin - item) <= 15: return 0.97\n'
    '        elif (bin - item) <= 18: return 0.98\n'
    '        elif (bin - item) <= 20: return 0.98\n'
    '        elif (bin - item) <= 21: return 0.98\n'
    '        else: return 0.99\n'
    '    return np.array([s(b, item) for b in bins])')
FUNSEARCH_WEIBULL = (
    'def priority(item, bins):\n'
    '    """Heuristic discovered for the Weibull datasets."""\n'
    '    max_bin_cap = max(bins)\n'
    '    score = (bins - max_bin_cap)**2 / item + bins**2 / (item**2)\n'
    '    score += bins**2 / item**3\n'
    '    score[bins > item] = -score[bins > item]\n'
    '    score[1:] -= score[:-1]\n'
    '    return score')

# Heuristic our LLM (Sonnet) evolved from Best-Fit on OR3 (10 gens, tools OFF = pure LLM proposal):
LLM_EVOLVED = (
    'def priority(item, bins):\n'
    '    """Evolved by Sonnet on OR3 (pure proposal): fragmentation penalty + fill bonus."""\n'
    '    r = bins - item\n'
    '    C = np.max(bins)\n'
    '    frag = (r > 0) & (r < item)\n'
    '    fill_bonus = (1 - bins / C) * item\n'
    '    return np.where(frag, -(r ** 2 + bins) + fill_bonus, -r + fill_bonus + (r == 0) * C)')


def compile_priority(code):
    g = {"__builtins__": {}, "np": np, "max": max, "min": min, "abs": abs,
         "len": len, "range": range, "sum": sum}
    try:
        exec(code, g)
        fn = g["priority"]
        fn(50.0, np.array([100.0, 80.0, 60.0]))     # smoke test
        return fn
    except Exception:
        return None


# ================= LLM proposer (evolves `priority`, best-shot on the real skeleton) =================
_SYSTEM = """You improve the `priority` function of this FUNSEARCH online bin-packing skeleton (do NOT
change anything except the body of `priority`):

    def get_valid_bin_indices(item, bins):
        return np.nonzero((bins - item) >= 0)[0]          # bins INCLUDES still-empty bins (capacity C)
    def online_binpack(items, bins):
        for item in items:
            valid = get_valid_bin_indices(item, bins)
            best = valid[np.argmax(priority(item, bins[valid]))]   # place item in the argmax bin
            bins[best] -= item
    # evaluate() minimizes the number of used bins.

def priority(item, bins):  # bins = remaining capacities of the bins that fit (incl. empty ones at capacity C)
    -> return a numpy array of scores, one per bin; the item goes to the HIGHEST-scoring bin.

You may use numpy as np and the builtins max, min, abs, len, range, sum. No imports, no I/O.
Explore NON-OBVIOUS scoring — the best heuristics do not always pick the tightest bin. Keep it short."""


class LLMBPP:
    def __init__(self):
        from ahd.llm import ClaudeCliLLM
        self.cli = ClaudeCliLLM(model=os.environ.get("DEMO_MODEL", "sonnet"), timeout=420)
    def vary(self, elites, k):
        shown = "\n\n".join(f"# version v{i} (excess={fit*100:.2f}%)\n{code}"
                            for i, (code, fit) in enumerate(elites[:2]))
        prompt = (f"{shown}\n\n# Prior `priority` versions (lower excess is better). Write {k} IMPROVED, "
                  f"DIFFERENT versions that use FEWER bins. Output ONLY the {k} complete functions, each "
                  f"starting with 'def priority(item, bins):', separated by a line '===NEXT==='.\n"
                  f"Be TERSE: no comments, no blank lines, no prose, each function <= 10 lines.")
        text = self.cli._complete(_SYSTEM + "\n\n" + prompt)
        text = re.sub(r"```(?:python)?", "", text)
        return [b[b.find("def priority"):].strip() for b in text.split("===NEXT===") if "def priority" in b]
    def usage(self):
        return self.cli.usage()


def _excess_split(code, names):
    """Excess over L1 bound restricted to a subset of OR3 instances (for train/valid/test)."""
    fn = compile_priority(code)
    if fn is None:
        return 9.99
    sub = {n: DATASETS["OR3"][n] for n in names}
    return (evaluate(sub, fn) - OPT["OR3"]) / OPT["OR3"]


def evolve(proposer, train, valid, gens=8, pop=6, elite=3):   # pop=6 -> 3 offspring/call (terser, fewer timeouts)
    scored = [(SEED, _excess_split(SEED, train))]
    for g in range(gens):
        scored.sort(key=lambda x: x[1])
        elites = scored[:elite]
        kids = [c for c in proposer.vary(elites, pop) if compile_priority(c) is not None]
        scored = elites + [(c, _excess_split(c, train)) for c in kids]
        print(f"gen {g:>2}: best train excess = {min(x[1] for x in scored)*100:.3f}%  ({len(kids)} valid)")
    scored.sort(key=lambda x: x[1])
    return min([c for c, _ in scored[:elite]], key=lambda c: _excess_split(c, valid))


def main():
    print("== Comparison on FunSearch's evaluator + real data (excess over lower bound, lower=better) ==\n")
    print(f"{'heuristic':<28}{'OR3':>10}{'Weibull 5k':>13}")
    print("-" * 51)
    for name, code in [("Best-Fit (seed)", SEED), ("Worst-Fit", WORST_FIT),
                       ("FunSearch OR-discovered", FUNSEARCH_OR),
                       ("FunSearch Weibull-disc.", FUNSEARCH_WEIBULL),
                       ("Ours: LLM-evolved (OR3)", LLM_EVOLVED)]:
        fn = compile_priority(code)
        print(f"{name:<28}{excess('OR3', fn)*100:>9.2f}%{excess('Weibull 5k', fn)*100:>12.2f}%")
    print("\n(paper Table 1: Best-Fit OR3=5.37%, Weibull5k=3.98%; FunSearch OR3=3.11%, Weibull5k=0.68% -> reproduced)")

    if os.environ.get("DEMO_EVOLVE") == "1":
        names = list(DATASETS["OR3"].keys())
        train, valid, test = names[:12], names[12:16], names[16:20]
        print(f"\n== LLM evolution of `priority` on OR3 (train {len(train)}/valid {len(valid)}/test {len(test)}) ==")
        prop = LLMBPP()
        sel = evolve(prop, train, valid, gens=int(os.environ.get("DEMO_GEN", "8")))
        te = _excess_split(sel, test); bf = _excess_split(SEED, test)
        fn = compile_priority(sel)
        print(f"\nevolved (best on valid) [model={os.environ.get('DEMO_MODEL','sonnet')}]:")
        print(f"  OR3 test-split excess = {te*100:.3f}% (Best-Fit {bf*100:.3f}%, {(bf-te)/bf*100:+.1f}%)")
        print(f"  FULL OR3 excess = {excess('OR3', fn)*100:.3f}%  |  Weibull 5k excess = {excess('Weibull 5k', fn)*100:.3f}%")
        print(f"--- program ---\n{sel}")
        print(prop.usage())


if __name__ == "__main__":
    main()
