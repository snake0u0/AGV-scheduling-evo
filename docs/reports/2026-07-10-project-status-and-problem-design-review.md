# 보고서 - 프로젝트 현황·문제설계·연구설계 종합 점검 (뒤엎을지 판단)

작성 2026-07-10.

## 결론 (한눈에)
- **뒤엎을 필요 없음.** 문제설계(joint FJSP+AGV)와 연구설계(N1 신규성, B1–B6 비교군, RQ1–4, train/valid/test 분리)는
  6/9 확정 이후 견고하며, **두 개의 독립적 검증**(① 자체 DES 엔진 vs salabim 두 번째 엔진의 규칙-순위 3/3 일치,
  ② FunSearch 공식 evaluator/데이터로 우리 하네스가 논문 Table 1을 소수점까지 재현)으로 **"프레임워크 자체가 맞게
  작동한다"는 근거는 이미 확보**되어 있음. 여기서 다시 시작하는 것은 낭비.
- **다만 하나의 구체적이고 긴급한 문제 발견**: 7/4에 bin-packing 데모에서 "`claude` CLI가 tool 접근이 켜진 채
  호출되어, 모델이 규칙을 제안하는 대신 스스로 evaluator를 실행해 버린" **tool-contamination 버그**를 발견해
  `--tools ""`로 고쳤다(commit `3a8ad01`). 커밋 메시지에 **"이 수정은 AGV 루프에도 적용됨"**이라고 직접 명시되어
  있는데 — **AGV 쪽 flagship 결과(L1 캠페인 P +1.7%, ReEvo 비교, B5/B6)는 전부 6/30에, 즉 이 수정이 들어가기
  4일 전에 생성됨.** 즉 지금 유일하게 존재하는 "우리 제안(P)이 이긴다"는 핵심 수치가 **오염 가능성이 검증되지
  않은 채로** 보고서(`2026-06-30-campaign-L1.md`)에 결론으로 박혀 있음. **재실행 전에는 이 수치를 믿지 말 것.**
- 그 외 이미 스스로 알고 있던 갭(통계 반복 없음, 소규모 문헌수치 재현 미완료)은 그대로 남아 있고, 7/2–7/4의
  4일은 AGV 캠페인이 아니라 별도 bin-packing 데모(교수님 발표용)에 전부 쓰여 **AGV 임계경로가 10일째 멈춰있음.**
- **권장 순서**: (1) tools-off로 L1 캠페인 재실행해 6/30 수치가 살아남는지 확인 → (2) 소규모(Bilge-Ulusoy 원본
  스케일)에서 문헌 수치 재현 → (3) 그 다음에야 통계 반복(≥3 seed·Wilcoxon)으로 확장. 이 순서가 사용자가 말한
  "작은 규모부터 꼼꼼히 확인"과 정확히 일치함.

---

## 1. 현재 프로젝트 진행 상황

| 마일스톤 | 상태 | 근거 |
|---|---|---|
| M1 프레이밍 확정 (제목·N1·타깃) | ✅ 완료 (6/9) | `research_plan.md`, `novelty_sweep.md` |
| M1 시뮬 v0→대규모화 (40–50 AGV+혼잡+FJSP) | ✅ 완료 (6/29–30) | `agv_fms.py`, `configs.py::LARGE_REGIMES`, salabim crosscheck 3/3 |
| M1 LLM-AHD 루프 동작 (`claude` CLI, ReEvo) | ✅ 동작함, **단 tools-off 검증 전** | `ahd/llm.py` |
| M2 baseline (B1 고전/B2 GP/B5/B6) | ✅ 하네스 완성, **L1 결과는 재검증 필요** | `ahd/campaign.py`, `ahd/gp.py` |
| M2 캠페인 첫 결과 (L1, P +1.7%) | 🔸 **오염 가능성 미확인** | 아래 §4 |
| M3 통계(≥3반복+Wilcoxon), 다regime | ⬜ 미착수 | 모든 보고서가 "다음"으로 반복 지목 |
| (사이드) FunSearch bin-packing 데모 | ✅ 완료, 방법론 검증에 유용 | `demo/bpp.py`, 7/2–7/4 |
| 문헌/novelty sweep | 🔸 **6/9 기준, 1개월 stale** | `novelty_sweep.md` 상단 날짜 |
| STATUS.md 날짜 | 🔸 6/9로 찍혀 있으나 본문은 6/30 캠페인까지 반영 — 갱신 필요 | 문서 정리 이슈, 사소함 |

