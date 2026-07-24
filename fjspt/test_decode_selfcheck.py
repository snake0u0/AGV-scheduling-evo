"""Regression test: a decoded schedule fed back through the timing core must yield
the identical makespan. This ties the two front-ends (decode / replay) to one core.
Run: python -m fjspt.test_decode_selfcheck"""
import random

from .evaluator import decode, self_check
from .instance import load_dauzere
from .rules import RULES


def random_chromosome(inst, seed):
    rng = random.Random(seed)
    OS = [j for j, ops in enumerate(inst.jobs) for _ in ops]
    rng.shuffle(OS)
    MS = [rng.randrange(len(ops[o])) for ops in inst.jobs for o in range(len(ops))]
    return OS, MS


def main():
    fails = 0
    runs = 0
    for stem in ["01a", "07a", "13a"]:
        for veh in [2, 4, 6]:
            inst = load_dauzere(stem, veh)
            for rname, rule in RULES.items():
                for seed in range(10):
                    OS, MS = random_chromosome(inst, seed)
                    sol, sched = decode(inst, OS, MS, rule)
                    ok, replay = self_check(inst, sol, sched.cmax)
                    runs += 1
                    if not ok:
                        fails += 1
                        print(f"FAIL {stem} {veh}veh {rname} seed{seed}: "
                              f"decode={sched.cmax} replay={replay}")
    print(f"{runs} decode/replay pairs checked, {fails} mismatches")
    print("PASS - decode and timing core agree everywhere" if fails == 0
          else "FAIL")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
