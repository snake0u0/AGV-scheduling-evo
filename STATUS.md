# START HERE - 여기서 이어서 (resume point)

최종 업데이트 **2026-07-31**. 새 세션에서 "이제 뭘 하면 돼?" -> 이 파일부터.

## 한 줄 현황

**설계가 2026-07-31 회의에서 크게 바뀌었다. 아래 "설계 개정" 절을 먼저 읽을 것.**
요약: 하위문제 4개를 **전부** 진화 대상으로 올리고(슬롯 5개 = 4 하위문제 + LNS destroy),
solver를 GA에서 **LNS**로 바꾸며, 목적은 **makespan 단일** 유지. 폴더 구조도 개편됨.
데이터 쪽은 Deroussi&Norre 계열이 열려 replay 게이트 10/10 통과(2026-07-31).

## 방향 결정 (2026-07-23 확정)

| | 내용 | 상태 |
|---|---|---|
| **B안** | 정적 문헌 벤치마크(Deroussi&Norre 등) + GA 뼈대, makespan | **유효** |
| A안 | 동적 FJSP, mean tardiness, 자체생성 40-50 AGV + 혼잡 | **보류** |

- A안 문서(`PLAN.md`, `docs/research/research_plan.md`)는 **superseded 표시만** 하고 보존. `sim/` `ahd/` 코드도 삭제하지 않음.
- B안 근거: 문헌과 직접 수치 비교 가능, 공개 best-known 해로 evaluator 검증 가능, DCGA/CP와 같은 링에서 싸울 수 있음.
- B안 약점(인지하고 있음): 이 계보는 **AGV 2대 고정**이고 소규모. 그래서 정적은 **검증용**으로 쓰고, 성능 주장은 동적/불확실 환경에서 한다(아래 링 분리).

### AGV 규모 결정 (2026-07-23 재확정)

**KIIE 스코프에서 40-50 AGV 타깃을 철회.** B안(공개 벤치마크·SOTA 비교)과 정면 충돌하기 때문 -
문헌 어디에도 6대를 넘는 FJSP-AGV 인스턴스가 없어(전부 확인함: Deroussi/Kumar/Homayouni-Fontes=2대,
Berterottière 자체 확장=2·4·6대 최대), 40-50대에서는 비교할 SOTA/best-known 자체가 존재하지 않는다.
비교 불가능한 규모를 고수하면 B안을 택한 이유(검증 가능성)가 사라짐.

- **새 스코프**: AGV 2·4·6대(Berterottière의 `Berterottiere/dpp{2,4,6}veh/` 확장 그대로 재사용).
  같은 job 데이터를 대수만 바꿔 실험한 문헌 결과가 이미 있어 스케일링 곡선(대수↑ → 성능/이득 변화)을
  **전부 문헌 앵커 위에서** 그릴 수 있음 - 손해가 아니라 오히려 깔끔한 실험 축.
- 40-50 AGV(A안 산물)는 **이번 논문과 완전히 분리**, SCIE 확장이든 별도 컨트리뷰션(우리가 새 벤치마크를
  만들어 오픈소스)이든 나중에 독립적으로 재검토. 지금 당장 되살릴 필요 없음.

## 지금 뭘 하면 되나 (우선순위)

**2026-07-23 갱신**: 1번 완료, 3번은 데이터 문제로 계획 수정.
설계 = `docs/reports/2026-07-23-skeleton-evaluator-design.md`,
결과 = `docs/reports/2026-07-23-evaluator-implementation-and-replay.md`.

1. **[완료] 파서 3종 + 타이밍 코어** - `simulator/` 패키지. 포맷 A/B/C 전부 동작.
   **타이밍 코어는 Berterottière(2024) 논문의 워크드 예제로 검증 통과**(Cmax 13, 중간 시각까지 일치).
2. **[완료] decode + rules + GA** - `2026-07-24-decode-ga-skeleton.md`. decode 자기검증 180/180 일치.
   D1/D2 비지배성 재현. 재현: 회귀 테스트 4종 (아래 "코드 자산" 참고)
   **문헌 대비 격차는 아래 6번 참고(65%). 이 보고서의 "+13~43%"는 3개 인스턴스 표본이라 무효.**
