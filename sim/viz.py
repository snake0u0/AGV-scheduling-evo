"""Visualization for the AGV-FJSP simulator: layout, time-series, animation, evolution curve.

Run:  python sim/viz.py        -> writes PNG/GIF into runs/<topic>/figures/
Non-invasive: records AGV legs by subclassing Simulator (overrides _push); samples machine
queue lengths via the run() on_step hook. No change to the core simulation logic.
"""
import os, sys, heapq
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from sim.agv_fms import Simulator, manhattan, LU
from sim.policies import POLICIES, MACHINE_POLICIES
from sim.configs import REGIMES, LARGE_REGIMES

FIGDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "docs", "research", "figures")


class RecSim(Simulator):
    """Simulator that records AGV travel legs and periodic machine-queue snapshots."""
    def __init__(self, *a, sample_dt=5.0, **k):
        super().__init__(*a, **k)
        self.legs = []           # (aid, t0, t1, (x0,y0), (x1,y1), state)
        self.qsamples = []       # (t, [qlen per machine id], n_busy, cong_factor)
        self._sample_dt = sample_dt
        self._next_s = 0.0

    def _push(self, t, kind, payload):
        if kind == "pickup":          # deadhead leg: agv.loc -> task.src over [now, t]
            a, task = payload
            self.legs.append((a.aid, self.now, t, a.loc, task.src, "deadhead"))
        elif kind == "dropoff":       # loaded leg: task.src -> task.dst_loc over [now, t]
            agv, task = payload
            self.legs.append((agv.aid, self.now, t, task.src, task.dst_loc, "loaded"))
        super()._push(t, kind, payload)

    def sample(self, sim, kind):
        if self.now >= self._next_s:
            qs = [len(self.machines[m].queue) for m in sorted(self.machines)]
            busy = sum(1 for a in self.agvs if not a.idle)
            self.qsamples.append((self.now, qs, busy, self._cong_factor()))
            self._next_s += self._sample_dt


def _run(cfg, sample_dt=5.0, seed=0):
    s = RecSim(cfg, POLICIES["NV"], seed, machine_policy=MACHINE_POLICIES["M_EDD"],
               sample_dt=sample_dt)
    m = s.run(on_step=s.sample)
    return s, m


