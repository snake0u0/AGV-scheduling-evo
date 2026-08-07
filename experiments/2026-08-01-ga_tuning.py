"""Stage 0c step 1: define the tuned GA, and separate population size from selection
pressure.

2026-07-31b showed pop70 -> pop1000 collapses the Dauzere gap 94.5% -> 24.1% at equal
time and equal evaluations. Two things changed at once, because n_elite is a fixed 10:
the population grew 14x AND the elite fraction fell from 14% to 1%. A 14% elite fraction
is heavy selection pressure and kills diversity fast, so the effect may be selection
pressure rather than population size. That matters practically: if it is elitism, a
pop70 run with fewer elites buys the same gain far more cheaply.

The two cross-matched configurations settle it:
  pop70_elite1     pop70 at pop1000's elite fraction (1.4%)
  pop1000_elite143 pop1000 at pop70's elite fraction (14.3%)
If elitism is the cause the two should swap places. If neither moves, population size
is genuinely the knob.

pop3000/pop10000 look for the plateau - pop1000's last improvement still lands at
0.92-0.98 of its generations, so it is budget-limited and not yet the ceiling.
pop70_pm05 asks whether mutation can buy the same diversity: the effective machine-gene
mutation rate today is pm=0.1 times mutate_ms rate 0.1, i.e. 1% of genes.

Both budgets are measured because the evolution loop scores candidates at 10s while the
final comparison runs at 600s, and the best configuration will not be the same for both.

No LLM calls.
"""
import itertools
import json
import multiprocessing as mp
import os
import statistics as st
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 문헌 기준값·격차·검정은 experiments/common.py 한 곳에서 온다.
# 출처와 주의사항 = data/literature/SOURCE.md  (2026-08-07 통합)
from experiments.common import (SEEDS, WORKERS, gap, mean_gap, paired,
                                pop_for, reference, run_parallel)
from model.ga import GA
from model.rules import rule_from_expr
from simulator.instance import load_dauzere, load_deroussi

BUDGETS = (10, 600)
P2 = "-(arrival + 0.7*empty_travel + 0.1*wait) - 0.3*max(0, machine_free-arrival)"

CASES = [
    ("dauzere", "01a", 2),
    ("dauzere", "09a", 2),
    ("dauzere", "15a", 2),
    ("dauzere", "18a", 2),
]

# name -> (pop_size, n_elite, pm)   pm=None keeps the default 0.1
CONFIGS = {
    "pop70":            (70,    10,  0.1),    # the historical setting
    "pop1000":          (1000,  10,  0.1),    # 2026-07-31b winner
    "pop3000":          (3000,  10,  0.1),
    "pop10000":         (10000, 10,  0.1),
    "pop70_elite1":     (70,     1,  0.1),    # pop1000's elite fraction at pop70
    "pop1000_elite143": (1000, 143,  0.1),    # pop70's elite fraction at pop1000
    "pop70_pm05":       (70,    10,  0.5),    # buy diversity with mutation instead
}

def one_run(job):
    family, stem, veh, config, budget, seed = job
    pop, elite, pm = CONFIGS[config]
    inst = (load_dauzere if family == "dauzere" else load_deroussi)(stem, veh)
    t0 = time.time()
    ga = GA(inst, rule_from_expr(P2), pop_size=pop, n_gen=10 ** 9, pm=pm,
            n_elite=elite, seed=seed, time_limit=budget)
    best, _ = ga.run()
    return {"family": family, "stem": stem, "veh": veh, "config": config,
            "budget": budget, "seed": seed, "cmax": best.fitness,
            "evals": ga.n_evals, "generations": ga.n_gen_done,
            "last_improve_frac": round(ga.last_improve_gen / max(1, ga.n_gen_done), 3),
            "elapsed": round(time.time() - t0, 1)}


