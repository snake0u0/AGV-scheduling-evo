"""Turn an evolved rule (a string expression over feature names) into a policy.

This is the plug for AHD: an LLM/GP produces a scoring expression over the feature
interface (sim/agv_fms.py::_features); we compile it into policy(features)->score.
Restricted eval (no builtins; only the feature vars + a few math helpers).
"""
_HELPERS = {"min": min, "max": max, "abs": abs}


def policy_from_expr(expr: str):
    code = compile(expr, "<rule>", "eval")

    def pol(f):
        try:
            return eval(code, {"__builtins__": {}}, {**f, **_HELPERS})
        except Exception:
            return -1e9

    pol.expr = expr
    return pol
