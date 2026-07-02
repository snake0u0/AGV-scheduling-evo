"""DEMO — LLM-based evolutionary heuristic search on the canonical easy benchmark:
Online Bin Packing (OBP), the FunSearch/EoH flagship problem.

SAME methodology as the AGV project (LLM proposes a scoring expression -> evaluate ->
evolve with fitness + reflection), on a simple, well-understood problem so the method is
easy to demonstrate and defend. Reuses the project's machinery:
  - sim.rule.policy_from_expr  (compile an expression string into score(features)->float)
  - ahd.llm.ClaudeCliLLM       (logged-in `claude` CLI proposer; no API key) + _valid/_extract_json

Heuristic evolved: score(item, remaining, capacity, num_bins) evaluated for each OPEN bin
that can still fit the item; the item goes to the highest-scoring feasible bin, else a new
bin is opened. Objective: minimize the number of bins (lower is better).

Run:  python -m demo.bpp            (uses claude if available, else a mock proposer)
      DEMO_LLM=0 python -m demo.bpp (force mock, free)
"""
import os, sys, json, random, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.rule import policy_from_expr
from ahd.llm import ClaudeCliLLM, _extract_json, _valid, cli_available

CAP = 1.0
FEATURES = {"item", "remaining", "capacity", "num_bins"}
# classical seeds expressible in the grammar
SEEDS = [
    "-remaining",                 # Best-Fit  (tightest bin)
    "remaining",                  # Worst-Fit (loosest bin)
    "-(remaining - item)",        # Best-Fit gap
    "-remaining + 0.1*item",      # BF variant
]
TRAIN = list(range(0, 16))
VALID = list(range(16, 20))
TEST = list(range(20, 24))

_SYSTEM = """You design a priority rule for ONLINE BIN PACKING (bin capacity=1.0).
Items arrive one at a time; each must be placed immediately. For each OPEN bin that can still
fit the item, your rule scores it; the item goes to the HIGHEST-scoring feasible bin. If no open
bin fits, a NEW bin is opened. Goal: MINIMIZE the total number of bins used.
Score features (all numeric): item (its size), remaining (that bin's remaining capacity),
capacity (=1.0), num_bins (bins opened so far).
GRAMMAR: only those names, numeric constants, + - * / ** %, parentheses, and min(), max(), abs().
One line, no other names. Guard divisions (e.g. / (remaining - item + 0.01)). Keep it short."""


def gen_items(n, seed):
    # Weibull-distributed items (FunSearch-standard OBP benchmark family): skewed, many small
    # items + a few large -> Best-Fit is no longer near-optimal, leaving headroom to improve.
    rng = random.Random(seed)
    items = []
    while len(items) < n:
        v = rng.weibullvariate(0.28, 3.0)      # scale, shape -> mean ~0.25, right-skewed
        if 0.02 < v <= 1.0:
            items.append(round(v, 3))
    return items


def pack(items, score_fn):
    """Greedy online packing under score_fn; returns number of bins used."""
    bins = []  # remaining capacities
    for it in items:
        best_i, best_s = -1, -1e18
        for i, r in enumerate(bins):
            if r + 1e-9 >= it:
                try:
                    s = score_fn({"item": it, "remaining": r, "capacity": CAP, "num_bins": len(bins)})
                    s = s if isinstance(s, (int, float)) else -1e18
                except Exception:
                    s = -1e18
                if s > best_s:
                    best_s, best_i = s, i
        if best_i >= 0:
            bins[best_i] -= it
        else:
            bins.append(CAP - it)
    return len(bins)


def fitness(expr, seeds, n_items=200):
    """Mean bins-used / lower-bound over instances (>=1; lower is better)."""
    fn = policy_from_expr(expr)
    ratios = []
    for s in seeds:
        items = gen_items(n_items, s)
        lb = max(1.0, sum(items) / CAP)
        ratios.append(pack(items, fn) / lb)
    return statistics.mean(ratios)


# ---- proposers (same interface style as the AGV loop) ----
class MockBPP:
    def __init__(self, seed=0):
        self.rng = random.Random(seed)
    def vary(self, elites, k):
        kids = []
        for _ in range(k):
            base = self.rng.choice([e for e, _ in elites])
            tweak = self.rng.choice([" + 0.1*item", " - 0.1*item", " * (1 + 0.05*num_bins)",
                                     " / (remaining - item + 0.01)"])
            kids.append(f"({base}){tweak}")
        return kids


class LLMBPP:
    def __init__(self):
        self.cli = ClaudeCliLLM()
    def vary(self, elites, k):
        ranked = "\n".join(f"{i+1}. bins/LB={fit:.3f}  score = {e}" for i, (e, fit) in enumerate(elites))
        prompt = (f"Current best rules, ranked best first (bins/LB, lower is better):\n{ranked}\n\n"
                  f"First reflect in one sentence on what the better rules do, then propose {k} NEW "
                  f"score expressions predicted to use FEWER bins. Explore nonlinear forms. "
                  f'Return ONLY single-line JSON: {{"reflection":"...","offspring":["<expr>", ...]}} '
                  f"with exactly {k} expressions.")
        text = self.cli._complete(_SYSTEM + "\n\n" + prompt)
        try:
            return list(_extract_json(text)["offspring"])
        except Exception:
            return []
    def usage(self):
        return self.cli.usage()


def evolve_bpp(proposer, seeds, gens=8, pop=12, elite=4, n_items=200, verbose=True):
    pool = SEEDS[:]
    scored = [(e, fitness(e, seeds, n_items)) for e in pool]
    for g in range(gens):
        scored.sort(key=lambda x: x[1])
        elites = scored[:elite]
        kids = [e for e in proposer.vary(elites, pop - elite) if _valid(e, FEATURES)]
        while len(kids) < pop - elite:
            kids.append(elites[len(kids) % len(elites)][0])
        scored = elites + [(e, fitness(e, seeds, n_items)) for e in kids]
        if verbose:
            b = min(scored, key=lambda x: x[1])
            print(f"gen {g:>2}: best bins/LB = {b[1]:.4f}   {b[0]}")
    scored.sort(key=lambda x: x[1])
    return [e for e, _ in scored[:elite]]


def main():
    use_llm = cli_available() and os.environ.get("DEMO_LLM") != "0"
    proposer = LLMBPP() if use_llm else MockBPP()
    tag = "CLAUDE-CLI" if use_llm else "MOCK"
    print(f"OBP demo | proposer={tag} | {len(TRAIN)} train / {len(VALID)} valid / {len(TEST)} test instances\n")

    bf = fitness("-remaining", TEST)                       # Best-Fit baseline
    wf = fitness("remaining", TEST)                        # Worst-Fit baseline
    print(f"baseline Best-Fit  bins/LB(test) = {bf:.4f}")
    print(f"baseline Worst-Fit bins/LB(test) = {wf:.4f}\n")

    elites = evolve_bpp(proposer, TRAIN, gens=int(os.environ.get("DEMO_GEN", "10")))
    sel = min(elites, key=lambda e: fitness(e, VALID))     # select on valid
    ev = fitness(sel, TEST)                                # report on test
    print(f"\nevolved rule (best on valid) | bins/LB(test) = {ev:.4f}  "
          f"({(bf - ev) / bf * 100:+.1f}% vs Best-Fit)")
    print(f"  rule: {sel}")
    if use_llm:
        print(proposer.usage())


if __name__ == "__main__":
    main()
