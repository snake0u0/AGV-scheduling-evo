"""Salabim port of the dynamic FJSP+AGV simulator (SPIKE / engine-comparison).

Faithful re-implementation of sim/agv_fms.py on top of salabim's process-based
DES engine, exposing the SAME interface:
    simulate_salabim(config, policy, seed=0, machine_policy=None) -> metrics dict
and the SAME feature set, so the LLM-AHD loop is engine-agnostic.

Instance generation replicates sim/agv_fms.py::_gen_jobs draw-for-draw, so for a
given (config, seed) BOTH engines see identical jobs -> any metric difference is
due to engine modelling (same-timestamp event ordering), not different instances.

Purpose: cross-check that salabim reproduces the validated engine's rule rankings
before committing to it. Headless (no animation). See sim/crosscheck_salabim.py.
"""
from __future__ import annotations
import random
import salabim as sim

sim.yieldless(False)   # use classic yield-based process generators (salabim >=26 defaults to yieldless)

LU = "LU"


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Job:
    def __init__(self, jid, arrival, due, ops):
        self.jid = jid
        self.arrival = arrival
        self.due = due
        self.ops = ops          # list of (eligible_machines_tuple, proc_time)
        self.op_idx = 0
        self.completion = -1.0
        self.q_entry = 0.0

    def remaining_proc(self):
        return sum(p for _, p in self.ops[self.op_idx:])

    def done(self):
        return self.op_idx >= len(self.ops)


class Task:
    def __init__(self, tid, job, src, dst_machine, dst_loc, ready_time):
        self.tid = tid
        self.job = job
        self.src = src
        self.dst_machine = dst_machine
        self.dst_loc = dst_loc
        self.ready_time = ready_time
        self.assigned = False


def gen_jobs(config, seed):
    """Replicates sim/agv_fms.py::_gen_jobs exactly (same RNG draw order)."""
    rng = random.Random(seed)
    c = config
    jobs, t = [], 0.0
    flex = c.get("flex", 1)
    for j in range(c["n_jobs"]):
        t += rng.expovariate(c["arrival_rate"])
        n_ops = rng.randint(*c.get("ops_range", (2, 4)))
        ops = []
        for _ in range(n_ops):
            if flex == 1:
                elig = (rng.randrange(c["n_machines"]),)       # match agv_fms.py rng sequence
            else:
                elig = tuple(rng.sample(range(c["n_machines"]), min(flex, c["n_machines"])))
            p = rng.uniform(*c.get("proc_range", (3.0, 9.0)))
            ops.append((elig, p))
        total = sum(p for _, p in ops)
        due = t + c.get("due_tightness", 3.0) * total
        jobs.append(Job(j, t, due, ops))
    return jobs


# ---- salabim components ----
class AGVComp(sim.Component):
    def setup(self, W, aid, loc):
        self.W, self.aid, self.loc = W, aid, loc
        self.task = None
        self.busy_time = self.travel = self.deadhead = 0.0

    def process(self):
        while True:
            if self.task is None:
                yield self.passivate()
                continue
            task = self.task
            dead = self.W.ttime(self.loc, task.src) * self.W._cong_factor()  # deadhead (congestion-slowed)
            self.travel += dead; self.deadhead += dead; self.busy_time += dead
            yield self.hold(dead)
            self.loc = task.src
            d = self.W.ttime(task.src, task.dst_loc) * self.W._cong_factor()  # loaded travel
            self.travel += d; self.busy_time += d
            yield self.hold(d)
            self.loc = task.dst_loc
            self.W.on_dropoff(self, task)
            self.task = None
            self.W.dispatch()


class MachineComp(sim.Component):
    def setup(self, W, mid, loc):
        self.W, self.mid, self.loc = W, mid, loc
        self.busy = False
        self.queue = []      # jobs waiting

    def process(self):
        while True:
            if self.busy or not self.queue:
                yield self.passivate()
                continue
            job = self.W.pick_job(self, self.queue)
            self.queue.remove(job)
            self.busy = True
            proc = job.ops[job.op_idx][1]
            yield self.hold(proc)
            self.busy = False
            self.W.on_op_complete(job, self)


class JobGen(sim.Component):
    def setup(self, W):
        self.W = W

    def process(self):
        for job in self.W.jobs:          # jobs already sorted by arrival
            yield self.hold(till=job.arrival)
            self.W.on_arrival(job)


