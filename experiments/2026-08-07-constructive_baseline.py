"""G4: the pure-constructive baseline - what does a single pass with no search give?

This number has never been measured. Every figure this project has reported sits on
top of a GA, and even the 1s budget in 2026-08-06 still ran 66 generations at pop20.
Without it there is no bottom rung on the ablation ladder, and no way to say how much
of the quality comes from the rules versus from the search wrapped around them.

`simulator/dispatch.build` makes it measurable for the first time: one pass, four
hand-written slot rules, no population and no iteration. Each slot is varied on its own
against a neutral default so the four subproblems can be ranked by how much they matter
in the constructive regime - which is the regime an evolved rule would have to be good
in if the search is ever removed.

Reference for scale: the tuned GA at 600s is 21.1% above the literature on Dauzere
(2026-08-01b) and the 1s GA is 158.7% (2026-08-06).

No LLM calls. Seconds to run - there is no search.
"""
import os
import statistics as st
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.common import gap, reference
from simulator.dispatch import build
from simulator.instance import DAUZERE_STEMS, DEROUSSI_STEMS, load_dauzere, load_deroussi
from simulator.timing import Params, check_consistency

# Two null baselines, because the obvious one is pathological.
#
# NEUTRAL scores everything 0, so _argmax takes the first candidate: always machine
# "first eligible" and always vehicle 1. That is not "no preference", it is "one
# vehicle does all the transport", and measuring against it would credit a rule for
# merely using the fleet.
#
# BALANCED is the honest null: shortest queue, i.e. spread the load and express no
# other preference. Slot importance should be read off BALANCED; NEUTRAL is kept only
# to show how large the load-balancing effect alone is.
NEUTRAL = {
    "machine_select": lambda f: 0.0,
    "op_sequence": lambda f: 0.0,
    "vehicle_select": lambda f: 0.0,
    "task_sequence": lambda f: 0.0,
}
BALANCED = {
    "machine_select": lambda f: -f["queue_len"],
    "op_sequence": lambda f: 0.0,
    "vehicle_select": lambda f: -f["queue_len"],
    "task_sequence": lambda f: 0.0,
}

# Hand-written rules, one per slot. Each is the plain textbook choice for its decision.
HAND = {
    # shortest processing time, penalised by how busy that machine already is
    "machine_select": lambda f: -f["proc_time"] - f["machine_free"],
    # earliest arrival at the machine (FIFO)
    "op_sequence": lambda f: -f["arrival"],
    # the vehicle that can reach the pickup point soonest (Han 2024 Decoding1 in spirit)
    "vehicle_select": lambda f: -(f["agv_free"] + f["empty_travel"]),
    # the task that would be delivered earliest
    "task_sequence": lambda f: -f["arrival"],
}

CASES = ([("dauzere", s, v) for s in DAUZERE_STEMS for v in (2, 4, 6)]
         + [("deroussi", s, 2) for s in DEROUSSI_STEMS])


def load(family, stem, veh):
    return (load_dauzere if family == "dauzere" else load_deroussi)(stem, veh)


def run(slots, cases=CASES):
    out = []
    for family, stem, veh in cases:
        inst = load(family, stem, veh)
        sol, sched = build(inst, slots, Params())
        assert not check_consistency(inst, sol), (stem, veh)
        out.append({"family": family, "stem": stem, "veh": veh, "cmax": sched.cmax})
    return out


def summarise(label, recs, store=None):
    d = [gap(r) for r in recs if r["family"] == "dauzere"]
    e = [gap(r) for r in recs if r["family"] == "deroussi"]
    all_g = st.mean(gap(r) for r in recs)
    print(f"  {label:<34} 전체 {all_g:>7.1f}%"
          f"   Dauzere {st.mean(d):>7.1f}%   Deroussi {st.mean(e):>6.1f}%")
    if store is not None:
        store[label] = {"all": round(all_g, 2), "dauzere": round(st.mean(d), 2),
                        "deroussi": round(st.mean(e), 2), "runs": recs}
    return all_g


def main():
    t0 = time.time()
    store = {}
    print(f"순수 구성형 - 탐색 0회. {len(CASES)} 케이스 (Dauzere 54 + Deroussi 10)\n")

    print("전체 조합")
    summarise("NEUTRAL (첫 후보 고정 - 병리적)", run(NEUTRAL), store)
    bal = summarise("BALANCED (짧은 큐 = 부하분산만)", run(BALANCED), store)
    hand = summarise("HAND (손규칙 4개)", run(HAND), store)

    print("\n슬롯별 기여 - 손규칙에서 슬롯 하나만 BALANCED 로 되돌림")
    print("  (양수가 클수록 그 슬롯의 손규칙이 중요하다)")
    for slot in HAND:
        s = dict(HAND); s[slot] = BALANCED[slot]
        g = summarise(f"{slot} 만 BALANCED", run(s), store)
        print(f"  {'':<34} -> 손규칙 대비 {g - hand:+.1f}%p\n", end="")

    print("\n슬롯별 단독 효과 - BALANCED 에서 슬롯 하나만 손규칙으로")
    for slot in HAND:
        s = dict(BALANCED); s[slot] = HAND[slot]
        g = summarise(f"{slot} 만 손규칙", run(s), store)
        print(f"  {'':<34} -> BALANCED 대비 {bal - g:+.1f}%p\n", end="")

    print(f"\n참고 - 탐색을 붙였을 때 (같은 문헌 기준값)")
    print(f"  {'GA 1초 (pop20)':<34} Dauzere  158.7%   [2026-08-06]")
    print(f"  {'GA 600초 (pop1000)':<34} Dauzere   21.1%   [2026-08-01b]")
    import json
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "results", "2026-08-07-constructive_baseline_result.json")
    json.dump({"cases": len(CASES), "configs": store}, open(out, "w"), indent=1)
    print(f"\nwrote {out}")
    print(f"{time.time()-t0:.1f}초 소요")


if __name__ == "__main__":
    main()
