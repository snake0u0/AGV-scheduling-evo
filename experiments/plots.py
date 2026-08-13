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

from model.experiment import evaluate_bundle
from model.rules import rule_from_expr
from simulator.dispatch import build as dispatch_build
from simulator.instance import load_dauzere

from experiments.common import gap

FIGDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "docs", "reports", "figures")

# Light fills so a job label printed inside the bar stays legible in black. Bars carry
# a thin dark edge instead of a pattern - the figure is read by its labels, not by hue,
# so there is no legend and no hatching.
_JOB_COLOURS = [
    "#a8c8ec", "#f6c39a", "#a9dcb8", "#f2a9a9", "#c9b6e4", "#d9c3ae",
    "#f3b0d3", "#cfcfcf", "#dfe3a2", "#a5dbe4", "#8fb8d8", "#eeb37c",
    "#8fcda3", "#e88f8f", "#b49bd8", "#c7ab92", "#e893c0", "#b6b6b6",
    "#cdd487", "#87c9d5",
]
_EMPTY_FILL = "#ededed"
_EDGE = "#4a4a4a"


def _job_colour(job):
    return _JOB_COLOURS[job % len(_JOB_COLOURS)]


def _label_bars(ax, bars, fontsize):
    """Write each bar's label inside it, horizontally, and drop the ones that do not fit.

    Never rotated: vertical text in a Gantt row is hard to read and crowds exactly the
    rows it lands in. Fit is measured on the rendered text rather than estimated, and a
    label that does not fit is dropped rather than clipped or overflowed - on a
    full-length chart that is unavoidable for the shortest operations, which is what the
    zoomed companion figure is for.

    Returns (labelled, total).
    """
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    x_lo, x_hi = ax.get_xlim()
    placed = 0
    for x0, x1, y, text in bars:
        if x1 <= x_lo or x0 >= x_hi:                  # outside a zoomed window
            continue
        vx0, vx1 = max(x0, x_lo), min(x1, x_hi)       # visible part of the bar
        span = ax.transData.transform((vx1, y))[0] - ax.transData.transform((vx0, y))[0]
        t = ax.text((vx0 + vx1) / 2, y, text, ha="center", va="center",
                    fontsize=fontsize, color="#111111", zorder=4)
        if t.get_window_extent(renderer).width + 3 <= span:
            placed += 1
        else:
            t.remove()
    return placed, len(bars)


def _fig_width(span):
    """Figure width for a visible time span, so bars keep a usable size.

    Grows with the span so a zoomed window gets room for its labels, but capped: the
    full length of a real instance would need metres of paper to label every operation,
    and a figure wider than the page only shrinks the text again when it is placed.
    """
    return min(24.0, max(13.0, 4.0 + span * 0.024))


def schedule_of(bundle, stem, veh):
    """Build the schedule a rule bundle produces for one instance."""
    slots = {slot: rule_from_expr(expr) for slot, expr in bundle.items()}
    inst = load_dauzere(stem, veh)
    sol, sched = dispatch_build(inst, slots)
    return inst, sol, sched


