"""AHD evaluation harness (stub): evaluate candidate rule expressions and rank them.

This mimics the inner loop of LLM-AHD (EoH/ReEvo): given a population of candidate
scoring expressions (which the LLM will generate), evaluate each on the simulator
and rank by fitness (mean tardiness). Swapping the static CANDIDATES list for
LLM-generated expressions = the full AHD loop. No LLM/API needed to run this.
"""
import statistics, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.agv_fms import simulate
from sim.rule import policy_from_expr

CONFIG = dict(n_machines=8, n_agvs=3, n_jobs=80, arrival_rate=0.16, grid_cols=4,
              ops_range=(2, 4), proc_range=(3, 9), due_tightness=2.5, machine_rule="EDD")
SEEDS = list(range(12))

# candidate scoring rules over features:
# travel_time, slack, task_wait, downstream_load, congestion, deadhead, battery_soc
CANDIDATES = [
    "-travel_time",                                                   # NV
    "-slack",                                                         # EDD
    "-(travel_time + 0.6*slack + 0.4*downstream_load - 0.3*task_wait)",
    "-(travel_time + 0.2*max(0, slack))",
    "-(0.8*travel_time + 0.5*downstream_load - 0.4*task_wait)",
    "-(travel_time + 0.15*slack + 0.3*downstream_load)",
    "task_wait - 1.5*travel_time",
    "-(travel_time*(1 + 0.05*downstream_load) + 0.1*max(0,slack))",
]


def fitness(expr):
    pol = policy_from_expr(expr)
    tard, mk = [], []
    for s in SEEDS:
        r = simulate(CONFIG, pol, seed=s)
        tard.append(r["mean_tardiness"]); mk.append(r["makespan"])
    return statistics.mean(tard), statistics.mean(mk)


if __name__ == "__main__":
    print(f"AHD eval harness | config M={CONFIG['n_machines']} AGV={CONFIG['n_agvs']} "
          f"jobs={CONFIG['n_jobs']} | {len(SEEDS)} seeds\n")
    results = [(expr, *fitness(expr)) for expr in CANDIDATES]
    results.sort(key=lambda x: x[1])  # by mean tardiness
    print(f"{'rank':<5}{'mean_tard':>11}{'makespan':>11}   rule")
    print("-" * 80)
    for i, (expr, t, m) in enumerate(results, 1):
        print(f"{i:<5}{t:>11.3f}{m:>11.2f}   {expr}")
    best = results[0]
    print(f"\nbest rule: {best[0]}\n(LLM-AHD loop = replace CANDIDATES with LLM-generated expressions, "
          f"keep best, mutate/reflect, repeat.)")
