"""N1 joint-rule demo: evolve BOTH the AGV dispatching rule and the machine
sequencing rule together, and rank joint (agv_rule, machine_rule) candidates.

This is the N1 contribution's decision interface: an LLM-AHD loop would generate
pairs of scoring expressions (one over AGV features, one over machine features);
here we evaluate a static set to show the joint interface works end to end.
"""
import statistics, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.agv_fms import simulate
from sim.rule import policy_from_expr

CONFIG = dict(n_machines=8, n_agvs=3, n_jobs=90, arrival_rate=0.20, grid_cols=4,
              ops_range=(3, 5), proc_range=(3, 10), due_tightness=2.2)
SEEDS = list(range(12))

# (label, agv_expr, machine_expr)
# agv features:     travel_time, task_wait, slack, downstream_load, congestion, deadhead, battery_soc
# machine features: proc_time, slack, job_wait, remaining_ops, remaining_proc, downstream_load
JOINT = [
    ("NV + EDD (baseline)", "-travel_time", "-slack"),
    ("NV + SPT",            "-travel_time", "-proc_time"),
    ("travel+cong + EDD",   "-(travel_time + 0.3*downstream_load)", "-slack"),
    ("travel+urg + slack/spt", "-(travel_time + 0.2*max(0,slack))", "-(slack + 0.5*proc_time)"),
    ("travel+cong + spt/slack", "-(travel_time*(1+0.05*downstream_load))", "-(0.6*proc_time + 0.4*slack)"),
    ("travel + lwr",        "-travel_time", "-(remaining_proc + 0.3*slack)"),
]


def fitness(agv_expr, m_expr):
    ap, mp = policy_from_expr(agv_expr), policy_from_expr(m_expr)
    tard, mk = [], []
    for s in SEEDS:
        r = simulate(CONFIG, ap, seed=s, machine_policy=mp)
        tard.append(r["mean_tardiness"]); mk.append(r["makespan"])
    return statistics.mean(tard), statistics.mean(mk)


if __name__ == "__main__":
    print(f"N1 joint-rule demo | M={CONFIG['n_machines']} AGV={CONFIG['n_agvs']} "
          f"jobs={CONFIG['n_jobs']} | {len(SEEDS)} seeds\n")
    rows = [(lab, *fitness(a, m)) for lab, a, m in JOINT]
    rows.sort(key=lambda x: x[1])
    print(f"{'rank':<5}{'mean_tard':>11}{'makespan':>11}   joint rule (AGV | machine)")
    print("-" * 78)
    for i, (lab, t, m) in enumerate(rows, 1):
        print(f"{i:<5}{t:>11.3f}{m:>11.2f}   {lab}")
    print("\n→ joint (AGV+machine) rules plug into the same simulate(..., machine_policy=...) "
          "interface. LLM-AHD = generate these pairs, keep best, reflect/mutate, repeat.")
