"""Priority rules: the genome the LLM evolves, and the sandbox that compiles it.

A rule scores the candidates for one decision and the dispatcher takes the highest
score. Each of the four slots in `simulator.dispatch` sees its own feature set, listed
in SLOT_FEATURES below. The two literature decodings (Han 2024) are two points in the
vehicle-side space, so they serve as exact ablations of an evolved rule.

Vehicle-side features, for a candidate vehicle v handling one transport:
  empty_travel   vehicle current location -> pickup point
  loaded_travel  pickup point -> destination machine
  arrival        time the job would arrive at its destination with this vehicle
  wait           idle time the vehicle spends waiting for the job to be ready
  agv_free       time the vehicle becomes free
  agv_cum_travel vehicle's cumulative travel so far
  machine_free   time the destination machine becomes free
  remaining_ops  operations left in this job
"""
import ast

# Feature names per slot, exactly as simulator/dispatch.py builds them (verified
# against the four feature-dict literals there). "_all" is added by dispatch's
# _with_all wrapper, not listed here since it is not a scalar feature name to compile
# against - a rule references it directly as f["_all"], a list of the other candidates'
# dicts (see rule_from_expr's function form).
SLOT_FEATURES = {
    "machine_select": ["proc_time", "machine_free", "travel_to", "queue_len",
                       "job_ready", "remaining_ops", "remaining_proc"],
    "op_sequence":    ["proc_time", "arrival", "wait", "idle", "job_wait",
                       "queue_len", "remaining_ops", "remaining_proc"],
    "vehicle_select": ["empty_travel", "loaded_travel", "agv_free", "agv_cum_travel",
                       "queue_len", "ready", "machine_free", "remaining_ops"],
    "task_sequence":  ["empty_travel", "loaded_travel", "arrival", "wait", "agv_free",
                       "agv_cum_travel", "machine_free", "remaining_ops", "remaining_proc"],
}


def decoding1(f):
    """Earliest arrival; ties broken by lowest vehicle index (Han 2024, Decoding1).

    The dispatcher already scans vehicles in index order and keeps the first
    maximum, so a pure -arrival reproduces the fixed-vehicle tie-break."""
    return -f["arrival"]


def decoding2(f, eps=1e-3):
    """Earliest arrival; ties broken by least cumulative travel (Han 2024, Decoding2)."""
    return -f["arrival"] - eps * f["agv_cum_travel"]


RULES = {"D1": decoding1, "D2": decoding2}


FAIL = -1e18            # score for a rule that raised; the dispatcher never picks it
NEVER = float("-inf")   # "not selectable now" - lets a resource idle (see dispatch._argmax)

_HELPERS = {"min": min, "max": max, "abs": abs, "sum": sum, "len": len,
            "sorted": sorted, "NEVER": NEVER}


def rule_from_expr(expr):
    """Compile an evolved rule. Two accepted forms:

      expression   "-arrival - 0.5*empty_travel"
      function     "def rule(f):\\n    ...\\n    return score"

    The expression form is the original one-liner and still works unchanged. The
    function form exists because an expression cannot branch, cannot name an
    intermediate value, and cannot look at the other candidates - which would leave an
    evolved rule with the same expressive power as Han 2024's fixed decodings, the only
    claimed difference being that an LLM wrote it.

    Inside a function the feature dict is the argument, so `f["_all"]` reaches every
    candidate's features and relative judgements ("is this vehicle the busiest in the
    fleet?") become expressible. Returning NEVER declines the candidate outright.

    Restricted namespace: no builtins, only the feature names plus min/max/abs/sum/
    len/sorted and NEVER. Any exception at call time scores FAIL rather than
    propagating, so one bad rule cannot stop a campaign.
    """
    src = expr.strip()
    is_fn = src.startswith("def ")

    if is_fn:
        # A rule runs millions of times per campaign, so a per-call timeout (signal,
        # tracing) costs more than the rule itself. Reject the hang at compile time
        # instead: `while` is the only unbounded construct reachable here. `for` is
        # safe because the only iterables in scope are our own feature values, and
        # recursion is already impossible - the function's name lives in the exec
        # namespace, not in its globals, so calling itself raises NameError -> FAIL.
        # Residual risk: a huge literal exponent (2**10**9) can still stall.
        if any(isinstance(n, ast.While) for n in ast.walk(ast.parse(src))):
            raise ValueError("while loops are not allowed in a rule")
        ns = {}
        exec(compile(src, "<rule>", "exec"), {"__builtins__": {}, **_HELPERS}, ns)
        fns = [v for v in ns.values() if callable(v)]
        if len(fns) != 1:
            raise ValueError(f"expected exactly one function, got {len(fns)}")
        inner = fns[0]

        def rule(f):
            try:
                return inner(f)
            except Exception:
                return FAIL
    else:
        code = compile(src, "<rule>", "eval")

        def rule(f):
            try:
                return eval(code, {"__builtins__": {}}, {**f, **_HELPERS})
            except Exception:
                return FAIL

    rule.expr = expr
    return rule
