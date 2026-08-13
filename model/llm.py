"""Four-slot rule proposer: the LLM side of the evolutionary loop.

A genome is a *bundle* - one scoring rule per subproblem, covering all four
`simulator.dispatch` slots at once - evaluated as a single individual under one shared
fitness. The proposer seeds a population, then varies the elites by asking the model
for improved bundles (ReEvo style: it sees each parent's fitness and is asked to
reflect before proposing).

`ClaudeBundleProposer` calls the logged-in `claude` CLI; `LocalBundleProposer` makes
the same interface work with no model, for testing the loop machinery.

`last_call` holds what the most recent vary() sent and received - prompt, raw reply,
reflection, parents, and every rejected candidate - so a run can be reconstructed
from its result file alone. The system prompt is a module constant and is not repeated
per call; record it once per run.
"""
from .llm_backend import ClaudeCliLLM, cli_available     # reuse validated CLI machinery
from .rules import FAIL, SLOT_FEATURES, rule_from_expr

# Three structurally different starting points: pure load balancing, textbook greedy,
# and a queue+arrival hybrid. "0" is a valid one-line expression - it always ties, so
# the dispatcher's first-candidate-wins order decides (see dispatch._argmax).
_SEEDS_BUNDLE = [
    {"machine_select": "-queue_len", "op_sequence": "0",
     "vehicle_select": "-queue_len", "task_sequence": "0"},                    # BALANCED
    {"machine_select": "-proc_time - machine_free", "op_sequence": "-arrival",
     "vehicle_select": "-(agv_free + empty_travel)", "task_sequence": "-arrival"},  # HAND
    {"machine_select": "-queue_len", "op_sequence": "-arrival",
     "vehicle_select": "-queue_len", "task_sequence": "-arrival"},             # MIX
]

_SYSTEM_BUNDLE = """You design FOUR priority rules that together build one complete schedule for a
flexible job-shop with AGV transport, in a single pass with NO search: each rule scores its
candidates once and the highest score is taken immediately - there is no chance to undo a
decision, and no metaheuristic wraps this. The objective is to MINIMIZE the makespan (the
completion time of the last operation).

The four rules and when each is called:
  machine_select   an operation is ready -> scores each ELIGIBLE MACHINE, highest is assigned
  op_sequence      a machine falls idle  -> scores each operation WAITING FOR THAT MACHINE
  vehicle_select   a transport is needed -> scores each AGV, highest is assigned to carry it
  task_sequence    an AGV falls idle     -> scores each transport WAITING FOR THAT AGV

The four rules do NOT share a feature set - only these names are valid for each:
  machine_select:  proc_time, machine_free, travel_to, queue_len, job_ready, remaining_ops, remaining_proc
  op_sequence:     proc_time, arrival, wait, idle, job_wait, queue_len, remaining_ops, remaining_proc
  vehicle_select:  empty_travel, loaded_travel, agv_free, agv_cum_travel, queue_len, ready, machine_free, remaining_ops
  task_sequence:   empty_travel, loaded_travel, arrival, wait, agv_free, agv_cum_travel, machine_free, remaining_ops, remaining_proc

Two forms are allowed for each rule:
  expression   "-queue_len"                            (one line, no def)
  function     "def rule(f):\\n    return -f['queue_len']"

Inside a function, f["_all"] is the list of every OTHER candidate's feature dict at this same
decision, so a rule can compare a candidate against the field (e.g. "is this the busiest AGV
right now?"). Returning float("-inf") declines a candidate outright.

EXPRESSION GRAMMAR (strict): only that rule's own feature names, numeric constants, the
operators + - * / ** %, parentheses, and the functions min(), max(), abs(), sum(), len(),
sorted(). No imports, no while loops, no comments. Keep each rule short and interpretable."""


def bundle_valid(slot, expr):
    """True iff `expr` compiles for `slot` and runs without error on a representative
    feature dict for that slot.

    Validated by compiling and calling it, not by scanning for feature names: the
    function form reads features as f["name"], which a static name scan cannot see."""
    if not isinstance(expr, str) or not expr.strip():
        return False
    try:
        rule = rule_from_expr(expr)
    except Exception:
        return False
    probe = {name: 1.0 for name in SLOT_FEATURES[slot]}
    probe["_all"] = [probe]
    try:
        val = rule(probe)
    except Exception:
        return False
    return val != FAIL and val == val          # not the error sentinel, not NaN


