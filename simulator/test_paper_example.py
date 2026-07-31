"""Ground-truth unit test for the timing core.

The worked example of Berterottiere, Dauzere-Peres & Yugma (2024), Tables 2-3 and
Figures 4-6: two jobs, two operations each, three machines, two vehicles.

  processing            travel (row = from, col = to)
  J1 op1: M1=2, M2=1           LU  M1  M2  M3
     op2: M3=3            LU    0   2   4   3
  J2 op3: M1=4, M2=5      M1    3   0   2   1
     op4: M1=6, M3=3      M2    4   3   0   2
                          M3    2   1   3   0

The solution drawn in Figures 5 and 6 assigns op1->M2, op2->M3, op3->M1, op4->M3,
sequences M3 as (op2, op4), and routes vehicle 1 as (op1, op4), vehicle 2 as (op3, op2).
Reading that Gantt chart off the paper gives a makespan of 13:

  V2 carries J2 LU->M1 during [0,2]; op3 runs on M1 during [2,6]
  V1 carries J1 LU->M2 during [0,4]; op1 runs on M2 during [4,5]
  V2 goes empty M1->M2 during [2,4], waits for op1, carries M2->M3 during [5,7]
  op2 runs on M3 during [7,10]
  V1 goes empty M2->M1 during [4,7], carries M1->M3 during [7,8]
  op4 waits for M3 and runs during [10,13]

Run:  python -m fjspt.test_paper_example
"""
from .instance import Instance
from .solution import Solution
from .timing import simulate

EXPECTED_CMAX = 13


def build():
    inst = Instance(
        name="berterottiere2024-example",
        n_jobs=2,
        n_machines=3,
        jobs=[
            [[(1, 2), (2, 1)], [(3, 3)]],          # J1: op gid 1, 2
            [[(1, 4), (2, 5)], [(1, 6), (3, 3)]],  # J2: op gid 3, 4
        ],
        travel=[[0, 2, 4, 3],
                [3, 0, 2, 1],
                [4, 3, 0, 2],
                [2, 1, 3, 0]],
        n_vehicles=2,
        source={"paper": "Berterottiere et al. 2024, Tables 2-3, Figures 5-6"},
    )
    sol = Solution(
        machine_of={1: 2, 2: 3, 3: 1, 4: 3},
        machine_seq={1: [3], 2: [1], 3: [2, 4]},
        vehicle_of={1: 1, 2: 2, 3: 2, 4: 1},
        vehicle_seq={1: [1, 4], 2: [3, 2]},
    )
    return inst, sol


def main():
    inst, sol = build()
    s = simulate(inst, sol)
    print("operation  machine  arrive  start  end")
    for g in sorted(s.end):
        print(f"    {g}         M{sol.machine_of[g]}     {s.arrive[g]:>4}   "
              f"{s.start[g]:>4}  {s.end[g]:>4}")
    print(f"\nmakespan: ours = {s.cmax}, paper = {EXPECTED_CMAX}")
    ok = s.cmax == EXPECTED_CMAX
    print("PASS - timing core matches the published worked example" if ok
          else "FAIL - timing core disagrees with the published worked example")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
