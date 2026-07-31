"""Stage 0c step (c): do the project's rule findings survive on a properly tuned GA?

Every rule comparison this project has made - the main campaign, the reproducibility
campaign, the 2x2 ablation that attributed the effect to the deadhead penalty, the
confound-removal re-evaluation - ran at population 70. 2026-08-01 showed pop70 is not
merely a weaker setting but roughly four times worse than the optimum at 600s
(94.5% vs 24.0% gap). Rule effects measured on top of a badly configured solver may
not transfer.

Two questions:

Q1 Does the ranking hold?  D1 / D2 / P_main / P2 / P3 re-ranked at 600s x pop1000.
   If the evolved rules still beat the two literature decodings, the headline result
   survives. If they collapse, the project's central claim needs rewriting.

Q2 Does the 2x2 ablation attribution hold?  The ablation concluded that the deadhead
   (empty_travel) penalty is the main effect and that coupling arrival with
   machine_free is null on its own but synergistic. The same four cells are re-run
   here, so the interaction can be re-estimated on the tuned solver.

Cells for Q2 (from 2026-07-24-ablation-two-ingredients):
   base      -arrival                                  neither ingredient
   dead      -arrival - 0.5*empty_travel               deadhead penalty only
   couple    -max(arrival, machine_free)               coupling only
   both      -max(arrival, machine_free) - 0.5*empty_travel

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
from simulator.instance import load_dauzere, load_deroussi

SEEDS = (0, 21, 42)
WORKERS = 12

# Tuned per 2026-08-01: population chosen so the run lands at a few hundred generations.
TUNED = {600: 1000, 10: 70}
BUDGETS = (600,)          # the claim budget; 10s is for the evolution loop, not for claims

# Eight cases spanning machine count, flexibility and vehicle count, plus two Deroussi
# for the other lineage. Same set as the 2026-07-31 gate so the two are comparable.
CASES = [
    ("dauzere", "01a", 2), ("dauzere", "07a", 4), ("dauzere", "09a", 2),
    ("dauzere", "12a", 2), ("dauzere", "15a", 2), ("dauzere", "18a", 2),
    ("deroussi", "fjsp1", 2), ("deroussi", "fjsp8", 2),
]

EVOLVED = {
    "P_main": "-max(arrival, machine_free) - 0.5*empty_travel - 0.3*max(0, wait-empty_travel) "
              "- 0.05*agv_cum_travel/(machine_free+1) - 0.01*agv_free",
    "P2": "-(arrival + 0.7*empty_travel + 0.1*wait) - 0.3*max(0, machine_free-arrival)",
    "P3": "-max(arrival,machine_free)-wait/(remaining_ops+1)",
}
ABLATION = {
    "base":   "-arrival",
    "dead":   "-arrival - 0.5*empty_travel",
    "couple": "-max(arrival, machine_free)",
    "both":   "-max(arrival, machine_free) - 0.5*empty_travel",
}
RANKING_RULES = ["D1", "D2", "P_main", "P2", "P3"]
ALL_RULES = RANKING_RULES + list(ABLATION)

TABLE8 = {"01a": (3029, 2812, 2756), "07a": (4157, 2860, 2758), "09a": (2448, 2213, 2146),
          "12a": (2484, 2173, 2133), "15a": (3034, 2367, 2288), "18a": (3017, 2355, 2264)}
VI = {2: 0, 4: 1, 6: 2}
DEROUSSI_BEST = {"fjsp1": 134, "fjsp8": 178}


def reference(family, stem, veh):
    return TABLE8[stem][VI[veh]] if family == "dauzere" else DEROUSSI_BEST[stem]


def make_rule(name):
    if name in RULES:
        return RULES[name]
    return rule_from_expr(EVOLVED.get(name) or ABLATION[name])


def one_run(job):
    family, stem, veh, rname, budget, seed = job
    inst = (load_dauzere if family == "dauzere" else load_deroussi)(stem, veh)
    t0 = time.time()
    ga = GA(inst, make_rule(rname), pop_size=TUNED[budget], n_gen=10 ** 9,
            seed=seed, time_limit=budget)
    best, _ = ga.run()
    return {"family": family, "stem": stem, "veh": veh, "rule": rname, "budget": budget,
            "pop": TUNED[budget], "seed": seed, "cmax": best.fitness,
            "evals": ga.n_evals, "generations": ga.n_gen_done,
            "elapsed": round(time.time() - t0, 1)}


def main():
    jobs = [(f, s, v, r, b, sd)
            for (f, s, v), r, b, sd in itertools.product(CASES, ALL_RULES, BUDGETS, SEEDS)]
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
                       "data", "results", "2026-08-01-rule_ranking_retest_result.json")
    json.dump({"protocol": {"seeds": SEEDS, "budgets": BUDGETS, "tuned_pop": TUNED,
                            "cases": CASES, "rules": ALL_RULES},
               "runs": recs}, open(out, "w"), indent=1)
    print(f"\nwrote {out}")
    report(recs)


def gap(r):
    ref = reference(r["family"], r["stem"], r["veh"])
    return 100 * (r["cmax"] - ref) / ref


def paired(recs, a, b):
    """Paired comparison over (case, seed): same instance, same seed, two rules."""
    ka = {(r["stem"], r["veh"], r["seed"]): r["cmax"] for r in recs if r["rule"] == a}
    kb = {(r["stem"], r["veh"], r["seed"]): r["cmax"] for r in recs if r["rule"] == b}
    keys = sorted(set(ka) & set(kb))
    xa = [ka[k] for k in keys]
    xb = [kb[k] for k in keys]
    wins = sum(1 for u, v in zip(xa, xb) if u < v)
    ties = sum(1 for u, v in zip(xa, xb) if u == v)
    t = stats.wilcoxon(xa, xb).pvalue if any(u != v for u, v in zip(xa, xb)) else 1.0
    return wins, ties, len(keys), t


def report(recs):
    print("\n=== Q1  규칙 순위 (600초 x pop1000, 8케이스 x 3시드) ===")
    print(f"{'규칙':<9}{'평균격차':>10}{'Dauzere':>10}{'Deroussi':>10}")
    order = []
    for rn in RANKING_RULES:
        g = [gap(r) for r in recs if r["rule"] == rn]
        gd = [gap(r) for r in recs if r["rule"] == rn and r["family"] == "dauzere"]
        ge = [gap(r) for r in recs if r["rule"] == rn and r["family"] == "deroussi"]
        order.append((st.mean(g), rn))
        print(f"{rn:<9}{st.mean(g):>9.2f}%{st.mean(gd):>9.2f}%{st.mean(ge):>9.2f}%")
    print("\n  순위(좋은 순): " + " < ".join(rn for _, rn in sorted(order)))
    print("  참고 pop70 600초 순위: P2 < P_main < D1 < D2 < P3  (2026-07-31 게이트)")

    print("\n=== Q1b  진화 규칙 vs 문헌 규칙, 짝지은 비교 ===")
    print(f"{'비교':<20}{'승':>5}{'무':>5}{'표본':>6}{'p(Wilcoxon)':>14}")
    for pr in ["P_main", "P2", "P3"]:
        for lit in ["D1", "D2"]:
            w, t, n, p = paired(recs, pr, lit)
            mark = " *" if p < 0.05 else ""
            print(f"{pr+' vs '+lit:<20}{w:>5}{t:>5}{n:>6}{p:>14.4f}{mark}")

    print("\n=== Q2  2x2 ablation 재측정 (공차 벌점 x 기계가용 결합) ===")
    cells = {}
    for c in ABLATION:
        cells[c] = st.mean(gap(r) for r in recs if r["rule"] == c)
    print(f"                    결합 없음      결합 있음")
    print(f"  공차벌점 없음   {cells['base']:>9.2f}%   {cells['couple']:>9.2f}%")
    print(f"  공차벌점 있음   {cells['dead']:>9.2f}%   {cells['both']:>9.2f}%")
    print(f"\n  공차 주효과   = {(cells['base']+cells['couple'])/2 - (cells['dead']+cells['both'])/2:>7.2f}%p")
    print(f"  결합 주효과   = {(cells['base']+cells['dead'])/2 - (cells['couple']+cells['both'])/2:>7.2f}%p")
    print(f"  상호작용      = {cells['base'] - cells['dead'] - cells['couple'] + cells['both']:>7.2f}%p")
    print()
    for a, b in [("dead", "base"), ("couple", "base"), ("both", "base"), ("both", "dead")]:
        w, t, n, p = paired(recs, a, b)
        mark = " *" if p < 0.05 else ""
        print(f"  {a+' vs '+b:<18}{w:>4}승 {t}무 /{n:>3}   p={p:.4f}{mark}")
    print("\n  참고 pop70 결론(2026-07-24): 공차=주효과(p=0.0001), 결합 단독=무효(p=0.62),")
    print("                               상호작용 유의(p=0.018)")


if __name__ == "__main__":
    main()