시간선: 6/9 프레이밍 확정 → 6/29–30 시뮬 대규모화+LLM루프+캠페인(하루 만에 몰아침, 세션 요약 참고) →
**7/2–7/4 나흘간 AGV가 아니라 bin-packing 데모로 완전히 전환** → 7/4 그 데모에서 tool-contamination 버그 발견·수정
→ **7/5–7/10(오늘) 6일간 커밋 없음, AGV 쪽에 수정 미반영.**

## 2. 문제설계(problem design) 상황

정의 자체는 명확하고 안정적이다 (`research_plan.md §1`, `simulator_spec.md §1–4`):
- **엔티티**: 기계 M대, AGV K대, job 동적 도착, 각 job=연산 시퀀스(적격기계 집합+처리시간), 연산 간 운반=AGV.
- **결정 2종(동시)**: (i) 기계 큐에서 다음 연산 선택(시퀀싱), (ii) 유휴 AGV→ready 운반태스크 매칭(디스패칭).
- **목적**: 평균 tardiness(주) + makespan/throughput/flowtime.
- **정책 인터페이스**(모든 방법·베이스라인 공유, LLM/GP가 진화하는 대상): `agv_policy(features)->score`,
  `machine_policy(features)->score`. features: AGV={travel_time, task_wait, slack, downstream_load,
  congestion, deadhead, battery_soc}, machine={proc_time, slack, job_wait, remaining_ops, remaining_proc,
  downstream_load}.
- **스케일 확정**: 40–50 AGV가 KIIE 본타깃(6/29 확정, k≤6은 연습이었음을 재확인).

이 부분에서 "설계가 틀렸다"고 볼 근거는 없음. 다만 두 개의 **미완성 검증 구멍**이 여전히 열려 있다(둘 다
이전 보고서에서 이미 스스로 지목했지만 아직 안 닫힘):
1. **소규모 문헌 수치 정합**: Bilge-Ulusoy(1995) 원본 규모(8기계·유연도2·차량2–6)에서 우리 시뮬이 논문 수치를
   재현하는지는 아직 확인 안 됨(`STATUS.md` 1번 항목, `execution_roadmap.md §1` 리스크절에 "follow-up"으로만
   적혀 있음). 지금까지 검증한 건 "**두 엔진끼리 순위가 일치**"(내적 정합성)이지 "**우리 시뮬이 실제 논문 절대
   수치와 일치**"(외적 정합성)가 아님. 사용자가 말한 "작은 규모부터 확인"이 정확히 이 구멍을 가리킴.
2. **대규모 인스턴스는 자체 생성**(기성 40–50 AGV FJSP+AGV 벤치마크가 없어서): 리뷰어가 "니들이 만든 문제에서
   니들이 이겼다"고 지적할 수 있음. 완화책(고전 벤치마크 혈통 인용, 오픈소스, 소규모 재현)은 설계돼 있으나
   **소규모 재현 실행이 아직 안 된 상태**라 지금은 리스크가 열려 있는 채로 대규모로 점프한 상태.

## 3. 연구설계(research design) 상황

`research_plan.md §5`가 마스터. 구조는 탄탄함:
- **RQ1(성능 우위) / RQ2(joint 필요성) / RQ3(해석성·전이) / RQ4(regime)** — 각 RQ에 대응하는 비교군이 명시적으로
  설계돼 있음(B5/B6이 RQ2용 ablation, unseen config 평가가 RQ3용 등).
- **비교 방법 6개**(B1 고전조합 / B2 GP-DEAP / B3 DRL(SCIE) / B4 D3QN-joint(SCIE) / B5 기계만-LLM / B6 AGV만-LLM
  / P 제안) — B1·B2·B5·B6·P는 하네스 완성(`campaign.py`), B3·B4는 의도적으로 SCIE로 미룸(합리적 스코프 컷).
- **train(0–19)/valid(20–24)/test(25–29) seed 분리**가 코드 레벨로 강제됨(`configs.py`) — 과적합 방지 설계는 이미
  구현돼 있고 건드릴 필요 없음.
- **통계 프로토콜(§5.7)**: ≥30 seed, Wilcoxon/Friedman — **설계는 있으나 실행이 없음.** 지금까지 나온 모든 수치
  (L1 캠페인, ReEvo 비교)는 **단일 런**이고, 모든 관련 보고서가 스스로 "단일 런이라 분산 큼, 결론 내리려면
  ≥3 반복 필요"라고 한계란에 적어 놓음. 이건 설계 결함이 아니라 **아직 안 돌린 실행 항목**.

