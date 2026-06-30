# 보고서 — 세션 종합 (2026-06-30)

두괄식 세션 요약. 세부는 같은 폴더의 개별 보고서 참조.

## 결론 (한눈에)
- 시뮬을 **40–50 AGV 대규모 + 혼잡 + FJSP**로 확장하고 두 엔진 교차검증으로 신뢰성을 확보했다.
- 실제 `claude` CLI 기반 **LLM-AHD 루프 + ReEvo**를 갖췄고, **캠페인 하네스(P vs B1/B2/B5/B6)**를 구축했다.
- L1(40 AGV) 첫 캠페인: **joint LLM-AHD(P)가 +1.7%로 최우수**, 단일측 ablation·고전보다 우위 → **N1(joint 필요성) 첫 증거**.
- 프로젝트 구조를 정리(INDEX/STATUS/PLAN, docs/lit)하고 **스텝별 보고서 컨벤션**을 세웠다.

## 오늘 한 일 (단계별)
1. **시뮬 대규모화 + 검증** — S1 혼잡-지연, S2 FJSP화+대규모 regime(L1/L3), S3 salabim 재-crosscheck(3/3)·정성검증. → `2026-06-30-simulator-large-scale-and-reevo.md`
2. **ReEvo 강화 + 비교** — vary에 fitness값+reflection. rank-only vs ReEvo 비교(1차 무효=throttle→`_complete` 에러 가시화 수정 후 재실행). 분산이 커서 단정 불가, ReEvo 기본 유지. → `2026-06-30-reevo-vs-rankonly-comparison.md`
3. **캠페인 + B1/B5/B6 + L1 결과** — `ahd/campaign.py`, `FrozenSide`. P +1.7% > B5 +0.9% > B6 0% ≈ B1. → `2026-06-30-campaign-L1.md`
4. **B2 GP baseline** — `ahd/gp.py`(자체 트리 GP). 캠페인에 통합. 해석성 대비(GP=길고 비해석, LLM=간결) 확보. (GP-on-L1 수치는 캠페인 보고서에 반영)
5. **구조 정리 + 보고 컨벤션** — `runs/...`→`docs/research`, `scripts/prompts`→`lit/`, `NEXT.md`→`STATUS.md`, `PLAN.md`=실험계획, `INDEX.md` 신설. 스텝마다 `docs/reports/`에 두괄식 보고서.

## 핵심 수치
- 혼잡/FJSP 효과·교차검증 3/3·차량수 수확체감 = 시뮬 타당.
- L1 캠페인: baseline 370.9 → **P 364.6 (+1.7%)**, B5 367.7(+0.9%), B6/B1 ~0%.
- LLM 비용: 캠페인 ~$1.8(fails=0). GP는 CPU-only·무료.

## 한계 / 다음 (우선순위)
- **통계적 신뢰성**: 단일 런 분산이 큼 → 조건당 ≥3 반복 + Wilcoxon, 다regime(L3·R).
- **출력 verbose 비용**: LLM 런당 ~20k 토큰 → 프롬프트 억제 검토.
- 이후: 해석성 표 정식화 → KIIE 초록/발표 → (SCIE) 교란·배터리·전이·DRL.

## 산출물 위치
- 코드: `sim/`, `ahd/`(loop·llm·run·campaign·gp)
- 결과: `docs/research/results/*.csv`, 그림 `docs/research/figures/`
- 보고서: `docs/reports/`
