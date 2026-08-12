"""Event-driven schedule builder with one rule slot per subproblem.

`evaluator.decode` can only express one of the four subproblems as a rule: machine
selection and operation sequencing come from the GA chromosome, and AGV sequencing is
not a decision at all - each vehicle's task order simply falls out of the order OS
happened to dispatch in. This module makes all four decisions explicit so a heuristic
can be evolved for each.

The four slots are the two resource types crossed with assignment and sequencing,
which is symmetric and leaves no ambiguous case:

    machine  slot 1 machine_select   an operation is released -> which machine's queue
             slot 2 op_sequence      a machine falls idle     -> which of its queued ops
    vehicle  slot 3 vehicle_select   a transport is created   -> which vehicle's queue
             slot 4 task_sequence    a vehicle falls idle     -> which of its queued tasks

Each slot is `f(features) -> score`; the highest score wins, ties go to the lower
index, exactly as in `rules.py`. The vehicle-side feature names match the ones
`rules.py` already uses, so D1/D2 and the evolved expressions drop into slot 3 or 4
unchanged.

Timing follows `timing.py` exactly - same transport condition, same recurrence, same
depot convention. That is not a matter of taste: `self_check` below feeds the produced
solution back through `timing.simulate` and requires the identical makespan, so any
divergence is a test failure rather than a silent difference.

An operation is *released* once its job predecessor has been **scheduled** (its end
time is known), not once that predecessor has finished. This is what allows a vehicle
to set off toward a pickup point before the job is ready and wait there, which
`timing.py`'s `max(v_free + travel, ready)` already models and which the published
solutions rely on.
"""
from .solution import Solution
from .timing import Params, Schedule

SLOTS = ("machine_select", "op_sequence", "vehicle_select", "task_sequence")


class DispatchError(Exception):
    pass


NEVER = float("-inf")


def _argmax(items, score):
    """Highest score wins; ties go to the first item, so callers control tie-breaks
    by the order they pass candidates in.

    A score of -inf means "not selectable now", which lets a resource sit idle rather
    than take whatever happens to be available. Returns None if every candidate is
    -inf. Evolved expressions never produce -inf (`rule_from_expr` returns -1e18 on
    error), so this is reserved for `forced_slots`.
    """
    best, best_s = None, None
    for it in items:
        sc = score(it)
        if sc == NEVER:
            continue
        if best is None or sc > best_s:
            best, best_s = it, sc
    return best


def _with_all(rule, cands, feat):
    """Score each candidate with `_all` = every candidate's features in the dict.

    Without this a rule sees one candidate at a time and can only judge it in
    absolute terms, which is exactly the expressive power of Han 2024's fixed
    decodings. Relative judgements - "is this the busiest vehicle in the fleet?",
    "is the travel spread small enough that load matters more?" - need the others.
    2026-08-07 measured why that matters: textbook greedy rules (fastest machine,
    earliest AGV) score 157.7% against 76.6% for plain load balancing, because
    everyone crowds the same good resource. Avoiding contention is a relative
    judgement.

    The feature dicts are built once and shared, so this stays O(V) per decision and
    `_argmax`/`forced_slots` are untouched.
    """
    feats = {c: feat(c) for c in cands}
    allf = list(feats.values())
    for f in allf:
        f["_all"] = allf
    return lambda c: rule(feats[c])


