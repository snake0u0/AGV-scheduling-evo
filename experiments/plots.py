"""Figures and comparison tables for reports.

Kept out of model/ and simulator/ on purpose: those hold experiment logic only, and
nothing there should import matplotlib. Reports embed the PNGs this writes.

Run standalone to regenerate a Gantt chart:
    python experiments/plots.py gantt <stem> <vehicles> <out.png>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from model.experiment import evaluate_bundle
from model.rules import rule_from_expr
from simulator.dispatch import build as dispatch_build
from simulator.instance import load_dauzere

from experiments.common import gap

FIGDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "docs", "reports", "figures")

# Colour-blind-safe qualitative palette; jobs past its length reuse a colour and are
# separated by hatching instead, so identity never rests on hue alone.
_JOB_COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
_HATCHES = ["", "///", "..."]


def _job_style(job):
    return _JOB_COLOURS[job % len(_JOB_COLOURS)], _HATCHES[job // len(_JOB_COLOURS) % len(_HATCHES)]


def schedule_of(bundle, stem, veh):
    """Build the schedule a rule bundle produces for one instance."""
    slots = {slot: rule_from_expr(expr) for slot, expr in bundle.items()}
    inst = load_dauzere(stem, veh)
    sol, sched = dispatch_build(inst, slots)
    return inst, sol, sched


def gantt(bundle, stem, veh, out=None, title=None):
    """Gantt chart of one instance: machine rows, then AGV rows.

    A machine bar is one operation being processed. An AGV bar is one transport, split
    into the loaded leg (job colour) and the deadhead/wait before it (grey hatch), so
    empty running is visible rather than hidden inside the task.
    """
    inst, sol, sched = schedule_of(bundle, stem, veh)
    n_rows = inst.n_machines + inst.n_vehicles
    fig, ax = plt.subplots(figsize=(14, 0.42 * n_rows + 2.2))

    labels, y = [], 0
    for k in range(1, inst.n_machines + 1):
        for g in range(1, inst.n_ops + 1):
            if sol.machine_of[g] != k:
                continue
            job, _ = inst.job_op(g)
            colour, hatch = _job_style(job)
            ax.barh(y, sched.end[g] - sched.start[g], left=sched.start[g], height=0.62,
                    color=colour, hatch=hatch, edgecolor="white", linewidth=0.4)
        labels.append(f"M{k}")
        y += 1

    for v in range(1, inst.n_vehicles + 1):
        free = 0
        for g in sol.vehicle_seq.get(v, []):
            job, _ = inst.job_op(g)
            colour, hatch = _job_style(job)
            pickup, arrive = sched.pickup[g], sched.arrive[g]
            if pickup > free:                       # deadhead + waiting for the job
                ax.barh(y, pickup - free, left=free, height=0.62,
                        color="#d9d7cc", hatch="xx", edgecolor="white", linewidth=0.4)
            ax.barh(y, arrive - pickup, left=pickup, height=0.62,
                    color=colour, hatch=hatch, edgecolor="white", linewidth=0.4)
            free = arrive
        labels.append(f"V{v}")
        y += 1

    ax.axvline(sched.cmax, color="#d03b3b", linestyle="--", linewidth=1.2, zorder=5)
    ax.text(sched.cmax, -1.15, f" Cmax {sched.cmax}", color="#d03b3b",
            va="top", ha="right", fontsize=9)

    ax.set_yticks(range(n_rows), labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("time")
    ax.set_xlim(0, sched.cmax * 1.01)
    ax.set_title(title or f"{stem}, {veh} AGVs - Cmax {sched.cmax}", fontsize=11)
    ax.grid(axis="x", color="#e3e2d9", linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)

    handles = [Patch(facecolor=_job_style(j)[0], hatch=_job_style(j)[1], label=f"job {j}")
               for j in range(inst.n_jobs)]
    handles.append(Patch(facecolor="#d9d7cc", hatch="xx", label="AGV empty / waiting"))
    ax.legend(handles=handles, ncol=min(6, len(handles)), fontsize=7.5,
              loc="upper center", bbox_to_anchor=(0.5, -0.13), frameon=False)

    out = out or os.path.join(FIGDIR, f"gantt-{stem}-{veh}v.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out, sched.cmax


def comparison(bundles, instances, family="dauzere"):
    """Mean Cmax and mean literature gap per bundle over `instances`.

    Returns {name: {"cmax": float, "gap": float, "per_instance": {stem_veh: cmax}}}.
    """
    rows = {}
    for name, bundle in bundles.items():
        slots = {slot: rule_from_expr(expr) for slot, expr in bundle.items()}
        per, gaps = {}, []
        for stem, veh in instances:
            inst = load_dauzere(stem, veh)
            _, sched = dispatch_build(inst, slots)
            per[f"{stem}_{veh}"] = sched.cmax
            gaps.append(gap({"family": family, "stem": stem, "veh": veh, "cmax": sched.cmax}))
        rows[name] = {"cmax": evaluate_bundle(bundle, instances),
                      "gap": sum(gaps) / len(gaps),
                      "per_instance": per}
    return rows


def comparison_markdown(rows, baseline=None):
    """Comparison table as a markdown block, best (lowest gap) first."""
    order = sorted(rows, key=lambda n: rows[n]["gap"])
    base = rows[baseline]["cmax"] if baseline else None
    head = "| rule bundle | mean Cmax | mean gap vs literature |"
    sep = "|---|---:|---:|"
    if base:
        head += " vs %s |" % baseline
        sep += "---:|"
    out = [head, sep]
    for n in order:
        line = f"| {n} | {rows[n]['cmax']:.1f} | {rows[n]['gap']:.1f}% |"
        if base:
            d = (rows[n]["cmax"] - base) / base * 100
            line += f" {d:+.1f}% |"
        out.append(line)
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "gantt":
        import json
        res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "results")
        latest = sorted(f for f in os.listdir(res) if f.endswith("bundle_evolution_result.json"))[-1]
        bundle = json.load(open(os.path.join(res, latest)))["best_bundle"]
        path, cmax = gantt(bundle, sys.argv[2], int(sys.argv[3]),
                           sys.argv[4] if len(sys.argv) > 4 else None)
        print(f"{path}  (Cmax {cmax}, bundle from {latest})")
    else:
        print(__doc__)
