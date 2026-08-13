"""Instance model and parsers for the three FJSP-with-transport benchmark formats.

Data is read exactly as written in the source files: no rescaling, no trimming,
no derived transformation of processing times or travel times.

Indexing convention (chosen to avoid off-by-one bugs):
  - machines are 1..m, exactly as numbered in the source files
  - index 0 is reserved for the L/U depot
  - so `travel[a][b]` is directly indexable with machine numbers, row=from, col=to
  - operations get a global id 1..N, assigned sequentially job by job
    (verified against the published solution files: 0 eligibility violations)
"""
import os
from dataclasses import dataclass, field

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "instances", "fjspt-lucasberter")


@dataclass
class Instance:
    name: str
    n_jobs: int
    n_machines: int
    jobs: list                      # jobs[j][o] = [(machine, proc_time), ...]
    travel: list = field(default_factory=list)   # (m+1)x(m+1), 0 = L/U, row=from col=to
    n_vehicles: int = 0             # NOT from the instance file - injected by caller
    source: dict = field(default_factory=dict)

    @property
    def n_ops(self):
        return sum(len(ops) for ops in self.jobs)

    def gid(self, j, o):
        """global operation id (1-based) of operation o of job j (both 0-based)."""
        return sum(len(self.jobs[x]) for x in range(j)) + o + 1

    def job_op(self, gid):
        """inverse of gid(): returns (job, op) both 0-based."""
        for j, ops in enumerate(self.jobs):
            if gid <= len(ops):
                return j, gid - 1
            gid -= len(ops)
        raise IndexError(f"operation id out of range")

    def proc_time(self, gid, machine):
        j, o = self.job_op(gid)
        for mk, pt in self.jobs[j][o]:
            if mk == machine:
                return pt
        raise KeyError(f"op {gid} cannot run on machine {machine}")

    def eligible(self, gid):
        j, o = self.job_op(gid)
        return [mk for mk, _ in self.jobs[j][o]]


def _tokens(path):
    with open(path) as f:
        return f.read().split()


def parse_format_a(path, name=None):
    """Bilge-Ulusoy lineage (DeroussiNorre/): `nJob nMachine ?`,
    then per job `nOps`, then per op `k m1..mk sharedTime`.
    The alternative machines of one operation share a single processing time.
    The third header field is read but never used (ambiguous across the corpus).

    Parsed by walking a cursor `i` through the flat token list and nesting the
    values back into job -> operation -> (machine, time) as they are consumed."""
    t = _tokens(path)
    i = 0
    n = int(t[i]); i += 1                    # number of jobs
    m = int(t[i]); i += 1                    # number of machines
    i += 1                                   # third field: deliberately unused
    jobs = []
    for _ in range(n):
        n_ops = int(t[i]); i += 1            # operations in this job
        ops = []
        for _ in range(n_ops):
            k = int(t[i]); i += 1            # how many machines can run this op
            machines = [int(t[i + q]) for q in range(k)]; i += k
            pt = int(t[i]); i += 1           # one processing time, shared by all k
            ops.append([(mk, pt) for mk in machines])
        jobs.append(ops)
    return Instance(name or os.path.basename(path).replace(".txt", ""), n, m, jobs,
                    source={"path": path, "format": "A"})


def parse_format_b(path, name=None):
    """Standard FJS (Dauzere_Data/, Homayouni_Brandimarte/): `nJob nMachine ?`,
    then per job `nOps`, then per op `k (machine,time) * k`.
    The third header field is read but never used."""
    t = _tokens(path)
    i = 0
    n = int(t[i]); i += 1
    m = int(t[i]); i += 1
    i += 1                                   # third field: deliberately unused
    jobs = []
    for _ in range(n):
        n_ops = int(t[i]); i += 1
        ops = []
        for _ in range(n_ops):
            k = int(t[i]); i += 1
            alts = []
            for _ in range(k):
                mk = int(t[i]); i += 1
                pt = int(t[i]); i += 1
                alts.append((mk, pt))
            ops.append(alts)
        jobs.append(ops)
    return Instance(name or os.path.basename(path).replace(".txt", ""), n, m, jobs,
                    source={"path": path, "format": "B"})


