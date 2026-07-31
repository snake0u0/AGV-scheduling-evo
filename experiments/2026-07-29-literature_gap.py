"""Gap of our rules to the literature best-known (Berterottiere 2024, Table 8).

Reuses the per-instance results already produced by the confound-removal
re-evaluation (GA 70x70, seeds 0-2, 33 held-out instances), so no re-run is
needed. Also breaks the gap down by machine flexibility, which is where it
concentrates.
"""
import json
import os
import statistics as st
import sys

sys.path.insert(0, "/home/dohyung/project/research-agent")
from simulator.instance import BASE, parse_format_b

# Berterottiere, Dauzere-Peres & Yugma (2024), Table 8, iteration-stop Cmax.
# (2 vehicles, 4 vehicles, 6 vehicles)
TABLE8 = {
    "01a": (3029, 2812, 2756), "02a": (2504, 2368, 2428), "03a": (2325, 2289, 2279),
    "04a": (3000, 2785, 2806), "05a": (2504, 2358, 2408), "06a": (2322, 2267, 2258),
    "07a": (4157, 2860, 2758), "08a": (3208, 2334, 2259), "09a": (2448, 2213, 2146),
    "10a": (4145, 2783, 2685), "11a": (3211, 2349, 2265), "12a": (2484, 2173, 2133),
    "13a": (6332, 3471, 2900), "14a": (4259, 2700, 2379), "15a": (3034, 2367, 2288),
    "16a": (6472, 3493, 2834), "17a": (4315, 2629, 2367), "18a": (3017, 2355, 2264),
}
VI = {2: 0, 4: 1, 6: 2}
LABEL = {"D1": "빠른도착 규칙(문헌)", "D2": "부하분산 규칙(문헌)",
         "P_main": "진화 규칙 P_main", "P1": "진화 규칙 P1",
         "P2": "진화 규칙 P2", "P3": "진화 규칙 P3"}

T = os.path.expanduser("~/.claude/jobs/a367775e/tmp/")
res = json.load(open(T + "confound_eval_result.json"))
per = res["per_instance"]

flex = {}
for stem in TABLE8:
    inst = parse_format_b(f"{BASE}/Dauzere_Data/Text/{stem}.txt", name=stem)
    n_alt = sum(len(alts) for ops in inst.jobs for alts in ops)
    n_op = sum(1 for ops in inst.jobs for _ in ops)
    flex[stem] = (n_alt / n_op, inst.n_machines)

out = {"budget": res["budget"], "seeds": res["seeds"], "source": "Berterottiere 2024 Table 8",
       "rules": {}, "per_instance_gap": {}}

print(f"{'규칙':<22} {'평균 격차':>10} {'차량2대':>9} {'차량4대':>9} {'문헌 초과':>10}")
print("-" * 66)
for rule in ["D1", "D2", "P_main", "P1", "P2", "P3"]:
    gaps, g2, g4, wins = [], [], [], 0
    for key, ours in per[rule].items():
        stem, veh = key.rsplit("_", 1); veh = int(veh)
        lit = TABLE8[stem][VI[veh]]
        gap = 100 * (ours - lit) / lit
        gaps.append(gap)
        (g2 if veh == 2 else g4).append(gap)
        wins += ours < lit
        out["per_instance_gap"].setdefault(rule, {})[key] = round(gap, 1)
    out["rules"][rule] = {"mean_gap": round(st.mean(gaps), 1),
                          "gap_2veh": round(st.mean(g2), 1),
                          "gap_4veh": round(st.mean(g4), 1),
                          "beat_literature": wins, "n": len(gaps)}
    print(f"{LABEL[rule]:<22} {st.mean(gaps):>9.1f}% {st.mean(g2):>8.1f}% "
          f"{st.mean(g4):>8.1f}% {wins:>7}/{len(gaps)}")

rows = []
for key, ours in per["P2"].items():
    stem, veh = key.rsplit("_", 1); veh = int(veh)
    lit = TABLE8[stem][VI[veh]]
    rows.append((flex[stem][0], flex[stem][1], veh, key, ours, lit,
                 100 * (ours - lit) / lit))

print(f"\n{'유연도':>6} {'기계':>4} {'차량':>4} {'인스턴스':<9} {'우리':>7} {'문헌':>7} {'격차':>8}")
for r in sorted(rows, key=lambda x: -x[6])[:8]:
    print(f"{r[0]:>6.2f} {r[1]:>4} {r[2]:>4} {r[3]:<9} {r[4]:>7.0f} {r[5]:>7} {r[6]:>7.0f}%")

lo = [r for r in rows if r[0] < 2.0]
hi = [r for r in rows if r[0] >= 2.0]
out["by_flexibility"] = {
    "low_lt2": {"n": len(lo), "mean_gap": round(st.mean(x[6] for x in lo), 1)},
    "high_ge2": {"n": len(hi), "mean_gap": round(st.mean(x[6] for x in hi), 1)},
}
print(f"\n유연도 낮음(<2.0) {len(lo)}개: 평균 격차 {st.mean(x[6] for x in lo):.0f}%")
print(f"유연도 높음(>=2.0) {len(hi)}개: 평균 격차 {st.mean(x[6] for x in hi):.0f}%")

out["flexibility"] = {k: {"avg_eligible_machines": round(v[0], 2), "machines": v[1]}
                      for k, v in flex.items()}
p = os.path.expanduser("~/.claude/jobs/a367775e/tmp/literature_gap_result.json")
json.dump(out, open(p, "w"), ensure_ascii=False, indent=2)
print("\n->", p)
