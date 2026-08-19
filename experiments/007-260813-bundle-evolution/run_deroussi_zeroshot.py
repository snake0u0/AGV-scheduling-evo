"""Zero-shot transfer: score the gen65 evolved bundle on Deroussi & Norre (2010),
a benchmark family the loop never trained or was even held out against.

Train and the "held-out" 15-instance Dauzere set are the same lineage - same authors,
same job-generation method, same travel-matrix construction. A rule that only learned
that lineage's specifics would still look good there. Deroussi is a different family
entirely, so this is a stricter check of whether anything general was found.

No LLM calls: this only replays the already-evolved bundle through the deterministic
constructive build, once per instance (~0.2s each).

Run:  python run_deroussi_zeroshot.py   (from this folder)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from experiments.common import gap, reference
from experiments.plots import benchmark_bars
from model.llm import _SEEDS_BUNDLE
from model.rules import rule_from_expr
from simulator.dispatch import build as dispatch_build
from simulator.instance import DEROUSSI_STEMS, load_deroussi

SOURCE = ("Deroussi & Norre (2010); cross-validated against Berterottiere et al. "
         "(2026) EJOR 332 Table 6; our simulator replays it exactly "
         "(tests/test_replay_deroussi.py, 10/10) - not a cited number, a verified one.")

SEED_NAMES = ["BALANCED", "HAND", "MIX"]


def main():
    evolved = json.load(open("result_full_resumed2.json"))["best_bundle"]
    instances = [(s, 2) for s in DEROUSSI_STEMS]

    bundles = {"evolved (gen65)": evolved, "BALANCED": _SEEDS_BUNDLE[0],
              "MIX": _SEEDS_BUNDLE[2], "HAND": _SEEDS_BUNDLE[1]}
    per = {}
    for name, b in bundles.items():
        slots = {slot: rule_from_expr(expr) for slot, expr in b.items()}
        row = {}
        for stem in DEROUSSI_STEMS:
            inst = load_deroussi(stem, 2)
            row[stem] = dispatch_build(inst, slots)[1].cmax
        per[name] = row

    print(f"{'instance':10s} {'lit':>6s} " + " ".join(f"{n:>16s}" for n in bundles))
    for stem in DEROUSSI_STEMS:
        ref = reference("deroussi", stem, 2)
        print(f"{stem:10s} {ref:6d} " + " ".join(f"{per[n][stem]:16d}" for n in bundles))

    summary = {}
    for name in bundles:
        gaps = [gap({"family": "deroussi", "stem": s, "veh": 2, "cmax": per[name][s]})
               for s in DEROUSSI_STEMS]
        summary[name] = sum(gaps) / len(gaps)
        print(f"{name:16s} mean gap {summary[name]:6.1f}%")

    fig_path, stats = benchmark_bars(
        evolved, _SEEDS_BUNDLE[0], instances, "deroussi", SOURCE,
        out="figures/benchmark-deroussi.png", fig_no=1,
        caption=f"Deroussi & Norre (2010) x 2 AGVs, zero-shot (never trained or "
               f"validated on). Mean gap vs literature: BALANCED {summary['BALANCED']:.1f}%, "
               f"ours {summary['evolved (gen65)']:.1f}%.")
    print("\nwrote", fig_path)

    json.dump({"instances": DEROUSSI_STEMS, "per_instance": per,
              "mean_gap": summary, "source": SOURCE},
             open("result_deroussi_zeroshot.json", "w"), indent=2)
    print("wrote result_deroussi_zeroshot.json")


if __name__ == "__main__":
    main()