3. **[완료 2026-07-31] replay 검증 - Deroussi&Norre에서 10/10 통과**.
   `2026-07-31-restructure-and-deroussi-unblock.md`. fjsp1-10 전부 공표 Cmax를 정확히 재현.
   막혔던 원인은 시뮬레이터가 아니라 **전제 오류**였다: 이 인스턴스는 4기계가 아니라 **8기계**(유연도 2는
   기계가 짝지어져 나오는 것), 행렬은 5x5가 아니라 **9x9**. 행렬은 추측이 아니라 Han 2024가 지목한
   데이터셋 페이지의 배포 PDF Table 5에서 **전사**했다.
   게이트: `python -m simulator.test_replay_deroussi`
   **단, Dauzere 계열(`Berterottiere/dpp*veh/`)의 해 파일은 여전히 헤더와 모순(54/54 불일치)**.
   -> 그 레포 해 파일 헤더 Cmax는 인용 금지, 논문 Table 8 값만 인용.
4. **[완료] experiment.py + LLM 루프 연결** - `2026-07-24-llm-loop-first-campaign.md`.
   전체 파이프라인(파서->decode->GA->진화->실제 claude CLI) 동작. `model/llm.py`(proposer, `model/llm_backend.py`의 _complete 재사용), `model/experiment.py`.
5. **[완료] 캠페인 3종: 본/재현성/교란제거** - `2026-07-24-{main-campaign, reproducibility-campaign,
   confound-removal-reeval}.md`. **읽는 순서 주의: 재현성 보고서의 비관적 결론은 교란제거 보고서가 뒤집음.**
   - **질적 통찰 재현(강함)**: 독립 진화 3회 모두 machine_free 사용, `max(arrival,machine_free)` 결합
     통찰 2/3 재등장. LLM이 "공정 시작 = 도착∨기계가용"을 run마다 독립 재발견.
   - **양적 우위(적정 예산에서 강함)**: 동일 고예산(GA 70x70/시드3)으로 4규칙 재평가 -> **3/4가 D1·D2
     양쪽 다 p<0.01로 이김**. 재현성 캠페인의 "1/3"은 가벼운 예산(60x60/시드2) 노이즈였음이 확정.
   - **못 이김**: best-of(D1,D2) 오라클(p≈0.1, 배포 불가라 실무 무관).
   - **방법론 교훈**: 평가 예산이 결론을 뒤집음. **모든 비교는 사전고정 적정예산(≥70x70/시드≥3)으로.**
6. **[완료] 통제 2x2 ablation** - `2026-07-24-ablation-two-ingredients.md`. **성분 귀속 정정**:
   두 성분이 대등하지 않음. **공차(empty_travel) 벌점 = 주효과**(단독 D1 이김 p=0.017, 주효과 p=0.0001).
   **기계가용 결합 = 단독 무효**(p=0.62)이나 **상승작용으로 기여**(interaction p=0.018; 둘 다 vs 공차단독
   p=0.047). 둘 다면 D1/D2 다 이김(vs D1 p=0.0009, vs D2 p=0.0002). 계수 c=0.3~0.7 robust.
   -> LLM의 진짜 주역 발견은 "결합 통찰"이 아니라 **공차 최소화**. 결합은 상보적 정제항. 자연실험(P3)이
   통제실험으로 왜 대체돼야 하는지의 사례.
   결과/스크립트 = `experiments/` + `data/results/`. 총비용 ~$1.0, 전체 실험 ~3.7h.
7. **[완료] 문헌 격차 실측** - `2026-07-29-literature-gap-measurement.md`.
   **문헌(Table 8) 대비 평균 격차 65%**, 33개 중 문헌을 넘어선 인스턴스 0개.
   격차는 **기계 유연도**와 연동: 유연도<2.0이면 36%, >=2.0이면 84%, 최악 172%(유연도 5.02, 10기계).
   -> **병목은 AGV 배차가 아니라 기계 선택.** 규칙 간 차이(2.6%p)와 전체 격차(65%)의 규모가 다름.
   이전 보고서들의 "+13~43%"는 인스턴스 3개 표본이라 무효(해당 보고서에 정정 주석 달아둠).

8. **[완료 2026-07-31] 예산 vs 구조 게이트** - `2026-07-31-budget-vs-structure-gate.md`.
   **평가를 61배(3.8만->233만) 늘려도 격차는 12%p만 감소**(76.1%->64.1%).
   Dauzere는 평가 10배당 -8.6%p라 남은 83.9%를 없애려면 10^9.7배가 더 필요 = 불가능.
   반면 Deroussi는 600초에 **4.6%**로 수렴(fjsp8은 3시드 전부 182). **GA가 고장난 게 아니라
   기계 선택 연산자가 구조를 안 쓰는 것이 문제.** -> **LNS 착수 승인(측정 근거)**.
   부수: 규칙 순위는 10초에서 Spearman 0.90으로 재현(상위 3개 정확) -> **진화 예산 10초 확정**.
   60초는 0.70으로 더 나쁨. DeroussiNorre는 천장이 4.6%라 **성능 주장은 Dauzere에서** 해야 함.

