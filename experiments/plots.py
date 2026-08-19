"""Figures and comparison tables for reports.

Kept out of model/ and simulator/ on purpose: those hold experiment logic only, and
nothing there should import matplotlib. Reports embed the PNGs this writes.

Run standalone to regenerate a Gantt chart:
    python experiments/plots.py gantt <stem> <vehicles> <out.png>
"""
import glob
import json
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from model.experiment import evaluate_bundle
from model.rules import rule_from_expr
from simulator.dispatch import build as dispatch_build
from simulator.instance import load_dauzere, load_deroussi

from experiments.common import gap, reference

EXPERIMENTS = os.path.dirname(os.path.abspath(__file__))

# Figures belong to the experiment that produced them, so the default output is
# figures/ under whatever directory the caller is working in - normally the
# experiment folder itself. Pass `out` to place a figure anywhere else.
FIGDIR = os.path.join(os.getcwd(), "figures")


def latest_bundle_result():
    """Newest stored bundle run across the experiment folders."""
    paths = [p for p in glob.glob(os.path.join(EXPERIMENTS, "*", "result*.json"))
             if "best_bundle" in json.load(open(p))]
    if not paths:
        raise SystemExit("no stored bundle run found under experiments/*/")
    return max(paths, key=os.path.getmtime)

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


def _running_best(record):
    """(fitness, bundle) of the incumbent after each logged generation.

    Recomputed from the population log rather than trusting the stored `history`
    array, though the two agree by construction - this is what makes the bundle behind
    each point available, which `history` (fitness only) does not carry.
    """
    best = None
    out = []
    for e in record:
        cand = min(e["population"], key=lambda r: r["fitness"])
        if best is None or cand["fitness"] < best["fitness"]:
            best = cand
        out.append((best["fitness"], best["bundle"]))
    return out


def _bundle_key(b):
    return tuple(sorted(b.items()))


