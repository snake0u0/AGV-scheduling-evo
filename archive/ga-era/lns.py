"""Large neighbourhood search over the four-slot builder. REJECTED - kept as evidence.

2026-08-10 gate: 105.6% against the tuned GA's 16.7% over the same 8 cases, seeds and
600s budget; 0/24 wins, p=0.0000. Report:
`experiments/006-260810-slot-expansion-and-lns-gate/report.md`.

The neighbourhood is empty. 232,599 iterations accepted 4 moves on average (0.002%),
the two hardest cases accepted none at all, and starting from a GA solution it improved
nothing in 8,109 tries. The cause is not what `fixed` preserves - relaxing it to
assignments only made things worse (01a: 9/120 improving moves became 0/120) - it is
that **repair uses the same deterministic rules that built the incumbent**, so whatever
is freed gets put back where those rules already prefer it. Noise perturbs the choice
but does not overcome the preference.

Reviving this needs a repair that differs from the construction, not a wider `fixed`.


One iteration: pick operations to drop (destroy), rebuild only those with the slot
rules (repair, via `dispatch.build(fixed=...)`), keep the result if it is not worse.

Why LNS and not tabu, which is what the strongest FJSP-AGV methods use: tabu's power
comes from evaluating a whole critical-path neighbourhood per iteration, which is only
affordable with incremental longest-path updates on a disjunctive graph. We have an
event-driven simulator, so every neighbour costs a full rebuild (~1ms). A tabu
iteration scanning ~200 neighbours would be ~200ms - about 3,000 iterations in 600s -
while LNS rebuilds once per iteration and gets ~600,000. Building the graph machinery
is the larger project, and our machine assignment changes node *and* arc weights
(han2024_formulation_notes), so the standard construction does not transfer directly.

The reason to prefer LNS over the tuned GA is not speed: 2026-08-01 and 2026-08-06 both
rejected the performance case for it, because matching population to budget kept closing
the gap. It is that **destroy is a fifth slot an LLM can evolve** - the decision humans
design worst (usually random or nearest-neighbour) and where VRPAgent found its SOTA.
"""
import random
import time

from model.rules import FAIL, NEVER
from simulator.dispatch import build
from simulator.solution import Solution
from simulator.timing import Params


def restrict(sol, keep):
    """The part of `sol` that survives destruction, as a Solution to pass as `fixed`."""
    return Solution(
        machine_of={g: k for g, k in sol.machine_of.items() if g in keep},
        machine_seq={k: [g for g in s if g in keep] for k, s in sol.machine_seq.items()},
        vehicle_of={g: v for g, v in sol.vehicle_of.items() if g in keep},
        vehicle_seq={v: [g for g in s if g in keep] for v, s in sol.vehicle_seq.items()},
    )


# --- destroy operators (hand-written; slot 5 replaces these) -----------------

def destroy_random(inst, sol, sched, rng, frac):
    """Drop a uniform sample. The null operator: no structure, so anything an evolved
    destroy achieves has to be measured against this."""
    ops = list(sol.machine_of)
    return set(rng.sample(ops, max(1, int(len(ops) * frac))))


def destroy_critical(inst, sol, sched, rng, frac):
    """Drop the operations finishing latest, i.e. those nearest the makespan.

    Rebuilding an operation that ends long before Cmax cannot lower Cmax on its own, so
    a uniform sample spends most of its budget where the objective cannot move. This is
    a cheap stand-in for a real critical path - we have no disjunctive graph, so
    "late-finishing" is the available proxy for "on the critical path".
    """
    ops = sorted(sol.machine_of, key=lambda g: sched.end.get(g, 0), reverse=True)
    n = max(1, int(len(ops) * frac))
    return set(ops[:n])


DESTROY = {"random": destroy_random, "critical": destroy_critical}


# --- repair noise -----------------------------------------------------------

def noisy(slots, rng, eta):
    """Perturb slot scores during repair.

    Destroy plus repair is the identity without this, and measurably so: rebuilding
    01a with the same deterministic rules that built it returned exactly the starting
    makespan in 60 of 60 draws at every destruction level up to 50% (2026-08-10). The
    rules are pure functions of the state, so they put every destroyed operation back
    where they had put it the first time - the neighbourhood is a single point. ALNS
    handles this the same way, by adding noise to the repair objective (Ropke & Pisinger).

    Necessary but not sufficient: with noise the acceptance rate rose only from 0 to
    0.002%, which is why the gate failed. Perturbing the choice does not overcome a
    repair rule that already prefers the incumbent's layout.

    The perturbation is scaled by the score's own magnitude, because slot scores differ
    by orders of magnitude (`-queue_len` is single digits, `-arrival` is thousands) and
    a fixed-width noise would erase one slot's preferences while barely touching
    another's. NEVER is passed through so "decline this candidate" stays absolute.
    """
    def wrap(fn):
        def scored(f):
            s = fn(f)
            if s == NEVER or s == FAIL:
                return s
            return s + rng.uniform(-eta, eta) * max(1.0, abs(s))
        return scored
    return {k: wrap(v) for k, v in slots.items()}


# --- the loop ---------------------------------------------------------------

def run(inst, slots, destroy=destroy_critical, frac=0.2, eta=0.1, time_limit=60.0,
        max_iter=None, seed=0, params=Params(), accept_equal=True):
    """Returns (best_solution, best_schedule, stats)."""
    rng = random.Random(seed)
    sol, sched = build(inst, slots, params)          # slot rules build the first solution
    best, best_sched = sol, sched
    incumbent = best_sched.cmax
    deadline = time.time() + time_limit
    it = accepted = sideways = 0

    while time.time() < deadline and (max_iter is None or it < max_iter):
        it += 1
        drop = destroy(inst, best, best_sched, rng, frac)
        keep = set(best.machine_of) - drop
        try:
            cand, cand_sched = build(inst, noisy(slots, rng, eta), params,
                                     fixed=restrict(best, keep))
        except Exception:
            continue                                  # infeasible rebuild: skip
        # Equal-cost moves are accepted so the search can drift across a plateau.
        # Improve-only stalls here: 2026-08-10 measured ~0.1% of rebuilds improving, so
        # the incumbent almost never moves and destroy keeps drawing from the same
        # solution. Sideways moves change the incumbent, hence the neighbourhood.
        if cand_sched.cmax < best_sched.cmax:
            best, best_sched = cand, cand_sched
            accepted += 1
        elif accept_equal and cand_sched.cmax == best_sched.cmax:
            best, best_sched = cand, cand_sched
            sideways += 1

    return best, best_sched, {"iterations": it, "accepted": accepted,
                              "sideways": sideways, "cmax": best_sched.cmax}
