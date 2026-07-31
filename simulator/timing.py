"""The timing core: the single place where schedule times are computed.

Both front-ends (replay of a published solution, and decoding of a GA chromosome)
call this, so validating it against published makespans validates both.

Recurrence, for operation o (the i-th operation of job j):

    transport needed  <=>  i == 0  or  machine(prev) != machine(o)
        (verified 2026-07-23 against the benchmark solutions: the omitted transports
         are exactly the same-machine consecutive pairs, 122/122, no counterexample)

    with transport, on vehicle v:
        pick_loc = L/U if i == 0 else machine(prev)
        ready    = 0   if i == 0 else C[prev]
        pickup   = max(v_free + travel[v_loc][pick_loc], ready)
        arrive   = pickup + load + travel[pick_loc][machine(o)] + unload
    without transport:
        arrive   = C[prev]                       # the job stays on the machine

    S[o] = max(arrive, C[predecessor of o on its machine])
    C[o] = S[o] + processing_time(o, machine(o))

Vehicles all start at the L/U depot at time 0 and never return to it after the
last operation (Berterottiere et al. 2025, section 3.1).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    """Assumptions the literature does not state explicitly. Defaults are the
    plain reading; replay.py can sweep them if a published makespan fails to
    reproduce (see the design report, section 6.2)."""
    load_time: int = 0
    unload_time: int = 0
    vehicles_start_at_depot: bool = True


class ScheduleError(Exception):
    pass


@dataclass
class Schedule:
    start: dict          # gid -> processing start
    end: dict            # gid -> processing end
    arrive: dict         # gid -> time the job is available at its machine
    pickup: dict         # gid -> time the vehicle picks the job up (transported ops only)
    transported: set     # gids that required a transport
    cmax: float


def needs_transport(inst, sol, gid):
    j, o = inst.job_op(gid)
    if o == 0:
        return True
    return sol.machine_of[inst.gid(j, o - 1)] != sol.machine_of[gid]


def simulate(inst, sol, params=Params()):
    """Compute all times for a fully-specified solution."""
    if not inst.travel:
        raise ScheduleError(f"{inst.name}: no travel matrix loaded")

    # predecessor of each operation on its machine
    mach_pred = {}
    for k, seq in sol.machine_seq.items():
        for idx, g in enumerate(seq):
            mach_pred[g] = seq[idx - 1] if idx else None

    # predecessor of each transport on its vehicle
    veh_pred = {}
    for v, seq in sol.vehicle_seq.items():
        for idx, g in enumerate(seq):
            veh_pred[g] = seq[idx - 1] if idx else None

    transported = {g for g in range(1, inst.n_ops + 1) if needs_transport(inst, sol, g)}

    arrive, pickup, start, end = {}, {}, {}, {}
    todo_arrive = set(range(1, inst.n_ops + 1))
    todo_end = set(range(1, inst.n_ops + 1))

    while todo_arrive or todo_end:
        progress = False

        for g in sorted(todo_arrive):
            j, o = inst.job_op(g)
            prev = inst.gid(j, o - 1) if o else None
            if prev is not None and prev not in end:
                continue

            if g not in transported:
                arrive[g] = end[prev]
                todo_arrive.discard(g)
                progress = True
                continue

            v = sol.vehicle_of.get(g)
            if v is None:
                raise ScheduleError(
                    f"{inst.name}: operation {g} needs a transport but the solution "
                    f"assigns no vehicle to it")
            pv = veh_pred[g]
            if pv is not None and pv not in arrive:
                continue

            if pv is None:
                v_free = 0
                v_loc = 0 if params.vehicles_start_at_depot else None
                if v_loc is None:            # vehicle starts wherever it is first needed
                    v_loc = 0 if o == 0 else sol.machine_of[prev]
            else:
                v_free = arrive[pv]
                v_loc = sol.machine_of[pv]

            pick_loc = 0 if o == 0 else sol.machine_of[prev]
            ready = 0 if o == 0 else end[prev]

            p = max(v_free + inst.travel[v_loc][pick_loc], ready)
            pickup[g] = p
            arrive[g] = (p + params.load_time
                         + inst.travel[pick_loc][sol.machine_of[g]]
                         + params.unload_time)
            todo_arrive.discard(g)
            progress = True

        for g in sorted(todo_end):
            if g not in arrive:
                continue
            mp = mach_pred.get(g)
            if mp is not None and mp not in end:
                continue
            k = sol.machine_of[g]
            start[g] = max(arrive[g], end[mp] if mp is not None else 0)
            end[g] = start[g] + inst.proc_time(g, k)
            todo_end.discard(g)
            progress = True

        if not progress:
            raise ScheduleError(
                f"{inst.name}: cannot resolve schedule - the machine and vehicle "
                f"sequences imply a cyclic dependency "
                f"({len(todo_end)} operations unresolved)")

    return Schedule(start=start, end=end, arrive=arrive, pickup=pickup,
                    transported=transported, cmax=max(end.values()))


def check_consistency(inst, sol):
    """Structural checks on a solution, independent of timing. Returns a list of
    problems (empty means consistent)."""
    problems = []
    all_ops = set(range(1, inst.n_ops + 1))

    covered = set(sol.machine_of)
    if covered != all_ops:
        problems.append(f"machine assignment covers {len(covered)} of {inst.n_ops} operations")

    for g, k in sol.machine_of.items():
        if k not in inst.eligible(g):
            problems.append(f"operation {g} is on machine {k}, eligible: {inst.eligible(g)}")

    need = {g for g in all_ops if needs_transport(inst, sol, g)}
    have = set(sol.vehicle_of)
    if need - have:
        problems.append(f"{len(need - have)} operations need a transport but have no vehicle "
                        f"(e.g. {sorted(need - have)[:5]})")
    if have - need:
        problems.append(f"{len(have - need)} operations have a vehicle but need no transport "
                        f"(e.g. {sorted(have - need)[:5]})")
    return problems
