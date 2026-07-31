"""Regime grid, scale grid, and train/valid/test seed splits for experiments.

Regimes encode the four bottleneck conditions from research_plan.md §5.1. Every key
here is read by sim/agv_fms.py::Simulator (n_machines, n_agvs, n_jobs, arrival_rate,
grid_cols, ops_range, proc_range, due_tightness), so simulate(REGIMES[r], policy, seed)
runs unchanged on the current engine.

Protocol: rules are EVOLVED on TRAIN_SEEDS, SELECTED on VALID_SEEDS, and final numbers
are reported ONLY on TEST_SEEDS (held out) — see research_plan.md §5.1.

R4 ("high disturbance") is currently realized via high arrival rate + tight due dates,
which the v0 engine honors. AGV failure + battery/charging (simulator_spec.md §9, v1/SCIE
tier) are NOT yet wired and would be added to the salabim engine per the CLAUDE.md engine
decision (agv_fms.py is the frozen oracle). Until then R4 is a valid heavy-load regime.
"""

REGIMES = {
    "R1": dict(  # transport bottleneck: few AGVs, large layout
        n_machines=6, n_agvs=2, n_jobs=60,
        arrival_rate=0.25, grid_cols=4,
        ops_range=(2, 5), proc_range=(3, 8), due_tightness=2.0,
    ),
    "R2": dict(  # machine bottleneck: few machines, long processing
        n_machines=6, n_agvs=4, n_jobs=60,
        arrival_rate=0.15, grid_cols=4,
        ops_range=(3, 6), proc_range=(8, 20), due_tightness=2.5,
    ),
    "R3": dict(  # balanced (current dev config)
        n_machines=10, n_agvs=3, n_jobs=90,
        arrival_rate=0.20, grid_cols=4,
        ops_range=(3, 5), proc_range=(3, 10), due_tightness=2.2,
    ),
    "R4": dict(  # high disturbance: high arrival + tight due (v1 adds failure/battery)
        n_machines=10, n_agvs=3, n_jobs=90,
        arrival_rate=0.30, grid_cols=4,
        ops_range=(3, 5), proc_range=(3, 10), due_tightness=1.8,
    ),
}

# Scale grid for sensitivity experiments (research_plan.md §5.1): (M, K) pairs.
SCALE_GRID = [(6, 2), (6, 3), (10, 3), (10, 4), (16, 4), (16, 6)]

# Large-scale regimes — KIIE TARGET (40-50 AGV). FJSP (flex>=2) + congestion on.
# Structure anchored on the FJSP+transport benchmark lineage (benchmark_anchor_notes.md);
# numeric operating points are INITIAL and to be calibrated against the data-set-1 reproduction (roadmap S3).
LARGE_REGIMES = {
    "L1": dict(  # transport bottleneck @ scale: congestion-limited (the core "AGV bottleneck" story)
        n_machines=24, n_agvs=40, n_jobs=500,
        arrival_rate=1.4, grid_cols=6,
        ops_range=(4, 8), proc_range=(3, 10), due_tightness=1.8,
        flex=2, congestion_alpha=1.5,
    ),
    "L3": dict(  # balanced @ scale
        n_machines=30, n_agvs=50, n_jobs=500,
        arrival_rate=1.2, grid_cols=6,
        ops_range=(3, 6), proc_range=(3, 10), due_tightness=2.0,
        flex=2, congestion_alpha=1.0,
    ),
}

# 30 seeds per regime·config, split once and reused everywhere.
TRAIN_SEEDS = list(range(0, 20))    # evolve on these
VALID_SEEDS = list(range(20, 25))   # select the rule on these
TEST_SEEDS = list(range(25, 30))    # report final numbers on these only
