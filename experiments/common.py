"""Shared harness for every experiment: reference values, the gap metric, the paired
test, the protocol constants, and the parallel runner.

The literature reference table is read from data/literature/ (provenance in its
SOURCE.md) exactly once, here, and never retyped into an experiment script. A single
typo in a duplicated copy would silently change that experiment's reported gap - no
error, no warning - at effect sizes of 1-5%p, which is the size of the differences
being measured.

Import instead of retyping:

    from common import gap, reference, paired, pop_for, SEEDS, run_parallel
"""
import csv
import multiprocessing as mp
import os
import statistics as st
import time

from scipy import stats

# --- protocol constants (fixed; do not vary per experiment) ------------------

SEEDS = (0, 21, 42)
WORKERS = 12                       # of 16 cores

# Evolution budget, sized to the AHD literature rather than to convenience. FunSearch
# and MCTS-AHD budget T=1000 evaluated heuristics; EoH runs 20x20. Anything an order of
# magnitude below that has not tested the regime those methods were shown to need, so a
# null result at a smaller budget says nothing about the method.
#   20 seeds + 65 generations x 15 children = 995 individuals over 65 LLM calls.
EVOLVE_POP, EVOLVE_GEN = 20, 65
MAX_CALLS = 80                     # hard cap; the proposer pads from elites past it

LIT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "literature")


def pop_for(budget_seconds):
    """GA population for a wall-clock budget.

    The optimum follows pop ~= 20 * budget^0.6, matching the measured optima
    20/70/300/1000 at 1/10/60/600s. Population is a U-curve with a sharp interior
    optimum - at 60s, pop1000 scores 145.3% where pop300 scores 74.0% - so it must
    never be fixed to a constant across budgets.
    """
    return max(2, round(20 * budget_seconds ** 0.6))


# --- literature reference values (data/literature/, never hardcoded) --------

def _load():
    dauzere = {}
    with open(os.path.join(LIT_DIR, "berterottiere2024_table8.tsv")) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            dauzere[row["instance"]] = {2: int(row["veh2"]), 4: int(row["veh4"]),
                                        6: int(row["veh6"])}
    deroussi = {}
    with open(os.path.join(LIT_DIR, "deroussi_published.tsv")) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            deroussi[row["instance"]] = {2: int(row["cmax"])}
    return {"dauzere": dauzere, "deroussi": deroussi}


REFERENCES = _load()


def reference(family, stem, veh):
    """Literature best-known makespan. Raises rather than guessing - a missing
    reference must fail loudly, not silently produce a gap against nothing."""
    try:
        return REFERENCES[family][stem][veh]
    except KeyError:
        raise KeyError(f"no literature reference for {family}/{stem}/{veh} vehicles "
                       f"(see data/literature/SOURCE.md)") from None


def gap(rec):
    """Percent above the literature best-known. Expects family/stem/veh/cmax keys."""
    ref = reference(rec["family"], rec["stem"], rec["veh"])
    return 100 * (rec["cmax"] - ref) / ref


# --- comparison -------------------------------------------------------------

def paired(recs, a, b, key="rule"):
    """Paired comparison of two configurations over (instance, seed).

    Paired because the seed-to-seed spread on the hard instances is the same size as
    the differences being measured, so unpaired tests waste the sample.
    Returns (wins_for_a, ties, n, wilcoxon_p).
    """
    ka = {(r["stem"], r["veh"], r["seed"]): r["cmax"] for r in recs if r[key] == a}
    kb = {(r["stem"], r["veh"], r["seed"]): r["cmax"] for r in recs if r[key] == b}
    keys = sorted(set(ka) & set(kb))
    xa, xb = [ka[k] for k in keys], [kb[k] for k in keys]
    wins = sum(1 for u, v in zip(xa, xb) if u < v)
    ties = sum(1 for u, v in zip(xa, xb) if u == v)
    p = stats.wilcoxon(xa, xb).pvalue if any(u != v for u, v in zip(xa, xb)) else 1.0
    return wins, ties, len(keys), p


def mean_gap(recs, **where):
    """Mean gap over the records matching every key=value in `where`."""
    sub = [r for r in recs if all(r.get(k) == v for k, v in where.items())]
    return st.mean(gap(r) for r in sub) if sub else float("nan")


# --- runner -----------------------------------------------------------------

def run_parallel(fn, jobs, budget_of=None, workers=WORKERS, every=20):
    """Map fn over jobs on a process pool, printing progress.

    budget_of(job) -> seconds is used only for the up-front cost estimate, so a long
    run announces its own wall-clock before committing to it.
    """
    if budget_of is not None:
        cpu = sum(budget_of(j) for j in jobs)
        print(f"{len(jobs)} runs, {cpu/3600:.1f} CPU-hours, {workers} workers "
              f"-> about {cpu/3600/workers:.1f} h wall\n", flush=True)
    t0, out = time.time(), []
    with mp.Pool(workers) as pool:
        for i, r in enumerate(pool.imap_unordered(fn, jobs), 1):
            out.append(r)
            if i % every == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}  ({time.time()-t0:.0f}s)", flush=True)
    return out