## 다음 (논문화 전)

1. **Stage 1: 이벤트 구동 평가기 + 4슬롯 분리** - `simulator/agv_fms.py`의 이벤트 루프와
   `timing.py`의 정확한 타이밍을 합친다. 완료 판정 = 손규칙 조합(SPT+D1)이 현행 `decode()`의
   D1과 같은 Cmax를 내는 동치성 회귀 테스트.
2. **Stage 2: LNS** (destroy + repair, 손규칙 연산자 먼저). 완료 판정 = 같은 시간예산에서
   LNS(손규칙)가 GA를 이긴다. **destroy는 반드시 기계 재배정을 건드려야 함**(위 8번).
3. **Stage 3: 진화 루프** - 5슬롯 개체, EoH 생각 + ReEvo 반성, 캐스케이드 평가, 16코어 병렬
4. Stage 4 ablation -> Stage 5 최종 600초 평가 + SOTA 비교
5. ~~data set 1 포함~~ **완료 2026-07-31** (이동시간 행렬 확보, replay 10/10)

## 코드 자산 (폴더 개편 2026-07-31)

역할 기준 구조. **`simulator/`는 `model/`에 의존하지 않는다**(단방향).

- **`simulator/`** 문제와 평가: `instance.py`(파서 3종 + 레지스트리 `load_dauzere`/`load_deroussi`),
  `solution.py`, `timing.py`(논문 예제 검증), `evaluator.py`(decode, 자기검증 180/180), `replay.py`,
  `agv_fms.py`(이벤트 구동 엔진 - 규칙 훅 2개 기보유), `policies.py`, `rule.py`
- **`model/`** 방법: `rules.py`(D1/D2 + 표현식 컴파일), `ga.py`, `llm.py`(proposer),
  `llm_backend.py`(claude CLI), `experiment.py`
- **`experiments/`** 캠페인 스크립트 | **`data/{instances,results,papers}`** | **`archive/`** A안 자산

회귀 테스트 4종 (전부 통과해야 함):
```
python -m simulator.test_paper_example      python -m simulator.test_replay_deroussi
python -m model.test_ga_operators           python -m model.test_decode_selfcheck
```

## 신뢰하면 안 되는 것

- **6/30 캠페인 수치 전부(P +1.7%, ReEvo 비교, B5/B6)**: tool-contamination 수정(commit `3a8ad01`, 7/4) **이전**에 생성됨.
  재실행 전까지 인용 금지. 보고서 `docs/reports/2026-06-30-campaign-L1.md`에 결론으로 박혀 있으니 주의.
- 게다가 그 수치는 A안(동적/tardiness) 세팅이라 B안과 직접 연결되지 않음.

## 설계 개정 (2026-07-31 확정) - 아래 "방법론 뼈대"보다 이것이 우선

| 항목 | 결정 |
|---|---|
| 구조 | **C안: 슬롯 5개 고정 스키마** = 기계선택 / 공정순서 / AGV선택 / AGV순서 + LNS destroy. 한 덩어리로 평가(개체 1개 = 5슬롯 한 벌) |
| solver | GA -> **LNS**. 근거: (a) 예산 게이트 측정(위 8번), (b) Berterottière 2026 결론이 LNS와 reconstruction 연산자를 지목, (c) VRPAgent가 VRP에서 같은 패러다임으로 SOTA 갱신 |
| 프롬프트 | **EoH**(슬롯별 `note` + 개체당 `design_rationale`) + **ReEvo**(슬롯 귀속 강제 단기반성 + 누적 설계원칙 노트). 검증반성층은 **제외** |
| 목적함수 | **makespan 단일**. TTT는 `sum(veh_cum)`으로 비용 0이라 보조 기록만. 다목적(MEoH)은 보류 |
| openevolve | 코드베이스 채택 안 함(claude CLI 백엔드 불일치). **캐스케이드 평가만 이식** |
| 분할 | train = **Dauzere 일부**, held-out = 나머지 Dauzere + **DeroussiNorre 10 전체**(zero-shot 전이) |
| 시드 | **(0, 21, 42)** 고정, 모든 설정 동일 = 짝지은 비교 |
| 예산 | 진화 중 **10초** + 캐스케이드 2단계 + 16코어 병렬 / **최종 평가만 600초**(문헌과 동일) |
| 베이스라인 | D1/D2·SPT/MWR/LFT는 별도 실험이 아니라 **슬롯 되돌리기 ablation과 동일물**. 방법 확정 후 마지막에 한 번만 |
| 데이터 | 즉시 사용 가능 **64 케이스**(Dauzere 54 + Deroussi 10). fattahi/Brandimarte/Kumar EX는 이동시간 미확보 |