def _machine_xy(cfg):
    cols = cfg.get("grid_cols", 4)
    return {mid: (1 + (mid % cols), 1 + (mid // cols)) for mid in range(cfg["n_machines"])}


# ---------------- 1. layout ----------------
def draw_layout(cfg, name, path):
    xy = _machine_xy(cfg)
    fig, ax = plt.subplots(figsize=(7, 6))
    for mid, (x, y) in xy.items():
        ax.add_patch(plt.Rectangle((x - 0.35, y - 0.35), 0.7, 0.7, fc="#cfe8ff", ec="#3a7bd5"))
        ax.text(x, y, f"M{mid}", ha="center", va="center", fontsize=7)
    ax.plot(0, 0, "s", ms=22, color="#ffce6b", mec="#b8860b")
    ax.text(0, 0, "L/U", ha="center", va="center", fontsize=8, weight="bold")
    # AGV fleet shown clustered at L/U depot
    import numpy as np
    K = cfg["n_agvs"]
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(-0.45, 0.45, K), rng.uniform(-0.9, -0.45, K),
               s=18, color="#e8553a", marker="^", label=f"{K} AGVs")
    ax.set_title(f"Layout [{name}]  M={cfg['n_machines']}  AGV={cfg['n_agvs']}  "
                 f"flex={cfg.get('flex',1)}  congestion_alpha={cfg.get('congestion_alpha',0.0)}")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.legend(loc="upper right")
    ax.set_aspect("equal"); ax.grid(alpha=0.2); ax.set_ylim(-1.3, max(y for _, y in xy.values()) + 1)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    print("wrote", path)


# ---------------- 2. time series ----------------
def plot_timeseries(s, metrics, name, path):
    jobs = [j for j in s.jobs if j.completion >= 0]
    comp = sorted(j.completion for j in jobs)
    # mean tardiness of jobs completed up to time t
    ev = sorted((j.completion, max(0.0, j.completion - j.due)) for j in jobs)
    ts, run_mean, tot, n = [], [], 0.0, 0
    for t, tard in ev:
        tot += tard; n += 1; ts.append(t); run_mean.append(tot / n)
    st = [q[0] for q in s.qsamples]
    busy = [q[2] for q in s.qsamples]
    totq = [sum(q[1]) for q in s.qsamples]
    cong = [q[3] for q in s.qsamples]

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    ax[0, 0].plot(comp, range(1, len(comp) + 1), color="#3a7bd5")
    ax[0, 0].set_title("Completed jobs over time"); ax[0, 0].set_xlabel("time"); ax[0, 0].set_ylabel("# completed")
    ax[0, 1].plot(ts, run_mean, color="#e8553a")
    ax[0, 1].set_title("Mean tardiness of completed-so-far (objective)"); ax[0, 1].set_xlabel("time"); ax[0, 1].set_ylabel("mean tardiness")
    ax[1, 0].plot(st, busy, color="#2a9d8f")
    ax[1, 0].set_title(f"Busy AGVs over time (fleet={s.cfg['n_agvs']})"); ax[1, 0].set_xlabel("time"); ax[1, 0].set_ylabel("# busy AGVs")
    axc = ax[1, 0].twinx(); axc.plot(st, cong, color="#9b59b6", alpha=0.5); axc.set_ylabel("congestion factor", color="#9b59b6")
    ax[1, 1].plot(st, totq, color="#b8860b")
    ax[1, 1].set_title("Total jobs queued at machines (WIP)"); ax[1, 1].set_xlabel("time"); ax[1, 1].set_ylabel("queued jobs")
    fig.suptitle(f"Dynamics [{name}]  makespan={metrics['makespan']}  mean_tardiness={metrics['mean_tardiness']}  agv_util={metrics['agv_util']}")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    print("wrote", path)


# ---------------- 3. animation ----------------
def animate(s, cfg, name, path, t_end=None, n_frames=120):
    xy = _machine_xy(cfg)
    legs = s.legs
    T = t_end or (max(l[2] for l in legs) if legs else 1)
    T = min(T, t_end or T)
    frames = [T * i / (n_frames - 1) for i in range(n_frames)]
    # machine queue length at sampled times -> interpolate by step
    qtimes = [q[0] for q in s.qsamples]; qvals = [q[1] for q in s.qsamples]

    def qlen_at(t):
        import bisect
        i = bisect.bisect_right(qtimes, t) - 1
        return qvals[max(0, i)] if qvals else [0] * cfg["n_machines"]

    fig, ax = plt.subplots(figsize=(7, 6.5))
    mids = sorted(xy)
    mx = [xy[m][0] for m in mids]; my = [xy[m][1] for m in mids]
    mscat = ax.scatter(mx, my, s=200, marker="s", c="#cfe8ff", edgecolors="#3a7bd5", zorder=1)
    ax.plot(0, 0, "s", ms=20, color="#ffce6b", mec="#b8860b", zorder=1); ax.text(0, 0, "L/U", ha="center", va="center", fontsize=7)
    agv_scat = ax.scatter([], [], s=22, zorder=3)
    title = ax.set_title("")
    ax.set_aspect("equal"); ax.grid(alpha=0.2)
    ax.set_xlim(-1.3, max(mx) + 1); ax.set_ylim(-1.3, max(my) + 1)

    def pos_at(t):
        xs, ys, cs = [], [], []
        for aid in range(cfg["n_agvs"]):
            active = [l for l in legs if l[0] == aid and l[1] <= t <= l[2]]
            if active:
                _, t0, t1, p0, p1, state = active[-1]
                f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                xs.append(p0[0] + (p1[0] - p0[0]) * f); ys.append(p0[1] + (p1[1] - p0[1]) * f)
                cs.append("#e8553a" if state == "loaded" else "#f4a261")  # loaded vs deadhead
            else:  # idle: last known endpoint <= t, else depot
                past = [l for l in legs if l[0] == aid and l[2] <= t]
                p = past[-1][4] if past else (0, 0)
                xs.append(p[0]); ys.append(p[1]); cs.append("#9aa0a6")
        return xs, ys, cs

    def update(t):
        xs, ys, cs = pos_at(t)
        agv_scat.set_offsets(list(zip(xs, ys))); agv_scat.set_color(cs)
        q = qlen_at(t)
        mscat.set_sizes([120 + 90 * q[m] for m in mids])      # machine marker grows with queue
        nb = sum(1 for c in cs if c != "#9aa0a6")
        title.set_text(f"[{name}] t={t:6.1f}   busy AGV={nb}/{cfg['n_agvs']}   "
                       f"(red=loaded, orange=deadhead, gray=idle; square size=queue)")
        return agv_scat, mscat, title

    anim = FuncAnimation(fig, update, frames=frames, blit=False)
    anim.save(path, writer=PillowWriter(fps=12)); plt.close(fig)
    print("wrote", path)


# ---------------- 4. evolution curve ----------------
def plot_evolution(path):
    from ahd.llm import MockLLM
    from ahd.loop import evolve
    from sim.agv_fms import simulate
    cfg = REGIMES["R3"]
    _, _, hist, _ = evolve(cfg, list(range(6)), MockLLM(seed=0), simulate,
                           pop_size=12, generations=12, elite=4, verbose=False)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(range(len(hist)), hist, "-o", color="#3a7bd5")
    ax.set_title("LLM-AHD objective over generations (R3, mock proposer)")
    ax.set_xlabel("generation"); ax.set_ylabel("best mean tardiness (train)")
    ax.grid(alpha=0.3); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    print("wrote", path)


if __name__ == "__main__":
    os.makedirs(FIGDIR, exist_ok=True)
    # layouts
    draw_layout(LARGE_REGIMES["L1"], "L1 (40 AGV, transport bottleneck)", os.path.join(FIGDIR, "layout_L1.png"))
    draw_layout(REGIMES["R3"], "R3 (small, balanced)", os.path.join(FIGDIR, "layout_R3.png"))
    # dynamics + animation on L1
    s, m = _run(LARGE_REGIMES["L1"], sample_dt=5.0)
    plot_timeseries(s, m, "L1", os.path.join(FIGDIR, "timeseries_L1.png"))
    animate(s, LARGE_REGIMES["L1"], "L1", os.path.join(FIGDIR, "agv_anim_L1.gif"), t_end=400, n_frames=120)
    # evolution curve
    plot_evolution(os.path.join(FIGDIR, "evolution_R3.png"))
    print("\nALL FIGURES in", FIGDIR)
