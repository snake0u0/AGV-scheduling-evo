"""B2 baseline — tree-based GP hyper-heuristic that JOINTLY evolves an AGV rule + a machine rule
as expression trees over the same feature interface as P. Standalone (no LLM, CPU-only); produces
(agv_expr, machine_expr) strings that plug into the same evaluator. Fitness = mean tardiness on
TRAIN; final selection on VALID — matching P's protocol so B2 vs P is a fair AHD-vs-AHD comparison.

This is a self-contained GP (DEAP-equivalent): tree = nested tuple, subtree crossover + mutation,
tournament selection, elitism. Grammar matches sim/rule.py (only +-*/, min, max, features, consts).
"""
import random
from sim.agv_fms import simulate
from sim.rule import policy_from_expr

BINOPS = ["+", "-", "*", "/"]
FUNCS = ["min", "max"]
CONSTS = [0.1, 0.3, 0.5, 1.0, 2.0]
FEATURES_AGV = ["travel_time", "task_wait", "slack", "downstream_load", "congestion", "deadhead", "battery_soc"]
FEATURES_M = ["proc_time", "slack", "job_wait", "remaining_ops", "remaining_proc", "downstream_load"]


# ---- tree = ('op',sym,l,r) | ('fn',sym,a,b) | ('term',name) | ('const',val) ----
def rand_tree(terms, rng, depth=0, max_depth=4):
    if depth >= max_depth or (depth > 0 and rng.random() < 0.3):
        if rng.random() < 0.75:
            return ("term", rng.choice(terms))
        return ("const", round(rng.choice(CONSTS) * rng.choice([-1, 1]), 3))
    if rng.random() < 0.7:
        return ("op", rng.choice(BINOPS),
                rand_tree(terms, rng, depth + 1, max_depth), rand_tree(terms, rng, depth + 1, max_depth))
    return ("fn", rng.choice(FUNCS),
            rand_tree(terms, rng, depth + 1, max_depth), rand_tree(terms, rng, depth + 1, max_depth))


def to_expr(t):
    k = t[0]
    if k == "term":
        return t[1]
    if k == "const":
        return f"{t[1]:.3f}"
    if k == "op":
        return f"({to_expr(t[2])} {t[1]} {to_expr(t[3])})"
    return f"{t[1]}({to_expr(t[2])}, {to_expr(t[3])})"     # fn


def _nodes(t, acc=None):
    """Pre-order list of all subtrees (for choosing a crossover/mutation point)."""
    acc = acc if acc is not None else []
    acc.append(t)
    if t[0] in ("op", "fn"):
        _nodes(t[2], acc)
        _nodes(t[3], acc)
    return acc


def _replace(t, target_idx, newsub, counter=None):
    """Return a copy of t with the pre-order node at target_idx replaced by newsub."""
    counter = counter if counter is not None else [0]
    here = counter[0]
    counter[0] += 1
    if here == target_idx:
        return newsub
    if t[0] in ("op", "fn"):
        l = _replace(t[2], target_idx, newsub, counter)
        r = _replace(t[3], target_idx, newsub, counter)
        return (t[0], t[1], l, r)
    return t


def crossover(a, b, rng):
    ai = rng.randrange(len(_nodes(a)))
    bnodes = _nodes(b)
    sub = bnodes[rng.randrange(len(bnodes))]
    return _replace(a, ai, sub)


def mutate(t, terms, rng):
    idx = rng.randrange(len(_nodes(t)))
    return _replace(t, idx, rand_tree(terms, rng, depth=0, max_depth=3))


# ---- evaluation ----
def _fitness(ind, config, seeds):
    ap = policy_from_expr(to_expr(ind[0]))
    mp = policy_from_expr(to_expr(ind[1]))
    try:
        vals = [simulate(config, ap, seed=s, machine_policy=mp)["mean_tardiness"] for s in seeds]
    except Exception:
        return 1e9
    return sum(vals) / len(vals)


def _vary_ind(ind, rng):
    a, m = ind
    if rng.random() < 0.5:                       # crossover within elites handled by caller; here mutate
        a = mutate(a, FEATURES_AGV, rng)
    if rng.random() < 0.5:
        m = mutate(m, FEATURES_M, rng)
    return (a, m)


def gp_evolve(config, train, valid, generations=15, pop_size=30, elite=4, seed=0, verbose=False):
    rng = random.Random(seed)
    # seed population of (agv_tree, machine_tree)
    pop = [(rand_tree(FEATURES_AGV, rng), rand_tree(FEATURES_M, rng)) for _ in range(pop_size)]
    scored = [(ind, _fitness(ind, config, train)) for ind in pop]
    for gen in range(generations):
        scored.sort(key=lambda x: x[1])
        elites = [ind for ind, _ in scored[:elite]]
        kids = []
        while len(kids) < pop_size - elite:
            if len(elites) >= 2 and rng.random() < 0.5:        # subtree crossover between two elites
                pa, pb = rng.sample(elites, 2)
                child = (crossover(pa[0], pb[0], rng), crossover(pa[1], pb[1], rng))
            else:
                child = _vary_ind(rng.choice(elites), rng)     # mutation
            kids.append(child)
        scored = ([(ind, f) for ind, f in scored[:elite]] +
                  [(k, _fitness(k, config, train)) for k in kids])
        if verbose:
            best = min(scored, key=lambda x: x[1])
            print(f"  gp gen {gen:>2}: best train tardiness = {best[1]:.2f}")
    # final selection on VALID among elites (avoid train overfit)
    scored.sort(key=lambda x: x[1])
    final = [ind for ind, _ in scored[:elite]]
    best = min(final, key=lambda ind: _fitness(ind, config, valid))
    return to_expr(best[0]), to_expr(best[1])
