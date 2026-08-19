# 시뮬레이터 설계 명세 — 동적 AGV-FMS 디스패칭 (자체 구축, AI 구현)
framing: B(일반 AGV-FMS) 확정 | 환경: 자체 이산사건 시뮬(DES) | 용도: AGV-aware AHD의 적합도 평가 + 모든 베이스라인 공통 실행

> 기본값은 [기본]으로 표기(필요시 변경). v0=KIIE 프로토타입, v1=SCIE 확장.

## 0. SCIE 신뢰성 장치 (필수)
자체 시뮬의 약점을 다음으로 방어:
1. **문헌 표준 문제에 앵커**: 동적 FJSP+AGV 정의를 #22/#24/#25 설정에 맞춤(임의 문제 금지) → 인용 가능.
2. **오픈소스 + seed 고정 + config 파일**: 인스턴스/난수 재현.
3. **다중 config**(layout·fleet·부하·교란율) + 반복실험 통계(평균±표준편차, 유의성).
4. **검증**: 고전 디스패칭 룰들의 상대 순위가 문헌 경향과 일치하는지 확인(시뮬 타당성 sanity check).
5. **공정비교**: 제안법·고전룰·GP·DRL·머신숍AHD를 **동일 시뮬**에서 비교(절대값 교차비교 대신 내부 공정비교).

## 1. 문제 정의 [기본: 단순화 동적 FJSP+AGV]
- 기계 M대(워크스테이션), AGV K대, 작업(job) 동적 도착.
- 각 job = 연산(operation) 시퀀스; 각 연산은 적격기계 집합 + 처리시간.
- 연속 연산 사이에 **운반 태스크**(기계A→기계B) 발생 → AGV가 수행.
- **결정대상(N1 핵심)**: **joint = 기계 시퀀싱 + AGV 디스패칭** 두 규칙을 동시 진화. 시뮬 지원·검증됨(`simulate(..., machine_policy=)`, `sim/joint_demo.py`). machine_policy=None이면 기계 EDD 고정(하위호환 v0).
- 목적: **평균 tardiness(주)**, makespan, throughput, (v1)에너지.

## 2. 엔티티
- **Layout**: 노드 그래프 또는 그리드 + 거리/이동시간. [기본] 그리드, Manhattan 거리, 등속.
- **Machine**: 처리 중/대기큐, 고장 가능.
- **Job/Operation**: 도착시각, 납기, 연산열(적격기계·처리시간).
- **TransportTask**: (pickup 기계, dropoff 기계, ready 시각, 연결 job 납기).
- **AGV**: 위치, 상태(idle/이동/적재), 속도, (옵션)배터리 SOC·용량, capacity=1.

## 3. DES 엔진
- 이벤트 큐(heap): job도착, 연산완료, AGV-pickup도착, AGV-dropoff도착, 기계고장/복구, (옵션)배터리임계.
- **결정 시점**: AGV가 idle이 되거나 새 운반태스크가 ready일 때 → 디스패칭 정책 호출.
- [기본] SimPy 또는 경량 자체 heap 루프. 순수 Python, 외부의존 최소.

## 4. 정책 인터페이스 (★ 모든 방법이 공유 — AHD의 진화 대상)
```python
def policy(features: dict) -> float:
    # 후보 (idle AGV, ready task) 쌍마다 호출, priority 점수 반환.
    # 디스패처는 최고점수 쌍을 매칭. 이 함수 '본문'을 LLM-AHD/GP가 진화.
    return score
```
- **feature set (AGV-aware terminals)** [기본]:
  `travel_time`(AGV→pickup), `task_wait`(현재-ready), `slack`(납기-현재-예상소요), `downstream_load`(dropoff 기계 큐), `congestion`(주변 ready태스크·AGV 수), `deadhead_ratio`, (옵션)`battery_soc`.
- 고전 룰도 이 인터페이스로 표현(NV=-travel_time, STT=-travel_time, EDD=-slack, FIFO=-task_wait 등) → 공정비교.

## 5. 교란(stochastic)
- 신규 job 도착: Poisson(λ). AGV 고장: 확률/MTBF. (옵션)배터리 소진→충전소 이동.
- config로 교란 강도 조절(Easy/Med/Hard).

## 6. 지표
makespan · 평균 tardiness · throughput · AGV 가동률 · deadhead 비율 · (v1)에너지(이동거리 proxy).

## 7. config/인스턴스
layout 크기 · M · K(fleet) · λ(도착) · 고장율 · (옵션)배터리 · seed. **전이테스트**: config A로 룰 진화 → 미관측 config B(다른 fleet/layout)에서 평가.

## 8. 베이스라인(정책으로 구현)
고전: NV, STT/D, EDD, FIFO, MOQS. + GP(DEAP, 동일 terminal). + DRL/MARL(PPO, 동일 상태). + 머신숍AHD 포팅(EoH/ReEvo, 기계전용 feature만).

## 9. 구현 단계
- **v0 (KIIE)**: 위 [기본] 구성(배터리 off, 기계시퀀싱 고정) + 고전룰 + EoH/ReEvo 최소 연결 → 동작·비교 확인.
- **v1 (SCIE)**: 배터리·충전, 다중 config 전이, GP·DRL 베이스라인, 머신숍AHD 포팅, ablation, 다목적.

## 10. 파일 배치(예정)
`research-agent/sim/` (엔진·엔티티·정책 인터페이스·config), `research-agent/baselines/`(고전룰), 평가 스크립트. (AHD 루프는 별도)
