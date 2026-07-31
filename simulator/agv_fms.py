"""Dynamic FJSP + AGV discrete-event simulator (v0).

Jobs arrive over time; each job is a sequence of operations on machines.
AGVs transport jobs between the L/U station and machines, and machine->machine.
The AGV DISPATCHING decision (which idle AGV takes which ready transport task) is
made by a pluggable `policy(features)->score`; the dispatcher assigns the highest
score (greedy matching). This is the decision the AGV-aware AHD will evolve.

Machine operation sequencing uses a fixed rule (FIFO/EDD) in v0.
Pure stdlib. Deterministic given a seed. See runs/.../simulator_spec.md.
"""
from __future__ import annotations
import heapq, random
from dataclasses import dataclass, field

LU = "LU"  # load/unload station id


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@dataclass
class Job:
    jid: int
    arrival: float
    due: float
    ops: list          # list of (machine_id, proc_time)
    op_idx: int = 0
    completion: float = -1.0
    q_entry: float = 0.0   # time this job entered its current machine queue

    def remaining_proc(self):
        return sum(p for _, p in self.ops[self.op_idx:])

    def done(self):
        return self.op_idx >= len(self.ops)


@dataclass
class Task:
    tid: int
    job: Job
    src: object         # location (x,y)
    dst_machine: object  # machine id or LU
    dst_loc: object      # location (x,y)
    ready_time: float
    assigned: bool = False


@dataclass
class AGV:
    aid: int
    loc: tuple
    idle: bool = True
    busy_time: float = 0.0
    travel: float = 0.0
    deadhead: float = 0.0


@dataclass
class Machine:
    mid: int
    loc: tuple
    busy: bool = False
    queue: list = field(default_factory=list)   # jobs waiting to be processed


