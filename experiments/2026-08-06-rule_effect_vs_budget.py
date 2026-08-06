"""Stage 0c (B): at what solver budget do the AGV rules actually matter?

2026-08-01b found that rule differences vanish at 600s x pop1000 - the tuned GA
absorbs a mediocre rule by adjusting OS/MS. But at 10s x pop70 the same rules were
6.26%p apart. If the rule effect is real but only survives at low budget, that is
where the paper's ring has to be, and it points back at fast/online decision making
rather than long offline metaheuristic runs.

The measurement has to tune the population per budget, otherwise it repeats the
mistake of 2026-07-31: population 70 is right at 10s and four times too small at
600s, so a fixed population confounds "budget" with "wrong configuration". Three
populations bracket the optimum at each budget, which also answers the open item
(D) - whether something below 70 is better in the 10s range the evolution loop uses.

Reported per budget:
  - which population wins (the tuned configuration for that budget)
  - at that population, the spread between the best and worst rule
  - that spread against the seed-to-seed noise, since 2026-08-01b found them
    to be the same size at 600s
  - paired Wilcoxon of each evolved rule against each literature decoding

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

from scipy import stats

from model.ga import GA
from model.rules import RULES, rule_from_expr
from simulator.instance import load_dauzere

SEEDS = (0, 21, 42)
WORKERS = 12

# Populations bracketing the expected optimum at each budget (2026-08-01: 10s -> 70,
# 600s -> 1000, and the rule of thumb "land at 400-1500 generations").
BUDGET_POPS = {
    1:   (20, 70, 300),
    10:  (20, 70, 300),
    60:  (70, 300, 1000),
    600: (300, 1000),
}

CASES = [("01a", 2), ("09a", 2), ("15a", 2), ("18a", 2)]

EVOLVED = {
    "P_main": "-max(arrival, machine_free) - 0.5*empty_travel - 0.3*max(0, wait-empty_travel) "
              "- 0.05*agv_cum_travel/(machine_free+1) - 0.01*agv_free",
    "P2": "-(arrival + 0.7*empty_travel + 0.1*wait) - 0.3*max(0, machine_free-arrival)",
    "P3": "-max(arrival,machine_free)-wait/(remaining_ops+1)",
}
RULE_NAMES = ["D1", "D2", "P_main", "P2", "P3"]
LITERATURE = ["D1", "D2"]
EVOLVED_NAMES = ["P_main", "P2", "P3"]

TABLE8 = {"01a": (3029, 2812, 2756), "09a": (2448, 2213, 2146),
          "15a": (3034, 2367, 2288), "18a": (3017, 2355, 2264)}
VI = {2: 0, 4: 1, 6: 2}


def make_rule(name):
    return RULES[name] if name in RULES else rule_from_expr(EVOLVED[name])


def one_run(job):
    stem, veh, rname, budget, pop, seed = job
    inst = load_dauzere(stem, veh)
    t0 = time.time()
    ga = GA(inst, make_rule(rname), pop_size=pop, n_gen=10 ** 9,
            seed=seed, time_limit=budget)
    best, _ = ga.run()
    return {"stem": stem, "veh": veh, "rule": rname, "budget": budget, "pop": pop,
            "seed": seed, "cmax": best.fitness, "evals": ga.n_evals,
            "generations": ga.n_gen_done, "elapsed": round(time.time() - t0, 1)}


def main():
    jobs = []
    for budget, pops in BUDGET_POPS.items():
        for (stem, veh), rname, pop, seed in itertools.product(
                CASES, RULE_NAMES, pops, SEEDS):
            jobs.append((stem, veh, rname, budget, pop, seed))
    cpu = sum(j[3] for j in jobs)
    print(f"{len(jobs)} runs, {cpu/3600:.1f} CPU-hours, {WORKERS} workers "
          f"-> about {cpu/3600/WORKERS:.1f} h wall\n", flush=True)

    t0, recs = time.time(), []
    with mp.Pool(WORKERS) as pool:
        for i, r in enumerate(pool.imap_unordered(one_run, jobs), 1):
            recs.append(r)
            if i % 40 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}  ({time.time()-t0:.0f}s)", flush=True)

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "results", "2026-08-06-rule_effect_vs_budget_result.json")
    json.dump({"protocol": {"seeds": SEEDS, "budget_pops": {str(k): list(v)
                                                            for k, v in BUDGET_POPS.items()},
                            "cases": CASES, "rules": RULE_NAMES}, "runs": recs},
              open(out, "w"), indent=1)
    print(f"\nwrote {out}")
    report(recs)


def gap(r):
    return 100 * (r["cmax"] - TABLE8[r["stem"]][VI[r["veh"]]]) / TABLE8[r["stem"]][VI[r["veh"]]]


def paired(recs, a, b):
    ka = {(r["stem"], r["veh"], r["seed"]): r["cmax"] for r in recs if r["rule"] == a}
    kb = {(r["stem"], r["veh"], r["seed"]): r["cmax"] for r in recs if r["rule"] == b}
    keys = sorted(set(ka) & set(kb))
    xa, xb = [ka[k] for k in keys], [kb[k] for k in keys]
    wins = sum(1 for u, v in zip(xa, xb) if u < v)
    p = stats.wilcoxon(xa, xb).pvalue if any(u != v for u, v in zip(xa, xb)) else 1.0
    return wins, len(keys), p


def report(recs):
    print("\n=== (D) 예산별 최적 population ===")
    print(f"{'예산':>7}" + "".join(f"{'pop'+str(p):>12}" for p in (20, 70, 300, 1000)))
    tuned = {}
    for budget, pops in BUDGET_POPS.items():
        cells = {}
        for p in (20, 70, 300, 1000):
            rs = [r for r in recs if r["budget"] == budget and r["pop"] == p]
            cells[p] = st.mean(gap(r) for r in rs) if rs else None
        tuned[budget] = min((v, k) for k, v in cells.items() if v is not None)[1]
        row = "".join(f"{cells[p]:>11.1f}%" if cells[p] is not None else f"{'-':>12}"
                      for p in (20, 70, 300, 1000))
        print(f"{budget:>6}초{row}   <- 최적 pop{tuned[budget]}")

    print("\n=== (B) 각 예산의 최적 설정에서, 규칙이 얼마나 중요한가 ===")
    print(f"{'예산':>7}{'pop':>7}{'최선규칙':>10}{'최악규칙':>10}{'규칙 폭':>10}"
          f"{'시드 노이즈':>12}{'비율':>8}")
    for budget in BUDGET_POPS:
        p = tuned[budget]
        sub = [r for r in recs if r["budget"] == budget and r["pop"] == p]
        means = {rn: st.mean(gap(r) for r in sub if r["rule"] == rn) for rn in RULE_NAMES}
        spread = max(means.values()) - min(means.values())
        noise = st.mean([st.pstdev([gap(r) for r in sub
                                    if r["rule"] == rn and r["stem"] == s and r["veh"] == v])
                         for rn in RULE_NAMES for s, v in CASES])
        best = min(means, key=means.get)
        worst = max(means, key=means.get)
        print(f"{budget:>6}초{p:>7}{best:>10}{worst:>10}{spread:>9.2f}p"
              f"{noise:>11.2f}p{spread/noise if noise else 0:>8.1f}x")

    print("\n=== 예산별 규칙 순위 (최적 population) ===")
    for budget in BUDGET_POPS:
        p = tuned[budget]
        sub = [r for r in recs if r["budget"] == budget and r["pop"] == p]
        means = {rn: st.mean(gap(r) for r in sub if r["rule"] == rn) for rn in RULE_NAMES}
        order = sorted(means, key=means.get)
        line = "  ".join(f"{rn}({means[rn]:.1f}%)" for rn in order)
        lit_rank = min(order.index("D1"), order.index("D2")) + 1
        print(f"  {budget:>4}초 (pop{p}): {line}    문헌 최고순위 {lit_rank}위")

    print("\n=== 진화 규칙 vs 문헌 규칙, 예산별 짝지은 Wilcoxon (12쌍) ===")
    print(f"{'예산':>7}" + "".join(f"{e+' vs '+l:>16}" for e in EVOLVED_NAMES for l in LITERATURE))
    for budget in BUDGET_POPS:
        p = tuned[budget]
        sub = [r for r in recs if r["budget"] == budget and r["pop"] == p]
        cells = []
        for e in EVOLVED_NAMES:
            for l in LITERATURE:
                w, n, pv = paired(sub, e, l)
                cells.append(f"{w}/{n} p={pv:.3f}" + ("*" if pv < 0.05 else " "))
        print(f"{budget:>6}초" + "".join(f"{c:>16}" for c in cells))


if __name__ == "__main__":
    main()
