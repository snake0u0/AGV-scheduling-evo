"""Four-slot bundle evolution with no measured hint in the system prompt.

The system prompt used to end with a measured finding - that load balancing beat a
textbook greedy bundle by more than 2x - which made it impossible to tell whether the
loop rediscovers that structure or is simply told it. This run removes the paragraph
and changes nothing else, so it is the ablation's other arm: same seeds, same
population, same generations, same train split.

What to look for: whether the evolved bundle still keeps a load-balancing skeleton
(-queue_len / -arrival) and still beats the hand-written seeds on the held-out split.

Run:  python experiments/007-260813-bundle-evolution/run_nohint.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from model.experiment import default_split, evaluate_bundle, evolve_bundle
from model.llm import _SEEDS_BUNDLE, _SYSTEM_BUNDLE, ClaudeBundleProposer
from model.llm_backend import cli_available

POP_SIZE, N_GENS, MAX_CALLS = 20, 6, 50
SEED_NAMES = ["BALANCED", "HAND", "MIX"]

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_nohint.json")


def main():
    if not cli_available():
        raise SystemExit("the `claude` CLI is not on PATH")
    assert "Measured fact" not in _SYSTEM_BUNDLE, \
        "the hint paragraph is still in the system prompt - this is not the no-hint arm"

    train, test = default_split()
    print(f"train {train}\ntest  {len(test)} instances (held out)\n")

    proposer = ClaudeBundleProposer(max_calls=MAX_CALLS, reevo=True)
    record = []
    t0 = time.time()
    best, best_fit, history = evolve_bundle(proposer, train, pop_size=POP_SIZE,
                                            n_gens=N_GENS, record=record)
    elapsed = time.time() - t0

    print(f"\n{proposer.usage()}")
    held_out = {"evolved": evaluate_bundle(best, test)}
    for name, seed in zip(SEED_NAMES, _SEEDS_BUNDLE):
        held_out[name] = evaluate_bundle(seed, test)
    print("held-out mean Cmax:", {k: round(v, 1) for k, v in held_out.items()})

    json.dump({
        "config": {"pop_size": POP_SIZE, "n_gens": N_GENS, "max_calls": MAX_CALLS,
                   "hint_in_prompt": False, "train": train, "test": test},
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
    print("wrote", OUT)


if __name__ == "__main__":
    main()
