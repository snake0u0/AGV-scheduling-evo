"""Cross-check: custom DES engine vs salabim port, SAME instances & interface.

Runs the classical dispatching rules on BOTH engines across seeds and reports:
  - side-by-side metrics + relative difference
  - ranking agreement (by mean_tardiness, the primary objective)
  - wall-clock time per engine (overhead is relevant to the engine decision)

If rankings agree, the salabim model is a faithful re-implementation and we keep
the custom engine as a validation oracle. Run: python sim/crosscheck_salabim.py
"""
import statistics, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim.agv_fms import simulate
from sim.agv_fms_salabim import simulate_salabim
from sim.policies import POLICIES

CONFIGS = {
    "small":  dict(n_machines=6, n_agvs=3, n_jobs=60, arrival_rate=0.18, grid_cols=3,
                   ops_range=(2, 4), proc_range=(3, 9), due_tightness=3.0, machine_rule="EDD"),
    "medium": dict(n_machines=10, n_agvs=4, n_jobs=120, arrival_rate=0.25, grid_cols=4,
                   ops_range=(3, 5), proc_range=(3, 9), due_tightness=3.0, machine_rule="EDD"),
    # validates the v1 features (FJSP flexibility + congestion-delay) across both engines
    "congested-fjsp": dict(n_machines=8, n_agvs=6, n_jobs=80, arrival_rate=0.5, grid_cols=4,
                           ops_range=(3, 5), proc_range=(3, 9), due_tightness=2.5,
                           flex=2, congestion_alpha=1.0, machine_rule="EDD"),
}
SEEDS = list(range(10))
KEY = ["makespan", "mean_tardiness", "deadhead_ratio"]


def mean_over_seeds(fn, cfg, pol):
    agg = {m: [] for m in KEY}
    for s in SEEDS:
        r = fn(cfg, pol, seed=s)
        for m in KEY:
            agg[m].append(r[m])
    return {m: statistics.mean(v) for m, v in agg.items()}


def run(name, cfg):
    print(f"\n{'='*86}\nconfig: {name}  (M={cfg['n_machines']} AGV={cfg['n_agvs']} "
          f"jobs={cfg['n_jobs']}) | {len(SEEDS)} seeds\n{'='*86}")
    custom, sala = {}, {}
    t0 = time.perf_counter()
    for p, pol in POLICIES.items():
        custom[p] = mean_over_seeds(simulate, cfg, pol)
    t_custom = time.perf_counter() - t0
    t0 = time.perf_counter()
    for p, pol in POLICIES.items():
        sala[p] = mean_over_seeds(simulate_salabim, cfg, pol)
    t_sala = time.perf_counter() - t0

    print(f"{'policy':<10}{'metric':<16}{'custom':>12}{'salabim':>12}{'rel.diff':>10}")
    print("-" * 60)
    for p in POLICIES:
        for m in KEY:
            c, s = custom[p][m], sala[p][m]
            rel = (s - c) / c * 100 if c else 0.0
            print(f"{p:<10}{m:<16}{c:>12.3f}{s:>12.3f}{rel:>9.1f}%")
        print()

    # ranking agreement on primary objective.
    # RANDOM excluded: its per-call RNG closure consumes a different stream length
    # per engine, so it is not a deterministic policy comparable across engines.
    det = [p for p in POLICIES if p != "RANDOM"]
    rank_c = sorted(det, key=lambda p: custom[p]["mean_tardiness"])
    rank_s = sorted(det, key=lambda p: sala[p]["mean_tardiness"])
    print(f"rank by mean_tardiness (excl. RANDOM)  custom : {' < '.join(rank_c)}")
    print(f"rank by mean_tardiness (excl. RANDOM)  salabim: {' < '.join(rank_s)}")
    print(f"  -> rankings {'MATCH' if rank_c == rank_s else 'DIFFER'}")
    print(f"time: custom={t_custom:.2f}s  salabim={t_sala:.2f}s  "
          f"(salabim {t_sala/t_custom:.1f}x)")
    return rank_c == rank_s


if __name__ == "__main__":
    print("CROSS-CHECK: custom DES vs salabim (identical instances & interface)")
    results = [run(name, cfg) for name, cfg in CONFIGS.items()]
    print(f"\n{'='*86}")
    print(f"OVERALL: ranking agreement on {sum(results)}/{len(results)} configs",
          "-> salabim model is faithful" if all(results) else "-> investigate divergence")