def gantt(bundle, stem, veh, out=None, caption=None, fig_no=None, xlim=None):
    """Gantt chart of one instance: machine rows on top, AGV rows below.

    A machine bar is one operation being processed. An AGV row alternates loaded legs
    (job colour) with the empty running and waiting between them, drawn in grey and
    labelled "empty", so deadhead is visible rather than hidden inside the task.

    Bars are labelled J<job> in place and there is no legend - identity is read off the
    bar. A label that will not fit inside its bar is dropped rather than clipped, which
    on a full-size instance is most of them; the figure then reads as machine occupancy
    and AGV deadhead, which is what it is for. The caption goes below the axes.
    """
    inst, sol, sched = schedule_of(bundle, stem, veh)
    n_rows = inst.n_machines + inst.n_vehicles
    lo, hi = xlim if xlim else (0, sched.cmax)
    fig, ax = plt.subplots(figsize=(_fig_width(hi - lo), 0.40 * n_rows + 1.9))

    to_label = []                       # (x0, x1, y, text), placed after a draw
    labels, y = [], 0

    for k in range(1, inst.n_machines + 1):
        for g in range(1, inst.n_ops + 1):
            if sol.machine_of[g] != k:
                continue
            job, _ = inst.job_op(g)
            x0, x1 = sched.start[g], sched.end[g]
            ax.barh(y, x1 - x0, left=x0, height=0.58, color=_job_colour(job),
                    edgecolor=_EDGE, linewidth=0.35, zorder=3)
            to_label.append((x0, x1, y, f"J{job + 1}"))
        labels.append(f"M{k}")
        y += 1

    for v in range(1, inst.n_vehicles + 1):
        free = 0
        for g in sol.vehicle_seq.get(v, []):
            job, _ = inst.job_op(g)
            pickup, arrive = sched.pickup[g], sched.arrive[g]
            if pickup > free:
                ax.barh(y, pickup - free, left=free, height=0.58, color=_EMPTY_FILL,
                        edgecolor=_EDGE, linewidth=0.35, zorder=3)
                to_label.append((free, pickup, y, "empty"))
            ax.barh(y, arrive - pickup, left=pickup, height=0.58, color=_job_colour(job),
                    edgecolor=_EDGE, linewidth=0.35, zorder=3)
            to_label.append((pickup, arrive, y, f"J{job + 1}"))
            free = arrive
        labels.append(f"V{v}")
        y += 1

    ax.set_yticks(range(n_rows), labels, fontsize=8.5)
    ax.set_ylim(n_rows - 0.5, -0.7)                  # inverted, with headroom at the top
    ax.set_xlim(lo - (hi - lo) * 0.004, hi + (hi - lo) * 0.02)
    ax.set_xlabel("time", fontsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_position(("data", lo))     # time axis closed on the left
    ax.spines["left"].set_linewidth(1.1)
    ax.spines["bottom"].set_linewidth(1.1)
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", length=0)

    # Makespan: drop a dashed line from the operation that ends last down to the axis,
    # and put the value on the axis rather than colouring the line for attention.
    if lo <= sched.cmax <= hi:
        last = max(sched.end, key=lambda g: sched.end[g])
        row = sol.machine_of[last] - 1
        ax.plot([sched.cmax, sched.cmax], [row, n_rows - 0.5], linestyle=(0, (4, 3)),
                color="#555555", linewidth=0.9, zorder=2)
        ticks = [t for t in ax.get_xticks() if lo <= t <= hi - (hi - lo) * 0.07]
        ax.set_xticks(ticks + [sched.cmax])
        ax.get_xticklabels()[-1].set_fontweight("bold")

    placed, total = _label_bars(ax, to_label, fontsize=6.0)

    fig.tight_layout()

    # Caption goes just under the x-axis label. Positioned off the measured label rather
    # than a guessed fraction, so it sits the same distance away at any row count; the
    # tight bounding box on save then trims to it.
    cap = caption or f"Instance {stem} with {veh} AGVs."
    if fig_no is not None:
        cap = f"Fig. {fig_no}.  {cap}"
    fig.canvas.draw()
    label_bottom = ax.xaxis.get_label().get_window_extent(fig.canvas.get_renderer()).y0
    y = fig.transFigure.inverted().transform((0, label_bottom))[1] - 0.055
    fig.text(0.5, y, cap, ha="center", va="top", fontsize=9.5)

    out = out or os.path.join(FIGDIR, f"gantt-{stem}-{veh}v.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return out, sched.cmax, (placed, total)


def gantt_pair(bundle, stem, veh, tag, what, fig_no=None, zoom=500):
    """Both views of one instance: the whole schedule, and a zoom on its opening window.

    The full chart shows the shape - machine occupancy, AGV saturation, where the
    makespan comes from - but most operations are too short to label at that scale. The
    zoom covers `zoom` time units at a scale where the labels do fit, so a reader can
    actually follow which job is where. Always produce both; neither answers the other's
    question.

    `tag` names the files (gantt-<tag>.png / gantt-<tag>-zoom.png) and `what` describes
    the rules in the caption.
    """
    base = os.path.join(FIGDIR, f"gantt-{tag}")
    full = gantt(bundle, stem, veh, out=f"{base}.png", fig_no=fig_no,
                 caption=f"Instance {stem} with {veh} AGVs, {what}.")
    n2 = None if fig_no is None else f"{fig_no}b"
    zoomed = gantt(bundle, stem, veh, out=f"{base}-zoom.png", fig_no=n2, xlim=(0, zoom),
                   caption=f"Instance {stem} with {veh} AGVs, {what} - first {zoom} time units.")
    return full, zoomed


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
        path, cmax, (placed, total) = gantt(bundle, sys.argv[2], int(sys.argv[3]),
                                           sys.argv[4] if len(sys.argv) > 4 else None)
        print(f"{path}  (Cmax {cmax}, {placed}/{total} bars labelled, bundle from {latest})")
    else:
        print(__doc__)
