"""Campaign runner — evaluate P (joint LLM-AHD) vs baselines on a regime, report on TEST seeds.

Methods (KIIE table):
  baseline  NV+EDD reference
  B1        best classical joint (machine x AGV grid, selected on valid)
  B5        machine-only LLM-AHD (AGV fixed to NV)         -> shows joint > machine-only
  B6        AGV-only LLM-AHD     (machine fixed to EDD)    -> ablation
  P         joint LLM-AHD (both evolved)                   -> proposed
(B2 GP and B3/B4 DRL are separate, heavier baselines — added later.)

Rules are evolved on TRAIN, selected on VALID, reported on TEST only. Writes
docs/research/results/<regime>.csv. Uses the real `claude` CLI when available, else MockLLM.

Run:  AHD_REGIME=L1 AHD_GEN=8 AHD_TRAIN_N=8 python -m ahd.campaign
"""
import os, sys, csv, statistics, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.agv_fms import simulate
from sim.rule import policy_from_expr
from sim.policies import POLICIES, MACHINE_POLICIES
from sim.configs import REGIMES, LARGE_REGIMES, TRAIN_SEEDS, VALID_SEEDS, TEST_SEEDS
from ahd.llm import MockLLM, ClaudeCliLLM, FrozenSide, render, cli_available
from ahd.loop import evolve, fitness
from ahd.gp import gp_evolve

METRIC_KEYS = ("mean_tardiness", "makespan", "throughput", "agv_util")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "docs", "research", "results")


def eval_metrics(ap, mp, config, seeds):
    """Mean test metrics for AGV policy fn `ap` + machine policy fn `mp`."""
    rows = [simulate(config, ap, seed=s, machine_policy=mp) for s in seeds]
    return {k: round(statistics.mean(r[k] for r in rows), 2) for k in METRIC_KEYS}


def pair_policies(pair):
    return policy_from_expr(render(pair[0])), policy_from_expr(render(pair[1]))


def best_classical_joint(config):
    """Grid over classical machine x AGV rules; pick the pair with lowest VALID tardiness."""
    best = None
    for mn, mp in MACHINE_POLICIES.items():
        for an, ap in POLICIES.items():
            if an == "RANDOM":
                continue
            v = statistics.mean(simulate(config, ap, seed=s, machine_policy=mp)["mean_tardiness"]
                                for s in VALID_SEEDS)
            if best is None or v < best[0]:
                best = (v, f"{an}+{mn}", ap, mp)
    return best


def run_evolved(config, proposer, train, gens):
    """Evolve on train, select the elite with best VALID fitness; return the selected pair."""
    _, _, _, elites = evolve(config, train, proposer, simulate,
                             pop_size=12, generations=gens, elite=4, verbose=False)
    return min(elites, key=lambda p: fitness(p, config, VALID_SEEDS, simulate))


def main():
    regime = os.environ.get("AHD_REGIME", "R3")
    config = {**REGIMES, **LARGE_REGIMES}[regime]
    gens = int(os.environ.get("AHD_GEN", "8"))
    train = TRAIN_SEEDS[:int(os.environ.get("AHD_TRAIN_N", str(len(TRAIN_SEEDS))))]
    use_cli = cli_available() and os.environ.get("AHD_FORCE_MOCK") != "1"  # FORCE_MOCK=1 for free testing
    newprop = (lambda: ClaudeCliLLM()) if use_cli else (lambda: MockLLM(seed=0))
    tag = "CLAUDE-CLI" if use_cli else "MOCK"

    print(f"CAMPAIGN | regime={regime} M={config['n_machines']} AGV={config['n_agvs']} "
          f"flex={config.get('flex',1)} cong={config.get('congestion_alpha',0.0)} | {tag} | "
          f"{len(train)} train / {len(VALID_SEEDS)} valid / {len(TEST_SEEDS)} test | gens={gens}\n")

    rows = []  # (method, metrics, rule)
    rows.append(("baseline NV+EDD",
                 eval_metrics(POLICIES["NV"], MACHINE_POLICIES["M_EDD"], config, TEST_SEEDS), "NV+EDD"))

    vfit, b1name, ap, mp = best_classical_joint(config)
    rows.append(("B1 best-classical", eval_metrics(ap, mp, config, TEST_SEEDS), b1name))

    # B2: GP hyper-heuristic (CPU-only, no LLM) — traditional-AHD comparison
    gpa, gpm = gp_evolve(config, train, VALID_SEEDS, seed=0,
                         generations=int(os.environ.get("AHD_GP_GEN", "12")),
                         pop_size=int(os.environ.get("AHD_GP_POP", "24")))
    rows.append(("B2 GP-joint", eval_metrics(policy_from_expr(gpa), policy_from_expr(gpm), config, TEST_SEEDS),
                 f"AGV[{gpa}] M[{gpm}]"))

    gap = int(os.environ.get("AHD_GAP", "60" if use_cli else "0"))  # pause between LLM runs (anti-throttle)

    def evolved_row(label, proposer, fixnote):
        sel = run_evolved(config, proposer, train, gens)
        if hasattr(proposer, "usage"):
            print(f"  [{label}] {proposer.usage()}")
        return (label, eval_metrics(*pair_policies(sel), config, TEST_SEEDS), fixnote(sel))

    rows.append(evolved_row("P joint-LLM", newprop(),
                            lambda s: f"AGV[{render(s[0])}] M[{render(s[1])}]"))
    time.sleep(gap)
    rows.append(evolved_row("B5 machine-only-LLM", FrozenSide(newprop(), fix_agv="-travel_time"),
                            lambda s: f"M[{render(s[1])}] (AGV=NV)"))
    time.sleep(gap)
    rows.append(evolved_row("B6 AGV-only-LLM", FrozenSide(newprop(), fix_machine="-slack"),
                            lambda s: f"AGV[{render(s[0])}] (M=EDD)"))

    base = rows[0][1]["mean_tardiness"]
    print(f"{'method':<22}{'tardiness':>11}{'vs base':>9}{'makespan':>10}{'thrput':>8}{'util':>7}  rule")
    print("-" * 100)
    for name, m, rule in rows:
        imp = (base - m["mean_tardiness"]) / base * 100
        print(f"{name:<22}{m['mean_tardiness']:>11.2f}{imp:>8.1f}%{m['makespan']:>10.1f}"
              f"{m['throughput']:>8.3f}{m['agv_util']:>7.2f}  {rule[:46]}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, f"{regime}.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", *METRIC_KEYS, "vs_base_pct", "rule"])
        for name, m, rule in rows:
            imp = round((base - m["mean_tardiness"]) / base * 100, 2)
            w.writerow([name, *[m[k] for k in METRIC_KEYS], imp, rule])
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