**성능 주장의 위치**: makespan SOTA(DCGA-CP)를 이긴다고 주장하지 않는다. DCGA-CP는 CPLEX로
최적성을 증명한 결과다. 주장은 "해석 가능한 5슬롯 결합 규칙을 LLM이 자동 설계했고, 문헌 고정
규칙과 손규칙을 이기며, SOTA 대비 격차와 계산시간의 트레이드오프가 이렇다"이다.

## 방법론 뼈대 (2026-07-23 정리, 일부는 위 개정으로 대체됨)

**빈틈**: FJSP-AGV는 하위문제가 4개(기계배정 / 기계순서 / AGV배정 / AGV순서)인데,
- 메타휴리스틱(Han 2024 DCGA, Meng 2025, Homayouni BRKGA)은 **앞의 2개만 진화**시키고 AGV측 2개는 **고정 디코딩 규칙**에 위임.
  Han은 Decoding1/Decoding2 중 우열을 못 가려 이중 집단으로 회피함(논문이 스스로 인정: MFJS04에서 1152 vs 1144, 다른 예제는 1643 vs 1688로 역전).
- RL/NCO(Cheng 2025, Li 2025 TSMC, Wang 2025)는 **사람이 만든 규칙 풀에서 선택하거나 가중치만 조정**. 전역 최적화가 아니라 구성적 디코더 학습.
- 즉 **양 계보가 같은 자리를 비워뒀고, 거기가 우리 자리**.

**제안 구조 (2계층 공진화)**: 해 수준 GA(OS/MS) x 규칙 수준 LLM(AGV 배정/순서 규칙 동시 진화).
DCGA와 같은 인코딩/벤치마크/목적함수를 쓰므로 비교가 공정하고, Decoding1/2가 그대로 ablation이 됨.

**수학적 입증 경로**:
- disjunctive graph로 통합 정식화. 핵심: **기계 배정 하나가 노드 가중치(`pt`)와 아크 가중치(`Tr`)를 동시에 바꿈**(일반 FJSP는 노드만). 이게 분리 불가의 근거.
- 비분리성 명제 + 반례 인스턴스(2 job x 2 op, 2 machine, 2 AGV면 충분). 순차 최적화가 임의로 나빠질 수 있음을 travel time 파라미터로 보이면 강화됨.
- 실증 뒷받침: arXiv 2604.24117 (joint vs modular coordination gap, 2026-04). 단 **병목 상황에서 joint 이점이 줄어든다**고 하므로 우리 결과 해석 프레임으로도 필요.

**링 분리** (성능/해석성/강건성 동시 달성):
- 정적 벤치마크 = **검증용**. 문헌 tabu/CP는 최대 600초를 쓰고 우리는 수십 초 규모.
  2026-07-29 실측 격차 65%(위 7번). 여기서 이기는 것을 목표로 두지 않음.
- 동적/불확실 = **주장하는 링**. 상대는 GA/CP가 아니라 규칙선택형 RL. 분포 이동(도착률/고장률/AGV대수) 하에서 성능 저하폭 비교 = 강건성.

## 데이터 자산 (2026-07-22 확보)

`data/instances/fjspt-lucasberter/` (github.com/lucasberter/FJSPT 전체 + 2026-07-31 추가분)

폴더가 **입력(인스턴스)과 출력(해)** 두 종류로 갈리는데 README에 설명이 없으니 주의:
- 인스턴스: `DeroussiNorre/`(10) `fattahi/`(20) `Dauzere_Data/Text/`(18x2) `Homayouni_Brandimarte/`(대문자 B)
- **해(결과)**: `Deroussi/` `Homayouni_brandimarte/`(소문자 b) `Homayouni_fattahi/` `Berterottiere/dpp{2,4,6}veh/`
- travel matrix: `BerterottiereTravelTimes/layout{5,8,10}.txt` (Dauzere용) · **`DeroussiNorreTravelTimes/layout8.txt` (DeroussiNorre용, 9x9, 2026-07-31 전사)**
- 원본 `BerterottiereTravelTimes/` - **(m+1)x(m+1) 비대칭**. 행=출발, 열=도착. 인덱스 0 = L/U.