즉 연구설계는 다시 짤 필요가 없고, **설계된 것 중 실행이 안 된 항목(통계 반복, 소규모 재현)을 채우는 단계**다.

## 4. SEED 휴리스틱이 뭔지

"SEED"는 이 프로젝트에 **두 군데**에서 쓰이고, 둘 다 "진화가 출발하는 초기 규칙"이라는 같은 개념이다. 헷갈리기
쉬운 게, 문헌 관례 용어(단수 SEED 함수 하나)와 진화 population 초기화(복수 seed 규칙 여러 개)가 둘 다 있어서다.

1. **`demo/bpp.py::SEED`** (bin-packing 데모, FunSearch 관례 그대로) — LLM이 개선을 시작하는 **출발점 함수 그 자체**.
   ```python
   def priority(item, bins):
       return -(bins - item)     # Best-Fit: 남는 공간이 가장 작은 상자에 높은 점수
   ```
   FunSearch 논문에서 "seed function"이라 부르는 것과 동일한 역할 — LLM은 이 함수의 **본문만** 고쳐나간다.
   `Best-Fit (seed)`라는 이름으로 비교표에도 등장한다(`demo/bpp.py:189`).

2. **AGV 쪽 `seed_population(n)`** (`ahd/llm.py:50,172,298`) — 진화 population을 **처음 채울 때** 무작위가 아니라
   고전 규칙 조합으로 시작시키는 함수. 실제 시드로 쓰는 4개 조합(`_CLASSICAL_EXPR`, `ahd/llm.py:107-112`):
   ```
   NV+EDD, NV+SPT, (NV+혼잡가중)+EDD, (NV+slack가중)+LWR
   ```
   즉 AGV 쪽엔 "seed 함수 1개"가 아니라 **"seed 규칙 쌍(agv_policy, machine_policy) 4개"**가 있고, population
   크기가 4보다 크면 이걸 돌려가며 채운다(`ahd/llm.py:174-175`). `research_plan.md §4`의 "(선택) seed=고전 규칙"과
   `§5.4` ablation의 "seed(고전 규칙) on-off"가 가리키는 게 바로 이것.

두 SEED 모두 **진화가 무(無)에서 시작하지 않고 알려진 좋은 규칙에서 출발**하게 해서 (a) 첫 세대부터 그럴듯한
후보를 갖게 하고 (b) "고전 규칙보다 최소한 나쁘진 않은 진화"를 보장하려는 같은 목적이다.

## 5. 지금 발견한 문제: tool-contamination이 AGV 결과에도 적용되는가

`ahd/llm.py::ClaudeCliLLM._complete`(AGV 루프가 실제 `claude` CLI를 부르는 유일한 지점)와
`demo/bpp.py`가 **같은 호출 패턴**(`claude -p --dangerously-skip-permissions`)을 썼다. 7/4에 bin-packing 데모에서
"tool을 안 끄면 모델이(특히 Opus가) 규칙을 텍스트로 제안하는 대신 **직접 evaluator를 import해서 자체 탐색**해
버린다"는 오염을 발견해 `--tools ""`를 추가했다(commit `3a8ad01`, diff 확인함: `ahd/llm.py:246-248`에 지금은
`--tools ""`가 들어가 있음). **커밋 메시지 원문**: *"The fix applies to the AGV loop too."*

문제는 — **AGV 쪽에서 이 문구 이상의 조치가 없었다는 것.** 재확인한 타임라인:
- 6/30: L1 캠페인 실행(`ahd/campaign.py`), `2026-06-30-campaign-L1.md` 작성 — **이때 코드엔 아직 `--tools ""`가
  없었음**(git diff 확인: 이 줄은 `3a8ad01`에서 처음 추가됨).
- 6/30: ReEvo vs rank-only 비교 실행 — 마찬가지로 tools-on 상태에서 실행.
- 7/4: 버그 발견·수정, **하지만 bin-packing 데모만 재실행**해서 새 수치로 교체. AGV 캠페인/ReEvo 비교는
  재실행되지 않았고, `2026-06-30-campaign-L1.md`는 지금도 오염 가능 수치를 결론으로 인용 중.

