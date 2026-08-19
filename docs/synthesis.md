# 종합 리포트 — AI Agent(LLM) 기반 AGV 스케줄링 휴리스틱 룰 생성·결정
run: agv-llm-heuristic-20260608 | 앵커: DSevolve (arXiv:2603.27628) | 후보 30편 (전문 9편 + abstract 21편)

> 근거 표기: 전문 정독 = [FT], 초록 기반 = [ab], 추론 = (추론). 방법 계보(LLM-AHD) 9편은 전문 확보, AGV·GP 클러스터는 초록 기반.

---

## 1. 문제정의 변화 (timeline)
- **~2017**: 고정 디스패칭 룰(SPT/LPT 등) + 기계·AGV 동시 스케줄링에 "초기 스케줄러"로 우선순위 룰 사용. 어떤 룰을 쓸지 정당화 부재 [ab #25 2017].
- **2017–2022**: **GP 하이퍼휴리스틱**으로 디스패칭 룰을 자동 진화. 동적 FJSP의 routing+sequencing 룰, 다목표, feature selection, surrogate, coevolution으로 고도화 [ab #12 survey 2023; ab #14 2019].
- **2020–2025**: **DRL/MARL**이 동적 스케줄링 주류로. end-to-end(GNN) 또는 rule-selection. AGV로도 확장(실시간 스케줄링, 에너지효율, 생산+AGV 동시) [ab #20 2020, #22 2025, #24 2021].
- **2024–2026**: **LLM-AHD** 급부상. FunSearch→EoH→ReEvo→HSEvo→DSevolve. "LLM이 해석가능 휴리스틱 코드를 진화" → 단일 elite의 한계를 DSevolve가 **품질다양성 포트폴리오 + 온라인 룰선택**으로 돌파 [FT DSevolve].
- **공통 흐름**: 수작업 고정 룰 → 자동 진화(GP) → 학습 정책(DRL) → **LLM 기반 자동 휴리스틱 설계(AHD)**. 적응성·해석성·전이성을 동시에 잡으려는 방향.

## 2. 데이터셋·벤치마크
- **AHD 계보**: bin-packing, TSP/CVRP, Taillard JSP/flow shop, **동적 FJSP**(DSevolve의 500+ 실산업 인스턴스) [FT]. 표준 AGV-AHD 벤치마크는 **없음**.
- **AGV 쪽**: 대부분 자체 FJSP+AGV 인스턴스/시뮬레이터. MARL 연구가 task selection+machine alloc+AGV alloc 통합 환경 제공 [ab #22, #24]. battery/충전 제약 포함 매스휴리스틱 인스턴스 [ab #21].
- **시사점**: 졸논은 기존 **FJSP+AGV(MARL) 환경**[#22/#24]이나 단순 AGV 디스패칭 시뮬을 재사용하는 게 현실적. (추론)

## 3. 방법론 family (5개)
| Family | 정의 | 대표 논문 | 핵심 contribution | 한계 |
|---|---|---|---|---|
| F1. 고전 HDR | 고정 우선순위 디스패칭 룰 | SPT/LPT/SRM; 기계+AGV 통합 초기룰 [#25] | 빠름·단순·해석가능 | 단일 정적 정책, 환경변화 대응 X |
| F2. GP 하이퍼휴리스틱 | 트리 기반 디스패칭 룰 자동 진화 | Survey [#12]; multi-obj DFJSS [#14]; surrogate [#13]; improved GP [#16] | 룰 자동설계, 다목표·feature selection | terminal set 표현력 한계, 진화된 룰은 단일 정적 |
| F3. DRL/MARL 스케줄링 | 상태→행동 정책 학습(end2end/rule-select) | GNN-FJSP(Song'22); AGV real-time mixed rule [#20]; 생산+AGV MARL [#24]; FJSP+AGV MARL [#22] | 적응성, 동적대응, AGV 통합 | 전이성↓, 학습비용, 해석성↓ |
| F4. **LLM-AHD** | LLM을 진화연산자로 해석가능 휴리스틱 코드 생성 | FunSearch(Nature'24)→EoH(ICML'24)→ReEvo(NeurIPS'24)→HSEvo(AAAI'25)→**DSevolve('26)** [FT] | 해석가능·신규 휴리스틱, 포트폴리오+온라인선택(DSevolve) | 오프라인 비용, 평가비용, **AGV 미적용** |
| F5. AGV 스케줄링/라우팅 | AGV 배차·경로·충전 최적화 | matheuristic+battery [#21]; conflict-free [#30]; charging [#26]; 기계+AGV 통합 [#25] | AGV 특수제약(배터리·충돌·이종) 모델링 | 휴리스틱은 수작업·고정, MILP는 느림 |

## 4. 최근 2년(2024–2026) 한계 주장
- DSevolve [FT §6]: feature space 수작업, 오프라인 KB 비용 선형증가, makespan 단일목표, 물리라인 미검증.
- AHD 전반 [FT §2.2]: 단일 elite 수렴(→DSevolve가 portfolio로 일부 해결), LLM 평가 호출 비용.
- AGV+MARL [ab #22, #24]: 기계 유연성 + 제한된 물류장비 + 잦은 동적이벤트로 협조 스케줄링 복잡도↑, 전이성·해석성 약함.

## 5. 컨트리뷰션 후보 5 + 연구 gap
**핵심 gap**: 필터 143편 중 **AGV ∩ LLM-AHD = 0편**. LLM-AHD는 job/flow/assembly shop에만, AGV는 수작업룰·MILP·DRL에 머묾. 가장 가까운 인접은 CVRP에 AHD 적용 [#9, 차량경로]과 LLM4DRD(assembly flow shop, DSevolve가 인용).

| # | 아이디어 | 근거(누가 한계라 했나) | 시도 방법 |
|--|---------|----------------------|----------|
| 1 ★ | **LLM-AHD를 AGV 디스패칭 룰 생성에 첫 적용** | AHD가 AGV 미적용(F4 한계) + AGV 룰 수작업(F5 한계) | EoH/ReEvo식 단일 LLM 진화 루프로 AGV 배차룰 생성 |
| 2 | AGV 전용 feature/terminal 설계 | DSevolve feature space 수작업 한계 [FT §6] | 배터리·거리·혼잡·충돌·대기를 AHD 프롬프트/terminal에 반영 |
| 3 | 동적 AGV 환경 룰 포트폴리오+상태별 선택 | 단일 elite 한계 [FT §2.2] | DSevolve식 축소판(소규모 portfolio + 간단 룰선택) |
| 4 | 해석성·전이성 비교 | DRL 전이성·해석성 약함(F3 한계) | 생성룰 vs DRL/GP 베이스라인, 해석성·일반화 평가 |
| 5 | 기계+AGV 통합 스케줄링에 AHD | 통합 스케줄링 복잡도 [ab #22,#24] | FJSP+AGV 환경[#22/#24]에 AHD 적용 |

## 6. 학부 3개월 scoped 계획 (권장안 = 후보 #1 + #2)
**목표 한 줄**: "EoH/ReEvo식 LLM-AHD로 **해석가능한 AGV 디스패칭 룰을 자동 생성**하고, 고전 AGV 룰·(가능시)DRL 대비 성능·해석성을 비교한다 — AHD의 AGV 첫 적용."

| 기간 | 할 일 | 검증 |
|---|---|---|
| M1 (1개월) | EoH/ReEvo 공개코드 최소 재현(토이 스케줄링); AGV 스케줄링 시뮬+고전 디스패칭 룰 베이스라인 확보(#22/#24 세팅 또는 단순 자체) | 베이스라인 makespan 재현 |
| M2 (1개월) | AHD를 AGV로 이식: AGV 상태 feature/terminal 정의, fitness=makespan/tardiness/energy, LLM(저가모델: GPT-4o-mini/DeepSeek)로 룰 생성·디버그 | 생성룰이 시뮬에서 동작 |
| M3 (1개월) | 실험: vs 고전룰·GP·(선택)DRL, ablation, 해석성 분석; 논문 작성(related work는 본 리포트 기반) | 표·그림·기여 정리 |

**리스크/완화**: ① AGV 벤치마크 부재 → #22/#24 환경 차용 또는 단순 자체 시뮬. ② LLM API 비용 → DSevolve처럼 저가 모델. ③ AHD 재현 난이도 → EoH/ReEvo 공개코드 활용. ④ DSevolve 풀시스템(포트폴리오+probe)은 스트레치로, M3 여유 시만.

**왜 학부 수준에 적절**: 방법은 기존 AHD 코드 재사용(밑바닥 구현 X), 신규성은 "도메인 이전(AGV)"에서 확보, 비교는 잘 정의된 베이스라인. gap이 실재(AGV∩AHD=0)해 기여 주장 명확.

---
## 부록: 산출물 위치
- 후보풀: `candidates.jsonl`(348) / `candidates_filtered.jsonl`(143) / `selected.jsonl`(30)
- Zotero: 컬렉션 `agv-llm-heuristic`(key JIREF4BS), 30편 (`archive_log.md`)
- 전문 PDF(OA 9편): `pdfs/` — 01 DSevolve, 02 FunSearch, 03 EoH, 04 ReEvo, 05 HSEvo, 06 QUBE, 08 MCTS-AHD, 09 CVRP-AHD, 11 LLM-HumanRobot
- 카드: `cards/dsevolve.md` (앵커 전문 카드)
