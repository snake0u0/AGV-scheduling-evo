"""Stage 0b: is the GA budget-limited or converged? And does ANY structure in the
machine-selection search help?

2026-07-31-budget-vs-structure-gate concluded that 61x more evaluations buys only
12%p, and read that as "the machine-selection operators ignore structure". The same
data is equally consistent with a different story: the population loses diversity
early and the remaining evaluations are wasted. The two diagnoses have different
cures - the second is fixable inside the GA and would not justify building an LNS.

That distinction also decides whether the eventual "LNS beats GA" comparison is
fair: beating a badly configured GA proves nothing. Whatever wins here becomes the
tuned GA baseline for the rest of the project.

Configurations (all at the same 600s wall-clock, so the comparison is like-for-like):
  pop70        the configuration used so far
  pop300       more diversity
  pop1000      much more diversity, far fewer generations
  restart10x60 ten independent 60s runs, best of - the cheapest cure for convergence
  greedyMS     pop70 but machine genes biased 80% to the shortest-processing-time
               machine; a direct test of "the MS search has no structural signal"

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

BUDGET = 600

# The rule is held fixed at the best one found so far; this experiment varies the
# GA configuration, not the rule.
P2 = "-(arrival + 0.7*empty_travel + 0.1*wait) - 0.3*max(0, machine_free-arrival)"

CASES = [
    ("dauzere", "01a", 2),   # 600s gap was 9%   - the easy end of Dauzere
    ("dauzere", "09a", 2),   # 87%
    ("dauzere", "15a", 2),   # 141%
    ("dauzere", "18a", 2),   # 140%  - worst
    ("deroussi", "fjsp8", 2),   # 2%, all three seeds identical: a converged control
]

CONFIGS = ["pop70", "pop300", "pop1000", "restart10x60", "greedyMS"]

def one_run(job):
    family, stem, veh, config, seed = job
    inst = (load_dauzere if family == "dauzere" else load_deroussi)(stem, veh)
    rule = rule_from_expr(P2)
    t0 = time.time()

    if config == "restart10x60":
        best, evals, gens, last = None, 0, 0, []
        for k in range(10):
            ga = GA(inst, rule, pop_size=70, n_gen=10 ** 9, seed=seed * 100 + k,
                    time_limit=BUDGET // 10)
            b, _ = ga.run()
            evals += ga.n_evals
            gens += ga.n_gen_done
            last.append(ga.last_improve_gen / max(1, ga.n_gen_done))
            best = b.fitness if best is None else min(best, b.fitness)
        cmax, n_evals, n_gen, frac = best, evals, gens, st.mean(last)
    else:
        pop = {"pop70": 70, "pop300": 300, "pop1000": 1000,
               "greedyMS": 70}[config]
        ms_init = "greedy" if config == "greedyMS" else "random"
        ga = GA(inst, rule, pop_size=pop, n_gen=10 ** 9, seed=seed,
                time_limit=BUDGET, ms_init=ms_init)
        b, _ = ga.run()
        cmax, n_evals, n_gen = b.fitness, ga.n_evals, ga.n_gen_done
        frac = ga.last_improve_gen / max(1, ga.n_gen_done)

    return {"family": family, "stem": stem, "veh": veh, "config": config, "seed": seed,
            "cmax": cmax, "evals": n_evals, "generations": n_gen,
            "last_improve_frac": round(frac, 3), "elapsed": round(time.time() - t0, 1)}


def main():
    jobs = [(f, s, v, c, sd)
            for (f, s, v), c, sd in itertools.product(CASES, CONFIGS, SEEDS)]
    print(f"{len(jobs)} runs x {BUDGET}s = {len(jobs)*BUDGET/3600:.1f} CPU-hours, "
          f"{WORKERS} workers -> about {len(jobs)*BUDGET/3600/WORKERS:.1f} h wall\n", flush=True)

    t0, recs = time.time(), []
    with mp.Pool(WORKERS) as pool:
        for i, r in enumerate(pool.imap_unordered(one_run, jobs), 1):
            recs.append(r)
            if i % 10 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}  ({time.time()-t0:.0f}s)", flush=True)

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "results", "2026-07-31-ga_diagnosis_result.json")
    json.dump({"protocol": {"seeds": SEEDS, "budget": BUDGET, "cases": CASES,
                            "configs": CONFIGS, "rule": P2}, "runs": recs},
              open(out, "w"), indent=1)
    print(f"\nwrote {out}")
    report(recs)


def report(recs):
    def cell(stem, veh, cfg, f):
        rs = [r for r in recs if r["stem"] == stem and r["veh"] == veh and r["config"] == cfg]
        return st.mean(f(r) for r in rs)

    print("\n=== A1  마지막 개선이 일어난 시점 (전체 세대 중 비율) ===")
    print("     1.0 에 가까우면 끝까지 개선 중 = 예산 부족")
    print("     0에 가까우면 초반에 멈춤 = 조기 수렴\n")
    print(f"{'케이스':<11}" + "".join(f"{c:>14}" for c in CONFIGS))
    for f, s, v in CASES:
        print(f"{s+'/'+str(v):<11}" +
              "".join(f"{cell(s, v, c, lambda r: r['last_improve_frac']):>14.2f}" for c in CONFIGS))

    print("\n=== A2/A3/B  설정별 문헌 대비 격차 (%) - 같은 600초 ===")
    print(f"{'케이스':<11}" + "".join(f"{c:>14}" for c in CONFIGS))
    for f, s, v in CASES:
        base = cell(s, v, "pop70", gap)
        row = "".join(f"{cell(s, v, c, gap):>13.1f}%" for c in CONFIGS)
        print(f"{s+'/'+str(v):<11}{row}")
    print(f"\n{'전체평균':<11}" +
          "".join(f"{st.mean(gap(r) for r in recs if r['config']==c):>13.1f}%" for c in CONFIGS))
    print(f"{'Dauzere만':<11}" +
          "".join(f"{st.mean(gap(r) for r in recs if r['config']==c and r['family']=='dauzere'):>13.1f}%"
                  for c in CONFIGS))

    print("\n=== pop70 대비 개선폭 (%p, 양수면 개선) ===")
    print(f"{'케이스':<11}" + "".join(f"{c:>14}" for c in CONFIGS[1:]))
    for f, s, v in CASES:
        base = cell(s, v, "pop70", gap)
        print(f"{s+'/'+str(v):<11}" +
              "".join(f"{base - cell(s, v, c, gap):>13.1f}p" for c in CONFIGS[1:]))

    print("\n=== 설정별 평가 횟수 / 세대 수 (평균) ===")
    for c in CONFIGS:
        rs = [r for r in recs if r["config"] == c]
        print(f"  {c:<14} {st.mean(r['evals'] for r in rs):>10,.0f}회 평가"
              f"   {st.mean(r['generations'] for r in rs):>8,.0f}세대")


if __name__ == "__main__":
    main()
