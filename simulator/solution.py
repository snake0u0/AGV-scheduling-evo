"""Fully-specified solution: what machine/vehicle does each operation, in what order.

This is the single representation shared by the two front-ends:
  - replay.py reads a published solution file into this
  - evaluator.py produces this from (OS, MS, rule)
so both feed the identical timing core.
"""
import re
from dataclasses import dataclass, field


@dataclass
class Solution:
    machine_of: dict = field(default_factory=dict)    # gid -> machine
    machine_seq: dict = field(default_factory=dict)   # machine -> [gid] in order
    vehicle_of: dict = field(default_factory=dict)    # gid -> vehicle (transported ops only)
    vehicle_seq: dict = field(default_factory=dict)   # vehicle -> [gid] in order
    meta: dict = field(default_factory=dict)


def parse_solution_file(path):
    """Published solution file:
        <name> #vehicles: V Cmax: C #iterations: I time: T
        [two more stopping-criterion lines]
        M<k>  <gid> <gid> ...      one line per machine, operations in processing order
        V<v>  T<gid> T<gid> ...    one line per vehicle, transports in execution order
    """
    with open(path) as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]

    header = lines[0]
    cmax = re.search(r"Cmax:\s*([\d.]+)", header)
    nveh = re.search(r"#vehicles:\s*(\d+)", header)

    sol = Solution(meta={
        "path": path,
        "published_cmax": float(cmax.group(1)) if cmax else None,
        "n_vehicles": int(nveh.group(1)) if nveh else None,
        "header": header,
    })

    for ln in lines[1:]:
        parts = ln.split()
        if not parts:
            continue
        tag = parts[0]
        if re.fullmatch(r"M\d+", tag):
            k = int(tag[1:])
            seq = [int(x) for x in parts[1:]]
            sol.machine_seq[k] = seq
            for g in seq:
                sol.machine_of[g] = k
        elif re.fullmatch(r"V\d+", tag):
            v = int(tag[1:])
            seq = [int(x.lstrip("T")) for x in parts[1:]]
            sol.vehicle_seq[v] = seq
            for g in seq:
                sol.vehicle_of[g] = v
    return sol