def convergence(files, instances, out=None, fig_no=None, caption=None,
                mean_label="held-out (mean)", spot_stem=None, spot_veh=2,
                train_label="train (mean)", baseline=None):
    """Best-so-far fitness across a chain of resumed runs, against a held-out set.

    Concatenates `files` in run order (each a result JSON from evolve_bundle, resumed
    or not), re-deriving the incumbent bundle at every logged generation - including the
    flat stretches where a call failed and nothing evolved, since those stalls are real
    history, not noise to smooth away. Held-out fitness is only recomputed when the
    incumbent bundle actually changes, since evaluation is deterministic and otherwise
    wasted; the earlier point widens into a flat run up to the next change instead.

    `instances` is the held-out split to score against (mean plotted as `mean_label`).
    Pass `spot_stem` to add a second panel tracking one instance by name (`spot_veh`
    vehicles) - useful when a single instance's swing is the point being made and the
    15-instance mean would average it away. `baseline` is an optional
    {"BALANCED": bundle, ...} dict drawn as thin reference lines on both panels.
    """
    seq = []                                   # (attempt_index, train_fit, bundle)
    failed_x = []                               # attempts where the proposer call failed
    idx = 0
    for path in files:
        d = json.load(open(path)) if isinstance(path, str) else path
        run = _running_best(d["record"])
        start = 1 if seq else 0                # drop the duplicate resume-boundary gen0
        for i, (fit, bundle) in enumerate(run[start:], start=start):
            seq.append((idx, fit, bundle))
            if i > 0 and not (d["record"][i].get("call", {}).get("response") or "").strip():
                failed_x.append(idx)            # gen 0 is the seed population, not a call
            idx += 1

    seen = {}
    def held_out_of(bundle):
        k = _bundle_key(bundle)
        if k not in seen:
            seen[k] = evaluate_bundle(bundle, instances)
        return seen[k]

    def spot_of(bundle):
        if spot_stem is None:
            return None
        k = ("spot", _bundle_key(bundle))
        if k not in seen:
            seen[k] = schedule_of(bundle, spot_stem, spot_veh)[2].cmax
        return seen[k]

    xs = [p[0] for p in seq]
    train_y = [p[1] for p in seq]
    held_y = [held_out_of(p[2]) for p in seq]
    spot_y = [spot_of(p[2]) for p in seq] if spot_stem else None

    n_panels = 2 if spot_stem else 1
    fig, axes = plt.subplots(n_panels, 1, figsize=(11, 3.2 * n_panels + 0.6), sharex=True)
    axes = [axes] if n_panels == 1 else list(axes)

    ax = axes[0]
    ax.plot(xs, train_y, color="#2a78d6", linewidth=1.6, label=train_label)
    ax.plot(xs, held_y, color="#eb6834", linewidth=1.6, linestyle="--", label=mean_label)
    if baseline:
        for name, b in baseline.items():
            ax.axhline(evaluate_bundle(b, instances), color="#b6b6b6", linewidth=0.8,
                       linestyle=":", zorder=1)
            ax.text(xs[-1], evaluate_bundle(b, instances), f" {name}", fontsize=7.5,
                    color="#898781", va="center")
    ax.set_ylabel("mean Cmax", fontsize=9)
    if failed_x:
        y0, y1 = ax.get_ylim()                  # fixed before adding markers, so they
        ax.scatter(failed_x, [y0 + (y1 - y0) * 0.02] * len(failed_x), marker="|",
                  color="#d03b3b", s=40, linewidths=0.9, zorder=5, clip_on=False,
                  label=f"call failed (n={len(failed_x)})")
        ax.set_ylim(y0, y1)                     # do not expand the axis themselves
    ax.legend(fontsize=8.5, frameon=False, loc="upper right")
    ax.grid(axis="y", color="#e3e2d9", linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    if spot_stem:
        ax2 = axes[1]
        ax2.plot(xs, spot_y, color="#1baf7a", linewidth=1.6,
                label=f"{spot_stem} ({spot_veh} AGVs)")
        if baseline:
            for name, b in baseline.items():
                v = schedule_of(b, spot_stem, spot_veh)[2].cmax
                ax2.axhline(v, color="#b6b6b6", linewidth=0.8, linestyle=":", zorder=1)
                ax2.text(xs[-1], v, f" {name}", fontsize=7.5, color="#898781", va="center")
        ax2.set_ylabel(f"{spot_stem} Cmax", fontsize=9)
        ax2.legend(fontsize=8.5, frameon=False, loc="upper right")
        ax2.grid(axis="y", color="#e3e2d9", linewidth=0.6)
        ax2.set_axisbelow(True)
        for side in ("top", "right"):
            ax2.spines[side].set_visible(False)

    axes[-1].set_xlabel("generation (attempt, chained across resumes)", fontsize=9)
    for a in axes:
        a.tick_params(labelsize=8)

    fig.tight_layout()
    cap = caption or "Best-so-far fitness across the run."
    if fig_no is not None:
        cap = f"Fig. {fig_no}.  {cap}"
    fig.subplots_adjust(bottom=0.16 if n_panels == 1 else 0.11)
    fig.text(0.5, 0.01, cap, ha="center", va="bottom", fontsize=9.5)

    out = out or os.path.join(FIGDIR, "convergence.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return out, {"n_points": len(xs), "n_unique_bundles": len(seen)}


def gap_bars(bundles, instances, out=None, fig_no=None, caption=None, family="dauzere"):
    """Horizontal bar chart of mean literature gap%, one bar per bundle, best on top.

    `bundles` is {name: bundle_dict}. Meant to put every run this session produced -
    different generation counts, different prompt conditions - on one scale next to the
    hand-written seeds, since the gap% table in a report is easy to skim past and a
    sorted bar chart is not.
    """
    rows = comparison(bundles, instances, family=family)
    order = sorted(rows, key=lambda n: rows[n]["gap"])

    fig, ax = plt.subplots(figsize=(9, 0.5 * len(order) + 1.2))
    ys = range(len(order))
    vals = [rows[n]["gap"] for n in order]
    colours = ["#2a78d6" if "evolved" in n or "gen" in n else "#b6b6b6" for n in order]
    ax.barh(ys, vals, height=0.6, color=colours, edgecolor="#4a4a4a", linewidth=0.4)
    for y, n, v in zip(ys, order, vals):
        ax.text(v + max(vals) * 0.015, y, f"{v:.1f}%", va="center", fontsize=8.5)
    ax.set_yticks(list(ys), order, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("mean gap vs literature (%, lower is better)", fontsize=9)
    ax.set_xlim(0, max(vals) * 1.14)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", color="#e3e2d9", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)

    fig.tight_layout()
    cap = caption or f"Mean gap vs literature across {len(instances)} instances."
    if fig_no is not None:
        cap = f"Fig. {fig_no}.  {cap}"
    fig.subplots_adjust(bottom=0.20)
    fig.text(0.5, 0.02, cap, ha="center", va="bottom", fontsize=9.5)

    out = out or os.path.join(FIGDIR, "gap-bars.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return out, rows


def benchmark_bars(evolved, baseline, instances, family, source, out=None, fig_no=None,
                   caption=None, baseline_label="BALANCED"):
    """Grouped bars per instance: literature Cmax, one hand-seed baseline, our bundle.

    Absolute Cmax rather than gap%, so the literature number is visible on the chart
    itself and not just implied by a percentage. `source` is printed as a citation line
    under the axis, not in the legend - a citation is not a series name, and putting a
    full reference into a legend entry blows out the legend box and starves the plot
    area, which is the mistake this function exists to avoid making twice.
    """
    stems = [s for s, _v in instances]
    veh = instances[0][1]
    lit = [reference(family, s, veh) for s in stems]

    def cmax_of(bundle, stem):
        slots = {slot: rule_from_expr(expr) for slot, expr in bundle.items()}
        inst = (load_dauzere if family == "dauzere" else load_deroussi)(stem, veh)
        return dispatch_build(inst, slots)[1].cmax

    base_v = [cmax_of(baseline, s) for s in stems]
    ours_v = [cmax_of(evolved, s) for s in stems]

    x = range(len(stems))
    w = 0.27
    fig, ax = plt.subplots(figsize=(max(9, 0.72 * len(stems)), 4.8))
    ax.bar([i - w for i in x], lit, width=w, color="#4a4a4a", label="literature")
    ax.bar([i for i in x], base_v, width=w, color="#b6b6b6", label=baseline_label)
    ax.bar([i + w for i in x], ours_v, width=w, color="#2a78d6", label="evolved (ours)")

    ax.set_xticks(list(x), stems, fontsize=9)
    ax.set_ylabel("Cmax", fontsize=9)
    ax.legend(fontsize=9, frameon=False, loc="upper left", ncol=3,
             bbox_to_anchor=(0.0, 1.10))
    ax.grid(axis="y", color="#e3e2d9", linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=8)

    mean_gap_base = sum((b - l) / l for b, l in zip(base_v, lit)) / len(lit) * 100
    mean_gap_ours = sum((o - l) / l for o, l in zip(ours_v, lit)) / len(lit) * 100
    cap = caption or (f"{family} x{veh}, zero-shot. Mean gap vs literature: "
                      f"{baseline_label} {mean_gap_base:.1f}%, ours {mean_gap_ours:.1f}%.")
    if fig_no is not None:
        cap = f"Fig. {fig_no}.  {cap}"

    # Wrap both blocks to the figure's own width, in characters - never trust a caller
    # not to hand back a source string inside `caption`, since that one long unwrapped
    # line is exactly what forces savefig's tight bbox to balloon the whole canvas.
    chars_wide = int(len(stems) * 11)
    cap_lines = textwrap.wrap(cap, width=chars_wide)
    src_lines = textwrap.wrap(f"Source: {source}", width=chars_wide)
    top = 0.10 + 0.030 * (len(cap_lines) + len(src_lines))
    fig.tight_layout(rect=(0, top, 1, 0.94))
    y = top - 0.035
    for line in cap_lines:
        fig.text(0.5, y, line, ha="center", va="top", fontsize=9.5)
        y -= 0.030
    y -= 0.010
    for line in src_lines:
        fig.text(0.5, y, line, ha="center", va="top", fontsize=7.5, color="#6a6a6a")
        y -= 0.026

    out = out or os.path.join(FIGDIR, f"benchmark-{family}.png")
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return out, {"lit": lit, "baseline": base_v, "ours": ours_v,
                 "mean_gap_baseline": mean_gap_base, "mean_gap_ours": mean_gap_ours}


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "gantt":
        latest = latest_bundle_result()
        bundle = json.load(open(latest))["best_bundle"]
        path, cmax, (placed, total) = gantt(bundle, sys.argv[2], int(sys.argv[3]),
                                           sys.argv[4] if len(sys.argv) > 4 else None)
        print(f"{path}  (Cmax {cmax}, {placed}/{total} bars labelled, "
              f"bundle from {os.path.relpath(latest, EXPERIMENTS)})")
    else:
        print(__doc__)
