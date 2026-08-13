"""Single-rule proposer (retired): evolve ONE AGV-selection rule under a GA.

Superseded by model/llm.py's ClaudeBundleProposer, which evolves all four dispatch
slots together in the constructive regime. Kept as a record of the earlier method;
it depends on model.experiment.evolve, which was retired with the GA.
"""
from .llm_backend import ClaudeCliLLM, cli_available     # reuse validated CLI machinery
from .rules import FAIL, SLOT_FEATURES, rule_from_expr

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
    the seed set and the prompt change.

    `last_call` holds what the most recent vary() actually sent and received, so a run
    can be reconstructed from its result file alone. Without it the prompt, the raw
    reply, the reflection the model was asked for, and every rejected candidate were
    all discarded (2026-08-10 review). The system prompt is a module constant
    (`_SYSTEM`) and is not repeated per call - record it once per run.
    """

    last_call = None

    def seed_population(self, n):
        pop = list(_SEEDS)
        while len(pop) < n:
            pop.append(_SEEDS[len(pop) % len(_SEEDS)])
        return pop[:n]

    def vary(self, elites, k):
        # elites: [(expr, fitness)] best-first, fitness = mean makespan (LOWER better)
        exprs = [e for e, _ in elites]
        parents = [{"expr": e, "fitness": f} for e, f in elites]
        if self.calls >= self.max_calls:
            out = [exprs[i % len(exprs)] for i in range(k)]
            self.last_call = {"skipped": "max_calls reached", "parents": parents,
                              "returned": out}
            return out
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
        kids, reflection = self._parse_rules(text)
        valid = [e for e in kids if valid_btrack(e)]
        rejected = [e for e in kids if not valid_btrack(e)]
        n_valid = len(valid)
        while len(valid) < k:
            valid.append(exprs[len(valid) % len(exprs)])
        out = valid[:k]
        self.last_call = {
            "prompt_user": prompt,          # _SYSTEM is constant; record it once per run
            "response": text,
            "reflection": reflection,
            "parents": parents,
            "proposed": kids,
            "rejected": rejected,           # dropped silently before 2026-08-10
            "n_padded": max(0, k - n_valid),  # elite copies used to fill the shortfall
            "returned": out,
        }
        return out

    def _parse_rules(self, text):
        """(offspring, reflection). The reflection is requested by the prompt and was
        previously parsed out and thrown away."""
        from .llm_backend import _extract_json
        try:
            obj = _extract_json(text)
            return list(obj["offspring"]), obj.get("reflection")
        except Exception:
            return [], None


class LocalProposer:
    """No-CLI proposer for testing the loop machinery. Seeds from the same rules and
    varies expressions by appending small structural terms. Deterministic given seed."""

    last_call = None

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
        kids, of = [], []
        for _ in range(k):
            base = self.rng.choice(exprs)
            kid = f"({base}) {self.rng.choice(terms)}"
            kids.append(kid if valid_btrack(kid) else base)
            of.append(base)
        # This proposer picks one parent per child, so it can record true per-child
        # lineage. The LLM proposer cannot: it is shown every elite and returns k
        # children without saying which came from which.
        self.last_call = {
            "prompt_user": None, "response": None, "reflection": None,
            "parents": [{"expr": e, "fitness": f} for e, f in elites],
            "proposed": kids, "rejected": [], "n_padded": 0, "returned": kids,
            "child_parent": of,
        }
        return kids

    def usage(self):
        return f"local-proposer (no CLI) calls={self.calls}"
