"""A-track rule proposer (retired): evolve (agv, machine) rule pairs for mean tardiness.

Built for the dynamic-FJSP track, over that track's feature set. The live loop evolves
four-slot bundles for makespan instead (model/llm.py). The CLI machinery this shared
with the live code now lives in model/llm_backend.py; this file keeps the A-track
genome, seeds, prompt and the MockLLM stand-in.
"""
from __future__ import annotations
import random

FEATURES_AGV = ["travel_time", "task_wait", "slack", "downstream_load",
                "congestion", "deadhead", "battery_soc"]
FEATURES_M = ["proc_time", "slack", "job_wait", "remaining_ops",
              "remaining_proc", "downstream_load"]

# classical seeds expressed as genomes (agv_genome, machine_genome)
_CLASSICAL = [
    ({"travel_time": -1.0}, {"slack": -1.0}),                              # NV + EDD
    ({"travel_time": -1.0}, {"proc_time": -1.0}),                          # NV + SPT
    ({"travel_time": -1.0, "downstream_load": -0.3}, {"slack": -1.0}),     # travel+cong + EDD
    ({"travel_time": -1.0, "slack": -0.2}, {"remaining_proc": -1.0}),      # + LWR
]


def render(genome) -> str:
    """Genome -> scoring expression string compiled by sim.rule.policy_from_expr.

    MockLLM genomes are {feature: weight} dicts; HaikuLLM genomes are already
    expression strings (passed through unchanged).
    """
    if isinstance(genome, str):
        return genome
    if not genome:
        return "0"
    return " + ".join(f"({w:.3f})*{f}" for f, w in genome.items())


class MockLLM:
    """Stand-in proposer. Deterministic given a seed (for reproducible loop runs)."""

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    # ---- API expected by ahd/loop.py (a real LLM implements the same two) ----
    def seed_population(self, n: int):
        pop = [(_clone(a), _clone(m)) for a, m in _CLASSICAL]
        while len(pop) < n:
            pop.append((self._rand_genome(FEATURES_AGV), self._rand_genome(FEATURES_M)))
        return pop[:n]

    def vary(self, elites, k: int):
        elites = [p for p, _ in elites]            # drop fitness (MockLLM edits structurally)
        kids = []
        for _ in range(k):
            if len(elites) >= 2 and self.rng.random() < 0.3:
                pa, pb = self.rng.sample(elites, 2)               # crossover
                kid = (self._cross(pa[0], pb[0]), self._cross(pa[1], pb[1]))
            else:
                pa = self.rng.choice(elites)                      # mutation
                kid = (self._mutate(pa[0], FEATURES_AGV), self._mutate(pa[1], FEATURES_M))
            kids.append(kid)
        return kids

    # ---- internal edits ----
    def _rand_genome(self, feats, k: int = 2):
        chosen = self.rng.sample(feats, min(k, len(feats)))
        return {f: round(self.rng.uniform(-1, 1), 3) for f in chosen}

    def _mutate(self, g, feats):
        if not isinstance(g, dict):        # frozen side (string expr) -> pass through unchanged
            return g
        g = _clone(g)
        r = self.rng.random()
        if g and r < 0.5:                                          # tweak a weight
            f = self.rng.choice(list(g))
            g[f] = round(g[f] + self.rng.gauss(0, 0.3), 3)
        elif r < 0.8:                                              # add a feature
            g.setdefault(self.rng.choice(feats), round(self.rng.uniform(-1, 1), 3))
        elif len(g) > 1:                                           # drop a feature
            del g[self.rng.choice(list(g))]
        return g

    def _cross(self, ga, gb):
        if not isinstance(ga, dict) or not isinstance(gb, dict):   # frozen side -> keep as-is
            return ga
        feats = set(ga) | set(gb)
        return {f: (ga.get(f, 0.0) + gb.get(f, 0.0)) / 2 for f in feats
                if self.rng.random() < 0.7} or _clone(ga)


def _clone(g):
    return {k: round(v, 3) for k, v in g.items()}


# ============ real LLM proposer (logged-in `claude` CLI — no API key) ============
import json, re, subprocess, shutil, sys

DEFAULT_MODEL = "sonnet"   # passed to `claude --model`

# Expression-string seeds (same classical rules as _CLASSICAL, but as strings,
# since the LLM proposer's genomes are expression strings rather than weight dicts).
_CLASSICAL_EXPR = [
    ("-travel_time", "-slack"),                            # NV + EDD
    ("-travel_time", "-proc_time"),                        # NV + SPT
    ("-travel_time - 0.3*downstream_load", "-slack"),      # NV+cong + EDD
    ("-travel_time - 0.2*slack", "-remaining_proc"),       # + LWR
]

