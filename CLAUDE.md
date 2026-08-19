# research-agent — Project Guide

An ACTIVE research project, not a blank workspace.
**Read `INDEX.md` (map) then `STATUS.md` (state + next) before doing anything.**
Do NOT re-litigate the topic, novelty, benchmark, or evaluator — they are settled. Build forward.

## Confirmed framing

- **Title**: *LLM-Evolved Interpretable Joint Dispatching Rules for Integrated Machine-and-AGV FJSP.*
- **Novelty (N1)**: jointly evolve the machine-side and AGV-side rules via LLM-AHD.
  Machine-only (DSevolve/EvoDR/SeEvo) and vehicle-only (MRE/VRPAgent) exist; joint + interpretable
  is open (DRL D3QN is joint but not interpretable).
- **Track (settled 2026-07-23)**: **B안 = static literature benchmark, objective makespan.**
  A안 (self-generated dynamic FMS, mean tardiness) is on hold in `archive/a-track/`.
  Anything describing `sim/`, `ahd/`, congestion features or 40–50 AGVs belongs to A안.
- **Target**: KIIE conference → SCIE journal. #1 competitor: **HUST (Liang Gao / Xinyu Li)** — speed matters.
- Positioning docs: `docs/proposal_kiie.md`, `docs/novelty_sweep.md`.

## Commands

```bash
python -m tests.run_all                                       # gate x5. run after touching anything
python experiments/007-260813-bundle-evolution/run.py         # the evolution loop (~$23, ~80 min)
python experiments/007-260813-bundle-evolution/run_resume.py  # continue a run cut short by a usage limit
python experiments/plots.py gantt 09a 2 out.png               # figures
```

Gates are not unit tests — they are the evidence the simulator is valid (10/10 published solutions
replayed exactly, a paper's worked example matched, stored bundles re-evaluating to the same fitness).

## Architecture

| Folder | What |
|---|---|
| `simulator/` | Problem and evaluation: parsers, timing core, `dispatch.py` (4-slot constructive builder). **Does not import `model/`** |
| `model/` | Method: `rules.py` (expression sandbox), `llm.py` (`ClaudeBundleProposer`), `llm_backend.py` (claude CLI), `experiment.py` (`evolve_bundle`/`evaluate_bundle`) |
| `experiments/` | One experiment = one folder `NNN-YYMMDD-slug` holding its code, results, figures and reports. Index: `experiments/README.md` |
| `tests/` | The five gates |
| `docs/` | Research documents. Index: `docs/README.md` |
| `archive/` | Retired assets. Nothing is deleted; it moves here |

`model/` and `simulator/` hold only what runs the current method. When the method changes, the
unused part moves to `archive/` the same day.

## Running an experiment

**`docs/experiment_protocol.md` is the contract.** "실험 돌려줘" means the documented budget —
pop 20 x 65 generations = 995 individuals over 65 LLM calls — never a convenience-sized run.
Create `experiments/NNN-YYMMDD-slug/`, write `run.py` / `result.json` / `report.md` inside it,
add a STATUS.md entry, and pass the gates.

Reports are conclusion-first Korean markdown with PNG figures (`_TEMPLATE.md`), one per step.

## Gotchas

- **Literature reference values come from `experiments/common.py` only** (which reads
  `data/literature/`). Retyping a number into an experiment silently changes its reported gap
  at exactly the effect size being measured.
- **No dates, changelogs or history in code comments** (the code will be published). History
  belongs in the reports.
- **The 2026-06-30 campaign numbers are not citable** — generated before the tool-contamination
  fix, with the model able to run the evaluator itself.
- **The GA-era claim "evolved rules beat the literature hand rules" was invalidated** by
  experiment 003: it held at population 70 and vanished under a tuned solver.
- Evolution overfits: at 65 generations train improved while held-out got worse (experiment 007).
  Held-out separation caught it; there is still **no validation split** in the protocol.
- Data ready to run: Dauzere 54 cases (18 x 2/4/6 vehicles) + DeroussiNorre 10.
  fattahi and Homayouni_Brandimarte are blocked on a missing travel matrix.

## Tools

- **Zotero MCP** (`mcp__zotero__*`): collection `agv-llm-heuristic` (key `JIREF4BS`, 91 papers).
  Many entries are `linked_url` with no file — the local PDFs in `docs/pdfs/` are the only copy.
- **`paper-lookup`** skill: 10-DB literature search. Semantic Scholar rate-limits hard without a
  key → prefer OpenAlex/arXiv, or `curl` with `--retry` backoff.
- **`literature-review`** skill (screening/synthesis), **`/dh-paper-review`** (writes `docs/cards/`),
  **`/dh-discuss`** (Q&A record), agent **`novelty-watch`** (scoop detection).
