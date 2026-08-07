"""Gates for the four-slot event-driven builder (`dispatch.build`).

G1 self-check     the built solution, fed back through the validated timing core,
                  must give the identical makespan. Catches any arithmetic that
                  drifted from timing.py.
G2 forced replay  with the slots forced to follow a published solution, the builder
                  must return that solution exactly and its published makespan.
                  Reproducing a schedule we did not produce is a stronger check than
                  agreeing with our own decoder.
G4 (the pure-constructive baseline) lives in experiments/, because simulator/
must not depend on the experiment harness.

Run: python -m simulator.test_dispatch
"""
from .dispatch import build, forced_slots, self_check
from .instance import DEROUSSI_STEMS, load_dauzere, load_deroussi
from .solution import parse_solution_file
from .timing import Params, check_consistency, simulate

# Hand-written slot rules, the literature defaults where one exists.
#   SPT   shortest processing time              (machine selection)
#   FIFO  earliest arrival at the machine       (operation sequencing)
#   D1    earliest arrival of the job           (vehicle selection, Han 2024)
#   EDD-ish earliest ready                      (task sequencing)
HAND = {
    "machine_select": lambda f: -f["proc_time"] - f["machine_free"],
    "op_sequence": lambda f: -f["arrival"],
    "vehicle_select": lambda f: -(f["agv_free"] + f["empty_travel"]),
    "task_sequence": lambda f: -f["arrival"],
}


def g2_forced_replay():
    print("G2  공표 해 강제 재현 (Deroussi 10개)")
    bad = []
    for stem in DEROUSSI_STEMS:
        inst = load_deroussi(stem)
        sol = parse_solution_file(inst.source["solution"])
        published = sol.meta["published_cmax"]

        fslots, fcommit = forced_slots(sol)
        built, sched = build(inst, fslots, Params(), on_commit=fcommit)

        same_assign = built.machine_of == sol.machine_of and built.vehicle_of == sol.vehicle_of
        same_mseq = {k: v for k, v in built.machine_seq.items() if v} == \
                    {k: v for k, v in sol.machine_seq.items() if v}
        same_vseq = {k: v for k, v in built.vehicle_seq.items() if v} == \
                    {k: v for k, v in sol.vehicle_seq.items() if v}
        ok = same_assign and same_mseq and same_vseq and sched.cmax == published
        print(f"  {stem:<8} 공표 {published:>6.0f}  builder {sched.cmax:>6}"
              f"  배정 {'=' if same_assign else 'X'}"
              f"  기계순서 {'=' if same_mseq else 'X'}"
              f"  차량순서 {'=' if same_vseq else 'X'}"
              f"   {'ok' if ok else 'MISMATCH'}")
        if not ok:
            bad.append(stem)
    return bad


def g1_self_check():
    print("\nG1  자기검증 - builder 의 해를 검증된 타이밍 코어에 되먹임")
    cases = [("deroussi", s, 2) for s in DEROUSSI_STEMS[:4]] + \
            [("dauzere", s, v) for s in ("01a", "07a", "15a", "18a") for v in (2, 4)]
    bad = []
    for family, stem, veh in cases:
        inst = (load_deroussi if family == "deroussi" else load_dauzere)(stem, veh)
        sol, sched = build(inst, HAND, Params())
        problems = check_consistency(inst, sol)
        ok, replay = self_check(inst, sol, sched.cmax)
        tag = "ok" if (ok and not problems) else "MISMATCH"
        print(f"  {stem+'/'+str(veh):<12} builder {sched.cmax:>6}  replay {replay:>6}"
              f"  구조검사 {len(problems)}건   {tag}")
        if not ok or problems:
            bad.append((stem, veh, problems))
    return bad


def main():
    bad2 = g2_forced_replay()
    bad1 = g1_self_check()
    if bad2 or bad1:
        raise SystemExit(f"FAIL - G2 {bad2}  G1 {bad1}")
    print("\nPASS - G1 자기검증, G2 강제 재현 통과")


if __name__ == "__main__":
    main()
