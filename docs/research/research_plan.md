# 연구 마스터 플랜 — LLM 진화 joint 디스패칭 룰 (통합 기계+AGV 동적 FJSP)
작성 2026-06-09. 이 문서가 마스터. 세부는 `novelty_sweep.md`, `contribution.md §8`, `simulator_spec.md`, `lab_research_flows.md`, `proposal_kiie.md` 참조.

## 0. 한눈에
- **주제**: 동적 유연 잡샵(FJSP)에서 **기계 시퀀싱 + AGV 디스패칭**을 LLM-AHD로 **동시(joint) 진화**해 해석가능·전이가능 규칙을 자동 생성.
- **제목(확정)**: *LLM-Evolved Interpretable Joint Dispatching Rules for Integrated Machine-and-AGV Dynamic Flexible Job-Shop Scheduling.*
- **타깃**: 대한산업공학회(KIIE) 학술대회 → SCIE 저널.
- **상태**: framing 확정(B+N1). 시뮬 v0(joint) 구축·검증 완료. 다음=LLM-AHD 루프.

## 1. 문제정의
동적 FJSP+AGV: 기계 M대, AGV K대, 작업(job) 동적 도착. job=연산 시퀀스(적격기계·처리시간). 연산 간 운반은 AGV가 수행. 교란: 신규 작업 도착(+v1: AGV 고장, 배터리 충전).
- **결정 2종**: (i) 기계가 큐에서 다음 작업 선택(시퀀싱), (ii) 유휴 AGV에 운반태스크 할당(디스패칭). 둘은 상호작용.
- **목적**: 평균 tardiness(주), makespan·throughput·flowtime, (v1) 에너지.

## 2. 컨트리뷰션 (N1) — 상세 `contribution.md §8`
기존 LLM-AHD는 **기계만**(DSevolve/EvoDR/SeEvo) 또는 **차량만**(MRE=AGV-드론, VRPAgent/LLM-VD=routing, PortAgent=항만) 진화. **기계+AGV를 동시 진화한 LLM-AHD는 없음**(통합은 DRL D3QN뿐, 비해석). 
**신규성 3기둥**: ① joint 동시 진화(상호작용 명시), ② 해석가능 + 미관측 환경 전이, ③ AGV-FMS 베이스라인(고전 joint·GP·DRL/D3QN·머신숍-only AHD) 대비 체계 비교.


- **RQ3 (해석성·전이)**: 진화 규칙이 해석가능하고, 미관측 layout/fleet/부하로 zero-shot 전이되는가? DRL 대비 전이 우위?
- **RQ4 (regime)**: 어떤 조건(운반병목 vs 기계병목, 교란강도)에서 LLM-AHD가 가장 유리한가?

## 4. 제안 방법 — 상세 `proposal_kiie.md §3`
EoH/ReEvo식 진화 루프에서 **두 scoring 규칙 쌍**(machine_policy, agv_policy)을 동시 생성·평가. LLM=crossover/mutation 연산자 + reflection. (선택) seed=고전 규칙. 적합도=훈련 인스턴스의 평균 tardiness. 온라인 배치=해석가능 규칙 ms 실행. 인터페이스·검증: `sim/joint_demo.py`.

## 5. 실험 설계 ★

### 5.1 환경·인스턴스
- 시뮬: `sim/`(순수 파이썬 DES, 검증됨). 문제정의는 #22/#24/#25(FJSP+AGV)에 앵커.
- **Regime(핵심)**: 단일 고전룰이 지배 못하게 다양화.
  - R1 운반병목(많은 job/적은 AGV, 큰 layout), R2 기계병목(적은 기계/긴 proc), R3 균형, R4 고교란(높은 도착율·고장).
- 파라미터: M∈{6,10,16}, K∈{2,3,4,6}, 도착율 λ, ops 2–6, proc, due tightness, layout grid, (v1)배터리·고장율.
- **훈련/검증/시험 분리**(과적합 방지): 규칙은 훈련 인스턴스로 진화, 검증으로 선택, **시험 인스턴스로만 최종 보고**.
- 반복: regime·config당 **≥30 seed**.

