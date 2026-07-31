"""Stage 0 gate: is the 65% gap to the literature a BUDGET problem or a STRUCTURE problem?

Two questions, one run.

Q1 (LNS gate). Does the gap close as the solver budget grows 10s -> 60s -> 600s?
    The previous gap figure was measured at GA 70x70 = 4,900 evaluations. 600s is
    100-270x that. If the gap collapses, more search is the answer and LNS is
    optional. If it plateaus, the GA's machine-selection operators are structurally
    blind and no budget will fix it - LNS with a critical-path destroy is required.

Q2 (evolution budget). Is the RANKING of rules preserved at a cheap budget?
    Evolution only needs to know "is rule A better than rule B". If the ranking at
    10s already matches the ranking at 600s, we can evolve cheaply. Our own history
    warns against assuming this: 2026-07-24-confound-removal-reeval showed a budget
    change flipping the conclusion.

No LLM calls. Pure evaluation.
"""
import itertools
import json
import multiprocessing as mp
import os
import statistics as st
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.ga import GA
from model.rules import RULES, rule_from_expr
from simulator.instance import load_dauzere, load_deroussi, parse_format_b, BASE

# --- protocol, fixed in advance (2026-07-31 design meeting) ------------------
SEEDS = (0, 21, 42)
BUDGETS = (10, 60, 600)          # wall-clock seconds per case
POP = 70                         # same population as the earlier campaigns
WORKERS = 12                     # of 16 cores

# Cases chosen to span the axes the gap was found to track: machine count and
# flexibility. The four worst gap instances from 2026-07-29 are all here.
CASES = [
    ("dauzere", "01a", 2),   # 5 machines, low flexibility  - gap was small
    ("dauzere", "07a", 4),   # 8 machines
    ("dauzere", "09a", 2),   # 8 machines, flex 4.03 - gap 113%
    ("dauzere", "12a", 2),   # 8 machines, flex 4.03 - gap 119%
    ("dauzere", "15a", 2),   # 10 machines, flex 5.02 - gap 162%
    ("dauzere", "18a", 2),   # 10 machines, flex 5.02 - gap 172% (worst)
    ("deroussi", "fjsp1", 2),   # different lineage/format: 8 paired machines
    ("deroussi", "fjsp8", 2),
]

# Rules with a KNOWN ranking from 2026-07-24-confound-removal-reeval (GA 70x70,
# mean gap): P_main 65.3, P2 65.3, P3 67.0, D1 67.9, D2 68.0. Q2 asks whether a
# cheap budget reproduces that order.
EVOLVED = {
    "P_main": "-max(arrival, machine_free) - 0.5*empty_travel - 0.3*max(0, wait-empty_travel) "
              "- 0.05*agv_cum_travel/(machine_free+1) - 0.01*agv_free",
    "P2": "-(arrival + 0.7*empty_travel + 0.1*wait) - 0.3*max(0, machine_free-arrival)",
    "P3": "-max(arrival,machine_free)-wait/(remaining_ops+1)",
}
RULE_NAMES = ["D1", "D2", "P_main", "P2", "P3"]

# Literature best-known makespan.
#   Dauzere : Berterottiere, Dauzere-Peres & Yugma (2024) EJOR 312(3), Table 8.
#   Deroussi: the published solution-file headers, which this repo reproduces
#             exactly (simulator/test_replay_deroussi, 10/10) and which agree with
#             Berterottiere et al. (2026) EJOR 332, Table 6.
TABLE8 = {"01a": (3029, 2812, 2756), "07a": (4157, 2860, 2758), "09a": (2448, 2213, 2146),
          "12a": (2484, 2173, 2133), "15a": (3034, 2367, 2288), "18a": (3017, 2355, 2264)}
VI = {2: 0, 4: 1, 6: 2}
DEROUSSI_BEST = {"fjsp1": 134, "fjsp8": 178}


def reference(family, stem, veh):
    return TABLE8[stem][VI[veh]] if family == "dauzere" else DEROUSSI_BEST[stem]


def load(family, stem, veh):
    return load_dauzere(stem, veh) if family == "dauzere" else load_deroussi(stem, veh)


