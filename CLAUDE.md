# research-agent — Project Guide

This subproject is an ACTIVE research project, not a blank workspace.
**Read `INDEX.md` then `STATUS.md` before doing anything.** Past sessions wasted effort
re-deriving decisions that are already settled below.

## Resume protocol
1. Read `INDEX.md` (project map) → `STATUS.md` (current status + next) → then `docs/research/research_plan.md` (master experiment design).
2. Do NOT re-litigate the topic, novelty, simulator, or competitor analysis — they are settled. Build forward.

## Confirmed framing (settled 2026-06-09)
- **Title**: *LLM-Evolved Interpretable Joint Dispatching Rules for Integrated Machine-and-AGV Dynamic FJSP.*
- **Novelty (N1)**: jointly evolve a machine sequencing rule + an AGV dispatching rule via LLM-AHD.
  White space: machine-only (DSevolve/EvoDR/SeEvo) or vehicle-only (MRE/VRPAgent) exist;
  joint + interpretable is open (DRL D3QN does joint but is non-interpretable).
- **Objective**: mean tardiness (primary); makespan, throughput, flowtime (secondary).
- **Target**: KIIE conference (~3 months) → SCIE journal. #1 competitor: **HUST (Liang Gao / Xinyu Li)** — speed matters (KIIE first).
- Key docs (under `docs/research/`): `contribution.md` §8, `novelty_sweep.md`, `simulator_spec.md`.

## Simulator (engine decision 2026-06-29)
- **Interface (engine-agnostic — this is what the LLM evolves)**:
  `policy(features)->score` for AGV dispatching + `machine_policy(features)->score` for machine sequencing.
  The dispatcher greedily matches the highest-scoring (idle AGV, ready task) pair.
- **Engines (both carry the v1 features — congestion-delay + FJSP flexibility — as of 2026-06-30)**:
  - `sim/agv_fms.py` — custom pure-Python DES. **Fast; the ACTIVE engine used for the evolutionary loop.**
  - `sim/agv_fms_salabim.py` — salabim port (same interface). Cross-validation + animation twin.
  - `sim/crosscheck_salabim.py` — proves the two agree on **rule rankings (3/3 configs incl. a
    congested-fjsp config)**; abs values diverge 3–7% because congestion depends on instantaneous
    busy-count. Cite as simulator-validity evidence. (The earlier "frozen oracle" framing is retired.)
- **AGV features**: `travel_time, task_wait, slack, downstream_load, congestion, deadhead, battery_soc`.
- **Machine features**: `proc_time, slack, job_wait, remaining_ops, remaining_proc, downstream_load`.
- salabim is ~2.5–3× slower → the loop uses the custom engine; salabim is for animation + cross-check.
  Further v1 physics (failure/battery/charging) = SCIE-tier, later.

## LLM-AHD loop
- `sim/ahd_stub.py`, `sim/joint_demo.py` — inner-loop harness (static candidate rules; no LLM needed).
- `ahd/` — the evolutionary loop. Real proposer = `ClaudeCliLLM` (logged-in `claude` CLI, no API key)
  with ReEvo signal (fitness+reflection); `MockLLM` is the no-LLM fallback. Run: `python -m ahd.run`
  (env `AHD_REGIME` / `AHD_GEN` / `AHD_TRAIN_N` / `AHD_REEVO`). See skill `ahd-loop`.

## Tools (MCP + skills)
- **Zotero MCP** (`mcp__zotero__*`): archiving + full-text PDF reading. Collection `agv-llm-heuristic` (key `JIREF4BS`, 40 papers).
- **`paper-lookup`** skill: 10-DB literature search (OpenAlex / Semantic Scholar / arXiv / Crossref / Unpaywall …).
  Semantic Scholar rate-limits hard without a key → prefer OpenAlex/arXiv, or `curl` with `--retry` backoff.
- **`literature-review`** skill: screening / synthesis.
- Custom **agent `novelty-watch`** (scoop detection) and **skill `ahd-loop`** (run the joint experiment).

## Scale & engine decisions (settled 2026-06-29)
- **SCALE = 40–50 AGV from KIIE** (NOT a SCIE stretch — earlier framing was wrong). k≤6 was only a
  loop-verification practice run. This is the confirmed target.
- This requires (critical path, see `docs/research/execution_roadmap.md` §1–2): a **congestion-delay model**
  (travel_time inflates with local AGV density — anchored on AMHS congestion lit, C&IE 2014
  doi:10.1016/j.cie.2014.02.002) + a **scaled instance generator** anchored on the FJSP+transport
  benchmark lineage **Bilge & Ulusoy 1995** (Zotero GP6HQQSG) → **Berterottière/Dauzère-Pérès 2024**
  (Zotero 3XNMDN47) → **Meng 2023 Multi-AGV FJSP** (2JMVT7DP). No off-the-shelf 40–50-AGV FJSP+AGV
  benchmark exists; we scale up the classic one + open-source it.
- **LLM = Sonnet-4-6 via the logged-in `claude` CLI** (no API key; `ahd/llm.py::ClaudeCliLLM`). DONE.

## Open TODOs
- **M1.5 sim large-scale-ification DONE** (congestion S1 + FJSP S2 + large regimes S2b + crosscheck S3b).
  Remaining S3 follow-up: exact Bilge-Ulusoy number-matching (needs static mode + travel matrix + data).
- **Next = M2/M3**: B1 best-classical-joint + B2 GP(DEAP) baselines → campaign (P vs B1/B2/B5/B6 on L1/R) →
  stats → KIIE write-up. GP/DRL (B3/B4) + v1 disturbances (failure/battery) = SCIE. See `docs/research/execution_roadmap.md`.