class Simulator:
    def __init__(self, config, policy, seed=0, machine_policy=None):
        self.cfg = config
        self.policy = policy               # AGV dispatching rule  policy(features)->score
        self.machine_policy = machine_policy  # optional machine sequencing rule (N1 joint); None=EDD
        self.rng = random.Random(seed)
        self.now = 0.0
        self._evq = []
        self._eseq = 0
        self._tid = 0
        # layout: machines on a grid, L/U at origin
        M = config["n_machines"]
        cols = config.get("grid_cols", 4)
        self.lu_loc = (0, 0)
        self.machines = {}
        for m in range(M):
            loc = (1 + (m % cols), 1 + (m // cols))
            self.machines[m] = Machine(m, loc)
        self.agvs = [AGV(a, self.lu_loc) for a in range(config["n_agvs"])]
        self.ready = []          # ready & unassigned transport tasks
        self.jobs = []
        self.speed = config.get("speed", 1.0)

    # ---- event queue ----
    def _push(self, t, kind, payload):
        heapq.heappush(self._evq, (t, self._eseq, kind, payload))
        self._eseq += 1

    def ttime(self, a, b):
        return manhattan(a, b) / self.speed

    def _cong_factor(self):
        """Congestion-delay multiplier: travel slows as more AGVs are concurrently active.
        factor = 1 + alpha * (busy_agvs / fleet). alpha=0 (default) => no congestion (v0).
        Anchored on AMHS congestion literature (C&IE 2014); see benchmark_anchor_notes.md."""
        alpha = self.cfg.get("congestion_alpha", 0.0)
        if not alpha:
            return 1.0
        busy = sum(1 for a in self.agvs if not a.idle)
        return 1.0 + alpha * (busy / len(self.agvs))

    # ---- job generation (Poisson arrivals) ----
    def _gen_jobs(self):
        c = self.cfg
        t = 0.0
        for j in range(c["n_jobs"]):
            t += self.rng.expovariate(c["arrival_rate"])
            n_ops = self.rng.randint(*c.get("ops_range", (2, 4)))
            flex = c.get("flex", 1)                                # FJSP: #eligible machines/op (1 = JSP)
            ops = []
            for _ in range(n_ops):
                if flex == 1:
                    elig = (self.rng.randrange(c["n_machines"]),)  # keep v0 rng sequence bit-identical
                else:
                    elig = tuple(self.rng.sample(range(c["n_machines"]), min(flex, c["n_machines"])))
                p = self.rng.uniform(*c.get("proc_range", (3.0, 9.0)))
                ops.append((elig, p))                              # op = (eligible_machines, proc_time)
            total = sum(p for _, p in ops)
            due = t + c.get("due_tightness", 3.0) * total
            job = Job(j, t, due, ops)
            self.jobs.append(job)
            self._push(t, "arrival", job)

    # ---- handlers ----
    def _on_arrival(self, job):
        # job appears at L/U, needs transport to an eligible machine of op0 (assignment rule)
        m0 = self.machines[self._assign(job.ops[0][0])]
        self._new_task(job, self.lu_loc, m0.mid, m0.loc)
        self._dispatch()

    def _new_task(self, job, src, dst_machine, dst_loc):
        self._tid += 1
        self.ready.append(Task(self._tid, job, src, dst_machine, dst_loc, self.now))

    def _assign(self, eligible):
        """FJSP machine-assignment rule (fixed, standard): least-loaded eligible machine.
        Deterministic; for flex=1 returns the single machine (no behavior change vs v0)."""
        if len(eligible) == 1:
            return eligible[0]
        return min(eligible, key=lambda mid: (len(self.machines[mid].queue), mid))

    def _mfeatures(self, job: Job, m: Machine):
        proc = job.ops[job.op_idx][1]
        rem = job.remaining_proc()
        nxt = job.op_idx + 1
        dl = min(len(self.machines[mid].queue) for mid in job.ops[nxt][0]) if nxt < len(job.ops) else 0
        return {
            "proc_time": proc,
            "slack": job.due - self.now - rem,
            "job_wait": self.now - job.q_entry,
            "remaining_ops": len(job.ops) - job.op_idx,
            "remaining_proc": rem,
            "downstream_load": dl,
        }

    def _start_machine(self, m: Machine):
        if m.busy or not m.queue:
            return
        if self.machine_policy is not None:
            # N1: machine sequencing is an evolved rule over machine features
            best, bscore = None, -1e18
            for jb in m.queue:
                try:
                    s = self.machine_policy(self._mfeatures(jb, m))
                except Exception:
                    s = -1e9
                if s > bscore:
                    bscore, best = s, jb
            job = best
            m.queue.remove(job)
        else:
            rule = self.cfg.get("machine_rule", "EDD")  # fixed fallback
            if rule == "EDD":
                m.queue.sort(key=lambda jb: jb.due)
            job = m.queue.pop(0)
        proc = job.ops[job.op_idx][1]
        m.busy = True
        self._push(self.now + proc, "op_complete", (job, m))

    def _on_op_complete(self, job, m: Machine):
        m.busy = False
        job.op_idx += 1
        if job.done():
            # final transport machine -> L/U
            self._new_task(job, m.loc, LU, self.lu_loc)
        else:
            nm = self.machines[self._assign(job.ops[job.op_idx][0])]
            self._new_task(job, m.loc, nm.mid, nm.loc)
        self._start_machine(m)      # let machine pick next queued job
        self._dispatch()

    def _on_pickup(self, agv: AGV, task: Task):
        agv.loc = task.src
        # loaded travel src -> dst (slowed by current congestion)
        d = self.ttime(task.src, task.dst_loc) * self._cong_factor()
        agv.travel += d
        agv.busy_time += d
        self._push(self.now + d, "dropoff", (agv, task))

    def _on_dropoff(self, agv: AGV, task: Task):
        agv.loc = task.dst_loc
        if task.dst_machine == LU:
            task.job.completion = self.now
        else:
            mm = self.machines[task.dst_machine]
            task.job.q_entry = self.now
            mm.queue.append(task.job)
            self._start_machine(mm)
        agv.idle = True
        self._dispatch()

    # ---- dispatching (the evolved decision point) ----
    def _features(self, agv: AGV, task: Task):
        tt = self.ttime(agv.loc, task.src)
        rem = task.job.remaining_proc()
        slack = task.job.due - self.now - rem
        if task.dst_machine == LU:
            dl = 0
        else:
            dl = len(self.machines[task.dst_machine].queue)
        return {
            "travel_time": tt,
            "task_wait": self.now - task.ready_time,
            "slack": slack,
            "downstream_load": dl,
            "congestion": len(self.ready),
            "deadhead": tt,
            "battery_soc": 1.0,
        }

    def _dispatch(self):
        idle = [a for a in self.agvs if a.idle]
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
        scored.sort(key=lambda x: x[0], reverse=True)
        cf = self._cong_factor()        # measured once per dispatch (pre-assignment traffic)
        used_a, used_t = set(), set()
        for s, aid, tid, a, t in scored:
            if aid in used_a or tid in used_t:
                continue
            used_a.add(aid); used_t.add(tid)
            a.idle = False; t.assigned = True
            dead = self.ttime(a.loc, t.src) * cf
            a.travel += dead; a.deadhead += dead; a.busy_time += dead
            self._push(self.now + dead, "pickup", (a, t))
        # purge assigned tasks from ready list
        self.ready = [t for t in self.ready if not t.assigned]

    # ---- main loop ----
    def run(self, on_step=None):
        self._gen_jobs()
        handlers = {
            "arrival": lambda p: self._on_arrival(p),
            "op_complete": lambda p: self._on_op_complete(*p),
            "pickup": lambda p: self._on_pickup(*p),
            "dropoff": lambda p: self._on_dropoff(*p),
        }
        guard = 0
        while self._evq:
            guard += 1
            if guard > self.cfg.get("max_events", 5_000_000):
                raise RuntimeError("event guard tripped")
            t, _, kind, payload = heapq.heappop(self._evq)
            self.now = t
            handlers[kind](payload)
            if on_step is not None:        # optional hook for viz/animation (no-op by default)
                on_step(self, kind)
        return self._metrics()

    def _metrics(self):
        comp = [j for j in self.jobs if j.completion >= 0]
        if not comp:
            return {"completed": 0}
        makespan = max(j.completion for j in comp)
        tard = [max(0.0, j.completion - j.due) for j in comp]
        flow = [j.completion - j.arrival for j in comp]
        tot_travel = sum(a.travel for a in self.agvs) or 1e-9
        tot_dead = sum(a.deadhead for a in self.agvs)
        tot_busy = sum(a.busy_time for a in self.agvs)
        return {
            "completed": len(comp),
            "makespan": round(makespan, 2),
            "mean_tardiness": round(sum(tard) / len(tard), 2),
            "max_tardiness": round(max(tard), 2),
            "mean_flowtime": round(sum(flow) / len(flow), 2),
            "throughput": round(len(comp) / makespan, 4),
            "agv_util": round(tot_busy / (len(self.agvs) * makespan), 3),
            "deadhead_ratio": round(tot_dead / tot_travel, 3),
        }


def simulate(config, policy, seed=0, machine_policy=None):
    return Simulator(config, policy, seed, machine_policy=machine_policy).run()