_SYSTEM = """You design priority rules for a dynamic flexible job-shop with AGV transport.
Two rules are evolved jointly to MINIMIZE mean job tardiness:

1) AGV dispatching rule: scores each (idle AGV, ready transport task) pair; the highest
   score is dispatched. Features (all numeric):
   - travel_time: time for the AGV to reach the task pickup (smaller = closer)
   - task_wait:   how long the task has waited (larger = more urgent)
   - slack:       job due - now - remaining processing (smaller/negative = more urgent)
   - downstream_load: queue length at the destination machine
   - congestion:  number of ready unassigned tasks in the system
   - deadhead:    empty travel distance to the pickup
   - battery_soc: AGV charge in [0,1] (currently constant 1.0)

2) Machine sequencing rule: scores each job in a machine queue; the highest is run next.
   Features: proc_time, slack, job_wait, remaining_ops, remaining_proc, downstream_load.

EXPRESSION GRAMMAR (strict): only the feature names listed for that rule, numeric
constants, operators + - * / ** %, parentheses, and the functions min(), max(), abs().
No other names, no comments, one line each. Guard divisions against zero, e.g.
travel_time / (downstream_load + 1). Keep rules short and interpretable."""


def _extract_json(text: str):
    """Pull the first {...} object out of an LLM reply (tolerates code fences/prose)."""
    text = re.sub(r"```(?:json)?", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(m.group(0)) if m else None


def _valid(expr, allowed):
    """True iff expr compiles and references only allowed feature names + min/max/abs."""
    if not isinstance(expr, str) or not expr.strip():
        return False
    try:
        code = compile(expr, "<v>", "eval")
    except SyntaxError:
        return False
    return set(code.co_names) <= (allowed | {"min", "max", "abs"})


_AGV_NAMES = set(FEATURES_AGV)
_M_NAMES = set(FEATURES_M)


class _ExprProposer:
    """Shared logic for LLM proposers whose genomes are free-form expression strings.

    Subclasses implement _complete(prompt)->str (the raw model reply). seed_population
    seeds from classical rules (always valid, contains the NV+EDD baseline); vary asks
    the model for k improved (agv, machine) pairs, validates them, and pads any shortfall
    by reusing elites so the loop never stalls on a bad/empty reply.
    """

    def __init__(self, max_calls: int = 50, reevo: bool = True):
        self.max_calls = max_calls
        self.reevo = reevo          # True: show fitness + reflection; False: rank-only (ablation)
        self.calls = 0

    def seed_population(self, n: int):
        pop = list(_CLASSICAL_EXPR)
        while len(pop) < n:                         # pad without spending a model call
            pop.append(_CLASSICAL_EXPR[len(pop) % len(_CLASSICAL_EXPR)])
        return pop[:n]

    def vary(self, elites, k: int):
        # elites: [(pair, fitness)] best-first. ReEvo: show fitness + ask to reflect, then propose.
        pairs = [p for p, _ in elites]
        if self.calls >= self.max_calls:            # budget cap reached
            return [pairs[i % len(pairs)] for i in range(k)]
        if self.reevo:                              # ReEvo: fitness values + reflection
            ranked = "\n".join(f"{i+1}. mean_tardiness={fit:.1f}  AGV: {a}   | MACHINE: {m}"
                               for i, ((a, m), fit) in enumerate(elites))
            prompt = (
                f"Current best rule pairs, ranked best first, with their mean tardiness "
                f"(LOWER is better — this is the objective to minimize):\n{ranked}\n\n"
                f"First, in one short sentence, reflect on what the lower-tardiness rules do well. "
                f"Then propose {k} NEW rule pairs predicted to achieve EVEN LOWER mean tardiness: "
                f"exploit the pattern you noted and explore structurally different forms "
                f"(ratios, products, min/max, nonlinear), not just weight tweaks.\n"
                f"OUTPUT FORMAT: respond with ONLY a single-line JSON object and nothing else "
                f"— no markdown fences. Exactly {k} offspring:\n"
                f'{{"reflection":"<one sentence>","offspring":[{{"agv":"<expr>","machine":"<expr>"}}]}}')
        else:                                       # ablation: rank-only (no fitness/reflection)
            ranked = "\n".join(f"{i+1}. AGV: {a}   | MACHINE: {m}"
                               for i, ((a, m), _) in enumerate(elites))
            prompt = (
                f"Current best rule pairs, ranked best first:\n{ranked}\n\n"
                f"Propose {k} NEW rule pairs predicted to achieve LOWER mean tardiness. "
                f"Explore structurally different forms (ratios, products, min/max, nonlinear), "
                f"not just weight tweaks.\n"
                f"OUTPUT FORMAT: respond with ONLY a single-line JSON object and nothing else "
                f"— no markdown fences. Exactly {k} items:\n"
                f'{{"offspring":[{{"agv":"<expr>","machine":"<expr>"}}]}}')
        text = self._complete(_SYSTEM + "\n\n" + prompt)
        kids = self._parse(text)
        valid = [(a, m) for a, m in kids if _valid(a, _AGV_NAMES) and _valid(m, _M_NAMES)]
        while len(valid) < k:
            valid.append(pairs[len(valid) % len(pairs)])
        return valid[:k]

    def _parse(self, text: str):
        try:
            obj = _extract_json(text)
            return [(o["agv"], o["machine"]) for o in obj["offspring"]]
        except Exception:
            return []

    def _complete(self, prompt: str) -> str:
        raise NotImplementedError


class ClaudeCliLLM(_ExprProposer):
    """Proposer backed by the logged-in `claude` CLI in headless mode — uses the account
    already authenticated for Claude Code, so no API key is needed. Each vary call shells
    out to `claude -p --output-format json` and reads the model text from `.result`.
    Cost/tokens are taken from the CLI's own usage envelope.
    """

    def __init__(self, model: str = DEFAULT_MODEL, max_calls: int = 50, timeout: int = 180,
                 reevo: bool = True):
        super().__init__(max_calls, reevo)
        self.model = model
        self.timeout = timeout
        self.cost = 0.0
        self.in_tok = 0
        self.out_tok = 0
        self.fails = 0

    def _complete(self, prompt: str) -> str:
        self.calls += 1
        proc = None
        try:
            proc = subprocess.run(
                ["claude", "-p", "--model", self.model, "--output-format", "json",
                 "--tools", "",                       # disable ALL tools -> pure text generation
                 "--dangerously-skip-permissions"],   # (nothing to permit once tools are off)
                input=prompt, capture_output=True, text=True, timeout=self.timeout)
            env = json.loads(proc.stdout)
        except Exception as e:                      # timeout / non-JSON / crash
            rc = proc.returncode if proc is not None else "n/a"
            err = (proc.stderr[:160] if proc is not None and proc.stderr else str(e)[:160])
            sys.stderr.write(f"[ClaudeCliLLM] call {self.calls} FAILED (rc={rc}): {err}\n")
            self.fails += 1
            return ""                               # vary pads from elites
        if env.get("is_error") or "result" not in env:   # error envelope (e.g. rate limit)
            sys.stderr.write(f"[ClaudeCliLLM] call {self.calls} ERROR envelope: "
                             f"{str(env.get('subtype') or env.get('result'))[:160]}\n")
            self.fails += 1
            return ""
        self.cost += env.get("total_cost_usd") or 0.0
        u = env.get("usage") or {}
        self.in_tok += u.get("input_tokens", 0) or 0
        self.out_tok += u.get("output_tokens", 0) or 0
        return env.get("result", "") or ""

    def usage(self) -> str:
        warn = f"  ⚠️ {self.fails}/{self.calls} CALLS FAILED (run invalid)" if self.fails else ""
        return (f"claude-cli ({self.model}) calls={self.calls}  fails={self.fails}  "
                f"in_tok={self.in_tok}  out_tok={self.out_tok}  reported_cost~${self.cost:.4f}{warn}")


def cli_available() -> bool:
    """True if the `claude` CLI is on PATH (so ClaudeCliLLM can be used)."""
    return shutil.which("claude") is not None


class FrozenSide:
    """Wrap a proposer to FIX one rule, evolving only the other (for ablations B5/B6).

    B5 machine-only = FrozenSide(proposer, fix_agv="-travel_time")   # AGV fixed to NV
    B6 AGV-only     = FrozenSide(proposer, fix_machine="-slack")     # machine fixed to EDD
    The fixed side (an expression string) overwrites every candidate after seed/vary, so the
    inner proposer's edits to that side are discarded.
    """

    def __init__(self, inner, fix_agv=None, fix_machine=None):
        self.inner = inner
        self.fix_agv = fix_agv
        self.fix_machine = fix_machine

    def _fix(self, pairs):
        return [(self.fix_agv if self.fix_agv is not None else a,
                 self.fix_machine if self.fix_machine is not None else m) for a, m in pairs]

    def seed_population(self, n):
        return self._fix(self.inner.seed_population(n))

    def vary(self, elites, k):
        return self._fix(self.inner.vary(elites, k))

    def usage(self):
        return getattr(self.inner, "usage", lambda: "")()
