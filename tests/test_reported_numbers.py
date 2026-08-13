"""Regression gate: every number that appears in a report must still be reproducible
from the stored results using the shared harness.

This exists because the reference table used to be copy-pasted into six scripts. A
typo in one copy would have changed that experiment's gap silently, with no error, at
effect sizes of 1-5%p. Consolidating the table into data/literature/ removed the
hazard; this test makes sure the consolidation did not move any published number, and
keeps guarding it if the reference files are ever edited.

Add a line here whenever a report states a number worth defending.

Run: python -m tests.test_reported_numbers
"""
import json
import os
import statistics as st

from experiments.common import gap, paired, pop_for

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "results")

FAILURES = []


def load(name):
    return json.load(open(os.path.join(RESULTS, name)))["runs"]


def check(label, got, want, tol=0.05):
    ok = abs(got - want) <= tol
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<44} {got:>9.3f}   reported {want:>9.3f}")
    if not ok:
        FAILURES.append(label)


def mean_gap(recs, **where):
    sub = [r for r in recs if all(r.get(k) == v for k, v in where.items())]
    assert sub, f"no records for {where}"
    return st.mean(gap(r) for r in sub)


def main():
    print("2026-07-31-budget-vs-structure-gate.md  (pop70; its conclusion was later rejected)")
    R = load("2026-07-31-budget_scaling_result.json")
    for b, want in [(10, 76.1), (60, 70.8), (600, 64.1)]:
        check(f"{b}s overall mean gap", mean_gap(R, budget=b), want)
    for rn, want in [("D1", 65.35), ("D2", 65.73), ("P_main", 62.00),
                     ("P2", 60.69), ("P3", 66.70)]:
        check(f"600s {rn}", mean_gap(R, rule=rn, budget=600), want, tol=0.01)

    print("\n2026-07-31b-ga-diagnosis-population-not-structure.md")
    R = load("2026-07-31-ga_diagnosis_result.json")
    for c, want in [("pop70", 94.5), ("pop300", 37.5), ("pop1000", 24.1),
                    ("restart10x60", 87.8), ("greedyMS", 102.0)]:
        check(f"Dauzere {c}", mean_gap(R, config=c, family="dauzere"), want, tol=0.1)

    print("\n2026-08-01-ga-tuning-population-generations-tradeoff.md")
    R = load("2026-08-01-ga_tuning_result.json")
    for c, want in [("pop70", 94.5), ("pop1000", 24.0), ("pop3000", 92.8),
                    ("pop10000", 144.9), ("pop70_elite1", 61.9),
                    ("pop1000_elite143", 23.9), ("pop70_pm05", 72.6)]:
        check(f"600s {c}", mean_gap(R, config=c, budget=600), want, tol=0.1)
    for c, want in [("pop70", 112.4), ("pop70_elite1", 111.9), ("pop1000", 169.4)]:
        check(f"10s {c}", mean_gap(R, config=c, budget=10), want, tol=0.1)

    print("\n2026-08-01b-rule-advantage-does-not-survive-a-tuned-solver.md")
    R = load("2026-08-01-rule_ranking_retest_result.json")
    for rn, want in [("D1", 16.73), ("D2", 16.28), ("P_main", 16.75),
                     ("P2", 17.00), ("P3", 17.72)]:
        check(f"{rn} mean gap", mean_gap(R, rule=rn), want, tol=0.01)
    check("Dauzere mean", st.mean(gap(r) for r in R
                                if r["family"] == "dauzere" and r["rule"] == "D1"), 21.08, tol=0.01)
    for a, b, w_want, p_want in [("P2", "D1", 10, 0.7088), ("P_main", "D1", 9, 0.7938),
                                 ("P3", "D1", 8, 0.0573)]:
        w, _, _, p = paired(R, a, b)
        check(f"{a} vs {b} wins", w, w_want, tol=0)
        check(f"{a} vs {b} p-value", p, p_want, tol=0.001)
    # 2x2 ablation: the deadhead main effect kept its direction but lost significance
    cells = {c: mean_gap(R, rule=c) for c in ("base", "dead", "couple", "both")}
    check("deadhead main effect (%p)",
          (cells["base"] + cells["couple"]) / 2 - (cells["dead"] + cells["both"]) / 2,
          1.27, tol=0.01)
    check("interaction (%p)",
          cells["base"] - cells["dead"] - cells["couple"] + cells["both"], 0.02, tol=0.01)

    print("\n2026-08-06-rule-effect-vs-budget.md")
    R = load("2026-08-06-rule_effect_vs_budget_result.json")
    for b, p, want in [(1, 20, 158.7), (10, 70, 115.5), (60, 300, 74.0), (600, 1000, 24.3)]:
        check(f"{b}s x pop{p} (best)", mean_gap(R, budget=b, pop=p), want, tol=0.1)
    for b, p, rn, want in [(1, 20, "P_main", 154.6), (10, 70, "P2", 113.2),
                           (60, 300, "D1", 68.2), (600, 1000, "D1", 23.5)]:
        check(f"{b}s {rn}", mean_gap(R, budget=b, pop=p, rule=rn), want, tol=0.1)
    w, _, _, p = paired([r for r in R if r["budget"] == 1 and r["pop"] == 20], "P2", "D2")
    check("1s P2 vs D2 wins", w, 10, tol=0)
    check("1s P2 vs D2 p-value", p, 0.016, tol=0.001)
    w, _, _, p = paired([r for r in R if r["budget"] == 60 and r["pop"] == 300], "P3", "D2")
    check("60s P3 vs D2 wins (evolved lost every pair)", w, 0, tol=0)

    print("\npop_for() formula vs measured best population")
    for b, measured in [(1, 20), (10, 70), (60, 300), (600, 1000)]:
        print(f"  {b:>4}s   measured pop{measured:<6} formula pop{pop_for(b)}")

    if FAILURES:
        raise SystemExit(f"\nFAIL - {len(FAILURES)} mismatches: {FAILURES}")
    print("\nPASS - every reported number reproduced")


if __name__ == "__main__":
    main()
