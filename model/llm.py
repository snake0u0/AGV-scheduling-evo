"""B-track rule proposer: evolve ONE AGV-selection rule to minimize makespan.

The A-track proposer (model/llm_backend.py) evolves (agv, machine) pairs over a different
feature set for mean tardiness. We do not touch it. Instead we reuse its validated
CLI call (ClaudeCliLLM._complete, which disables tools with `--tools ""`) and layer
a B-track prompt and single-rule genome on top.

A genome here is a single expression string over the B-track AGV features. D1/D2
are two points in this space, so they are exact ablations of any evolved rule.
"""
from .llm_backend import ClaudeCliLLM, cli_available     # reuse validated CLI machinery

BTRACK_FEATURES = ["empty_travel", "loaded_travel", "arrival", "wait",
                   "agv_free", "agv_cum_travel", "machine_free", "remaining_ops"]
_NAMES = set(BTRACK_FEATURES)

# D1/D2 as seed expressions (same rules as fjspt/rules.py, in string form).
_SEEDS = [
    "-arrival",                              # Decoding1
    "-arrival - 0.001*agv_cum_travel",       # Decoding2
    "-arrival - 0.5*empty_travel",           # arrival + prefer less deadhead
    "-loaded_travel - empty_travel",         # least total travel
]

_SYSTEM = """You design a priority rule for assigning AGVs (vehicles) to transport tasks
in a flexible job-shop. When an operation is ready to move to its machine, each free
vehicle is a candidate; your rule scores every candidate and the HIGHEST score is chosen.
The objective is to MINIMIZE the makespan (the completion time of the last operation).

Features available for a candidate vehicle (all numeric):
  empty_travel   travel time for the vehicle to reach the pickup point (deadhead)
  loaded_travel  travel time to carry the job from pickup to its destination machine
  arrival        time the job would arrive at its destination if this vehicle is used
  wait           idle time the vehicle would spend waiting for the job to be ready
  agv_free       time the vehicle becomes free
  agv_cum_travel the vehicle's cumulative travel so far (load balancing signal)
  machine_free   time the destination machine becomes free
  remaining_ops  operations left in this job

EXPRESSION GRAMMAR (strict): only the feature names above, numeric constants, the
operators + - * / ** %, parentheses, and the functions min(), max(), abs(). No other
names, no comments, one line. Guard divisions against zero, e.g. x/(machine_free+1).
Keep the rule short and interpretable. A good baseline is "-arrival" (earliest arrival)."""


def valid_btrack(expr):
    if not isinstance(expr, str) or not expr.strip():
        return False
    try:
        code = compile(expr, "<v>", "eval")
    except SyntaxError:
        return False
    return set(code.co_names) <= (_NAMES | {"min", "max", "abs"})


class ClaudeRuleProposer(ClaudeCliLLM):
    """Single-rule B-track proposer. Reuses ClaudeCliLLM._complete/usage/cost; only
    the seed set and the prompt change."""

    def seed_population(self, n):
        pop = list(_SEEDS)
        while len(pop) < n:
            pop.append(_SEEDS[len(pop) % len(_SEEDS)])
        return pop[:n]

    def vary(self, elites, k):
        # elites: [(expr, fitness)] best-first, fitness = mean makespan (LOWER better)
        exprs = [e for e, _ in elites]
        if self.calls >= self.max_calls:
            return [exprs[i % len(exprs)] for i in range(k)]
        if self.reevo:
            ranked = "\n".join(f"{i+1}. makespan={fit:.1f}   {e}"
                               for i, (e, fit) in enumerate(elites))
            prompt = (
                f"Current best AGV rules, ranked best first, with their mean makespan "
                f"(LOWER is better):\n{ranked}\n\n"
                f"First, in one short sentence, reflect on what the lower-makespan rules do well. "
                f"Then propose {k} NEW rules predicted to achieve EVEN LOWER makespan: exploit that "
                f"pattern and explore structurally different forms (ratios, products, min/max), "
                f"not just weight tweaks.\n"
                f"OUTPUT: respond with ONLY a single-line JSON object, no markdown fences. "
                f'Exactly {k} rules:\n'
                f'{{"reflection":"<one sentence>","offspring":["<expr>","<expr>"]}}')
        else:
            ranked = "\n".join(f"{i+1}. {e}" for i, (e, _) in enumerate(elites))
            prompt = (
                f"Current best AGV rules, ranked best first:\n{ranked}\n\n"
                f"Propose {k} NEW rules predicted to achieve LOWER makespan. Explore structurally "
                f"different forms (ratios, products, min/max), not just weight tweaks.\n"
                f"OUTPUT: respond with ONLY a single-line JSON object, no markdown fences. "
                f'Exactly {k} rules:\n{{"offspring":["<expr>","<expr>"]}}')
        text = self._complete(_SYSTEM + "\n\n" + prompt)
        kids = self._parse_rules(text)
        valid = [e for e in kids if valid_btrack(e)]
        while len(valid) < k:
            valid.append(exprs[len(valid) % len(exprs)])
        return valid[:k]

    def _parse_rules(self, text):
        from ahd.llm import _extract_json
        try:
            obj = _extract_json(text)
            return list(obj["offspring"])
        except Exception:
            return []


class LocalProposer:
    """No-CLI proposer for testing the loop machinery. Seeds from the same rules and
    varies expressions by appending small structural terms. Deterministic given seed."""

    def __init__(self, seed=0):
        import random
        self.rng = random.Random(seed)
        self.calls = 0
        self.fails = 0

    def seed_population(self, n):
        pop = list(_SEEDS)
        while len(pop) < n:
            pop.append(_SEEDS[len(pop) % len(_SEEDS)])
        return pop[:n]

    def vary(self, elites, k):
        exprs = [e for e, _ in elites]
        terms = ["- 0.1*empty_travel", "- 0.05*agv_cum_travel", "- 0.2*wait",
                 "- 0.1*machine_free", "+ 0.1*remaining_ops", "- 0.1*loaded_travel"]
        kids = []
        for _ in range(k):
            base = self.rng.choice(exprs)
            kid = f"({base}) {self.rng.choice(terms)}"
            kids.append(kid if valid_btrack(kid) else base)
        return kids

    def usage(self):
        return f"local-proposer (no CLI) calls={self.calls}"
