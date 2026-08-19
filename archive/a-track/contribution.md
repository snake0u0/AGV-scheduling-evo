# Contribution 포지셔닝 — 투고용 (KIIE / SCIE)
run: agv-llm-heuristic-20260608 | 정밀 novelty 검증(2026-06-08, OpenAlex+Scholar+arXiv+S2 인용그래프) 반영
> **읽기 안내**: 최신·확정 내용은 **`research_plan.md`(마스터)** + 아래 **§8(최종 확정)**. §1–7은 결정에 이른 사고과정 기록이며 일부 superseded(예: §7 팹-AMHS 특화안은 **미선택** — B+N1 채택).

## 1. 정직한 novelty 지형
"AGV에 LLM 첫 적용"은 **이미 선점됨**. 투고 전 반드시 알아야 할 인접 연구:

| 군 | 대표 | LLM 사용 | 방법 | 도메인 | 진화/탐색 | AGV 고유(충돌·배터리) |
|---|---|---|---|---|---|---|
| 에이전트 codegen | **PortAgent** (arXiv 2512.14417, 2025) | 멀티에이전트+RAG+Reflexion | 시스템 자동설계 | **항만 차량배차** | X | 항만 한정 |
| 진화형 AHD | DSevolve('26), SeEvo, **EvoDR**(2601.15738), LLM4DRD, AutoProg-SelfEvo(2410.22657) | LLM=진화연산자 | population 진화 | **machine/assembly flow shop** | O | **X** |
| AHD 시조 | FunSearch/EoH/ReEvo/HSEvo | LLM 진화/reflection | 진화 | bin-packing/TSP/CVRP/JSP | O | X |
| AGV 스케줄링 | DRL+digital twin, MDP+DoubleQ, MARL(#20/#22/#24), matheuristic(#21) | **없음** | DRL/메타휴리스틱 | AGV/FMS | - | O (단 해석성·전이성 약) |

→ **열린 white space**: *진화형 LLM-AHD × AGV 고유구조 × 해석가능 룰 × 동적 교란*. 이 교집합은 아직 비어 보임(잔여 리스크는 §5).

## 2. 권장 contribution (SCIE 방어 가능)
**제목(가안)**: *AGV-aware Automatic Heuristic Design: LLM-Evolved Interpretable Dispatching Rules for Dynamic AGV-Served Manufacturing*

**한 줄**: "EoH/ReEvo/DSevolve식 진화형 LLM-AHD를 AGV로 가져오되, **머신숍 AHD가 못 잡는 AGV 고유 구조(혼잡·충돌위험·배터리 SOC·deadhead)를 behavioral feature space와 terminal set에 내장**해, 동적 교란(신규작업·차량고장·배터리) 하에서 고전 AGV 룰·GP·DRL/MARL과 견주는 **해석가능·전이가능** 디스패칭 룰을 자동 생성한다."

**신규성 3기둥 (단순 '이전'이 아님)**:
1. **방법론**: AGV-aware feature space + terminal set (머신숍 AHD의 process-time/machine-load 대신 congestion/conflict/battery/deadhead). DSevolve feature space의 AGV 확장.
2. **문제범위**: 진화 룰 안에 배터리·충전·혼잡·충돌회피를 동적 교란과 함께 처리 → PortAgent(정적 항만 시스템 설계)·머신숍 AHD가 안 다룸.
3. **실증**: 해석가능성 + 미관측 layout/fleet로의 zero-shot 전이를 DRL/MARL 대비 입증(이쪽이 약한 지점).

**차별화 문장(리뷰어용)**: "PortAgent와 달리 (i) 항만이 아닌 일반 AGV-FMS, (ii) 에이전트 codegen이 아닌 quality-diverse 진화 탐색, (iii) 정적 설계가 아닌 동적 교란·배터리 처리. 머신숍 AHD(DSevolve/SeEvo/EvoDR)와 달리 AGV 고유 feature/terminal과 vehicle-task-path 결합을 명시 모델링."

## 3. 대안 framing (백업)
- **A. 벤치마크/실증 중심**: "동적 AGV 디스패칭을 위한 LLM-AHD vs DRL 체계적 비교 + 해석성/전이성 연구" — 방법 신규성↓ 실증 신규성↑. (ESWA/C&IE 류)
- **B. 통합 스케줄링**: 기계+AGV 동시 스케줄링(FJSP+AGV)에 AHD 적용 — #22/#24 환경 재사용. 범위 넓고 기여 분명하나 난이도↑.
- **C. 포트폴리오+상태선택**: DSevolve식 룰 포트폴리오를 AGV 혼잡 핑거프린트로 온라인 선택 — 스트레치, 저널 확장용.

## 4. 투고 현실 + 단계 계획
**솔직히**: 학부 3개월 → SCIE 직행은 빡빡함(SCIE는 SOTA 대비 충분한 실험·ablation·인지된 벤치마크 요구). **단계 전략 권장**:
- **1단계 — 대한산업공학회(KIIE) 학술대회 (~3개월)**: AGV-aware AHD 프로토타입 + 고전룰·(GP)·DRL 1종 비교 + 해석성 사례. → 발표/초록 확보.
- **2단계 — SCIE 저널 (+3~6개월 확장)**: 벤치마크 다양화(layout/fleet 전이), 머신숍 AHD를 AGV로 포팅한 비교군 추가, ablation(AGV-feature on/off, 배터리 on/off), 다목표(makespan·tardiness·energy). 타깃: *Computers & Industrial Engineering, Expert Systems with Applications, Journal of Intelligent Manufacturing, Robotics and CIM, Swarm & Evolutionary Computation, IEEE T-ASE, Applied Soft Computing, IJPR*.

**SCIE에 필요한 실험 세트**:
- 환경: 동적 AGV-FMS(신규작업·차량고장·배터리), 다중 layout/fleet(전이용). (#22/#24 MARL 세팅 또는 공개 AGV-FJSP 벤치 재사용)
- 베이스라인: 고전 AGV 룰(NV, STT/D, MOQS 등) + GP 진화룰 + DRL/MARL(#20/#22/#24) + **머신숍 AHD 포팅(DSevolve/ReEvo)** ← AGV-awareness가 중요함을 입증
- 지표: makespan/tardiness/throughput, energy, AGV 가동률, 해석성, zero-shot 전이
- ablation: AGV-aware feature, 배터리 처리

## 5. 잔여 novelty 리스크 + 투고 전 체크리스트
- 본 검증은 2026-06 시점. AGV-AHD 교집합은 빠르게 차고 있음(PortAgent가 6개월 전엔 없었음).
- **투고 직전 systematic novelty sweep 필수**: Scholar + arXiv listing(cs.AI/cs.RO 최신) + Semantic Scholar의 PortAgent/DSevolve/SeEvo **forward citations** 재확인. "evolutionary LLM-AHD for AGV" 정확 일치가 나오면 framing A/B/C로 선회.
- Related work에 PortAgent를 **명시적으로 위치**시키고 차별점 3개를 본문에 박을 것.

## 6. 다음 액션 (파이프라인)
1. 신규 경쟁/인접 논문을 Zotero 컬렉션에 추가: PortAgent(2512.14417), EvoDR(2601.15738), AutoProg-SelfEvo(2410.22657), SeEvo, LLM-guided VRP evolution(ESWA 2026), AGV digital-twin+DRL, AGV MDP+DoubleQ, AGV soft-computing(2025), stamping AGV(JIM 2025).
2. 위 신규 논문 전문 카드 → related-work 정밀화.
3. 확정 framing으로 1-page proposal(문제정의·방법·실험·기여) 작성 → KIIE 초록 초안.

---

## 7. 랩 지형 반영 — 정밀화 (`lab_research_flows.md` 기반)
**위협 재평가**: 최대 경쟁은 **HUST(Liang Gao·Xinyu Li)** — 머신숍 LLM-AHD를 거의 다 점령하고 **운반·다자원(LLM-MILP 멀티로봇)**으로 확장 중. "LLM-AHD for AGV/통합 스케줄링"이 그들의 자연스러운 다음 수 → **속도(KIIE 선점) + 도메인 차별**이 필수.

**권장 정밀화(강한 추천)**: 일반 AGV 대신 **반도체 팹 AMHS(OHT/AGV) 동적 디스패칭**으로 특화.
- 근거: **한국 도메인 본가 KAIST 장영재**(OHT/AMHS+RL: Q(λ) 라우팅 IJPR'19, MARL+GNN OHT 재배치 IISE Trans'21, RL 팹 디스패칭)와 **방법 본가 KAIST 박진규/CityU Zhang**(ReEvo/EoH)가 **둘 다 팹 AMHS에 LLM-AHD를 아직 안 함**.
- 이점: (i) **KIIE/한국 IE 적합성↑**(반도체는 한국 산업공학의 핵심), (ii) **장영재 랩 RL 디스패칭 = 강력한 베이스라인·문제설정 재사용**, (iii) AMHS 고유구조(**혼잡·교착(deadlock) 회피·유휴차량 재배치·OHT 트랙 경합**)로 **방법 신규성↑**, (iv) PortAgent(항만)·HUST(머신숍)·CityU(범용)와 **도메인 충돌 최소**.
- 즉 §2의 "AGV-aware AHD"를 **"AMHS-aware AHD: 반도체 팹 OHT/AGV 디스패칭 룰의 진화형 LLM 생성"**으로 구체화. feature/terminal에 OHT 트랙 혼잡·교착위험·재배치 압력·차량위치 추가.

**해석성·전이성 주장의 정당화**: Victoria Wellington(Zhang/Mei) GP 전통(해석가능·전이가능 진화룰)을 **명시 계승**해 리뷰 방어.

**대안 유지**: 팹 AMHS가 데이터/시뮬 확보 어려우면 일반 AGV-FMS(§2 원안)로 후퇴. (팹 특화가 기여·적합성에서 우월하나 진입장벽↑)

**투고 전**: HUST·CityU·PortAgent·장영재 랩 **forward-citation sweep** 재확인(특히 HUST의 AGV 신작).

---

## 8. ★최종 확정 (2026-06-09) — B + N1
사용자 결정: **B**(일반 AGV-FMS, fab특화 미선택) + **N1 수용**. (정밀 novelty sweep `novelty_sweep.md` 반영: "AGV-aware feature 신규" 헤드라인은 MRE 때문에 약함 → joint로 전환)

**확정 제목**: *"LLM-Evolved Interpretable **Joint** Dispatching Rules for **Integrated Machine-and-AGV** Dynamic Flexible Job-Shop Scheduling"*

**핵심 신규성**: 기존 LLM-AHD는 **기계 시퀀싱만**(DSevolve/EvoDR/SeEvo) 또는 **차량만**(MRE=AGV-드론 coord, VRPAgent/LLM-VD=routing) 진화. 우리는 **기계 시퀀싱 룰 + AGV 디스패칭 룰을 동시(joint) 진화** → 통합 동적 FJSP+AGV. 이 joint 결합이 빈칸.

**신규성 3기둥**: ① joint machine+AGV 룰 동시 진화(기존 AHD는 한쪽만) ② 동적 교란 하 해석가능 + 미관측 layout/fleet 전이 ③ AGV-FMS 베이스라인(D3QN/MARL/GP/고전 joint) 대비 체계 비교.

**차별 표(본문용)**:
| 경쟁 | 진화 | 기계 | AGV운반 | joint | 해석성 |
|---|---|---|---|---|---|
| DSevolve/EvoDR/SeEvo | O | O | X | X | O |
| MRE (AGV-드론) | O | X | O(coord) | X | O |
| VRPAgent/LLM-VD | O | X | O(routing) | X | O |
| PortAgent | agentic | X | O(항만) | X | △ |
| D3QN green-FJSP-AGV | DRL | O | O | O | **X** |
| **우리(N1)** | **O** | **O** | **O** | **O** | **O** |

→ "진화+기계+AGV+joint+해석가능"을 다 갖춘 건 우리뿐.

**구현 상태**: 시뮬레이터가 joint 결정 지원·검증 완료(`sim/`, `simulate(..., machine_policy=)`; `joint_demo.py`에서 joint 룰이 NV+EDD 베이스라인 능가). 다음 = LLM-AHD 루프로 joint 룰 쌍 생성(`ahd_stub.py` 확장).
