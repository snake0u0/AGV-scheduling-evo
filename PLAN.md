# PLAN — 전체 실험계획

연구: **LLM-Evolved Interpretable Joint Dispatching Rules for Integrated Machine-and-AGV Dynamic FJSP.**
타깃: KIIE 학술대회(~3개월) → SCIE 저널. 이 문서 = 실험계획 개요.
상세 설계 = `docs/research/research_plan.md`, 실행 순서·기간 = `docs/research/execution_roadmap.md`.

## 목표 / 컨트리뷰션
- 동적 FJSP+AGV에서 **기계 시퀀싱 규칙 + AGV 디스패칭 규칙을 LLM-AHD로 동시(joint) 진화** → 해석가능·전이가능 규칙 자동 생성 (N1).
- 차별점: 기존 LLM-AHD는 기계만(DSevolve/EvoDR) 또는 차량만(MRE/VRPAgent); 통합 LLM-AHD는 빈칸(통합은 DRL D3QN뿐·비해석).
- 규모: **40–50 AGV 대규모 + 혼잡** (KIIE부터). 기성 벤치마크 없음 → 고전 FJSP+운반 벤치마크(Bilge-Ulusoy→Dauzère-Pérès) 혈통 위에서 스케일업 + 혼잡-지연. 근거: `docs/research/benchmark_anchor_notes.md`.

## 실험 설계 (요약; 상세 research_plan.md §5)
- **목적함수**: 평균 tardiness(주), makespan·throughput·flowtime(부); 해석성(규칙 복잡도)·전이.
- **Regime**: R1 운반병목 / R2 기계병목 / R3 균형 / R4 고교란. 대규모판 `LARGE_REGIMES`(L1/L3, 40–50 AGV).
- **비교 방법(baseline)**:
  | | 방법 | 기계 | AGV |
  |---|---|---|---|
  | B1 | 최우수 고전 joint | 고전 | 고전 |
  | B2 | GP 하이퍼휴리스틱(DEAP) | 진화 | 진화 |
  | B3/B4 | DRL/MARL · D3QN (SCIE) | 학습 | 학습 |
  | B5 | 기계만 LLM-AHD | 진화 | 고정 |
  | B6 | AGV만 LLM-AHD | 고정 | 진화 |
  | **P** | **제안 joint LLM-AHD** | **진화** | **진화** |
- **분리**: train으로 진화 → valid로 선택 → **test로만 보고**. regime·config당 ≥30 seed. 통계: Wilcoxon/Friedman.
- **공정성**: 모든 방법 동일 시뮬·동일 feature·동일 평가예산. LLM = Sonnet-4-6 via `claude` CLI(비용/토큰 로깅).

## 실행 단계 (마일스톤; 상세 execution_roadmap.md)
- **M1 LLM-AHD 루프 동작** ✅ — 실제 `claude` CLI proposer, ReEvo(fitness+reflection), train/valid/test 분리.
- **M1.5 시뮬 대규모화** ✅ — 혼잡-지연(S1)·FJSP화(S2)·대규모 regime(S2b)·교차검증(S3b). (BU 정확재현=follow-up)
- **M2 baseline 셋** ⬜ — B1 선택 + B2 GP(DEAP). (B3/B4 DRL = SCIE)
- **M3 캠페인·전이·ablation** ⬜ — L1/R 에서 P vs B1/B2/B5/B6 표 + 해석성 + regime 분석.
- **M4 집필** ⬜ — KIIE 초록/발표 → SCIE 확장(교란·배터리·전이·DRL·다목적).

## 진행 추적
스텝/실험마다 두괄식 결과 보고서 → `docs/reports/`. 현재 상태·바로 다음 = `STATUS.md`.
