"""Classical AGV dispatching rules as policy(features)->score (dispatcher picks max).

Each policy maps a (idle AGV, ready task) feature dict to a priority score.
These are the baselines; an LLM-AHD/GP loop will later evolve new scoring functions
over the SAME feature interface (see sim/agv_fms.py::_features).
"""
import random


def nv(f):      # nearest vehicle / shortest travel time
    return -f["travel_time"]


def edd(f):     # earliest due date -> smallest slack first (most urgent)
    return -f["slack"]


def fifo(f):    # longest-waiting task first
    return f["task_wait"]


def lqs(f):     # least downstream queue (avoid piling onto loaded machines)
    return -f["downstream_load"]


def composite(f):  # hand-crafted reference rule (the kind AHD should beat/find)
    # prioritize near + urgent + uncongested
    return -(f["travel_time"] + 0.6 * f["slack"] + 0.4 * f["downstream_load"] - 0.3 * f["task_wait"])


def make_random(seed=0):
    rng = random.Random(seed)
    return lambda f: rng.random()


POLICIES = {
    "NV": nv,
    "EDD": edd,
    "FIFO": fifo,
    "LQS": lqs,
    "COMPOSITE": composite,
    "RANDOM": make_random(0),
}


# --- machine sequencing rules (N1 joint) ---
# features: proc_time, slack, job_wait, remaining_ops, remaining_proc, downstream_load
def m_edd(f):   # earliest due date (smallest slack)
    return -f["slack"]


def m_spt(f):   # shortest processing time
    return -f["proc_time"]


def m_fifo(f):  # first in queue
    return f["job_wait"]


def m_lwr(f):   # least work remaining
    return -f["remaining_proc"]


MACHINE_POLICIES = {"M_EDD": m_edd, "M_SPT": m_spt, "M_FIFO": m_fifo, "M_LWR": m_lwr}
