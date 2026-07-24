"""Confound-removal re-evaluation (reproducibility report section 5.1).

Evaluate ALL four evolved rules (P_main from the main campaign, P1/P2/P3 from the
reproducibility campaign) against D1/D2 under ONE identical, higher budget
(GA 70x70, seeds 0-2 = the main campaign's test budget). This removes the budget
confound: the reproducibility run used a lighter GA (60x60, 2 seeds) which may have
added noise that washed out the D1 advantage.

Question: at this budget, do the evolved rules beat D1, or was P_main special?
No LLM calls - pure evaluation.
"""
import json
import sys
import time

sys.path.insert(0, "/home/dohyung/project/research-agent")

from scipy import stats

from fjspt.ga import GA
from fjspt.instance import DAUZERE_STEMS, load_dauzere
from fjspt.rules import RULES, rule_from_expr

TRAIN = [("01a", 2), ("13a", 2), ("07a", 4)]
TEST = [(s, v) for v in (2, 4) for s in DAUZERE_STEMS if (s, v) not in TRAIN]

GA_POP, GA_GEN = 70, 70
SEEDS = (0, 1, 2)

EVOLVED = {
    "P_main": "-max(arrival, machine_free) - 0.5*empty_travel - 0.3*max(0, wait-empty_travel) "
              "- 0.05*agv_cum_travel/(machine_free+1) - 0.01*agv_free",
    "P1": "-arrival - 0.5*empty_travel - 0.2*machine_free/(agv_free+1) "
          "- 0.1*agv_cum_travel/(agv_free+1)",
    "P2": "-(arrival + 0.7*empty_travel + 0.1*wait) - 0.3*max(0, machine_free-arrival)",
    "P3": "-max(arrival,machine_free)-wait/(remaining_ops+1)",
}

LOGP = "/home/dohyung/.claude/jobs/a367775e/tmp/confound_eval.log"
LOG = open(LOGP, "a")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    LOG.write(m + "\n"); LOG.flush()


def main():
    t0 = time.time()
    log(f"\n===== CONFOUND-REMOVAL RE-EVAL =====")
    log(f"budget GA {GA_POP}x{GA_GEN}, seeds {SEEDS}; {len(TEST)} test instances")

    rules = {"D1": RULES["D1"], "D2": RULES["D2"],
             **{k: rule_from_expr(v) for k, v in EVOLVED.items()}}
    per_inst = {name: {} for name in rules}

    for stem, veh in TEST:
        inst = load_dauzere(stem, veh)
        for name, r in rules.items():
            vals = [GA(inst, r, pop_size=GA_POP, n_gen=GA_GEN, seed=s).run()[0].fitness
                    for s in SEEDS]
            per_inst[name][f"{stem}_{veh}"] = sum(vals) / len(vals)
        log(f"  {stem}_{veh} done ({time.time()-t0:.0f}s)")

    keys = list(per_inst["D1"].keys())

    def col(n):
        return [per_inst[n][k] for k in keys]

    def mean(x):
        return sum(x) / len(x)

    D1, D2 = col("D1"), col("D2")
    log(f"\n===== RESULTS (GA {GA_POP}x{GA_GEN}, {len(SEEDS)} seeds) =====")
    log(f"test means: D1={mean(D1):.1f}  D2={mean(D2):.1f}  "
        + "  ".join(f"{k}={mean(col(k)):.1f}" for k in EVOLVED))

    log(f"\n{'rule':<8} {'testMean':>9} {'vs D1: wins  p':>22} {'vs D2: wins  p':>22} "
        f"{'vs best-of: wins  p':>22}")
    best_base = [min(a, b) for a, b in zip(D1, D2)]
    summary = {"budget": [GA_POP, GA_GEN], "seeds": list(SEEDS), "test": TEST,
               "evolved": EVOLVED, "per_instance": per_inst, "runs": {}}
    for k in EVOLVED:
        P = col(k)
        w1 = stats.wilcoxon(P, D1, alternative="less").pvalue
        w2 = stats.wilcoxon(P, D2, alternative="less").pvalue
        wb = stats.wilcoxon(P, best_base, alternative="less").pvalue
        n1 = sum(1 for a, b in zip(P, D1) if a < b)
        n2 = sum(1 for a, b in zip(P, D2) if a < b)
        nb = sum(1 for a, b in zip(P, best_base) if a < b)
        log(f"{k:<8} {mean(P):>9.1f} {f'{n1}/{len(P)}  p={w1:.4f}':>22} "
            f"{f'{n2}/{len(P)}  p={w2:.4f}':>22} {f'{nb}/{len(P)}  p={wb:.4f}':>22}")
        summary["runs"][k] = {"test_mean": mean(P),
                              "vs_D1": {"wins": n1, "p": w1},
                              "vs_D2": {"wins": n2, "p": w2},
                              "vs_best_of": {"wins": nb, "p": wb}}

    n_both = sum(1 for v in summary["runs"].values()
                 if v["vs_D1"]["p"] < 0.05 and v["vs_D2"]["p"] < 0.05)
    n_d1 = sum(1 for v in summary["runs"].values() if v["vs_D1"]["p"] < 0.05)
    n_d2 = sum(1 for v in summary["runs"].values() if v["vs_D2"]["p"] < 0.05)
    log(f"\nunder this higher budget: beat D1 (p<0.05) in {n_d1}/{len(EVOLVED)}, "
        f"beat D2 in {n_d2}/{len(EVOLVED)}, beat BOTH in {n_both}/{len(EVOLVED)}")
    summary["n_beat_d1"] = n_d1
    summary["n_beat_d2"] = n_d2
    summary["n_beat_both"] = n_both
    summary["elapsed_sec"] = time.time() - t0

    json.dump(summary,
              open("/home/dohyung/.claude/jobs/a367775e/tmp/confound_eval_result.json", "w"),
              indent=2)
    log(f"[done] {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
