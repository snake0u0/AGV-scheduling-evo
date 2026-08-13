"""Replay gate: feed each published Deroussi & Norre solution through the timing core
and require the makespan stated in its own header.

This is the strongest end-to-end check available - it exercises the parser, the travel
matrix, the operation numbering and the timing recurrence at once, against numbers we
did not produce. The travel matrix comes from the authors' dataset page
(DeroussiNorreTravelTimes/SOURCE.md).

Run: python -m simulator.test_replay_deroussi
"""
from .instance import DEROUSSI_STEMS, load_deroussi
from .solution import parse_solution_file
from .timing import Params, check_consistency, simulate


def main():
    bad = []
    for stem in DEROUSSI_STEMS:
        inst = load_deroussi(stem)
        sol = parse_solution_file(inst.source["solution"])
        check_consistency(inst, sol)
        cmax = simulate(inst, sol, Params()).cmax
        published = sol.meta["published_cmax"]
        print(f"{stem:<8} published {published:>6.0f}   replay {cmax:>6}"
              f"   {'ok' if cmax == published else 'MISMATCH'}")
        if cmax != published:
            bad.append((stem, published, cmax))

    if bad:
        raise SystemExit(f"FAIL - {len(bad)} mismatches: {bad}")
    print(f"PASS - {len(DEROUSSI_STEMS)}/{len(DEROUSSI_STEMS)} published makespans reproduced")


if __name__ == "__main__":
    main()
