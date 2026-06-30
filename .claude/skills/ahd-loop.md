---
name: ahd-loop
description: Run or extend the LLM-AHD joint evolution experiment for the AGV FJSP project — evolve (machine_expr, agv_expr) rule pairs against the simulator, rank by mean tardiness, keep the best, mutate/reflect, repeat. Use when working on the core contribution (the heuristic-evolution loop) or wiring a real LLM in place of the mock.
---

# LLM-AHD joint evolution loop

The project's core contribution: an EoH/ReEvo-style loop that **jointly** evolves a machine
sequencing rule and an AGV dispatching rule, both as scoring expressions over the simulator's
feature interface. This skill is the procedure for running and extending it.

## Where it lives
- `ahd/loop.py` — the evolutionary loop (population → evaluate → select → vary → repeat).
- `ahd/llm.py` — the proposers. `MockLLM` (no LLM) varies linear weight-dict rules; `ClaudeCliLLM` varies free-form expression strings by calling the logged-in `claude` CLI headless. `ahd/run.py` auto-selects ClaudeCliLLM when `claude` is on PATH, else MockLLM.
- `ahd/run.py` — entry point. Run from the project root: `python -m ahd.run`.
- Predecessors (static, no LLM): `sim/joint_demo.py`, `sim/ahd_stub.py`.

## The interface being evolved
A candidate = `(agv_expr, machine_expr)`: two scoring expressions. Higher score = higher priority.
- AGV features: `travel_time, task_wait, slack, downstream_load, congestion, deadhead, battery_soc`.
- Machine features: `proc_time, slack, job_wait, remaining_ops, remaining_proc, downstream_load`.
- `sim/rule.py::policy_from_expr` compiles an expression string into `policy(features)->score`
  (restricted eval; invalid expr → score −1e9, so bad candidates are simply unfit).
- Fitness = mean `mean_tardiness` over a fixed seed set (lower is better). Primary objective.

## Procedure
1. **Seed** the population with classical rules (NV=`-travel_time`, EDD=`-slack`, …) + random combos,
   so the loop never starts worse than known baselines.
2. **Evaluate** every candidate: run `simulate(config, agv_policy, seed, machine_policy=...)` over seeds, average tardiness.
   - Default engine: `sim/agv_fms.py` (fast). For animation/physics use `sim/agv_fms_salabim.py` (same interface, ~2.5–3× slower).
3. **Select** the elite (top-k by fitness).
4. **Vary** via the proposer (mock: mutate weights / add-drop a feature / crossover; real LLM: prompt to mutate+reflect).
5. **Repeat** for N generations, keeping elites (elitism). Track and print the best each generation.

## Success criteria (sanity)
- The evolved best must **beat the NV+EDD baseline** on mean tardiness (as `joint_demo.py` already shows for hand-picked pairs).
- Rules must stay **interpretable** (short expressions) — that is a contribution claim, not just performance.
- Report should separate **train / validation / test** instances (see `research_plan.md §5`) to avoid overfitting.

## Real LLM (ClaudeCliLLM — implemented, no API key)
`ahd/llm.py::ClaudeCliLLM` is the real proposer. It uses the **logged-in `claude` CLI** (the account
already authenticated for Claude Code — no separate API key/billing): each `vary` shells out to
`claude -p --model sonnet --output-format json --dangerously-skip-permissions`, reads the model text from
the JSON envelope's `.result`, and accumulates the CLI's reported cost/tokens. Genomes are **free-form
expression strings** (nonlinear, interpretable rules — the point of LLM-AHD over weight search). Shared
logic lives in `_ExprProposer`: `vary` sends the elites (ranked best-first), asks for `k` improved
`(agv, machine)` pairs as single-line JSON, and validates each (`_valid`: compiles + only allowed feature
names) before it enters the population; the model call is isolated in `_complete` for testing. Keep the
prompt JSON-only (no prose) — verbose replies blow up output tokens (75s→9s/call). Soft budget cap via
`max_calls`; usage via `proposer.usage()`.
- **Run it**: `python -m ahd.run` (auto-uses the CLI when `claude` is on PATH). ~$0.4 / ~minutes per full run.
- **ReEvo signal** (done): `evolve` passes elites as `(pair, fitness)` best-first; `_ExprProposer.vary`
  shows each elite's mean_tardiness and asks the model to reflect (one sentence) then propose improved
  offspring. Genome stays a free-form expression string; parser ignores the `reflection` field.
- **Enhancements** (not yet done): larger pop/generations & budget; LLM-seeded initial population;
  multi-step reflection; quantify ReEvo gain via an old-vs-new comparison run.

## Output
Print per-generation best; save the final best pair + fitness curve under `runs/<topic>-<date>/`.
