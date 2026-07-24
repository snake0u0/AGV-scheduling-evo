"""Reproducibility campaign: run the evolution K times independently (the Claude
proposer is stochastic, so each run explores differently), then evaluate every
evolved rule against D1/D2 on the SAME held-out test set under one budget.

Two questions:
  1. Does an independently evolved rule reliably beat D1/D2 (Wilcoxon each run)?
  2. Does the key structural motif max(arrival, machine_free) recur?
"""
import json
import re
import sys
import time

sys.path.insert(0, "/home/dohyung/project/research-agent")

from scipy import stats

from fjspt.experiment import evolve
from fjspt.ga import GA
from fjspt.instance import DAUZERE_STEMS, load_dauzere
from fjspt.llm import ClaudeRuleProposer
from fjspt.rules import RULES, rule_from_expr

TRAIN = [("01a", 2), ("13a", 2), ("07a", 4)]
TEST = [(s, v) for v in (2, 4) for s in DAUZERE_STEMS if (s, v) not in TRAIN]

K = 3                                   # independent evolution runs
EVOLVE_POP, EVOLVE_GEN = 16, 6
INNER_GA_POP, INNER_GA_GEN = 40, 40
TEST_GA_POP, TEST_GA_GEN = 60, 60
TEST_SEEDS = (0, 1)

LOGP = "/home/dohyung/.claude/jobs/a367775e/tmp/repro_campaign.log"
LOG = open(LOGP, "a")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    LOG.write(m + "\n"); LOG.flush()


def has_start_time_motif(expr):
    """True if the rule couples arrival with machine_free (the key insight),
    e.g. max(arrival, machine_free) or min/max mixing the two."""
    e = expr.replace(" ", "")
    return bool(re.search(r"(max|min)\([^()]*arrival[^()]*machine_free", e)
                or re.search(r"(max|min)\([^()]*machine_free[^()]*arrival", e))


def main():
    t0 = time.time()
    log(f"\n===== REPRODUCIBILITY CAMPAIGN (K={K}) =====")
    log(f"train {TRAIN}  test {len(TEST)} instances")

    # evolve K times independently
    rules = {}
    for run in range(1, K + 1):
        prop = ClaudeRuleProposer(model="sonnet", max_calls=50, reevo=True)
        # vary inner GA seed per run so fitness ranking isn't identical; LLM adds its own noise
        expr, fit, hist = evolve(
            prop, TRAIN, pop_size=EVOLVE_POP, n_gens=EVOLVE_GEN,
            ga_pop=INNER_GA_POP, ga_gen=INNER_GA_GEN, seeds=(run,),
            log=lambda *a: None)
        rules[f"P{run}"] = expr
        log(f"[evolve run {run}] train_fit={fit:.1f}  motif={has_start_time_motif(expr)}")
        log(f"    rule: {expr}")
        log(f"    {prop.usage()}  ({time.time()-t0:.0f}s)")
        json.dump({"rules_so_far": rules},
                  open("/home/dohyung/.claude/jobs/a367775e/tmp/repro_rules.json", "w"), indent=2)

    # evaluate D1, D2, and each Pk on the test set (one budget, shared seeds)
    all_rules = {"D1": RULES["D1"], "D2": RULES["D2"],
                 **{k: rule_from_expr(v) for k, v in rules.items()}}
    per_inst = {name: {} for name in all_rules}
    log(f"\n[test] {len(TEST)} instances, GA {TEST_GA_POP}x{TEST_GA_GEN}, seeds {TEST_SEEDS}")
    for stem, veh in TEST:
        inst = load_dauzere(stem, veh)
        for name, r in all_rules.items():
            vals = [GA(inst, r, pop_size=TEST_GA_POP, n_gen=TEST_GA_GEN, seed=s).run()[0].fitness
                    for s in TEST_SEEDS]
            per_inst[name][f"{stem}_{veh}"] = sum(vals) / len(vals)
        log(f"  {stem}_{veh} done ({time.time()-t0:.0f}s)")

    keys = list(per_inst["D1"].keys())

    def col(name):
        return [per_inst[name][k] for k in keys]

    def mean(x):
        return sum(x) / len(x)

    log(f"\n===== RESULTS =====")
    log(f"test means: D1={mean(col('D1')):.1f}  D2={mean(col('D2')):.1f}  "
        + "  ".join(f"{k}={mean(col(k)):.1f}" for k in rules))

    summary = {"train": TRAIN, "test": TEST, "rules": rules,
               "config": {"K": K, "evolve": [EVOLVE_POP, EVOLVE_GEN],
                          "inner_ga": [INNER_GA_POP, INNER_GA_GEN],
                          "test_ga": [TEST_GA_POP, TEST_GA_GEN], "test_seeds": list(TEST_SEEDS)},
               "per_instance": per_inst, "runs": {}}

    log(f"\n{'run':<5} {'motif':>6} {'testMean':>9} {'vs D1 (p)':>18} {'vs D2 (p)':>18}")
    for k in rules:
        P = col(k); D1 = col("D1"); D2 = col("D2")
        w1 = stats.wilcoxon(P, D1, alternative="less").pvalue
        w2 = stats.wilcoxon(P, D2, alternative="less").pvalue
        win1 = sum(1 for a, b in zip(P, D1) if a < b)
        win2 = sum(1 for a, b in zip(P, D2) if a < b)
        motif = has_start_time_motif(rules[k])
        log(f"{k:<5} {str(motif):>6} {mean(P):>9.1f} "
            f"{f'{win1}/{len(P)} p={w1:.4f}':>18} {f'{win2}/{len(P)} p={w2:.4f}':>18}")
        summary["runs"][k] = {"expr": rules[k], "motif": motif, "test_mean": mean(P),
                              "vs_D1": {"wins": win1, "p": w1},
                              "vs_D2": {"wins": win2, "p": w2}}

    n_motif = sum(1 for k in rules if has_start_time_motif(rules[k]))
    n_sig = sum(1 for k in summary["runs"].values()
                if summary["runs"] and k["vs_D1"]["p"] < 0.05 and k["vs_D2"]["p"] < 0.05)
    log(f"\nmotif recurred in {n_motif}/{K} runs; "
        f"P beat BOTH D1 and D2 (p<0.05) in {n_sig}/{K} runs")
    summary["n_motif"] = n_motif
    summary["n_significant_both"] = n_sig
    summary["elapsed_sec"] = time.time() - t0

    json.dump(summary,
              open("/home/dohyung/.claude/jobs/a367775e/tmp/repro_campaign_result.json", "w"),
              indent=2)
    log(f"[done] {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
