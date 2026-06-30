# Systematic Novelty Sweep — LLM-AHD × AGV/vehicle 디스패칭
일시: 2026-06-09. 소스: OpenAlex(8 교차쿼리+6 핵심논문 forward citation), Semantic Scholar, arXiv, Google Scholar(web) 다각도. 목적: 컨트리뷰션 확실화.

## 한 줄 결론
**"AGV에 LLM-AHD 적용" / "AGV-aware feature" 헤드라인은 이미 약함**(MRE가 AGV-드론에 battery/congestion 진화룰을 보임 + VRPAgent/LLM-VD/PortAgent/RideAgent가 "LLM×차량" 점령 중). **그러나 "LLM-AHD로 통합 machine+AGV 동적 FJSP 디스패칭(+conflict/congestion 결합)"은 아직 비어 있고**(이건 DRL만 했음), 우리가 짓는 FJSP+AGV 시뮬과 정확히 맞음 → **여기로 좁히면 방어 가능**.

---

## T1. 직접 위협 (LLM-AHD × AGV/vehicle 디스패칭)
| 논문 | 무엇 | AGV 직접성 | 우리와 구분 |
|---|---|---|---|
| **MRE** (Memetic&Reflective AHD, MDPI Appl.Sci. 2025, 10.3390/app15158735) — shortlist #7 | **일반 AHD 방법** 논문; 테스트 3개 중 하나가 **"AGV-드론 스케줄링"**, 진화룰이 urgency·**battery·congestion** bidding | ★높음(데모) | MRE는 *방법*+AGV-드론 *coordination(bidding)* 데모. 우리는 **machine-coupled FJSP의 multi-AGV 디스패칭**(드론X, bidding X, FJSP 통합 O) |
| **PortAgent** (arXiv:2512.14417, 2025) | 항만 컨테이너터미널 VDS 자동설계(에이전트 codegen) | 높음(항만 AGV) | 항만≠FMS, agentic codegen≠진화 |
| **LLM-VD** (Transp.Res.E 2026, 10.1016/j.tre.2026.104760) | **vehicle-drone 협조 라우팅** AHD | 중(라우팅) | 라우팅≠동적 FJSP 디스패칭 |
| **VRPAgent** (arXiv:2510.07073, ai4co/KAIST Park) | 정적 VRP(CVRP/VRPTW)용 LLM 연산자+GA, "VRP SOTA 최초" | 중 | 정적 VRP 연산자≠동적 AGV-FMS 룰 |
| **RideAgent** (arXiv:2505.06608) | 전기 택시 fleet MIP 목적함수 자동화+variable fixing | 낮(MoD) | MIP 가이드≠디스패칭 룰 진화 |

## T2. 방법 계보 (LLM-AHD × 기계 스케줄링) — 두터움
FunSearch→EoH→ReEvo→HSEvo→QUBE→MCTS-AHD→**DSevolve·EvoDR·SeEvo/AutoProg·LLM4DRD**(머신숍) + 신규: **LLM4EO**(arXiv:2511.16485, FJSP 진화연산자), **CALM**(arXiv:2505.12285), **PathWise**(arXiv:2601.20539), "End-to-End JSS scheme generation". → **전부 기계 스케줄링, AGV 운반 결합 없음**.

## T3. AGV 도메인 (LLM 아님) — 베이스라인
DRL/MARL AGV(#20/#22/#24), **D3QN green-FJSP+AGV 운반**(ScienceDirect S2210650225003384, 복합 디스패칭룰 DRL 학습), conflict-free routing(GA/CP/MIP, 다수), digital-twin+DRL(#36). → AGV+FJSP를 **DRL**은 하지만 **LLM-AHD는 안 함**.

## 열린 틈 (검색상 미점유)
- **N1 ★권장**: **LLM-AHD로 통합 machine+AGV 동적 FJSP 디스패칭 룰(공동: 기계 시퀀싱+AGV 운반 할당)** — DRL(D3QN green-FJSP-AGV)만 했고, 머신숍 AHD(DSevolve/EvoDR)는 AGV 운반 미포함, MRE는 AGV-드론 coordination(FJSP 통합X). **결합이 빈칸.** 우리 시뮬(FJSP+AGV)과 일치.
- **N2**: **conflict-free routing / 경로혼잡을 인지하는 AGV 디스패칭 룰의 LLM-AHD** — conflict-free는 GA/CP/MIP/DRL만, LLM-AHD 미적용. N1의 feature로 흡수 가능.

## 컨트리뷰션 재정의 (확실화)
- ✗ 버릴 헤드라인: "AGV에 LLM 최초", "AGV-aware feature가 신규"(MRE가 반례).
- ✓ **권장 헤드라인(N1)**: *"LLM-Evolved Interpretable Dispatching Rules for **Integrated Machine-and-AGV Dynamic Flexible Job-Shop Scheduling**"* — 기계 스케줄링 AHD(운반 무시)와 AGV-coordination AHD(MRE, FJSP 무시) **사이의 빈칸**을 메움 + conflict/congestion/battery 인지(N2) + 해석성·전이성을 DRL(D3QN/MARL) 대비 입증.
- 신규성 기둥(수정): ① **machine-AGV 결합 룰**을 LLM이 동시 진화(기존 AHD는 한쪽만), ② 동적 교란 하 해석가능 룰 + 전이성, ③ AGV-FMS 베이스라인(D3QN/MARL/GP/고전룰) 대비 체계적 비교.
- 차별 표(본문용): MRE(AGV-드론 coordination·bidding), VRPAgent/LLM-VD(라우팅), PortAgent(항만 codegen), DSevolve/EvoDR(기계 only), D3QN(DRL·해석성↓) — 우리=**FJSP+AGV 통합·진화·해석가능·전이**.

## 잔여 리스크 / 투고 전 필수
- 공간이 **매우 빠르게 차는 중**(2025–2026 집중). N1이 비었음을 **투고 직전 재확인**: forward citations of MRE·DSevolve·EvoDR·VRPAgent + arXiv cs.RO/cs.AI 최신 listing.
- MRE 전문 확보(현재 MDPI 봇 차단·OA초록만) → 수동 다운로드 목록에 포함(정확한 차별 위해 본문 필요).
- HUST(Gao/Li)·ai4co(KAIST Park)가 N1을 먼저 낼 위험 최상 → **속도(KIIE 선점)**.

## 출처(주요)
- MRE https://www.mdpi.com/2076-3417/15/15/8735 · PortAgent https://arxiv.org/abs/2512.14417 · LLM-VD https://doi.org/10.1016/j.tre.2026.104760 · VRPAgent https://arxiv.org/abs/2510.07073 (코드 https://github.com/ai4co/vrpagent) · RideAgent https://arxiv.org/abs/2505.06608
- LLM4EO https://arxiv.org/abs/2511.16485 · CALM https://arxiv.org/abs/2505.12285 · PathWise https://arxiv.org/abs/2601.20539
- D3QN green-FJSP+AGV https://www.sciencedirect.com/science/article/abs/pii/S2210650225003384
