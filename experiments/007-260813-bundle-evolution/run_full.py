"""Four-slot bundle evolution at the AHD-literature budget.

Budget comes from experiments/common.py (EVOLVE_POP x EVOLVE_GEN = 995 individuals over
65 LLM calls), not from convenience. A smaller run does not test the regime FunSearch,
MCTS-AHD and EoH were shown to need, so its result - win or lose - says nothing about
the method.

The system prompt carries no measured hint, so a load-balancing structure appearing in
the result is the loop's own finding.

Held-out instances are never touched during evolution; they are scored once at the end,
against the same hand-written seeds the population starts from.

Run:  python experiments/2026-08-13-bundle_evolution_full.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from experiments.common import EVOLVE_GEN, EVOLVE_POP, MAX_CALLS
from model.experiment import default_split, evaluate_bundle, evolve_bundle
from model.llm import _SEEDS_BUNDLE, _SYSTEM_BUNDLE, ClaudeBundleProposer
from model.llm_backend import cli_available

SEED_NAMES = ["BALANCED", "HAND", "MIX"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_full.json")


def main():
    if not cli_available():
        raise SystemExit("the `claude` CLI is not on PATH")
    assert "Measured fact" not in _SYSTEM_BUNDLE, \
        "the hint paragraph is back in the system prompt - this run would not be clean"

    train, test = default_split()
    n_children = EVOLVE_POP - max(2, EVOLVE_POP // 4)
    print(f"budget: pop {EVOLVE_POP} x {EVOLVE_GEN} generations "
          f"= {EVOLVE_POP + EVOLVE_GEN * n_children} individuals over {EVOLVE_GEN} LLM calls",
          flush=True)
    print(f"train {train}\ntest  {len(test)} instances (held out)\n", flush=True)

    proposer = ClaudeBundleProposer(max_calls=MAX_CALLS, reevo=True)
    record = []
    t0 = time.time()

    def log(msg):
        print(f"[{time.time() - t0:6.0f}s] {msg}", flush=True)

    best, best_fit, history = evolve_bundle(proposer, train, pop_size=EVOLVE_POP,
                                            n_gens=EVOLVE_GEN, log=log, record=record)
    elapsed = time.time() - t0

    print(f"\n{proposer.usage()}", flush=True)
    held_out = {"evolved": evaluate_bundle(best, test)}
    for name, seed in zip(SEED_NAMES, _SEEDS_BUNDLE):
        held_out[name] = evaluate_bundle(seed, test)
    print("held-out mean Cmax:", {k: round(v, 1) for k, v in held_out.items()}, flush=True)

    json.dump({
        "config": {"pop_size": EVOLVE_POP, "n_gens": EVOLVE_GEN, "max_calls": MAX_CALLS,
                   "hint_in_prompt": False, "train": train, "test": test,
                   "individuals": EVOLVE_POP + EVOLVE_GEN * n_children},
        "system_prompt": _SYSTEM_BUNDLE,
        "best_bundle": best,
        "best_train_fitness": best_fit,
        "history": history,
        "held_out": held_out,
        "record": record,
        "usage": {"calls": proposer.calls, "fails": proposer.fails,
                  "cost_usd": proposer.cost,
                  "in_tok": proposer.in_tok, "out_tok": proposer.out_tok},
        "elapsed_sec": elapsed,
    }, open(OUT, "w"), indent=2)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