class World:
    def __init__(self, env, config, policy, machine_policy, seed):
        self.env = env
        self.cfg = config
        self.policy = policy
        self.machine_policy = machine_policy
        self.speed = config.get("speed", 1.0)
        self._tid = 0
        self.ready = []
        self.jobs = gen_jobs(config, seed)
        # layout: machines on grid, L/U at origin (identical to agv_fms.py)
        cols = config.get("grid_cols", 4)
        self.lu_loc = (0, 0)
        self.machines = {}
        for m in range(config["n_machines"]):
            loc = (1 + (m % cols), 1 + (m // cols))
            self.machines[m] = MachineComp(W=self, mid=m, loc=loc)
        self.agvs = [AGVComp(W=self, aid=a, loc=self.lu_loc)
                     for a in range(config["n_agvs"])]
        JobGen(W=self)

    def now(self):
        return self.env.now()

    def ttime(self, a, b):
        return manhattan(a, b) / self.speed

    def _cong_factor(self):
        """Congestion-delay multiplier (mirrors agv_fms.py): 1 + alpha*(busy/fleet)."""
        alpha = self.cfg.get("congestion_alpha", 0.0)
        if not alpha:
            return 1.0
        busy = sum(1 for a in self.agvs if a.task is not None)
        return 1.0 + alpha * (busy / len(self.agvs))

    def _assign(self, eligible):
        """FJSP machine-assignment rule (mirrors agv_fms.py): least-loaded eligible machine."""
        if len(eligible) == 1:
            return eligible[0]
        return min(eligible, key=lambda mid: (len(self.machines[mid].queue), mid))

    def _new_task(self, job, src, dst_machine, dst_loc):
        self._tid += 1
        self.ready.append(Task(self._tid, job, src, dst_machine, dst_loc, self.now()))

    # ---- machine sequencing (joint N1) ----
    def _mfeatures(self, job, m):
        proc = job.ops[job.op_idx][1]
        rem = job.remaining_proc()
        nxt = job.op_idx + 1
        dl = min(len(self.machines[mid].queue) for mid in job.ops[nxt][0]) if nxt < len(job.ops) else 0
        return {"proc_time": proc, "slack": job.due - self.now() - rem,
                "job_wait": self.now() - job.q_entry,
                "remaining_ops": len(job.ops) - job.op_idx,
                "remaining_proc": rem, "downstream_load": dl}

    def pick_job(self, m, queue):
        if self.machine_policy is not None:
            best, bscore = None, -1e18
            for jb in queue:
                try:
                    s = self.machine_policy(self._mfeatures(jb, m))
                except Exception:
                    s = -1e9
                if s > bscore:
                    bscore, best = s, jb
            return best
        # fixed fallback: EDD (smallest due first) -- matches agv_fms.py v0
        return min(queue, key=lambda jb: jb.due)

    # ---- AGV dispatching features (identical to agv_fms.py::_features) ----
    def _features(self, agv, task):
        tt = self.ttime(agv.loc, task.src)
        rem = task.job.remaining_proc()
        slack = task.job.due - self.now() - rem
        dl = 0 if task.dst_machine == LU else len(self.machines[task.dst_machine].queue)
        return {"travel_time": tt, "task_wait": self.now() - task.ready_time,
                "slack": slack, "downstream_load": dl,
                "congestion": len([t for t in self.ready if not t.assigned]),
                "deadhead": tt, "battery_soc": 1.0}

    def dispatch(self):
        idle = [a for a in self.agvs if a.task is None]
        ready = [t for t in self.ready if not t.assigned]
        if not idle or not ready:
            return
        scored = []
        for a in idle:
            for t in ready:
                try:
                    s = self.policy(self._features(a, t))
                except Exception:
                    s = -1e9
                scored.append((s, a.aid, t.tid, a, t))
        scored.sort(key=lambda x: (-x[0], x[1], x[2]))   # score desc, then aid,tid
        used_a, used_t = set(), set()
        for s, aid, tid, a, t in scored:
            if aid in used_a or tid in used_t:
                continue
            used_a.add(aid); used_t.add(tid)
            a.task = t; t.assigned = True
            if a.ispassive():
                a.activate()
        self.ready = [t for t in self.ready if not t.assigned]

    # ---- event handlers ----
    def on_arrival(self, job):
        m0 = self.machines[self._assign(job.ops[0][0])]
        self._new_task(job, self.lu_loc, m0.mid, m0.loc)
        self.dispatch()

    def on_dropoff(self, agv, task):
        if task.dst_machine == LU:
            task.job.completion = self.now()
        else:
            mm = self.machines[task.dst_machine]
            task.job.q_entry = self.now()
            mm.queue.append(task.job)
            if mm.ispassive():
                mm.activate()

    def on_op_complete(self, job, m):
        job.op_idx += 1
        if job.done():
            self._new_task(job, m.loc, LU, self.lu_loc)
        else:
            nm = self.machines[self._assign(job.ops[job.op_idx][0])]
            self._new_task(job, m.loc, nm.mid, nm.loc)
        self.dispatch()

    def metrics(self):
        comp = [j for j in self.jobs if j.completion >= 0]
        if not comp:
            return {"completed": 0}
        makespan = max(j.completion for j in comp)
        tard = [max(0.0, j.completion - j.due) for j in comp]
        flow = [j.completion - j.arrival for j in comp]
        tot_travel = sum(a.travel for a in self.agvs) or 1e-9
        tot_dead = sum(a.deadhead for a in self.agvs)
        tot_busy = sum(a.busy_time for a in self.agvs)
        return {"completed": len(comp), "makespan": round(makespan, 2),
                "mean_tardiness": round(sum(tard) / len(tard), 2),
                "max_tardiness": round(max(tard), 2),
                "mean_flowtime": round(sum(flow) / len(flow), 2),
                "throughput": round(len(comp) / makespan, 4),
                "agv_util": round(tot_busy / (len(self.agvs) * makespan), 3),
                "deadhead_ratio": round(tot_dead / tot_travel, 3)}


def simulate_salabim(config, policy, seed=0, machine_policy=None):
    env = sim.Environment(random_seed=seed)
    W = World(env, config, policy, machine_policy, seed)
    env.run()
    return W.metrics()
