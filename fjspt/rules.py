"""AGV selection rules: the slot the LLM will eventually evolve.

A rule scores candidate vehicles for one transport and the dispatcher takes the
highest score. The two literature decodings (Han 2024) are two points in this
same space, so they become exact ablations of an evolved rule.

Features available for a candidate vehicle v handling a transport (see evaluator):
  empty_travel   vehicle current location -> pickup point
  loaded_travel  pickup point -> destination machine
  arrival        time the job would arrive at its destination with this vehicle
  wait           idle time the vehicle spends waiting for the job to be ready
  agv_free       time the vehicle becomes free
  agv_cum_travel vehicle's cumulative travel so far
  machine_free   time the destination machine becomes free
  remaining_ops  operations left in this job
"""


def decoding1(f):
    """Earliest arrival; ties broken by lowest vehicle index (Han 2024, Decoding1).

    The dispatcher already scans vehicles in index order and keeps the first
    maximum, so a pure -arrival reproduces the fixed-vehicle tie-break."""
    return -f["arrival"]


def decoding2(f, eps=1e-3):
    """Earliest arrival; ties broken by least cumulative travel (Han 2024, Decoding2)."""
    return -f["arrival"] - eps * f["agv_cum_travel"]


RULES = {"D1": decoding1, "D2": decoding2}


def rule_from_expr(expr):
    """Compile an evolved scoring expression over the feature names into a rule.
    Restricted eval: no builtins, only the feature vars plus min/max/abs.
    Reuses the approach already used on the A-track (sim/rule.py)."""
    helpers = {"min": min, "max": max, "abs": abs}
    code = compile(expr, "<rule>", "eval")

    def rule(f):
        try:
            return eval(code, {"__builtins__": {}}, {**f, **helpers})
        except Exception:
            return -1e18

    rule.expr = expr
    return rule