포맷 3종:
- **A. Bilge-Ulusoy 계보**(`DeroussiNorre/`): `nJob nMachine 유연도` / op당 `대체기계수 m m 공통시간`. 대체기계 2개의 **처리시간이 같고** 기계가 (1,2)(3,4)... 로 짝지어짐.
- **B. 표준 FJS**(`Dauzere_Data/`, `Homayouni_Brandimarte/`): `nJob nMachine 평균` / op당 `적격기계수 (기계,시간)...`. op마다 적격기계수와 시간이 다름.
- **C. Fattahi**(`fattahi/`): `총op수 선행관계수 기계수` / 선행쌍 리스트 / op당 `적격기계수 (기계,시간)...`. **job 경계가 선행관계로 표현됨.**
- **해 파일**: 헤더에 `#vehicles / Cmax / iterations / time`, 그 아래 `M1 ...`(기계별 연산순서) `V1 T..`(차량별 운반순서). **전체 시퀀스가 다 있음** -> replay 검증 가능.

### 주의: 확인된 문제 2가지
1. **`Homayouni_Brandimarte/setb4xxx.txt`와 `seti5xxx.txt`가 바이트 단위로 동일** (업스트림 레포 파일 착오로 보임).
   둘 다 헤더 `15 18 1`인데, seti5(15job x 15기계 +3)는 18이 맞지만 setb4(15 x 11 +3)는 14가 나와야 함.
   **둘을 별개 인스턴스로 실험에 넣고 보고하면 논문 레벨 오류.** 사용 전 원 출처에서 setb4xxx를 다시 받을 것.
2. **Data set 1(Bilge-Ulusoy 계보)용 travel matrix가 레포에 없음.** `BerterottiereTravelTimes/`는 Dauzere용(5/8/10 기계).
   `DeroussiNorre/`에 맞는 4기계 레이아웃(5x5)은 Bilge & Ulusoy 1995 논문(Zotero `GP6HQQSG`) 또는 Kumar 2011(`KQK9HJMJ`) Fig 3에서 **직접 전사**해야 함.
   -> 착수는 travel matrix가 이미 있는 **Dauzere 계보가 더 빠름**.

`docs/data/papers/` - 정독용 PDF 5편(Ham2020, Han2024, Homayouni2023, Kumar2011, Meng2025).

## 읽는 순서 (Zotero `agv-llm-heuristic` = JIREF4BS, 91편)

우선순위 최상위 3편:
1. **Bilge & Ulusoy 1995** `GP6HQQSG` - 문제 원전 + travel matrix 출처
2. **Zhou, Yang & Zheng 2019** `P584GSG3` - 기계배정+공정순서 **공진화** GP. 우리 joint의 방법론적 선조. "2019년에 이미 했잖아"에 답하려면 필독
3. **arXiv 2604.24117** joint vs modular coordination gap - **아직 Zotero에 없음, 추가 필요**

그 다음: Medikondu&Rao 2017 `NV3DRCFI`(디스패칭룰 통합), Zhang Min 2023 `5HFVPVZ6`(운반부족 동적 FJSP),
Homayouni BRKGA `I5P4WGSW`(카드에 미확인 항목 많음 - 전문 읽기 필요), MRE `R6EF89RJ`(차별 문장용, 전문 미확보).

**Zotero에 없어서 채워야 할 원전**: Deroussi&Norre 2010, Fattahi 2007, Dauzere-Peres&Paulli 1997, Hurink 1994,
Berterottiere 2026(total travel time, hal-05409040), arXiv 2604.24117.

## 재개 검증 (코드 살아있는지)

```
cd ~/project/research-agent
python sim/run_eval.py     # A안 시뮬 sanity (보류 상태지만 동작 확인용)
```

## 핵심 사실 캐시

- **타깃**: KIIE 학술대회 -> SCIE 저널.
- **Zotero**: 컬렉션 `agv-llm-heuristic` (key `JIREF4BS`, **91편**). 2026-07-23 중복 6쌍 정리 완료(메모 있는 사본 유지).
  주의: 6/8 배치로 넣은 항목 상당수가 **`linked_url`(파일 없음)** -> 로컬 PDF `docs/research/pdfs/`가 유일본.
- **위협 1순위**: HUST(Gao Liang / Li Xinyu) 그룹 - `Z8A3C7S9`, `Z33PYZZ7`, DSevolve. 속도로 선점.
- **A안 자산(보류, 삭제 안 함)**: `sim/`(DES + salabim 트윈 + crosscheck), `ahd/`(LLM 루프 + campaign + gp).
- **프로젝트 가이드**: `CLAUDE.md`(헌법), agent `novelty-watch`, skill `ahd-loop`.
