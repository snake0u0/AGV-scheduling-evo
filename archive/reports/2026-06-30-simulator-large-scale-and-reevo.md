# 보고서 — 시뮬 대규모화(혼잡+FJSP) + 검증 + ReEvo 강화

작성 2026-06-30.

## 결론 (한눈에)
- 시뮬레이터를 **40–50 AGV 대규모 + 혼잡-지연 + 진짜 FJSP**로 확장하고, **두 독립 엔진 교차검증 3/3 순위 일치**로 신뢰성을 확인했다.
- 대규모 L1(40 AGV)에서 실제 LLM-AHD 루프가 **해석가능·혼잡인지 규칙**을 진화시켜 held-out test에서 **NV+EDD 대비 +2.1%**(R3의 +1.7%보다 큼).
- LLM 신호를 **순위만 → fitness 값+reflection(ReEvo)**으로 강화했다(구현·검증 완료).

## 처음 목적 / 왜
- KIIE 타깃이 **40–50 AGV 대규모**로 확정(2026-06-29). 그런데 기존 시뮬은 (a) AGV 간 혼잡 0(50대가 무간섭), (b) 연산당 기계 1개 고정(=JSP, FJSP 아님)이라 "대규모 AGV 병목 완화"라는 컨트리뷰션을 담을 수 없었다.
- 문헌 조사 결과 **기성 40–50대 FJSP+AGV 벤치마크는 없음**, 선행연구(Berterottière 2024)는 "대규모 fleet은 혼잡 유발"을 인정하나 모델링은 회피(fleet 제한) → **우리 빈칸**. 앵커 전략: 고전 FJSP+운반 벤치마크(Bilge-Ulusoy→Dauzère-Pérès) 혈통 위에서 스케일업+혼잡.

## 무엇을 어떻게 바꿨나
- **S1 혼잡-지연** (`sim/agv_fms.py::_cong_factor`): travel_time = base × (1 + α·busy/fleet). config `congestion_alpha`, 기본 0 = 기존과 비트동일(무회귀).
- **S2a FJSP화**: 연산을 `(적격기계 집합, 처리시간)`으로, 기계배정은 **고정 최소부하 룰**(`_assign`). config `flex`, 기본 1 = 비트동일. 진화는 기계시퀀싱+AGV 2개 joint 유지(N1 그대로).
- **S2b 대규모 regime** (`sim/configs.py::LARGE_REGIMES`): L1(40 AGV 운반병목), L3(50 AGV 균형). flex=2·혼잡 on.
- **S3 검증**: (b) 혼잡+flex를 salabim 엔진에 포팅 후 재-crosscheck. (a) 문헌 정성관계 재현.
- **ReEvo 강화** (`ahd/loop.py`, `ahd/llm.py`): loop이 elite를 fitness와 함께 vary에 전달 → LLM이 각 규칙의 mean_tardiness를 보고 reflection 후 개선안 생성. `reevo` 토글로 ablation 가능.

## 결과 (수치 / 비교)
- **FJSP 유연성 효과**(50 AGV, NV): makespan flex1=982 → flex2=822 → flex3=809 (부하분산, 수확체감).
- **혼잡 효과**(50 AGV): α 0→3에서 mean_tardiness 237→325, agv_util 0.26→0.83 (혼잡이 실제 비용).
- **교차검증**(custom vs salabim, 혼잡+flex 포함): **순위 3/3 일치**. 절대값 3–7%차 = 혼잡이 순간 busy-count에 의존하는 엔진 타이밍 민감도(정직히 기록). 룰 비교의 핵심인 순위는 일치 → salabim 충실.
- **정성 검증**: 차량수↑→makespan 단조감소+수확체감(Δ 675→323→…→168), 문헌(Berterottière) 패턴 재현.
- **L1 실런**(40 AGV, 8세대, 8 LLM 호출, ~$1): baseline 370.9 → train 364→360 개선 → **test 362.99 (+2.1%)**. 진화 AGV규칙이 `-downstream_load/(congestion+1)`로 혼잡 인지.
- **ReEvo 구현 검증**: 1회 호출 4개 유효 규칙, fitness+reflection 프롬프트 정상 파싱. mock 경로 무회귀.

## 한계 / 다음
- L1 +2.1%는 아직 modest(작은 버짓·LLM stochastic). **ReEvo old vs new 비교 런** 진행 중 → 별도 보고서.
- BU 정확 number-matching은 정적모드+explicit travel matrix+인스턴스 데이터 필요 → follow-up.
- 다음: 비교 런 정량화 → 캠페인(P vs B1/B5/B6) → 통계/집필.

## 관련 파일
- 코드: `sim/agv_fms.py`, `sim/agv_fms_salabim.py`, `sim/configs.py`, `sim/crosscheck_salabim.py`, `sim/viz.py`, `ahd/loop.py`, `ahd/llm.py`, `ahd/run.py`
- 문서: `archive/a-track/execution_roadmap.md`, `benchmark_anchor_notes.md`
- 그림: `docs/research/figures/` (layout/timeseries/anim/evolution)
