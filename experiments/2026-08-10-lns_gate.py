"""Stage 3 gate: does LNS over the four slots match the tuned GA at the same budget?

Same protocol as 2026-08-01b so the numbers are directly comparable: the same 8 cases,
seeds (0, 21, 42), 600s wall-clock per run. The GA side of that comparison is read from
its stored result rather than re-run.

The bar is "not meaningfully worse", not "wins". LNS is not here for speed - 2026-08-01
and 2026-08-06 both rejected that case, because matching population to the budget kept
closing the GA's gap. It is here because destroy becomes a fifth slot for the LLM to
evolve. But if LNS is far behind, every later five-slot number inherits that deficit,
so this has to be checked before Stage 4 is built on top of it.

Repair noise is not a tuning knob here, it is load-bearing: without it destroy+repair is
the identity (60/60 rebuilds returned the starting makespan, 2026-08-10).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.common import SEEDS, gap, mean_gap, paired, run_parallel
from model.lns import destroy_critical, run
from simulator.instance import load_dauzere, load_deroussi

CASES = [("dauzere", "01a", 2), ("dauzere", "07a", 4), ("dauzere", "09a", 2),
         ("dauzere", "12a", 2), ("dauzere", "15a", 2), ("dauzere", "18a", 2),
         ("deroussi", "fjsp1", 2), ("deroussi", "fjsp8", 2)]
BUDGET = 600
FRAC, ETA = 0.2, 0.1          # chosen on 01a at 30s (2026-08-10); see report

# Load balancing on assignment, earliest-arrival on sequencing. 2026-08-07 measured the
# textbook greedy alternative ("fastest machine", "earliest AGV") at 157.7% against
# 76.6% for this, because everyone crowds the same good resource.
SLOTS = {"machine_select": lambda f: -f["queue_len"],
         "op_sequence":    lambda f: -f["arrival"],
         "vehicle_select": lambda f: -f["queue_len"],
         "task_sequence":  lambda f: -f["arrival"]}

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "results", "2026-08-01-rule_ranking_retest_result.json")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "results", "2026-08-10-lns_gate_result.json")


def load(family, stem, veh):
    return (load_dauzere if family == "dauzere" else load_deroussi)(stem, veh)


def one(job):
    family, stem, veh, seed = job
    inst = load(family, stem, veh)
    _, sched, st = run(inst, SLOTS, destroy=destroy_critical, frac=FRAC, eta=ETA,
                       time_limit=BUDGET, seed=seed)
    return {"family": family, "stem": stem, "veh": veh, "seed": seed,
            "rule": "LNS", "cmax": sched.cmax,
            "iterations": st["iterations"], "accepted": st["accepted"]}


def main():
    jobs = [(f, s, v, sd) for (f, s, v) in CASES for sd in SEEDS]
    print(f"LNS gate: {len(jobs)} runs x {BUDGET}s, frac={FRAC} eta={ETA}\n", flush=True)
    lns = run_parallel(one, jobs, budget_of=lambda j: BUDGET, every=6)

    ref = json.load(open(REF))
    ga = [r for r in ref["runs"] if r.get("rule") == "D1" and r.get("budget") == BUDGET]
    for r in ga:
        r["rule"] = "GA_D1"

    both = lns + ga
    print(f"\n{'':<10}{'LNS':>12}{'GA(D1)':>12}")
    for label, where in (("dauzere", {"family": "dauzere"}),
                         ("deroussi", {"family": "deroussi"}), ("all", {})):
        a = mean_gap(both, rule="LNS", **where)
        b = mean_gap(both, rule="GA_D1", **where)
        print(f"{label:<10}{a:>11.1f}%{b:>11.1f}%")

    wins, ties, n, p = paired(both, "LNS", "GA_D1")
    print(f"\npaired LNS vs GA(D1): {wins}/{n} wins, {ties} ties, p={p:.4f}")

    json.dump({"protocol": {"cases": CASES, "seeds": list(SEEDS), "budget": BUDGET,
                            "frac": FRAC, "eta": ETA, "slots": "hand (balanced+arrival)"},
               "runs": both}, open(OUT, "w"), indent=1)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
