"""Experiment harness for the constructive (search-free) regime.

A genome is a *bundle*: one scoring rule per subproblem, for all four
`simulator.dispatch.SLOTS` at once. Every bundle is evaluated by a single
constructive pass per instance - no metaheuristic wraps it - so the rules alone
decide the schedule and the fitness is deterministic.

Train and test splits are disjoint, so an evolved bundle is never reported on the
instances it was tuned on.
"""
from statistics import mean

from simulator.dispatch import build as dispatch_build
from simulator.instance import DAUZERE_STEMS, load_dauzere
from .rules import rule_from_expr

DEADLOCK_PENALTY = 1e9


def evaluate_bundle(bundle_expr, instances):
    """Mean Cmax of a {slot: expr} bundle across `instances`, one constructive pass
    each. `instances` is a list of (stem, vehicles). Lower is better.

    There is no seeds parameter: the sandbox in rule_from_expr exposes no randomness
    and no search is wrapped around the build, so a bundle's Cmax on a given instance
    is deterministic - there is nothing to average over.

    A bundle that deadlocks (e.g. every candidate scores -inf, which LLM-proposed
    rules can do by overusing NEVER) takes a large fixed penalty instead of crashing
    the campaign.
    """
    slots = {slot: rule_from_expr(expr) for slot, expr in bundle_expr.items()}
    vals = []
    for stem, veh in instances:
        inst = load_dauzere(stem, veh)
        try:
            _, sched = dispatch_build(inst, slots)
            vals.append(sched.cmax)
        except Exception:
            vals.append(DEADLOCK_PENALTY)
    return mean(vals)


def evolve_bundle(proposer, train, pop_size=20, n_gens=6, log=print, record=None):
    """ReEvo-style outer loop over bundles: seed a population, evaluate each on the
    train split, keep the best as elites, ask the proposer to vary them.

    Returns (best_bundle, best_fitness, history), where `history` tracks the running
    best per generation. Pass a list as `record` to also collect every generation's
    full population, which is what makes a run auditable afterwards:
        {"gen": int, "population": [{"bundle", "fitness", "origin"}, ...]}
    with origin "seed" / "elite" / "child", plus the proposer's prompt, reply,
    reflection, parents and rejected candidates under "call".
    """
    seen = {}

    def key(bundle):
        return tuple(sorted(bundle.items()))

    def fit(bundle):
        # Proposers repeat bundles - seed_population pads by repeating its seeds, and
        # the LLM re-proposes surviving elites - so memoise or the same build runs
        # several times for an identical answer.
        k = key(bundle)
        if k not in seen:
            seen[k] = evaluate_bundle(bundle, train)
        return seen[k]

    def snapshot(bundles, origin):
        return [{"bundle": b, "fitness": f, "origin": origin} for b, f in bundles]

    population = [(b, fit(b)) for b in proposer.seed_population(pop_size)]
    population.sort(key=lambda x: x[1])
    best = population[0]
    history = [best[1]]
    if record is not None:
        record.append({"gen": 0, "population": snapshot(population, "seed")})
    log(f"gen 0: best={best[1]:.1f}  bundle={best[0]}")

    for g in range(1, n_gens + 1):
        n_elite = max(2, pop_size // 4)
        elites = population[:n_elite]
        kids = proposer.vary(elites, pop_size - n_elite)
        scored_kids = [(b, fit(b)) for b in kids]
        population = sorted(elites + scored_kids, key=lambda x: x[1])
        if population[0][1] < best[1]:
            best = population[0]
        history.append(best[1])
        if record is not None:
            entry = {"gen": g,
                     "population": snapshot(elites, "elite") + snapshot(scored_kids, "child")}
            call = getattr(proposer, "last_call", None)
            if call:
                entry["call"] = call
            record.append(entry)
        log(f"gen {g}: best={best[1]:.1f}  bundle={best[0]}")

    return best[0], best[1], history


def default_split():
    """Train on three instances spanning the machine sizes (5/8/10); test on the rest.
    Two vehicles only, to keep the campaign small and comparable."""
    train = [("01a", 2), ("07a", 2), ("13a", 2)]
    test = [(s, 2) for s in DAUZERE_STEMS if (s, 2) not in train]
    return train, test