def parse_format_c(path, name=None):
    """Fattahi (fattahi/): `nOps nPrecedencePairs nMachines`, then the precedence
    pairs, then one line per operation `k (machine,time) * k`.
    Job boundaries are NOT given explicitly: they are recovered by following the
    precedence chains. Machines are 0-indexed in this format and are shifted to
    our 1..m convention (a re-indexing, not a change of any value)."""
    t = _tokens(path)
    i = 0
    n_ops = int(t[i]); i += 1
    n_prec = int(t[i]); i += 1
    m = int(t[i]); i += 1

    succ, has_pred = {}, set()
    for _ in range(n_prec):
        a = int(t[i]); i += 1
        b = int(t[i]); i += 1
        succ[a] = b
        has_pred.add(b)

    op_alts = []
    for _ in range(n_ops):
        k = int(t[i]); i += 1
        alts = []
        for _ in range(k):
            mk = int(t[i]); i += 1
            pt = int(t[i]); i += 1
            alts.append((mk + 1, pt))        # 0-indexed in file -> our 1..m
        op_alts.append(alts)

    jobs = []
    for head in sorted(set(range(n_ops)) - has_pred):
        chain, cur = [], head
        while cur is not None:
            chain.append(op_alts[cur])
            cur = succ.get(cur)
        jobs.append(chain)
    if sum(len(c) for c in jobs) != n_ops:
        raise ValueError(f"{path}: precedence chains cover "
                         f"{sum(len(c) for c in jobs)} of {n_ops} operations")
    return Instance(name or os.path.basename(path).replace(".txt", ""),
                    len(jobs), m, jobs, source={"path": path, "format": "C"})


def load_travel(path):
    """Square travel-time matrix, (m+1)x(m+1), index 0 = L/U. Asymmetric."""
    with open(path) as f:
        mat = [[int(x) for x in ln.split()] for ln in f if ln.strip()]
    if any(len(r) != len(mat) for r in mat):
        raise ValueError(f"{path}: travel matrix is not square")
    return mat


# --- dataset registry -------------------------------------------------------
# Pairing an instance with its travel matrix is a provenance decision, not something
# a parser should infer, so the pairing is written out explicitly per dataset.


def load_dauzere(stem, n_vehicles):
    """Dauzere-Peres & Paulli instance + the Berterottiere layout of matching size."""
    inst = parse_format_b(f"{BASE}/Dauzere_Data/Text/{stem}.txt", name=stem)
    layout = f"{BASE}/BerterottiereTravelTimes/layout{inst.n_machines}.txt"
    inst.travel = load_travel(layout)
    if len(inst.travel) != inst.n_machines + 1:
        raise ValueError(f"{stem}: layout size {len(inst.travel)} != m+1 "
                         f"({inst.n_machines + 1})")
    inst.n_vehicles = n_vehicles
    inst.source["travel"] = layout
    inst.source["solution"] = (f"{BASE}/Berterottiere/dpp{n_vehicles}veh/"
                               f"dpp{stem}_{n_vehicles}veh.txt")
    return inst


def load_deroussi(stem, n_vehicles=2):
    """Deroussi & Norre (2010) instance + its layout.

    These have **8 machines**, not 4: the flexibility-2 structure comes from machines
    being paired (M1;M2), (M3;M4), (M5;M6), (M7;M8). Earlier sessions assumed 4 machines,
    which is why every reconstruction of the travel matrix failed.
    Matrix provenance: DeroussiNorreTravelTimes/SOURCE.md. Replay gate: test_replay_deroussi.
    """
    inst = parse_format_a(f"{BASE}/DeroussiNorre/{stem}.txt", name=stem)
    layout = f"{BASE}/DeroussiNorreTravelTimes/layout{inst.n_machines}.txt"
    inst.travel = load_travel(layout)
    if len(inst.travel) != inst.n_machines + 1:
        raise ValueError(f"{stem}: layout size {len(inst.travel)} != m+1 "
                         f"({inst.n_machines + 1})")
    inst.n_vehicles = n_vehicles
    inst.source["travel"] = layout
    inst.source["solution"] = f"{BASE}/Deroussi/{stem}.txt"
    return inst


DEROUSSI_STEMS = [f"fjsp{i}" for i in range(1, 11)]

DAUZERE_STEMS = [f"{i:02d}a" for i in range(1, 19)]
DAUZERE_VEHICLES = [2, 4, 6]

# Known-bad data, must never enter an experiment (see STATUS.md):
#   Homayouni_Brandimarte/setb4xxx.txt is byte-identical to seti5xxx.txt upstream.
BLOCKED = {"setb4xxx"}
