# [연구계획 초안 — 대한산업공학회(KIIE) 학술대회용 / SCIE 확장 기반]

**국문 제목(가안)**: 통합 기계·AGV 동적 유연 잡샵을 위한 LLM 진화 해석가능 공동 디스패칭 규칙
**영문 제목(가안)**: LLM-Evolved Interpretable Joint Dispatching Rules for Integrated Machine-and-AGV Dynamic Flexible Job-Shop Scheduling
> framing **B + N1 확정**(2026-06-09). "AGV에 LLM 최초/AGV-aware feature 신규" 주장 금지(MRE 반례). 신규성 = **기계 시퀀싱 룰 + AGV 디스패칭 룰의 동시(joint) 진화** — 기존 AHD는 한쪽만.

> 표기: [설정]=본 계획에서 확정, [결정필요]=학생이 확정해야 함(보통 선택지 제시), [근거]=수집 논문 기반.

---

## 1. 연구 배경 및 문제정의
유연제조·물류 현장에서 AGV(무인운반차) 배차는 처리율·납기·에너지에 직접적이다. 현장은 **동적 교란**(신규 운반작업 도착, AGV 고장, 배터리 소진에 따른 충전)으로 최적 배차 전략이 수시로 바뀐다 [근거: #22, #24, DSevolve].

본 연구의 결정 문제: **각 배차 시점**(AGV 유휴 발생 또는 작업 도착)에서 *어떤 작업을 어떤 AGV에 할당할지*를, 동적 교란·배터리 제약 하에서 결정하는 **AGV 디스패칭 규칙**을 자동 생성한다.

기존 한계:
- 고전 디스패칭 규칙(NV, STT/D 등)은 빠르나 **단일 정적 정책**으로 교란 대응 약함 [근거: #25].
- 유전프로그래밍(GP)/DRL은 규칙을 자동설계/학습하나 **고정 terminal set·약한 해석성**(GP) 또는 **전이성·해석성 저하**(DRL) [근거: EoH, #20·#22].
- 최신 **LLM 기반 자동 휴리스틱 설계(AHD)**(FunSearch→EoH→ReEvo→DSevolve)는 해석가능·신규 규칙을 진화시키지만, **전부 job/flow/assembly shop의 기계 스케줄링** 대상이며 **AGV 고유 구조를 다루지 않는다** [근거: DSevolve, EvoDR, SeEvo 전문/초록].

## 2. 관련연구 및 차별성
| 군 | 대표 | 방법 | 도메인 | AGV 고유(혼잡·충돌·배터리) |
|---|---|---|---|---|
| LLM 에이전트 codegen | PortAgent (2025, Tongji·COSCO·Dalian Maritime / 교통·항만) | 멀티에이전트+RAG+Reflexion 시스템설계 | **항만** 차량배차 | 항만 한정, 동적교란 미명시 |
| 진화형 LLM-AHD | DSevolve·EoH·ReEvo·EvoDR·SeEvo | LLM=진화연산자, 규칙 진화 | **기계/조립 숍** | **없음** |
| AGV 스케줄링 | DRL/MARL·digital twin·matheuristic [#20–#24,#36,#37] | RL/메타휴리스틱 | AGV/FMS | 있음(단 해석성·전이성 약) |

**본 연구의 위치(빈틈)**: *진화형 LLM-AHD × AGV 고유구조 × 해석가능 규칙 × 동적 교란.* 
**PortAgent와의 차별 3가지**(리뷰 대응): ① 항만이 아닌 **일반 AGV-FMS**, ② 에이전트 codegen이 아닌 **품질다양성 진화 탐색**, ③ 정적 시스템 설계가 아닌 **동적 교란·배터리·혼잡 처리**. *("AGV에 LLM 최초 적용" 주장은 하지 않는다.")*

**★확정 각도(N1)**: 일반 AGV-FMS 유지(B). 신규성은 도메인 이전이 아니라 **joint 진화** — 정밀 sweep(`novelty_sweep.md`) 결과 기존 LLM-AHD는 **기계만**(DSevolve/EvoDR/SeEvo) 또는 **차량만**(MRE=AGV-드론 coord, VRPAgent/LLM-VD=routing) 진화하고, **기계+AGV를 동시(joint) 진화한 LLM-AHD는 없음**(DRL D3QN만 통합). → 우리: **기계 시퀀싱 룰 + AGV 디스패칭 룰을 한 진화 루프에서 동시 생성**.
> (팹 AMHS 특화안은 미선택 — 데이터/진입장벽. 장영재 랩 OHT/RL은 도메인 동기·인용으로만 활용.)

## 3. 제안 방법: Joint Machine-AGV AHD (N1)
EoH/ReEvo식 진화형 LLM-AHD를 차용하되, **두 결정 규칙을 한 진화 루프에서 동시 생성**:
- **기계 시퀀싱 규칙** `machine_policy(features)`: 기계가 대기열에서 다음 작업 선택. features: proc_time·slack·job_wait·remaining_proc·downstream_load.
- **AGV 디스패칭 규칙** `agv_policy(features)`: 유휴 AGV에 운반태스크 할당. features: travel_time·task_wait·slack·downstream_load·congestion·deadhead·(배터리).
두 규칙이 상호작용(기계 선택이 운반 부하를, 운반이 기계 가동을 좌우) → **joint 최적화가 신규성**. (구현·검증됨: `sim/joint_demo.py`)

**(a) AGV-aware terminal/feature set** [설정·일부 결정필요]
기계숍 AHD의 입력(처리시간·기계부하·잔여작업) 대신 AGV 결정에 필요한 변수:
- 작업측: 대기시간, 납기 여유(slack), 작업 우선순위
- 차량-경로측: AGV↔픽업 **이동거리/시간**, **deadhead 비율**, **경로 혼잡도/충돌 위험**(지역 내 AGV·작업 수)
- 에너지측: **배터리 SOC**, 충전 임계 근접도
- 하류측: 목적지 기계/버퍼 부하

**(b) 진화 루프** [설정]
규칙(우선순위 함수/코드) 모집단 → LLM을 **crossover/mutation 연산자**로 사용 + **reflection**(ReEvo식 언어적 그래디언트). (선택) **multi-persona 시딩 + AGV-aware behavioral feature space 위 quality-diversity archive**(DSevolve식). 적합도 = 동적 AGV 시나리오 시뮬레이션의 makespan/tardiness/energy.

**(c) 온라인 배치** [설정]
진화된 **해석가능 규칙**을 ms 단위로 실행. (스트레치) 규칙 포트폴리오 + 혼잡 핑거프린트 기반 상태별 온라인 선택(DSevolve 변형).

## 4. 실험 설계
| 항목 | 내용 |
|---|---|
| 환경 | **[확정] 자체 DES 시뮬레이터**(`simulator_spec.md`, AI 구현). 문제정의는 #22/#24/#25 **동적 FJSP+AGV에 앵커**(임의 문제 금지). 신뢰성: 오픈소스·seed고정·다중config·고전룰 순위가 문헌과 일치하는지 검증 |
| 전이 테스트 | 서로 다른 layout/fleet 크기에서 zero-shot 평가(진화는 A, 평가는 미관측 B) |
| 베이스라인 | **고전 joint 조합**(AGV: NV/STT/MOQS × 기계: EDD/SPT/FIFO) · GP 진화규칙(DEAP) · DRL/MARL(#20/#22/#24) · **D3QN green-FJSP+AGV**(통합 DRL, 해석성 약점 대비) · **머신숍-only AHD 포팅(EoH/ReEvo, 기계만)** ← joint의 가치 입증 |
| 지표 | makespan·평균 tardiness·throughput·**에너지**·AGV 가동률/deadhead · **해석성**(규칙 길이/가독성) · **전이성**(미관측 환경 성능) |
| ablation | AGV-aware feature on/off · 배터리 처리 on/off · reflection on/off · QD archive on/off |
| LLM | 저비용 모델(GPT-4o-mini/DeepSeek-V3 등, DSevolve와 동일 기조) |

## 5. 기대 기여 (3기둥)
1. **방법론**: AGV 고유 feature space·terminal set을 내장한 진화형 LLM-AHD(머신숍 AHD가 못 잡는 혼잡·충돌·배터리·deadhead를 규칙이 직접 사용).
2. **문제범위**: 동적 교란·배터리·혼잡을 진화 규칙 안에서 처리 → PortAgent(정적 항만 설계)·머신숍 AHD가 미해결.
3. **실증**: 해석가능성 + 미관측 layout/fleet **zero-shot 전이**를 DRL/MARL 대비 입증(DRL의 약점).

## 6. 추진 계획 (단계)
- **1단계 (KIIE 학술대회, ~3개월)**: EoH/ReEvo 공개코드 최소 재현 → AGV-aware feature 정의·이식 → 단순 동적 AGV 시뮬 + 고전규칙·(GP)·DRL 1종 비교, 해석성 사례. → 초록/발표.
- **2단계 (SCIE 저널, +3~6개월)**: layout/fleet 전이, 머신숍 AHD 포팅 비교군, 다목표(makespan·tardiness·energy), 전체 ablation. 타깃: *Computers & Industrial Engineering / Expert Systems with Applications / Journal of Intelligent Manufacturing / Robotics and CIM / IEEE T-ASE*.
- **투고 직전**: systematic novelty sweep(PortAgent·DSevolve·SeEvo forward citations) 재확인, related work에 PortAgent 명시.

## 핵심 참고문헌 (Zotero 컬렉션 `agv-llm-heuristic`)
- DSevolve (arXiv:2603.27628, 2026) — 진화형 LLM-AHD + 포트폴리오/온라인선택, DFJSP
- Liu et al., EoH (ICML 2024); Ye et al., ReEvo (NeurIPS 2024); Romera-Paredes et al., FunSearch (Nature 2024)
- EvoDR (arXiv:2601.15738); SeEvo/AutoProg (arXiv:2410.22657, IEEE T-Fuzzy 2025) — 머신숍 LLM-AHD
- **PortAgent (arXiv:2512.14417, 2025)** — 항만 차량배차 LLM 에이전트 (최근접 경쟁, 명시 차별)
- AGV 스케줄링: DRL real-time(#20, 2020), FJSP+AGV MARL(#22, 2025), 생산+AGV MARL(#24, 2021), digital-twin+DRL(#36), battery matheuristic(#21, EJOR 2021)
- **한국 도메인(OHT/AMHS)**: Jang(KAIST) — Q(λ) OHT 동적 라우팅(IJPR 2019), MARL+GNN OHT 유휴차량 재배치(IISE Trans 2021), RL 팹 디스패칭; Park(KAIST) — ReEvo·RL4CO·OHT MARL
- Nguyen et al., GP·ML for heuristic design survey (IEEE TEVC 2023)