def main():
    jobs = [(f, s, v, c, b, sd)
            for (f, s, v), c, b, sd in itertools.product(CASES, CONFIGS, BUDGETS, SEEDS)]
    cpu = sum(j[4] for j in jobs)
    print(f"{len(jobs)} runs, {cpu/3600:.1f} CPU-hours, {WORKERS} workers "
          f"-> about {cpu/3600/WORKERS:.1f} h wall\n", flush=True)

    t0, recs = time.time(), []
    with mp.Pool(WORKERS) as pool:
        for i, r in enumerate(pool.imap_unordered(one_run, jobs), 1):
            recs.append(r)
            if i % 20 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}  ({time.time()-t0:.0f}s)", flush=True)

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "results", "2026-08-01-ga_tuning_result.json")
    json.dump({"protocol": {"seeds": SEEDS, "budgets": BUDGETS, "cases": CASES,
                            "configs": {k: list(v) for k, v in CONFIGS.items()},
                            "rule": P2}, "runs": recs}, open(out, "w"), indent=1)
    print(f"\nwrote {out}")
    report(recs)


def report(recs):
    names = list(CONFIGS)

    for b in BUDGETS:
        print(f"\n=== {b}초 예산: 문헌 대비 격차 (%) ===")
        print(f"{'케이스':<10}" + "".join(f"{n:>18}" for n in names))
        for f, s, v in CASES:
            row = []
            for n in names:
                rs = [r for r in recs if r["stem"] == s and r["config"] == n
                      and r["budget"] == b]
                row.append(st.mean(gap(r) for r in rs))
            print(f"{s+'/'+str(v):<10}" + "".join(f"{x:>17.1f}%" for x in row))
        print(f"{'평균':<10}" + "".join(
            f"{st.mean(gap(r) for r in recs if r['config']==n and r['budget']==b):>17.1f}%"
            for n in names))

    print("\n=== 교란 판정: population 인가 선택압인가 ===")
    for b in BUDGETS:
        g = {n: st.mean(gap(r) for r in recs if r["config"] == n and r["budget"] == b)
             for n in names}
        print(f"\n  [{b}초]")
        print(f"    pop70            (엘리트 14.3%)  {g['pop70']:>7.1f}%")
        print(f"    pop70_elite1     (엘리트  1.4%)  {g['pop70_elite1']:>7.1f}%"
              f"   <- pop70 대비 {g['pop70']-g['pop70_elite1']:+.1f}%p")
        print(f"    pop1000          (엘리트  1.0%)  {g['pop1000']:>7.1f}%")
        print(f"    pop1000_elite143 (엘리트 14.3%)  {g['pop1000_elite143']:>7.1f}%"
              f"   <- pop1000 대비 {g['pop1000']-g['pop1000_elite143']:+.1f}%p")
        print(f"    pop70_pm05       (변이 0.5)      {g['pop70_pm05']:>7.1f}%"
              f"   <- pop70 대비 {g['pop70']-g['pop70_pm05']:+.1f}%p")
        best = min(g, key=g.get)
        print(f"    -> {b}초 최선 설정: {best} ({g[best]:.1f}%)")

    print("\n=== 마지막 개선 시점 (600초, 1.0이면 끝까지 개선 중) ===")
    print(f"{'케이스':<10}" + "".join(f"{n:>18}" for n in names))
    for f, s, v in CASES:
        print(f"{s+'/'+str(v):<10}" + "".join(
            f"{st.mean(r['last_improve_frac'] for r in recs if r['stem']==s and r['config']==n and r['budget']==600):>18.2f}"
            for n in names))

    print("\n=== 600초 평가 횟수 / 세대 수 ===")
    for n in names:
        rs = [r for r in recs if r["config"] == n and r["budget"] == 600]
        print(f"  {n:<18} {st.mean(r['evals'] for r in rs):>10,.0f}회"
              f"   {st.mean(r['generations'] for r in rs):>8,.0f}세대")


if __name__ == "__main__":
    main()
