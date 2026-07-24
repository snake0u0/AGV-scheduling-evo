"""Main B-track campaign: evolve an AGV rule on a train split, then compare it to
D1/D2 on held-out test instances with multiple seeds and a Wilcoxon significance test.

Bigger budget than the first demo (per design section 9). Honest reporting: we test
whether the evolved rule significantly beats the fixed decodings on unseen instances.
"""
import json
import sys
import time

sys.path.insert(0, "/home/dohyung/project/research-agent")

from scipy import stats

from fjspt.experiment import evaluate_rule, evolve
from fjspt.ga import GA
from fjspt.instance import DAUZERE_STEMS, load_dauzere
from fjspt.llm import ClaudeRuleProposer
from fjspt.rules import RULES, rule_from_expr

# --- configuration ----------------------------------------------------------
# Train spans machine sizes (5/8/10) and both vehicle counts, kept to 3 instances
# with a cheap inner GA (it is only a ranking signal). The careful, multi-seed,
# larger-GA evaluation is reserved for the held-out test comparison.
TRAIN = [("01a", 2), ("13a", 2), ("07a", 4)]           # 5/10/8 machines, 2/2/4 veh
TEST_VEH = [2, 4]
TEST = [(s, v) for v in TEST_VEH for s in DAUZERE_STEMS
        if (s, v) not in TRAIN]                          # 33 held-out instances

EVOLVE_POP, EVOLVE_GEN = 16, 6
INNER_GA_POP, INNER_GA_GEN = 40, 40
INNER_SEEDS = (0,)

TEST_GA_POP, TEST_GA_GEN = 70, 70
TEST_SEEDS = (0, 1, 2)

LOG = open("/home/dohyung/.claude/jobs/a367775e/tmp/main_campaign.log", "a")


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    LOG.write(msg + "\n")
    LOG.flush()


def main():
    t0 = time.time()
    log(f"\n===== MAIN CAMPAIGN start =====")
    log(f"train({len(TRAIN)}): {TRAIN}")
    log(f"test({len(TEST)}): {TEST}")
    log(f"evolve pop{EVOLVE_POP}x{EVOLVE_GEN}, inner GA {INNER_GA_POP}x{INNER_GA_GEN} "
        f"seeds{INNER_SEEDS}; test GA {TEST_GA_POP}x{TEST_GA_GEN} seeds{TEST_SEEDS}")

    # --- baselines on train (same budget the evolution uses) ---
    d1_tr = evaluate_rule(RULES["D1"], TRAIN, pop=INNER_GA_POP, n_gen=INNER_GA_GEN,
                          seeds=INNER_SEEDS)
    d2_tr = evaluate_rule(RULES["D2"], TRAIN, pop=INNER_GA_POP, n_gen=INNER_GA_GEN,
                          seeds=INNER_SEEDS)
    log(f"[train baselines] D1={d1_tr:.1f}  D2={d2_tr:.1f}  ({time.time()-t0:.0f}s)")

    # --- evolve ---
    prop = ClaudeRuleProposer(model="sonnet", max_calls=50, reevo=True)
    best_expr, best_fit, hist = evolve(
        prop, TRAIN, pop_size=EVOLVE_POP, n_gens=EVOLVE_GEN,
        ga_pop=INNER_GA_POP, ga_gen=INNER_GA_GEN, seeds=INNER_SEEDS, log=log)
    log(f"[evolved] train_fit={best_fit:.1f}  rule={best_expr}")
    log(f"[usage] {prop.usage()}  ({time.time()-t0:.0f}s)")

    # --- test: per-instance mean makespan over seeds, for each rule ---
    rules = {"D1": RULES["D1"], "D2": RULES["D2"], "P": rule_from_expr(best_expr)}
    per_inst = {name: {} for name in rules}
    for stem, veh in TEST:
        inst = load_dauzere(stem, veh)
        for name, r in rules.items():
            vals = [GA(inst, r, pop_size=TEST_GA_POP, n_gen=TEST_GA_GEN, seed=s).run()[0].fitness
                    for s in TEST_SEEDS]
            per_inst[name][f"{stem}_{veh}"] = sum(vals) / len(vals)
        log(f"  {stem}_{veh}: D1={per_inst['D1'][f'{stem}_{veh}']:.0f} "
            f"D2={per_inst['D2'][f'{stem}_{veh}']:.0f} "
            f"P={per_inst['P'][f'{stem}_{veh}']:.0f}  ({time.time()-t0:.0f}s)")

    keys = list(per_inst["P"].keys())
    P = [per_inst["P"][k] for k in keys]
    D1 = [per_inst["D1"][k] for k in keys]
    D2 = [per_inst["D2"][k] for k in keys]
    best_base = [min(a, b) for a, b in zip(D1, D2)]

    def summ(x):
        return sum(x) / len(x)

    log(f"\n[test means] D1={summ(D1):.1f}  D2={summ(D2):.1f}  P={summ(P):.1f}  "
        f"best-of(D1,D2)={summ(best_base):.1f}")

    def wilcox(a, b, label):
        # paired, one-sided: is a < b (P better)?
        diff = [x - y for x, y in zip(a, b)]
        nz = [d for d in diff if d != 0]
        if not nz:
            log(f"  {label}: all ties")
            return
        try:
            w = stats.wilcoxon(a, b, alternative="less")
            wins = sum(1 for d in diff if d < 0)
            losses = sum(1 for d in diff if d > 0)
            log(f"  {label}: P better in {wins}/{len(diff)} (losses {losses}), "
                f"mean delta {summ(diff):+.1f}, Wilcoxon p(P<other)={w.pvalue:.4f}")
        except Exception as e:
            log(f"  {label}: wilcoxon failed ({e})")

    log("[significance] one-sided paired Wilcoxon, P vs each:")
    wilcox(P, D1, "P vs D1")
    wilcox(P, D2, "P vs D2")
    wilcox(P, best_base, "P vs best-of(D1,D2)")

    out = {
        "train": TRAIN, "test": TEST,
        "config": {"evolve_pop": EVOLVE_POP, "evolve_gen": EVOLVE_GEN,
                   "inner_ga": [INNER_GA_POP, INNER_GA_GEN], "inner_seeds": list(INNER_SEEDS),
                   "test_ga": [TEST_GA_POP, TEST_GA_GEN], "test_seeds": list(TEST_SEEDS)},
        "train_baselines": {"D1": d1_tr, "D2": d2_tr},
        "evolved": {"expr": best_expr, "train_fit": best_fit, "history": hist},
        "usage": prop.usage(),
        "per_instance": per_inst,
        "test_means": {"D1": summ(D1), "D2": summ(D2), "P": summ(P),
                       "best_of": summ(best_base)},
        "elapsed_sec": time.time() - t0,
    }
    json.dump(out, open("/home/dohyung/.claude/jobs/a367775e/tmp/main_campaign_result.json", "w"),
              indent=2)
    log(f"[done] {time.time()-t0:.0f}s  -> main_campaign_result.json")


if __name__ == "__main__":
    main()
