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
import ast


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
    intermediate value, and cannot look at the other candidates - so an evolved rule
    had the same expressive power as Han 2024's fixed decodings, and the only claimed
    difference was that an LLM wrote it (2026-08-10 review).

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
