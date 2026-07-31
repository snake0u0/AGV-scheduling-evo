"""Run the AGV-FMS simulator across policies x seeds and print a comparison table.

Usage: python -m sim.run_eval   (from research-agent/)  or  python sim/run_eval.py
"""
import statistics, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.agv_fms import simulate
from sim.policies import POLICIES

CONFIGS = {
    "small": dict(n_machines=6, n_agvs=3, n_jobs=60, arrival_rate=0.18,
                  grid_cols=3, ops_range=(2, 4), proc_range=(3, 9),
                  due_tightness=3.0, machine_rule="EDD"),
    "medium": dict(n_machines=10, n_agvs=4, n_jobs=120, arrival_rate=0.25,
                   grid_cols=4, ops_range=(3, 5), proc_range=(3, 9),
                   due_tightness=3.0, machine_rule="EDD"),
}
SEEDS = list(range(10))
METRICS = ["makespan", "mean_tardiness", "mean_flowtime", "throughput", "agv_util", "deadhead_ratio"]


def run_config(name, cfg):
    print(f"\n=== config: {name}  (M={cfg['n_machines']} AGV={cfg['n_agvs']} jobs={cfg['n_jobs']}) "
          f"| {len(SEEDS)} seeds ===")
    rows = {}
    for pname, pol in POLICIES.items():
        agg = {m: [] for m in METRICS}
        for s in SEEDS:
            r = simulate(cfg, pol, seed=s)
            for m in METRICS:
                agg[m].append(r[m])
        rows[pname] = {m: statistics.mean(v) for m, v in agg.items()}
    # print table sorted by mean_tardiness (primary objective)
    order = sorted(rows, key=lambda p: rows[p]["mean_tardiness"])
    hdr = f"{'policy':<10} " + " ".join(f"{m:>14}" for m in METRICS)
    print(hdr); print("-" * len(hdr))
    for p in order:
        print(f"{p:<10} " + " ".join(f"{rows[p][m]:>14.3f}" for m in METRICS))
    return rows


def validate(rows):
    print("\n=== sanity checks ===")
    def cmp(a, b, metric, msg):
        ok = rows[a][metric] < rows[b][metric]
        print(f"  [{'PASS' if ok else 'WARN'}] {msg}: {a}={rows[a][metric]:.2f} vs {b}={rows[b][metric]:.2f}")
    cmp("NV", "RANDOM", "makespan", "NV beats RANDOM on makespan")
    cmp("EDD", "FIFO", "mean_tardiness", "EDD beats FIFO on tardiness")
    cmp("COMPOSITE", "RANDOM", "mean_tardiness", "COMPOSITE beats RANDOM on tardiness")
    cmp("NV", "RANDOM", "deadhead_ratio", "NV lowers deadhead vs RANDOM")


if __name__ == "__main__":
    for name, cfg in CONFIGS.items():
        rows = run_config(name, cfg)
        validate(rows)
