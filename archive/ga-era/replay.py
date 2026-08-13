"""Replay verification: feed a published solution through our timing core and
check we get the published makespan.

No policy is involved - the published file fixes all four subproblems - so this
isolates the timing logic. It is the gate for everything built on top.

Run:  python -m fjspt.replay
"""
import sys

from .instance import DAUZERE_STEMS, DAUZERE_VEHICLES, load_dauzere
from .solution import parse_solution_file
from .timing import Params, ScheduleError, check_consistency, simulate


def replay_one(inst, params=Params()):
    sol = parse_solution_file(inst.source["solution"])
    problems = check_consistency(inst, sol)
    if problems:
        return {"ok": False, "published": sol.meta["published_cmax"],
                "ours": None, "problems": problems}
    try:
        sched = simulate(inst, sol, params)
    except ScheduleError as e:
        return {"ok": False, "published": sol.meta["published_cmax"],
                "ours": None, "problems": [str(e)]}
    published = sol.meta["published_cmax"]
    return {"ok": sched.cmax == published, "published": published,
            "ours": sched.cmax, "problems": [],
            "n_transported": len(sched.transported), "n_ops": inst.n_ops}


def replay_dauzere(params=Params(), verbose=True):
    rows, n_ok = [], 0
    for stem in DAUZERE_STEMS:
        for veh in DAUZERE_VEHICLES:
            inst = load_dauzere(stem, veh)
            r = replay_one(inst, params)
            r["instance"], r["vehicles"] = stem, veh
            rows.append(r)
            n_ok += bool(r["ok"])
            if verbose:
                if r["ours"] is None:
                    detail = f"FAILED  {r['problems'][0][:70]}"
                else:
                    diff = r["ours"] - r["published"]
                    detail = (f"{'MATCH ' if r['ok'] else 'differ'}  ours={r['ours']:>8.1f}"
                              f"  published={r['published']:>8.1f}"
                              f"  diff={diff:+.1f}"
                              f"  ({r['n_transported']}/{r['n_ops']} transported)")
                print(f"{stem} {veh}veh  {detail}")
    return rows, n_ok


def main():
    print("Replay verification: Dauzere lineage, 18 instances x {2,4,6} vehicles\n")
    rows, n_ok = replay_dauzere()
    total = len(rows)
    print(f"\n{'=' * 70}")
    print(f"exact matches: {n_ok}/{total}")
    if n_ok != total:
        diffs = [r["ours"] - r["published"] for r in rows if r["ours"] is not None]
        if diffs:
            over = sum(1 for d in diffs if d > 0)
            print(f"of the {len(diffs)} that ran: {over} above published, "
                  f"{len(diffs) - over} at or below")
            print(f"difference range: {min(diffs):+.1f} .. {max(diffs):+.1f}")
        failed = [r for r in rows if r["ours"] is None]
        if failed:
            print(f"{len(failed)} could not be simulated; first problem: "
                  f"{failed[0]['problems'][0]}")
        return 1
    print("timing core reproduces every published makespan exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
