"""Controlled 2^2 factorial ablation of the two evolved-rule ingredients.

Factor A (start-time coupling):  off = -arrival (D1's term)
                                 on  = -max(arrival, machine_free)
Factor B (deadhead penalty):     off = (nothing)
                                 on  = - c*empty_travel

Four cells fully crossed; cell (off,off) is exactly D1. Each cell is evaluated on
every test instance (instance = block, paired design), so instance-to-instance
variation is removed. The replicate unit is the INSTANCE (33), not the GA seed:
GA seeds are repeated measurements, averaged per instance before analysis
(avoids pseudoreplication). Fixed adequate budget (GA 70x70, 3 seeds) per the
methodological lesson from the confound-removal re-eval.

Reports main effects, the A×B interaction, and Wilcoxon signed-rank tests, plus a
coefficient-sensitivity check for c in {0.3,0.5,0.7}.
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
C = 0.5                                   # canonical empty_travel coefficient

RULES_TO_EVAL = {
    "R00 (A off,B off)=D1": "-arrival",
    "R10 (A on, B off)":    "-max(arrival, machine_free)",
    "R01 (A off,B on)":     f"-arrival - {C}*empty_travel",
    "R11 (A on, B on)":     f"-max(arrival, machine_free) - {C}*empty_travel",
    "R11_c0.3":             "-max(arrival, machine_free) - 0.3*empty_travel",
    "R11_c0.7":             "-max(arrival, machine_free) - 0.7*empty_travel",
    "D2 (ref)":             None,          # RULES["D2"]
}

LOGP = "/home/dohyung/.claude/jobs/a367775e/tmp/ablation.log"
LOG = open(LOGP, "a")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    LOG.write(m + "\n"); LOG.flush()


def main():
    t0 = time.time()
    log(f"\n===== 2x2 FACTORIAL ABLATION =====")
    log(f"budget GA {GA_POP}x{GA_GEN}, seeds {SEEDS}, {len(TEST)} test instances "
        f"(block=instance, paired); empty_travel coef c={C}")

    compiled = {name: (RULES["D2"] if expr is None else rule_from_expr(expr))
                for name, expr in RULES_TO_EVAL.items()}
    per_inst = {name: {} for name in compiled}

    for stem, veh in TEST:
        inst = load_dauzere(stem, veh)
        for name, r in compiled.items():
            vals = [GA(inst, r, pop_size=GA_POP, n_gen=GA_GEN, seed=s).run()[0].fitness
                    for s in SEEDS]
            per_inst[name][f"{stem}_{veh}"] = sum(vals) / len(vals)   # avg over seeds -> 1 per instance
        log(f"  {stem}_{veh} done ({time.time()-t0:.0f}s)")

    keys = list(per_inst["R00 (A off,B off)=D1"].keys())

    def col(n):
        return [per_inst[n][k] for k in keys]

    def mean(x):
        return sum(x) / len(x)

    y00 = col("R00 (A off,B off)=D1")
    y10 = col("R10 (A on, B off)")
    y01 = col("R01 (A off,B on)")
    y11 = col("R11 (A on, B on)")

    log(f"\n===== CELL MEANS (lower=better) =====")
    log(f"                     B off        B on")
    log(f"  A off (arrival)   {mean(y00):>8.1f}   {mean(y01):>8.1f}")
    log(f"  A on  (max coupl) {mean(y10):>8.1f}   {mean(y11):>8.1f}")
    log(f"  [D2 reference: {mean(col('D2 (ref)')):.1f}]")

    # per-instance factorial contrasts (paired; instance = block)
    A_eff = [((a - o) + (b - c)) / 2 for o, a, c, b in zip(y00, y10, y01, y11)]  # coupling
    B_eff = [((c - o) + (b - a)) / 2 for o, a, c, b in zip(y00, y10, y01, y11)]  # deadhead
    AB_int = [(b - c) - (a - o) for o, a, c, b in zip(y00, y10, y01, y11)]        # interaction

    def wtest(effects, label):
        # H1: effect < 0 (ingredient REDUCES makespan). Signed-rank on per-instance effects.
        neg = sum(1 for e in effects if e < 0)
        pos = sum(1 for e in effects if e > 0)
        try:
            p_less = stats.wilcoxon(effects, alternative="less").pvalue
        except Exception:
            p_less = float("nan")
        log(f"  {label:<34} mean={mean(effects):>+8.1f}  "
            f"({neg} reduce / {pos} increase)  p(<0)={p_less:.4f}")
        return {"mean": mean(effects), "neg": neg, "pos": pos, "p_less": p_less}

    log(f"\n===== MAIN EFFECTS & INTERACTION (paired, n={len(keys)} instances) =====")
    log("  (negative mean = ingredient lowers makespan = good)")
    res = {}
    res["main_A_coupling"] = wtest(A_eff, "main effect A (coupling)")
    res["main_B_deadhead"] = wtest(B_eff, "main effect B (deadhead)")
    res["interaction_AB"] = wtest(AB_int, "interaction A x B")

    # each cell vs baseline D1 (=R00), and R11 vs each single-ingredient cell + D2
    def pair(a, b, label):
        diff = [x - y for x, y in zip(a, b)]
        neg = sum(1 for d in diff if d < 0)
        p = stats.wilcoxon(a, b, alternative="less").pvalue
        log(f"  {label:<34} mean d={mean(diff):>+8.1f}  wins {neg}/{len(diff)}  p={p:.4f}")
        return {"mean_delta": mean(diff), "wins": neg, "n": len(diff), "p": p}

    log(f"\n===== PAIRWISE (is left < right?) =====")
    res["R10_vs_D1"] = pair(y10, y00, "coupling-only vs D1")
    res["R01_vs_D1"] = pair(y01, y00, "deadhead-only vs D1")
    res["R11_vs_D1"] = pair(y11, y00, "both vs D1")
    res["R11_vs_R10"] = pair(y11, y10, "both vs coupling-only")
    res["R11_vs_R01"] = pair(y11, y01, "both vs deadhead-only")
    res["R11_vs_D2"] = pair(y11, col("D2 (ref)"), "both vs D2")

    log(f"\n===== SENSITIVITY: both-on at c in {{0.3,0.5,0.7}} =====")
    for name in ["R11_c0.3", "R11 (A on, B on)", "R11_c0.7"]:
        log(f"  {name:<20} mean={mean(col(name)):.1f}")

    out = {"config": {"budget": [GA_POP, GA_GEN], "seeds": list(SEEDS), "c": C,
                      "n_instances": len(keys)},
           "cell_means": {"y00_D1": mean(y00), "y10_coupling": mean(y10),
                          "y01_deadhead": mean(y01), "y11_both": mean(y11),
                          "D2": mean(col("D2 (ref)"))},
           "effects": res, "per_instance": per_inst,
           "sensitivity": {n: mean(col(n)) for n in ["R11_c0.3", "R11 (A on, B on)", "R11_c0.7"]},
           "elapsed_sec": time.time() - t0}
    json.dump(out, open("/home/dohyung/.claude/jobs/a367775e/tmp/ablation_result.json", "w"),
              indent=2)
    log(f"[done] {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
