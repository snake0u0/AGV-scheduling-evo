"""Continue a bundle-evolution run that stopped short of its budget.

A long run can lose the model partway through - a usage limit is the usual reason - and
the generations after that point recycle parents without evolving anything. This script
picks up the last real population from a previous result file and runs the generations
that are still owed, so the protocol budget is met without paying for the work already
done.

It counts an earlier generation as *effective* only if the model actually replied, so a
run that coasted for thirty generations is credited with the ones that evolved, not the
ones that were logged.

Run:  python experiments/2026-08-13-bundle_evolution_resume.py [previous_result.json]
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.common import EVOLVE_GEN, EVOLVE_POP, MAX_CALLS
from model.experiment import default_split, evaluate_bundle, evolve_bundle
from model.llm import _SEEDS_BUNDLE, _SYSTEM_BUNDLE, ClaudeBundleProposer
from model.llm_backend import cli_available

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "results")
PREV = os.path.join(RESULTS, "2026-08-13-bundle_evolution_full_result.json")
STEM = "2026-08-13-bundle_evolution_full_resumed"
SEED_NAMES = ["BALANCED", "HAND", "MIX"]


def effective_generations(record):
    """Generations whose proposer call actually returned a reply."""
    return sum(1 for e in record
               if e["gen"] > 0 and (e.get("call", {}).get("response") or "").strip())


def credited_generations(prev):
    """Effective generations behind `prev`, including any it inherited.

    A resume can itself be cut short, so the count has to carry forward across a chain
    of them; reading only this file's record would credit the last link alone and ask
    for generations that were already paid for.
    """
    carried = prev.get("config", {}).get("effective_generations_total")
    return carried if carried is not None else effective_generations(prev["record"])


def next_output_path():
    """A fresh numbered file, so a later resume never overwrites an earlier one."""
    n = 2
    while os.path.exists(os.path.join(RESULTS, f"{STEM}{n}_result.json")):
        n += 1
    return os.path.join(RESULTS, f"{STEM}{n}_result.json")


def main():
    if not cli_available():
        raise SystemExit("the `claude` CLI is not on PATH")
    assert "Measured fact" not in _SYSTEM_BUNDLE, \
        "the hint paragraph is back in the system prompt - this run would not be clean"

    prev_path = sys.argv[1] if len(sys.argv) > 1 else PREV
    prev = json.load(open(prev_path))
    done = credited_generations(prev)
    owed = EVOLVE_GEN - done
    if owed <= 0:
        raise SystemExit(f"{os.path.basename(prev_path)} already has {done} effective "
                         f"generations; the budget is {EVOLVE_GEN}")

    init_pop = [row["bundle"] for row in prev["record"][-1]["population"]]
    train, test = default_split()

    print(f"resuming {os.path.basename(prev_path)}", flush=True)
    print(f"  effective generations so far : {done}/{EVOLVE_GEN}  "
          f"(this file logged {len(prev['record']) - 1} gens, "
          f"{prev['usage']['fails']} calls failed)", flush=True)
    print(f"  generations still owed       : {owed}", flush=True)
    print(f"  starting population          : {len(init_pop)} bundles, "
          f"best {prev['best_train_fitness']:.1f}\n", flush=True)

    out_path = next_output_path()
    proposer = ClaudeBundleProposer(max_calls=MAX_CALLS, reevo=True)
    record = []
    t0 = time.time()

    def log(msg):
        print(f"[{time.time() - t0:6.0f}s] {msg}", flush=True)

    best, best_fit, history = evolve_bundle(proposer, train, pop_size=EVOLVE_POP,
                                            n_gens=owed, log=log, record=record,
                                            init_pop=init_pop)
    elapsed = time.time() - t0
    gained = effective_generations(record)

    print(f"\n{proposer.usage()}", flush=True)
    print(f"effective generations this run: {gained}/{owed}", flush=True)
    print(f"total effective across both runs: {done + gained}/{EVOLVE_GEN}", flush=True)

    held_out = {"evolved": evaluate_bundle(best, test)}
    for name, seed in zip(SEED_NAMES, _SEEDS_BUNDLE):
        held_out[name] = evaluate_bundle(seed, test)
    print("held-out mean Cmax:", {k: round(v, 1) for k, v in held_out.items()}, flush=True)

    json.dump({
        "config": {"pop_size": EVOLVE_POP, "n_gens_requested": owed,
                   "max_calls": MAX_CALLS, "hint_in_prompt": False,
                   "train": train, "test": test,
                   "resumed_from": os.path.basename(prev_path),
                   "effective_generations_before": done,
                   "effective_generations_this_run": gained,
                   "effective_generations_total": done + gained,
                   "budget_generations": EVOLVE_GEN},
        "system_prompt": _SYSTEM_BUNDLE,
        "best_bundle": best,
        "best_train_fitness": best_fit,
        "history": history,
        "history_before": prev["history"],
        "held_out": held_out,
        "record": record,
        "usage": {"calls": proposer.calls, "fails": proposer.fails,
                  "cost_usd": proposer.cost,
                  "in_tok": proposer.in_tok, "out_tok": proposer.out_tok},
        "elapsed_sec": elapsed,
    }, open(out_path, "w"), indent=2)
    print("wrote", out_path, flush=True)


if __name__ == "__main__":
    main()
