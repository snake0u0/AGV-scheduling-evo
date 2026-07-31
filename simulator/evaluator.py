"""decode: turn a GA chromosome (OS, MS) + an AGV rule into a full schedule.

This is the GA-facing front-end. It builds the same Solution object that replay
reads from a file, and computes times with the same recurrence as timing.py, so a
decoded schedule fed back into timing.simulate must yield the identical makespan
(see self_check). That equality is a free, strong regression test.

Encoding (Han 2024, section 4.2):
  OS: a permutation of job ids with job j repeated (number of ops of j) times.
      The k-th occurrence of j denotes the k-th operation of job j.
  MS: indexed in canonical operation order (global id 1..N); MS[gid-1] is the
      index into that operation's eligible-machine list.
"""
from .solution import Solution
from .timing import Params, Schedule, simulate


def decode(inst, OS, MS, rule, params=Params()):
    """Return (Solution, Cmax). Vehicles are chosen greedily by `rule`; machine
    order on each machine is the order operations are dispatched in OS."""
    if not inst.travel:
        raise ValueError(f"{inst.name}: no travel matrix loaded")

    machine_of, machine_seq = {}, {k: [] for k in range(1, inst.n_machines + 1)}
    vehicle_of, vehicle_seq = {}, {v: [] for v in range(1, inst.n_vehicles + 1)}

    machine_free = {k: 0 for k in range(1, inst.n_machines + 1)}
    veh_free = {v: 0 for v in range(1, inst.n_vehicles + 1)}
    veh_loc = {v: 0 for v in range(1, inst.n_vehicles + 1)}          # 0 = L/U depot
    veh_cum = {v: 0 for v in range(1, inst.n_vehicles + 1)}

    job_prev_end = {}        # job -> end time of its previous operation
    job_prev_mach = {}       # job -> machine of its previous operation
    next_op = {j: 0 for j in range(inst.n_jobs)}   # next operation index per job

    start, end, arrive = {}, {}, {}

    for j in OS:
        o = next_op[j]
        next_op[j] += 1
        g = inst.gid(j, o)

        eligible = inst.eligible(g)
        k = eligible[MS[g - 1]]
        machine_of[g] = k

        if o == 0:
            pick_loc, ready = 0, 0
            transport = True
        else:
            pick_loc, ready = job_prev_mach[j], job_prev_end[j]
            transport = (job_prev_mach[j] != k)

        if transport:
            best_v, best_arr, best_pick = None, None, None
            for v in range(1, inst.n_vehicles + 1):
                empty = inst.travel[veh_loc[v]][pick_loc]
                pickup = max(veh_free[v] + empty, ready)
                loaded = inst.travel[pick_loc][k]
                arr = pickup + params.load_time + loaded + params.unload_time
                feat = {
                    "empty_travel": empty,
                    "loaded_travel": loaded,
                    "arrival": arr,
                    "wait": max(0, ready - (veh_free[v] + empty)),
                    "agv_free": veh_free[v],
                    "agv_cum_travel": veh_cum[v],
                    "machine_free": machine_free[k],
                    "remaining_ops": len(inst.jobs[j]) - o,
                }
                score = rule(feat)
                if best_v is None or score > best_score:
                    best_v, best_arr, best_pick, best_score = v, arr, pickup, score

            arrive[g] = best_arr
            vehicle_of[g] = best_v
            vehicle_seq[best_v].append(g)
            veh_cum[best_v] += (inst.travel[veh_loc[best_v]][pick_loc]
                                + inst.travel[pick_loc][k])
            veh_free[best_v] = best_arr
            veh_loc[best_v] = k
        else:
            arrive[g] = ready

        s = max(arrive[g], machine_free[k])
        e = s + inst.proc_time(g, k)
        start[g], end[g] = s, e
        machine_free[k] = e
        machine_seq[k].append(g)
        job_prev_end[j], job_prev_mach[j] = e, k

    sol = Solution(machine_of=machine_of, machine_seq=machine_seq,
                   vehicle_of=vehicle_of, vehicle_seq=vehicle_seq,
                   meta={"decoded": True, "rule": getattr(rule, "expr", getattr(rule, "__name__", "?"))})
    cmax = max(end.values())
    sched = Schedule(start=start, end=end, arrive=arrive, pickup={},
                     transported=set(vehicle_of), cmax=cmax)
    return sol, sched


def self_check(inst, sol, decoded_cmax, params=Params()):
    """Feed the decoded Solution back through the timing core; the makespan must match.
    Returns (ok, replay_cmax)."""
    replay = simulate(inst, sol, params)
    return replay.cmax == decoded_cmax, replay.cmax
