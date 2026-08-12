"""Experiment harness: evolve an AGV rule on a train split, evaluate on a held-out
test split, and compare against the D1/D2 baselines under an identical GA budget.

The only thing that varies between a baseline and an evolved rule is the rule passed
to decode; the GA operators, budget, and seeds are shared, so the comparison is a
clean ablation. Train/test are disjoint so an evolved rule cannot be reported on the
instances it was tuned on.
"""
from statistics import mean, pstdev

from .ga import GA
from simulator.instance import DAUZERE_STEMS, load_dauzere
from .rules import RULES, rule_from_expr


def _as_rule(rule):
    return rule if callable(rule) else rule_from_expr(rule)


def evaluate_rule(rule, instances, pop=40, n_gen=40, seeds=(0,)):
    """Mean best-makespan of the rule across instances, averaged over GA seeds.
    Lower is better. `instances` is a list of (stem, vehicles)."""
    r = _as_rule(rule)
    per_inst = []
    for stem, veh in instances:
        inst = load_dauzere(stem, veh)
        vals = [GA(inst, r, pop_size=pop, n_gen=n_gen, seed=s).run()[0].fitness
                for s in seeds]
        per_inst.append(mean(vals))
    return mean(per_inst)


def evolve(proposer, train, pop_size=20, n_gens=6, ga_pop=40, ga_gen=40,
           seeds=(0,), log=print, record=None):
    """EoH/ReEvo-style outer loop: propose rules, evaluate each on the train split
    via the GA, keep the best as elites, ask the proposer to vary them. Returns
    (best_expr, best_fitness, history).

    `history` keeps only the running best, so the discarded candidates - the ones that
    show what the proposer actually tried - were previously unrecoverable. Pass a list
    as `record` to also collect every generation's full population:
        {"gen": int, "population": [{"expr", "fitness", "origin"}, ...]}
    with origin "seed" / "elite" / "child". EoH stores the same thing as one file per
    generation. Omitting `record` leaves the old behaviour untouched."""
    seen = {}                       # expr -> fitness; the GA is seeded, so this is exact

    def fit(expr):
        # The proposer re-proposes the same expression across generations (observed
        # 2026-08-10: one candidate appeared in three consecutive generations), and
        # seed_population pads by repeating its seeds, so without this the same GA
        # runs several times for an identical answer.
        if expr not in seen:
            seen[expr] = evaluate_rule(expr, train, pop=ga_pop, n_gen=ga_gen, seeds=seeds)
        return seen[expr]

    population = [(e, fit(e)) for e in proposer.seed_population(pop_size)]
    population.sort(key=lambda x: x[1])
    best = population[0]
    history = [best[1]]
    if record is not None:
        record.append({"gen": 0, "population": [
            {"expr": e, "fitness": f, "origin": "seed"} for e, f in population]})
    log(f"gen 0: best={best[1]:.1f}  rule={best[0]}")

    for g in range(1, n_gens + 1):
        n_elite = max(2, pop_size // 4)
        elites = population[:n_elite]
        kids = proposer.vary(elites, pop_size - n_elite)
        scored_kids = [(e, fit(e)) for e in kids]
        population = elites + scored_kids
        population.sort(key=lambda x: x[1])
        if population[0][1] < best[1]:
            best = population[0]
        history.append(best[1])
        if record is not None:
            entry = {"gen": g, "population":
                     [{"expr": e, "fitness": f, "origin": "elite"} for e, f in elites]
                     + [{"expr": e, "fitness": f, "origin": "child"}
                        for e, f in scored_kids]}
            call = getattr(proposer, "last_call", None)
            if call:
                entry["call"] = call     # prompt / reply / reflection / parents / rejected
            record.append(entry)
        log(f"gen {g}: best={best[1]:.1f}  rule={best[0]}")

    return best[0], best[1], history


def compare(rules, instances, pop=100, n_gen=100, seeds=(0, 1, 2), log=print):
    """Compare rules on `instances` under a common GA budget with several seeds.
    rules: dict name -> expr-or-callable. Returns {name: {stem_veh: (mean, std)}}."""
    results = {}
    for name, rule in rules.items():
        r = _as_rule(rule)
        row = {}
        for stem, veh in instances:
            inst = load_dauzere(stem, veh)
            vals = [GA(inst, r, pop_size=pop, n_gen=n_gen, seed=s).run()[0].fitness
                    for s in seeds]
            row[f"{stem}_{veh}"] = (mean(vals), pstdev(vals) if len(vals) > 1 else 0.0)
        results[name] = row
        log(f"{name}: " + "  ".join(f"{k}={v[0]:.0f}" for k, v in row.items()))
    return results


def default_split():
    """Train on three instances spanning the machine sizes (5/8/10); test on the rest.
    Two vehicles only, to keep the first campaign small and comparable."""
    train = [("01a", 2), ("07a", 2), ("13a", 2)]
    test = [(s, 2) for s in DAUZERE_STEMS if (s, 2) not in train]
    return train, test
