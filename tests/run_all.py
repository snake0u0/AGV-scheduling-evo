"""Run every gate. Anything that touches model/ or simulator/ must pass this first.

These are not unit tests. Each one is evidence that the simulator computes the right
thing, and most of it is checked against numbers we did not produce - a published
worked example, ten published solutions replayed exactly. That is what makes results
built on this simulator citable, so a failure here invalidates the research output,
not just the code.

  paper_example     the timing recurrence against the worked example in the literature
  replay_deroussi   ten published solutions, each reproducing its own published makespan
  dispatch          the builder agrees with the timing core, and can be forced to
                    reproduce a published schedule exactly
  reported_numbers  every number quoted in a report is still derivable from the
                    stored results
  determinism       a stored evolved bundle re-evaluates to the fitness it was saved
                    with - the gate that proves a refactor changed no behaviour

Run:  python -m tests.run_all
"""
import json
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from model.experiment import default_split, evaluate_bundle
from tests import (test_dispatch, test_paper_example, test_replay_deroussi,
                   test_reported_numbers)

RESULTS = os.path.join(ROOT, "data", "results")


def determinism():
    """Every stored bundle result must re-evaluate to the fitness it recorded.

    Constructive evaluation has no seeds and no search, so this is an exact equality,
    not a tolerance - any drift means the evaluator changed.
    """
    files = sorted(f for f in os.listdir(RESULTS) if f.endswith("_result.json")
                   and "bundle_evolution" in f)
    if not files:
        print("  no stored bundle runs to check")
        return
    train, test = default_split()
    for f in files:
        r = json.load(open(os.path.join(RESULTS, f)))
        got_train = evaluate_bundle(r["best_bundle"], train)
        got_test = evaluate_bundle(r["best_bundle"], test)
        ok = (got_train == r["best_train_fitness"]
              and got_test == r["held_out"]["evolved"])
        print(f"  {f:<52} train {got_train:.4f}  test {got_test:.4f}  "
              f"{'ok' if ok else 'MISMATCH'}")
        if not ok:
            raise SystemExit(f"FAIL - {f} does not reproduce its stored fitness")
    print(f"PASS - {len(files)} stored run(s) reproduce their fitness exactly")


GATES = [
    ("paper_example", test_paper_example.main),
    ("replay_deroussi", test_replay_deroussi.main),
    ("dispatch", test_dispatch.main),
    ("reported_numbers", test_reported_numbers.main),
    ("determinism", determinism),
]


def main():
    failed = []
    for name, fn in GATES:
        print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
        try:
            fn()
        except SystemExit as e:
            print(e)
            failed.append(name)
        except Exception:
            traceback.print_exc()
            failed.append(name)

    print(f"\n{'=' * 70}")
    if failed:
        raise SystemExit(f"FAIL - {len(failed)}/{len(GATES)} gates failed: {failed}")
    print(f"PASS - all {len(GATES)} gates green")


if __name__ == "__main__":
    main()