class ClaudeBundleProposer(ClaudeCliLLM):
    """Four-slot proposer: seeds and varies {slot: expr} bundles, one fitness each."""

    last_call = None

    def seed_population(self, n):
        pop = [dict(b) for b in _SEEDS_BUNDLE]
        while len(pop) < n:
            pop.append(dict(_SEEDS_BUNDLE[len(pop) % len(_SEEDS_BUNDLE)]))
        return pop[:n]

    def vary(self, elites, k):
        # elites: [(bundle, fitness)] best-first, fitness = mean makespan (LOWER better)
        bundles = [b for b, _ in elites]
        parents = [{"bundle": b, "fitness": f} for b, f in elites]
        if self.calls >= self.max_calls:
            out = [bundles[i % len(bundles)] for i in range(k)]
            self.last_call = {"skipped": "max_calls reached", "parents": parents,
                              "returned": out}
            return out

        ranked = "\n".join(
            f"{i+1}. makespan={fit:.1f}\n"
            f"   machine_select: {b['machine_select']}\n"
            f"   op_sequence:    {b['op_sequence']}\n"
            f"   vehicle_select: {b['vehicle_select']}\n"
            f"   task_sequence:  {b['task_sequence']}"
            for i, (b, fit) in enumerate(elites))
        prompt = (
            f"Current best rule bundles, ranked best first, with their mean makespan "
            f"(LOWER is better):\n{ranked}\n\n"
            f"First, in one short sentence, reflect on what the lower-makespan bundles do "
            f"well. Then propose {k} NEW bundles predicted to achieve EVEN LOWER makespan. "
            f"You may change any subset of the four rules per bundle - changing all four is "
            f"not required.\n"
            f"OUTPUT: respond with ONLY a single-line JSON object, no markdown fences. "
            f'Exactly {k} bundles:\n'
            f'{{"reflection":"<one sentence>","offspring":[{{"machine_select":"<expr>",'
            f'"op_sequence":"<expr>","vehicle_select":"<expr>","task_sequence":"<expr>"}}, '
            f'...]}}')
        text = self._complete(_SYSTEM_BUNDLE + "\n\n" + prompt)
        kids, reflection = self._parse_bundles(text)
        valid, rejected = [], []
        for b in kids:
            if (isinstance(b, dict) and set(b) == set(SLOT_FEATURES)
                    and all(bundle_valid(slot, b[slot]) for slot in SLOT_FEATURES)):
                valid.append(b)
            else:
                rejected.append(b)
        n_valid = len(valid)
        while len(valid) < k:
            valid.append(bundles[len(valid) % len(bundles)])
        out = valid[:k]
        self.last_call = {
            "prompt_user": prompt,
            "response": text,
            "reflection": reflection,
            "parents": parents,
            "proposed": kids,
            "rejected": rejected,
            "n_padded": max(0, k - n_valid),
            "returned": out,
        }
        return out

    def _parse_bundles(self, text):
        from .llm_backend import _extract_json
        try:
            obj = _extract_json(text)
            return list(obj["offspring"]), obj.get("reflection")
        except Exception:
            return [], None


class LocalBundleProposer:
    """No-CLI bundle proposer for testing the loop machinery, deterministic given seed."""

    last_call = None

    def __init__(self, seed=0):
        import random
        self.rng = random.Random(seed)
        self.calls = 0
        self.fails = 0

    def seed_population(self, n):
        pop = [dict(b) for b in _SEEDS_BUNDLE]
        while len(pop) < n:
            pop.append(dict(_SEEDS_BUNDLE[len(pop) % len(_SEEDS_BUNDLE)]))
        return pop[:n]

    def vary(self, elites, k):
        bundles = [b for b, _ in elites]
        terms = {
            "machine_select": ["- 0.1*travel_to", "- 0.2*job_ready", "+ 0.1*remaining_ops"],
            "op_sequence":    ["- 0.1*wait", "- 0.2*idle", "+ 0.1*remaining_proc"],
            "vehicle_select": ["- 0.1*empty_travel", "- 0.05*agv_cum_travel", "- 0.2*ready"],
            "task_sequence":  ["- 0.1*empty_travel", "- 0.05*agv_cum_travel", "- 0.2*wait"],
        }
        kids = []
        for _ in range(k):
            base = self.rng.choice(bundles)
            kid = dict(base)
            slot = self.rng.choice(list(SLOT_FEATURES))
            cand = f"({kid[slot]}) {self.rng.choice(terms[slot])}"
            kid[slot] = cand if bundle_valid(slot, cand) else kid[slot]
            kids.append(kid)
        self.last_call = {
            "prompt_user": None, "response": None, "reflection": None,
            "parents": [{"bundle": b, "fitness": f} for b, f in elites],
            "proposed": kids, "rejected": [], "n_padded": 0, "returned": kids,
        }
        return kids

    def usage(self):
        return f"local-bundle-proposer (no CLI) calls={self.calls}"
