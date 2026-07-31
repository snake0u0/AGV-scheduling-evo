"""The LLM-AHD joint evolution loop.

Evolve (agv_genome, machine_genome) pairs against the simulator, ranked by mean
tardiness. Engine-agnostic and proposer-agnostic: pass any engine `simulate` with
the signature simulate(config, agv_policy, seed, machine_policy=...) and any
proposer exposing seed_population(n) / vary(elites, k). See skill `ahd-loop`.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.rule import policy_from_expr
from ahd.llm import render


def fitness(pair, config, seeds, simulate):
    """Mean tardiness over seeds for a (agv_genome, machine_genome) pair (lower better)."""
    ap = policy_from_expr(render(pair[0]))
    mp = policy_from_expr(render(pair[1]))
    vals = [simulate(config, ap, seed=s, machine_policy=mp)["mean_tardiness"] for s in seeds]
    return sum(vals) / len(vals)


def evolve(config, seeds, proposer, simulate, pop_size=12, generations=10, elite=4, verbose=True):
    """Run the loop. Returns (best_pair, best_fitness, history, final_elites).

    final_elites is the top-`elite` pairs by TRAIN fitness; the caller re-ranks them
    on a held-out validation split to pick the reported rule (avoids train overfit).
    """
    pop = proposer.seed_population(pop_size)
    scored = [(p, fitness(p, config, seeds, simulate)) for p in pop]
    history = []
    for gen in range(generations):
        scored.sort(key=lambda x: x[1])
        elites_scored = scored[:elite]                 # [(pair, fitness)] best-first (for ReEvo signal)
        kids = proposer.vary(elites_scored, pop_size - elite)
        scored = ([(p, f) for p, f in scored[:elite]] +
                  [(k, fitness(k, config, seeds, simulate)) for k in kids])
        best = min(scored, key=lambda x: x[1])
        history.append(best[1])
        if verbose:
            print(f"gen {gen:>2}: best mean_tardiness = {best[1]:7.3f}   "
                  f"AGV[{render(best[0][0])}]  M[{render(best[0][1])}]")
    scored.sort(key=lambda x: x[1])
    final_elites = [p for p, _ in scored[:elite]]
    return scored[0][0], scored[0][1], history, final_elites