bin-packing 데모에서 실측된 오염 효과는 모델별로 컸다(Opus가 자체탐색으로 "FunSearch를 이겼다"고 착각했던
사례가 대표적, `2026-07-04-demo-presentation.md §6`). AGV 캠페인이 쓴 모델(Sonnet)은 데모에서 상대적으로
영향이 작았던 쪽이긴 하나, **AGV 시뮬은 bin-packing 채점기보다 코드가 훨씬 크고(`sim/agv_fms.py` 등) 모델이
tool로 직접 열어볼 유인도 더 큼** — 오염 방향(과대평가/과소평가/무관)을 지금은 아무도 모른다. **"단일 런이라
분산이 크다"는 이미 알려진 한계와는 별개로, 이건 "그 단일 런이 애초에 우리가 재는 대상(순수 LLM 제안)을
쟀는지조차 불확실하다"는 더 근본적인 문제다.** N1의 핵심 증거(joint P > B5/B6 ablation)가 이 수치에 의존하므로
캠페인 재실행 없이는 KIIE 초록에 그대로 못 씀.

## 6. 뒤엎을지 vs 지금 것 쓸지 — 판단

**뒤엎지 않는다.** 근거:
- 문제설계·연구설계·시뮬 인터페이스는 문헌 앵커(Bilge-Ulusoy 계보)·경쟁분석(novelty_sweep)·엔지니어링
  결정(engine choice) 모두 명시적 근거를 남기며 결정됐고, 재검토해도 같은 결론에 도달할 내용들임.
- LLM-AHD 루프라는 **방법론 자체**는 이미 독립적으로 검증됨: FunSearch의 실제 채점기·데이터 위에서 우리
  하네스가 논문 Table 1을 재현했고, 우리 LLM이 (tools-off 클린 상태로) FunSearch 자신의 핵심 통찰을
  재발견했다. 이는 "우리가 만든 진화 루프 코드가 실제로 옳게 동작한다"는, AGV 도메인과 무관한 강한 증거다.
- 시뮬 엔진도 두 번째 독립 구현(salabim)과 순위 3/3 일치로 교차검증됨.

**그러나 "지금 만든 결과를 그대로 쓸 수 있느냐"는 별개 질문이고, 답은 "아직 아니오"다.** 재작업은 처음부터가
아니라 **아래 세 가지, 순서대로**:

1. **[긴급] L1 캠페인 + ReEvo 비교를 tools-off(`--tools ""`, 이미 코드엔 반영됨) 상태로 재실행.** 수치가
   6/30과 비슷하면(방향·크기 유지) 기존 결론(P > B5 > B2 > B6 ≈ B1) 유지하고 보고서에 "재검증 완료" 각주만
   추가. 크게 달라지면 그게 오염의 증거이므로 결론 자체를 다시 써야 함. 반나절이면 끝나는 작업.
2. **[사용자가 원한 "작은 규모부터"] Bilge-Ulusoy 원본 스케일(8기계·차량2–6)에서 우리 시뮬이 문헌 절대
   수치를 재현하는지 확인** — `execution_roadmap.md`가 이미 "follow-up"으로 지목했지만 미착수. 정적 모드+
   explicit travel matrix+원 논문 인스턴스 데이터가 필요(§1 참고). 이게 끝나야 40–50대 확장판을 리뷰어에게
   방어할 수 있음.
3. **그다음에** 조건당 ≥3 반복+Wilcoxon으로 통계화, 다른 regime(L3·R) 확장 — `research_plan.md §5.7`에
   이미 설계돼 있는 대로.

부수적으로: novelty sweep(6/9, 1개월 경과)을 지금 한 번 더 돌려서 KIIE 3개월 시계 중간점 기준 HUST 등의
움직임을 확인해 두는 게 좋음(투고 직전까지 미루면 손 쓰기 늦을 수 있음). STATUS.md 날짜 스탬프도 갱신 필요.

## 관련 파일
- 문제/연구설계: `archive/a-track/research_plan.md`, `archive/a-track/execution_roadmap.md`, `archive/a-track/simulator_spec.md`, `docs/novelty_sweep.md`
- 시뮬/루프 코드: `sim/agv_fms.py`, `sim/configs.py`, `ahd/llm.py`(`_CLASSICAL_EXPR`, `seed_population`, `ClaudeCliLLM._complete`), `ahd/campaign.py`
- tool-contamination 발견/수정: commit `3a8ad01`, `demo/bpp.py`, `archive/reports/2026-07-04-demo-presentation.md §6-7`
- 재검증 필요한 기존 결과: `archive/reports/2026-06-30-campaign-L1.md`, `archive/reports/2026-06-30-reevo-vs-rankonly-comparison.md`