def one_run(job):
    """(family, stem, veh, rule_name, budget, seed) -> record. Rules are rebuilt from
    their source here because compiled closures do not survive pickling."""
    family, stem, veh, rname, budget, seed = job
    inst = load(family, stem, veh)
    rule = RULES[rname] if rname in RULES else rule_from_expr(EVOLVED[rname])
    t0 = time.time()
    ga = GA(inst, rule, pop_size=POP, n_gen=10 ** 9, seed=seed, time_limit=budget)
    best, _ = ga.run()
    return {"family": family, "stem": stem, "veh": veh, "rule": rname,
            "budget": budget, "seed": seed, "cmax": best.fitness,
            "generations": ga.n_gen_done, "evals": (ga.n_gen_done + 1) * POP,
            "elapsed": round(time.time() - t0, 1)}


def main():
    jobs = [(f, s, v, r, b, sd)
            for (f, s, v), r, b, sd in itertools.product(CASES, RULE_NAMES, BUDGETS, SEEDS)]
    cpu = sum(b for *_, b, _ in jobs)
    print(f"{len(jobs)} runs, {cpu/3600:.1f} CPU-hours, {WORKERS} workers "
          f"-> about {cpu/3600/WORKERS:.1f} h wall\n", flush=True)

    t0 = time.time()
    recs = []
    with mp.Pool(WORKERS) as pool:
        for i, r in enumerate(pool.imap_unordered(one_run, jobs), 1):
            recs.append(r)
            if i % 20 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}  ({time.time()-t0:.0f}s elapsed)", flush=True)

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "results", "2026-07-31-budget_scaling_result.json")
    json.dump({"protocol": {"seeds": SEEDS, "budgets": BUDGETS, "pop": POP,
                            "cases": CASES, "rules": RULE_NAMES},
               "runs": recs}, open(out, "w"), indent=1)
    print(f"\nwrote {out}")
    report(recs)


def gap(rec):
    ref = reference(rec["family"], rec["stem"], rec["veh"])
    return 100 * (rec["cmax"] - ref) / ref


def report(recs):
    by = {}
    for r in recs:
        by.setdefault((r["rule"], r["budget"], r["stem"], r["veh"]), []).append(r)

    # --- Q1: does the gap close with budget?
    print("\n=== Q1  예산별 문헌 대비 격차 (%) - 규칙 D1 기준 ===")
    print(f"{'케이스':<12}{'10초':>9}{'60초':>9}{'600초':>9}   {'10->600 변화':>12}")
    for f, s, v in CASES:
        row = []
        for b in BUDGETS:
            rs = by.get(("D1", b, s, v), [])
            row.append(st.mean(gap(r) for r in rs) if rs else float("nan"))
        print(f"{s+'/'+str(v)+'대':<12}" + "".join(f"{x:>8.0f}%" for x in row)
              + f"   {row[0]-row[2]:>10.0f}%p")

    print("\n=== Q1  전체 평균 격차 (모든 규칙·케이스) ===")
    for b in BUDGETS:
        g = [gap(r) for r in recs if r["budget"] == b]
        ev = st.mean(r["evals"] for r in recs if r["budget"] == b)
        print(f"  {b:>4}초:  평균 격차 {st.mean(g):>6.1f}%   (평균 {ev:>10,.0f}회 평가)")

    # --- Q2: is the rule ranking stable across budgets?
    print("\n=== Q2  예산별 규칙 순위 (평균 격차 %, 낮을수록 좋음) ===")
    print(f"{'규칙':<9}" + "".join(f"{str(b)+'초':>11}" for b in BUDGETS))
    order = {}
    for rn in RULE_NAMES:
        cells = []
        for b in BUDGETS:
            g = [gap(r) for r in recs if r["rule"] == rn and r["budget"] == b]
            cells.append(st.mean(g))
            order.setdefault(b, []).append((st.mean(g), rn))
        print(f"{rn:<9}" + "".join(f"{c:>10.2f}%" for c in cells))
    print()
    for b in BUDGETS:
        print(f"  {b:>4}초 순위: " + " < ".join(rn for _, rn in sorted(order[b])))


if __name__ == "__main__":
    main()