def build(inst, slots, params=Params(), on_commit=None, fixed=None):
    """Run the four slots over `inst` and return (Solution, Schedule).

    `slots` maps each name in SLOTS to a callable f(features) -> score.
    `on_commit(kind, resource, gid)` is called after each committed decision, where
    kind is "machine" or "vehicle"; `forced_slots` uses it to advance its pointers.

    `fixed` is a Solution whose assignments are kept: any operation in
    `fixed.machine_of` takes its machine from there instead of asking slot 1, and
    likewise for vehicles and slot 3. Operations absent from it are decided by the
    slots as usual. That is LNS repair - destroy drops operations out of `fixed`, and
    the rules place only those.

    It is a parameter rather than a `NEVER`-returning slot wrapper (which would also
    work) because a fixed decision is structural, not a preference. Hiding it in the
    scoring channel would leave the builder unable to tell "the rule strongly prefers
    machine 3" from "this is not a decision", which blocks incremental rebuild,
    per-iteration logging of what the rules actually chose, and any check that repair
    touched only the destroyed operations.
    """
    missing = [s for s in SLOTS if s not in slots]
    if missing:
        raise DispatchError(f"missing slot(s): {missing}")
    if not inst.travel:
        raise DispatchError(f"{inst.name}: no travel matrix loaded")

    # Assignments are fixed by lookup; sequences by a head pointer per resource, so a
    # kept operation may only be taken when it is next in its prescribed order while a
    # destroyed one competes freely. Fixing assignments alone would let repair reshuffle
    # every queue, which is a restart with hints rather than a large neighbourhood.
    fix_m = fixed.machine_of if fixed is not None else {}
    fix_v = fixed.vehicle_of if fixed is not None else {}
    fseq_m = dict(fixed.machine_seq) if fixed is not None else {}
    fseq_v = dict(fixed.vehicle_seq) if fixed is not None else {}
    fset_m = {k: set(s) for k, s in fseq_m.items()}
    fset_v = {v: set(s) for v, s in fseq_v.items()}
    fpos_m = {k: 0 for k in fseq_m}
    fpos_v = {v: 0 for v in fseq_v}

    def _selectable(cands, seq, sset, pos):
        """Kept operations only at the head of their prescribed order; the rest free."""
        if seq is None:
            return cands
        head = seq[pos] if pos < len(seq) else None
        return [g for g in cands if g not in sset or g == head]

    M = range(1, inst.n_machines + 1)
    V = range(1, inst.n_vehicles + 1)

    machine_free = {k: 0 for k in M}
    machine_seq = {k: [] for k in M}
    mq = {k: [] for k in M}                       # assigned to k, not yet sequenced

    veh_free = {v: 0 for v in V}
    veh_loc = {v: 0 for v in V}                   # 0 = L/U depot
    veh_cum = {v: 0 for v in V}
    veh_seq = {v: [] for v in V}
    vq = {v: [] for v in V}                       # assigned to v, not yet sequenced

    machine_of, vehicle_of = {}, {}
    start, end, arrive, pickup = {}, {}, {}, {}
    job_next = {j: 0 for j in range(inst.n_jobs)}   # next operation index to release

    def prev_of(g):
        j, o = inst.job_op(g)
        return inst.gid(j, o - 1) if o else None

    def job_tail(g):
        """(operations left in this job including g, their shortest processing time)."""
        j, o = inst.job_op(g)
        ops = inst.jobs[j][o:]
        return len(ops), sum(min(pt for _, pt in alts) for alts in ops)

    # --- release: assign a machine (slot 1) and, if a transport is implied, a vehicle
    def release():
        moved = False
        for j in range(inst.n_jobs):
            o = job_next[j]
            if o >= len(inst.jobs[j]):
                continue
            g = inst.gid(j, o)
            prev = prev_of(g)
            if prev is not None and prev not in end:
                continue                          # predecessor not scheduled yet
            pick_loc = 0 if prev is None else machine_of[prev]
            ready = 0 if prev is None else end[prev]
            n_left, proc_left = job_tail(g)

            def mfeat(k):
                return {
                    "_gid": g, "_cand": k,
                    "proc_time": inst.proc_time(g, k),
                    "machine_free": machine_free[k],
                    "travel_to": inst.travel[pick_loc][k],
                    "queue_len": len(mq[k]),
                    "job_ready": ready,
                    "remaining_ops": n_left,
                    "remaining_proc": proc_left,
                }

            k = (fix_m.get(g) if g in fix_m else
                 _argmax(inst.eligible(g), _with_all(slots["machine_select"],
                                                     inst.eligible(g), mfeat)))
            machine_of[g] = k
            job_next[j] += 1
            moved = True

            if prev is not None and machine_of[prev] == k:
                arrive[g] = ready                 # stays on the machine, no transport
                mq[k].append(g)
                continue

            loaded = inst.travel[pick_loc][k]

            def vfeat(v):
                return {
                    "_gid": g, "_cand": v,
                    "empty_travel": inst.travel[veh_loc[v]][pick_loc],
                    "loaded_travel": loaded,
                    "agv_free": veh_free[v],
                    "agv_cum_travel": veh_cum[v],
                    "queue_len": len(vq[v]),
                    "ready": ready,
                    "machine_free": machine_free[k],
                    "remaining_ops": n_left,
                }

            v = (fix_v.get(g) if g in fix_v else
                 _argmax(list(V), _with_all(slots["vehicle_select"], list(V), vfeat)))
            vehicle_of[g] = v
            vq[v].append(g)
        return moved

    # --- a vehicle takes one task from its own queue (slot 4)
    def run_vehicle(v):
        def feat(g):
            prev = prev_of(g)
            pick_loc = 0 if prev is None else machine_of[prev]
            ready = 0 if prev is None else end[prev]
            k = machine_of[g]
            empty = inst.travel[veh_loc[v]][pick_loc]
            p = max(veh_free[v] + empty, ready)
            n_left, proc_left = job_tail(g)
            return {
                "_gid": g, "_cand": v,
                "empty_travel": empty,
                "loaded_travel": inst.travel[pick_loc][k],
                "arrival": p + params.load_time + inst.travel[pick_loc][k] + params.unload_time,
                "wait": max(0, ready - (veh_free[v] + empty)),
                "agv_free": veh_free[v],
                "agv_cum_travel": veh_cum[v],
                "machine_free": machine_free[k],
                "remaining_ops": n_left,
                "remaining_proc": proc_left,
            }

        cands = _selectable(vq[v], fseq_v.get(v), fset_v.get(v, ()), fpos_v.get(v, 0))
        g = _argmax(cands, _with_all(slots["task_sequence"], cands, feat))
        if g is None:
            return False                          # the vehicle waits
        if v in fpos_v and fpos_v[v] < len(fseq_v[v]) and fseq_v[v][fpos_v[v]] == g:
            fpos_v[v] += 1
        vq[v].remove(g)
        prev = prev_of(g)
        pick_loc = 0 if prev is None else machine_of[prev]
        ready = 0 if prev is None else end[prev]
        k = machine_of[g]

        p = max(veh_free[v] + inst.travel[veh_loc[v]][pick_loc], ready)
        pickup[g] = p
        arrive[g] = (p + params.load_time + inst.travel[pick_loc][k] + params.unload_time)
        veh_cum[v] += inst.travel[veh_loc[v]][pick_loc] + inst.travel[pick_loc][k]
        veh_free[v] = arrive[g]
        veh_loc[v] = k
        veh_seq[v].append(g)
        mq[k].append(g)
        if on_commit:
            on_commit("vehicle", v, g)
        return True

    # --- a machine takes one operation from its own queue (slot 2)
    def run_machine(k):
        ready_ops = [g for g in mq[k] if g in arrive]
        def feat(g):
            n_left, proc_left = job_tail(g)
            return {
                "_gid": g, "_cand": k,
                "proc_time": inst.proc_time(g, k),
                "arrival": arrive[g],
                "wait": max(0, arrive[g] - machine_free[k]),
                "idle": max(0, machine_free[k] - arrive[g]),
                "job_wait": machine_free[k] - arrive[g],
                "queue_len": len(ready_ops),
                "remaining_ops": n_left,
                "remaining_proc": proc_left,
            }

        cands = _selectable(ready_ops, fseq_m.get(k), fset_m.get(k, ()), fpos_m.get(k, 0))
        g = _argmax(cands, _with_all(slots["op_sequence"], cands, feat))
        if g is None:
            return False                          # the machine idles
        if k in fpos_m and fpos_m[k] < len(fseq_m[k]) and fseq_m[k][fpos_m[k]] == g:
            fpos_m[k] += 1
        mq[k].remove(g)
        s = max(arrive[g], machine_free[k])
        start[g], end[g] = s, s + inst.proc_time(g, k)
        machine_free[k] = end[g]
        machine_seq[k].append(g)
        if on_commit:
            on_commit("machine", k, g)
        return True

    # --- main loop: release everything possible, then advance the earliest resource
    guard = 0
    while len(end) < inst.n_ops:
        release()

        # vehicles first at equal times, so arrivals exist before machines consume them
        actions = [(veh_free[v], 0, v, "v") for v in V if vq[v]]
        actions += [(machine_free[k], 1, k, "m") for k in M
                    if any(g in arrive for g in mq[k])]
        if not actions:
            raise DispatchError(
                f"{inst.name}: stuck with {inst.n_ops - len(end)} operations unscheduled")
        for _, _, idx, kind in sorted(actions):
            if run_vehicle(idx) if kind == "v" else run_machine(idx):
                break
        else:
            raise DispatchError(
                f"{inst.name}: every resource declined to act with "
                f"{inst.n_ops - len(end)} operations unscheduled")

        guard += 1
        if guard > 4 * inst.n_ops + 16:
            raise DispatchError(f"{inst.name}: loop did not terminate")

    sol = Solution(machine_of=machine_of, machine_seq=machine_seq,
                   vehicle_of=vehicle_of, vehicle_seq=veh_seq,
                   meta={"built_by": "dispatch.build"})
    sched = Schedule(start=start, end=end, arrive=arrive, pickup=pickup,
                     transported=set(vehicle_of), cmax=max(end.values()))
    return sol, sched


