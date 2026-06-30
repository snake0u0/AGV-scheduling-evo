"""Entry point for the LLM-AHD joint evolution loop (mock LLM, no API key needed).

Run from the project root:  python -m ahd.run   (or: python ahd/run.py)

Swap MockLLM for a real LLM proposer to get the full LLM-AHD loop (see skill `ahd-loop`).
Sanity goal: the evolved best should beat the NV+EDD baseline on mean tardiness.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.agv_fms import simulate            # fast custom engine (default)
from sim.rule import policy_from_expr
from sim.configs import REGIMES, LARGE_REGIMES, TRAIN_SEEDS, VALID_SEEDS, TEST_SEEDS
from ahd.llm import MockLLM, ClaudeCliLLM, render, cli_available
from ahd.loop import evolve, fitness

# Overridable via env: AHD_REGIME (name in REGIMES/LARGE_REGIMES), AHD_GEN, AHD_TRAIN_N (budget knobs).
REGIME = os.environ.get("AHD_REGIME", "R3")


def main():
    use_cli = cli_available()
    reevo = os.environ.get("AHD_REEVO", "1") != "0"     # AHD_REEVO=0 -> rank-only ablation
    proposer = ClaudeCliLLM(reevo=reevo) if use_cli else MockLLM(seed=0)
    tag = (f"CLAUDE-CLI/{'reevo' if reevo else 'rank-only'}") if use_cli else "MOCK"

    config = {**REGIMES, **LARGE_REGIMES}[REGIME]
    gens = int(os.environ.get("AHD_GEN", "10"))
    train = TRAIN_SEEDS[:int(os.environ.get("AHD_TRAIN_N", str(len(TRAIN_SEEDS))))]

    baseline = ({"travel_time": -1.0}, {"slack": -1.0})           # NV + EDD
    base_test = fitness(baseline, config, TEST_SEEDS, simulate)
    print(f"LLM-AHD joint loop ({tag}) | regime={REGIME} M={config['n_machines']} "
          f"AGV={config['n_agvs']} jobs={config['n_jobs']} flex={config.get('flex',1)} "
          f"cong={config.get('congestion_alpha',0.0)}")
    print(f"split: {len(train)} train / {len(VALID_SEEDS)} valid / {len(TEST_SEEDS)} test seeds | gens={gens}")
    print(f"baseline NV+EDD test mean_tardiness = {base_test:.3f}\n")

    # Evolve on TRAIN only; evolve returns the final elite pool.
    _, _, _, elites = evolve(config, train, proposer, simulate,
                             pop_size=12, generations=gens, elite=4)

    # Select the reported rule on VALID (held out from evolution).
    selected = min(elites, key=lambda p: fitness(p, config, VALID_SEEDS, simulate))

    # Report on TEST (held out from both evolution and selection).
    test_fit = fitness(selected, config, TEST_SEEDS, simulate)
    print(f"\nselected rule (best on valid) | test mean_tardiness = {test_fit:.3f}  "
          f"({(base_test - test_fit) / base_test * 100:+.1f}% vs NV+EDD baseline)")
    print(f"  AGV rule:     {render(selected[0])}")
    print(f"  machine rule: {render(selected[1])}")
    print("\n[OK] evolved rule beats NV+EDD baseline on held-out test"
          if test_fit < base_test else
          "\n[WARN] did not beat baseline on test — increase generations/pop or check config")
    if use_cli:
        print(proposer.usage())


if __name__ == "__main__":
    main()
