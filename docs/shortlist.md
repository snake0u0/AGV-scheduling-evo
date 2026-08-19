# AGV × LLM/AHD 휴리스틱 스케줄링 — shortlist (2026-06-08)  [수집 348 → 필터 143 → 후보 30]

앵커: **DSevolve** (arXiv:2603.27628). 주제: AI Agent(LLM) 기반 AGV 스케줄링 휴리스틱 룰 생성·결정 (학부 졸논, ~3개월).

## 핵심 발견 (gap)
필터된 143편 중 **AGV-side 38 / AHD-side 41, 둘 다인 것은 단 1편**. → **LLM/AHD를 AGV 스케줄링에 적용한 연구는 거의 없음** = 학부 수준에서 노릴 만한 빈틈. 가장 가까운 인접: CVRP(차량경로)에 LLM-AHD 적용(아래 #9).

태그: A=AGV 도메인, H=AHD/LLM 방법. Rel=관련도(1-5). Keep=기본 채택(B=borderline, 당신이 쳐내기 쉬움).

---

### 0. 앵커
| # | Title | Year | Venue | Cit | tag | Rel | Keep | 메모 |
|--|-------|------|-------|----:|-----|----:|------|------|
| 1 | DSevolve: Real-Time Adaptive Scheduling with LLM-Evolved Heuristic Portfolios | 2026 | arXiv | 0 | H | 5 | Y | 방법 골격(오프라인 QD 포트폴리오+온라인 선택) |

### A. LLM-AHD 방법 계보 (논문이 쓸 방법의 뿌리)
| # | Title | Year | Venue | Cit | tag | Rel | Keep | 메모 |
|--|-------|------|-------|----:|-----|----:|------|------|
| 2 | FunSearch: Mathematical discoveries from program search with LLMs | 2023 | Nature | 339 | H | 5 | Y | LLM-AHD 시초 |
| 3 | EoH: Evolution of Heuristics — Automatic Algorithm Design using LLM | 2024 | ICML | 13 | H | 5 | Y | LLM+EA 휴리스틱 진화, DSevolve 직계 |
| 4 | ReEvo: LLMs as Hyper-Heuristics with Reflective Evolution | 2024 | NeurIPS | 11 | H | 5 | Y | reflective evolution(DSevolve가 확장) |
| 5 | HSEvo: AHD with Diversity-Driven Harmony Search | 2025 | AAAI | 8 | H | 4 | Y | diversity→DSevolve의 QD와 연결 |
| 6 | QUBE: AHD via Quality-Uncertainty Balanced Exploration | 2024 | arXiv | 1 | H | 3 | B | AHD 탐색 변형 |
| 7 | Memetic & Reflective Evolution Framework for AHD using LLM | 2025 | Applied Sciences | 2 | H | 4 | Y | 최신 AHD 프레임워크 |
| 8 | MCTS for Comprehensive Exploration in LLM-Based AHD | 2025 | arXiv | 0 | H | 4 | Y | 탐색 전략 대안 |
| 9 | Enhancing CVRP Solver through LLM-driven AHD | 2026 | arXiv | 0 | H | 5 | Y | **차량경로(AGV에 가장 근접)에 AHD 적용** |
| 10 | LLM-Assisted Automatic Memetic Algorithm for Lot-Streaming Hybrid JSP | 2025 | IEEE TEVC | 6 | H | 4 | Y | LLM+메타휴리스틱 for JSP |
| 11 | Leveraging LLMs for efficient scheduling in Human–Robot collaboration | 2025 | npj Adv. Manuf. | 6 | H | 3 | B | LLM+로봇 스케줄링 |

### B. GP 하이퍼휴리스틱 / 동적 (F)JSP (LLM 이전 AHD 전통 + 베이스라인)
| # | Title | Year | Venue | Cit | tag | Rel | Keep | 메모 |
|--|-------|------|-------|----:|-----|----:|------|------|
| 12 | Survey on Genetic Programming & ML for Heuristic Design | 2023 | IEEE TEVC | 131 | H | 5 | Y | **핵심 서베이** |
| 13 | Surrogate-assisted automatic evolving of dispatching rules (multi-obj dynamic FJSP) | 2022 | ESWA | 71 | H | 4 | Y | |
| 14 | Evolving Dispatching Rules for Multi-objective Dynamic FJSP | 2019 | — | 70 | H | 4 | Y | |
| 15 | GP-based hyper-heuristic for dynamic job shop scheduling | 2021 | Computers & OR | 68 | H | 4 | Y | |
| 16 | Improved GP hyper-heuristic for the dynamic flexible job shop | 2024 | J. Manuf. Syst. | 52 | H | 4 | Y | |
| 17 | Efficient Feature Selection for Evolving Job Shop Scheduling Rules | 2017 | IEEE TEVC | 127 | H | 3 | B | 방법 깊이용 |
| 18 | Hyper-Heuristic Coevolution of Machine Assignment & Job Sequencing | 2018 | IEEE Access | 65 | H | 3 | B | |
| 19 | Multi-Tree GP Hyper-Heuristic for Dynamic Flexible Workflow Scheduling | 2024 | IEEE TSMC | 22 | H | 3 | B | |

### C. AGV 스케줄링 (타깃 도메인)
| # | Title | Year | Venue | Cit | tag | Rel | Keep | 메모 |
|--|-------|------|-------|----:|-----|----:|------|------|
| 20 | DRL-based AGVs real-time scheduling with mixed rule | 2020 | Comput. & Ind. Eng. | 231 | A | 5 | Y | **AGV+DRL+룰, 핵심** |
| 21 | A matheuristic for AGV scheduling with battery constraints | 2021 | EJOR | 131 | A | 4 | Y | |
| 22 | Real-Time Scheduling for Flexible Job Shop With AGVs using Multiagent RL | 2025 | IEEE TSMC | 49 | A | 5 | Y | AGV+FJSP+MARL |
| 23 | DRL for dynamic scheduling of energy-efficient AGVs | 2023 | J. Intell. Manuf. | 40 | A | 4 | Y | |
| 24 | Simultaneous Production and AGV Scheduling using Multi-Agent DRL | 2021 | Procedia CIRP | 31 | A | 4 | Y | |
| 25 | Integrated Scheduling of Machines and AGVs in FMS using Dispatching Rules | 2017 | J. Prod. Res. | 26 | A | 4 | Y | **AGV+디스패칭룰(주제에 근접)** |
| 26 | Real-Time Charging Scheduling of AGVs in Cyber-Physical Systems | 2023 | IEEE TII | 28 | A | 3 | B | |
| 27 | Dynamic Integrated Scheduling of Production Equipment and AGV | 2024 | Processes | 22 | A | 3 | B | |
| 28 | Cooperative agent DRL for flexible job shop (with AGV) | 2025 | ESWA | 12 | A | 3 | B | |
| 29 | Optimal Scheduling of AGVs in a Reentrant Blocking Job-shop | 2018 | Procedia CIRP | 22 | A | 3 | B | |
| 30 | Large-scale multi-load AGVs conflict-free scheduling (intelligent e-coordination) | 2024 | — | 1 | A | 3 | B | 최신 AGV |

---

## 🛑 체크포인트 — 당신 승인 필요

- **기본 Keep = 21편** (B 표시 9편은 borderline; 쳐내거나 살리세요).
- 승인하면 Stage 4(Zotero 저장: 새 컬렉션 `agv-llm-heuristic` + OA PDF 자동첨부) → Stage 5(전문 카드) → Stage 6(종합) 진행.

검토 포인트:
1. **Keep 확정**: 위 표에서 빼거나 추가할 것 (예: "B 전부 제외", "12·20·9는 필수")
2. **누락 보강**: 빠진 유명 논문 있으면 알려주세요 (Google Scholar/arXiv 최신은 자동수집에서 일부 누락 가능)
3. **범위(scope) 결정** — 아래 참고
4. 통과 후 archiving 진행 OK?

### 학부 3개월 scope 제안 (참고)
DSevolve 풀시스템(오프라인 QD 포트폴리오 + MAP-Elites + 온라인 핑거프린팅 + look-ahead)은 학부 3개월엔 과함.
- **현실적 안 (권장)**: EoH/ReEvo 스타일의 **간단한 LLM-AHD 루프**로 **AGV 스케줄링용 디스패칭 룰을 생성**, 공개 AGV/FJSP-AGV 벤치마크에서 **고전 AGV 디스패칭 룰 + (가능하면) DRL 베이스라인**과 비교. → 기여: "AHD를 AGV 스케줄링에 적용(거의 첫 시도)".
- **스트레치**: DSevolve식 룰 포트폴리오 + 동적 교란 시 온라인 룰 선택까지.

어떻게 할지 알려주세요. (예: "B 9편 중 17·20·22·25만 남기고 나머지 B 제외, scope는 권장안으로, archiving 진행")
