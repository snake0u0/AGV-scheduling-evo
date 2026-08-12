"""Record every generation's full population during an LLM evolution run.

Purpose is instrumentation, not measurement. Until now `evolve()` returned only the
running best, so the candidates the proposer actually produced and the loop then threw
away were never written anywhere - the one surviving trace of an evolved rule's
lineage is three hand-copied lines in the 2026-07-24 report. EoH keeps one JSON per
generation for exactly this reason; this run makes ours do the same.

The budget here is deliberately small and is NOT the deployment regime, so the
makespan numbers it prints must not be compared with any campaign result
(2026-08-06: a rule's ranking does not survive a change of regime).

Run:  python experiments/2026-08-10-population_log.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.experiment import evolve
from model.llm import _SYSTEM, ClaudeRuleProposer, LocalProposer
from model.llm_backend import cli_available

TRAIN = [("01a", 2), ("07a", 2)]        # 5- and 8-machine, 2 vehicles

# Sized to the AHD literature rather than to our own past campaigns. FunSearch and
# MCTS-AHD budget T=1000 evaluated heuristics; EoH runs 20x20. Our largest run so far
# was 16x6 = 88 individuals over 6 LLM calls, which is an order of magnitude short of
# the regime those methods were shown to need, so "the loop did not beat D1" has never
# been tested at the scale the claim would require.
#   20 seeds + 65 generations x 15 children = 995 individuals over 65 LLM calls.
EVOLVE_POP, EVOLVE_GEN = 20, 65
MAX_CALLS = 80                          # hard cap; the proposer pads from elites after
GA_POP, GA_GEN, GA_SEEDS = 30, 30, (0,)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "results", "2026-08-10-population_log.json")


def show(gen):
    """One generation, best first, with where each candidate came from."""
    print(f"\n--- generation {gen['gen']} ---")
    for row in sorted(gen["population"], key=lambda r: r["fitness"]):
        print(f"  {row['fitness']:>8.1f}  [{row['origin']:>5}]  {row['expr']}")


def main():
    proposer = (ClaudeRuleProposer(max_calls=MAX_CALLS) if cli_available()
                else LocalProposer())
    n_elite = max(2, EVOLVE_POP // 4)
    print(f"proposer: {type(proposer).__name__}")
    print(f"train={TRAIN}  evolve {EVOLVE_POP}x{EVOLVE_GEN}  "
          f"inner GA {GA_POP}x{GA_GEN} seeds{GA_SEEDS}")
    print(f"individuals: {EVOLVE_POP + EVOLVE_GEN * (EVOLVE_POP - n_elite)}  "
          f"LLM calls: {EVOLVE_GEN}\n", flush=True)

    record = []
    t0 = time.time()
    best_expr, best_fit, history = evolve(
        proposer, TRAIN, pop_size=EVOLVE_POP, n_gens=EVOLVE_GEN,
        ga_pop=GA_POP, ga_gen=GA_GEN, seeds=GA_SEEDS, record=record)
    elapsed = time.time() - t0

    # Every generation is in the JSON; the console gets the two ends plus a digest,
    # because 65 generations x 20 individuals is not readable as a list.
    show(record[0])
    show(record[-1])

    print("\n--- per generation: best / median / distinct exprs ---")
    for gen in record:
        fits = sorted(r["fitness"] for r in gen["population"])
        distinct = len({r["expr"] for r in gen["population"]})
        print(f"  gen {gen['gen']:>2}  best={fits[0]:>8.1f}  "
              f"median={fits[len(fits)//2]:>8.1f}  distinct={distinct}/{len(fits)}")

    all_exprs = {r["expr"] for gen in record for r in gen["population"]}
    print(f"\nindividuals={sum(len(g['population']) for g in record)}  "
          f"distinct expressions={len(all_exprs)}")
    print(f"best: {best_fit:.1f}  {best_expr}")
    print(f"elapsed {elapsed:.0f}s")
    if hasattr(proposer, "usage"):
        print(proposer.usage())

    json.dump({
        "config": {"train": TRAIN, "evolve_pop": EVOLVE_POP, "evolve_gen": EVOLVE_GEN,
                   "ga_pop": GA_POP, "ga_gen": GA_GEN, "ga_seeds": list(GA_SEEDS),
                   "proposer": type(proposer).__name__,
                   "system_prompt": _SYSTEM},   # constant across calls, stored once
        "generations": record,
        "best": {"expr": best_expr, "fitness": best_fit},
        "history": history,
        "elapsed_sec": elapsed,
        "note": "instrumentation run; budget is not the deployment regime",
    }, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