# --- gates ------------------------------------------------------------------

def self_check(inst, sol, built_cmax, params=Params()):
    """Feed the built solution back through the validated timing core. Any divergence
    in the builder's own arithmetic shows up here as a mismatch."""
    from .timing import simulate
    replay = simulate(inst, sol, params)
    return replay.cmax == built_cmax, replay.cmax


def forced_slots(sol):
    """Slots + an on_commit hook that reproduce an existing solution, for the replay gate.

    Only the head of each resource's prescribed sequence is selectable; everything else
    scores -inf, so a machine or vehicle waits rather than taking whatever arrived
    first. Without that the builder diverges whenever an operation physically arrives
    out of the prescribed order, which is exactly what happened on fjsp5 and fjsp6.

    Returns (slots, on_commit) - pass both to `build`.
    """
    head = {("machine", k): 0 for k in sol.machine_seq}
    head.update({("vehicle", v): 0 for v in sol.vehicle_seq})
    seqs = {("machine", k): seq for k, seq in sol.machine_seq.items()}
    seqs.update({("vehicle", v): seq for v, seq in sol.vehicle_seq.items()})

    def is_head(kind, res, g):
        seq = seqs.get((kind, res), [])
        i = head[(kind, res)]
        return i < len(seq) and seq[i] == g

    def on_commit(kind, res, g):
        head[(kind, res)] += 1

    return {
        "machine_select": lambda f: 0.0 if f["_cand"] == sol.machine_of[f["_gid"]] else NEVER,
        "vehicle_select": lambda f: 0.0 if f["_cand"] == sol.vehicle_of[f["_gid"]] else NEVER,
        "op_sequence": lambda f: 0.0 if is_head("machine", f["_cand"], f["_gid"]) else NEVER,
        "task_sequence": lambda f: 0.0 if is_head("vehicle", f["_cand"], f["_gid"]) else NEVER,
    }, on_commit