### 5.2 비교 방법
| # | 방법 | 기계규칙 | AGV규칙 | 역할 |
|---|---|---|---|---|
| B1 | 고전 joint(최우수 조합) | EDD/SPT/FIFO/LWR | NV/STT/MOQS/LQS | 하한 베이스라인 |
| B2 | GP 하이퍼휴리스틱(DEAP) | 진화 | 진화 | 전통 AHD 비교 |
| B3 | DRL/MARL(PPO) | 학습 | 학습 | 학습기반 비교 |
| B4 | D3QN green-FJSP+AGV류 | 학습(통합) | 학습(통합) | **통합 DRL**(해석성 약점 대비) |
| B5 | 머신숍-only LLM-AHD(EoH/ReEvo) | 진화 | 고정(NV) | **joint 필요성 입증** |
| B6 | AGV-only LLM-AHD | 고정(EDD) | 진화 | ablation |
| **P** | **제안 joint LLM-AHD** | **진화** | **진화** | 본 연구 |

### 5.3 지표
| 범주 | 지표 |
|---|---|
| 성능 | 평균 tardiness(주), makespan, throughput, mean flowtime |
| AGV | 가동률, deadhead 비율, (v1)에너지 |
| 해석성 | 규칙 복잡도(길이/항 수), 사람 가독성(정성) |
| 전이 | 미관측 환경 성능 저하폭(train→unseen) |
| 비용 | LLM 호출 수·토큰, 진화 시간 |

### 5.4 Ablation (RQ2/RQ3)
joint vs AGV-only vs machine-only / feature on-off(congestion·deadhead·downstream·slack) / reflection on-off / population·budget 민감도 / seed(고전 규칙) on-off.

### 5.5 전이·일반화 (RQ3)
규칙을 config A로 진화 → **미관측** B(다른 M·K·부하·layout)에서 zero-shot 평가. 제안 규칙 vs DRL의 전이 저하폭 비교(DRL이 더 크게 저하될 것이라는 가설).

### 5.6 Regime 분석 (RQ4)
운반병목↔기계병목, 교란강도 sweep → 각 방법의 우위 영역 히트맵. "언제·왜 LLM-AHD가 이기나" 서술.

### 5.7 통계·재현 프로토콜
≥30 seed, 평균±표준편차, **유의성검정**(Wilcoxon signed-rank / Friedman + posthoc Nemenyi), 효과크기. **오픈소스**(시뮬·인스턴스·진화규칙·프롬프트·seed) 공개.

### 5.8 LLM-AHD 셋업
모델=저비용(GPT-4o-mini/DeepSeek-V3 등). EoH(thought+code)/ReEvo(reflection) 프롬프트. population·generation·budget 명시. 공정성: 모든 방법 동일 시뮬·동일 feature 인터페이스·동일 평가예산.

## 6. 신뢰성(자체 시뮬 방어)
문헌 문제 앵커 + 오픈소스 + 다중 regime + 고전룰 순위가 문헌과 일치 검증(이미 PASS) + train/test 분리. (상세 `simulator_spec.md §0`)

## 7. 단계 계획
- **KIIE (≈3개월)**: [완료] v0 joint 시뮬·고전 baseline. → GP(DEAP) baseline + **LLM-AHD joint 루프(기본)** + R1·R3 두 regime 비교 + 해석성 예시 → 초록/발표.
- **SCIE (+3~6개월)**: 교란·배터리, 4 regime, 전이, DRL/D3QN baseline, 전체 ablation, 통계, 다목적 → 저널(C&IE/ESWA/JIM/RCIM/IEEE T-ASE).
- **마일스톤**: M1 LLM-AHD 루프 동작(키 연결) → M2 baseline 셋(GP·DRL) → M3 regime/전이/ablation → M4 집필.

## 8. 리스크 / 완화
- novelty 잠식(공간 빠름) → KIIE 선점 + 투고 직전 sweep(`novelty_sweep §잔여리스크`).
- 자체 시뮬 신뢰성 → §6.
- LLM 비용/변동성 → 저비용 모델·예산상한·seed 반복.
- AHD가 안 이김 → regime 설계로 "언제 이기나"를 기여로(RQ4) + 해석성/전이(RQ3)로 가치 확보.
- DRL baseline 재현 난이도 → 공개구현/D3QN 논문 설정 차용.

## 9. 산출물·진행 인덱스
- 계획/포지셔닝: 이 문서, `contribution.md`, `proposal_kiie.md`, `novelty_sweep.md`, `lab_research_flows.md`, `leading_labs.md`, `manual_download_list.md`, `STATUS.md`.
- 코드: `sim/`(DES+baseline+joint+AHD 하네스, 검증), `scripts/`(수집·아카이빙·PDF).
- 데이터: Zotero 컬렉션 `agv-llm-heuristic`(40편), `candidates/filtered/selected(+new)`, `cards/`.
- 남은 빌드: LLM-AHD 진화 루프(LLM 키/모델), v1 교란·전이 config, GP·DRL baseline.
