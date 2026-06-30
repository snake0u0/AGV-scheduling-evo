# sim/ — 동적 FJSP+AGV 시뮬레이터 (v0)

순수 파이썬 이산사건(DES) 시뮬레이터. 동적 FJSP+AGV 디스패칭 연구용. 외부 의존 없음.

## 실행
```
cd research-agent
python sim/run_eval.py     # 고전 룰 6종 × 2 config × 10 seed 비교 + sanity check
python sim/ahd_stub.py     # AHD 평가 하네스: 후보 룰 표현식 랭킹(= LLM-AHD 내부 루프)
```

## 구성
- `agv_fms.py` — DES 엔진. 잡 도착(Poisson)→기계 연산→AGV 운반(L/U·기계간). **AGV 디스패칭 결정**이 핵심.
- `policies.py` — 고전 디스패칭 룰(NV/EDD/FIFO/LQS/COMPOSITE/RANDOM), `policy(features)->score`.
- `rule.py` — 진화된 룰 문자열식 → policy (AHD plug).
- `ahd_stub.py` — 후보 룰 평가·랭킹(LLM 생성으로 교체하면 full AHD 루프).
- `run_eval.py` — 비교 실험 + sanity check.

## 정책 인터페이스 (모든 방법 공유 — AHD 진화 대상)
`policy(features) -> score`, 디스패처가 (idle AGV, ready task) 쌍 중 최고점 매칭.
features: `travel_time, task_wait, slack, downstream_load, congestion, deadhead, battery_soc`.

## v0 검증 결과 (sane)
NV가 RANDOM을 makespan/deadhead에서, EDD가 FIFO를 tardiness에서 이김 → 문헌 직관과 일치.
현재 config는 **운반 병목**이라 NV 우세. AHD가 이기려면 v1에서 **기계병목·교란 혼합 regime** 필요(단일 고전룰이 지배 못하는 영역).

## v1 (SCIE 확장) 예정
배터리·충전, AGV 고장 교란, 다중 layout/fleet 전이 테스트, GP(DEAP)·DRL/MARL·D3QN 베이스라인,
기계+AGV 공동 룰 진화(N1), 다목적, ablation. + LLM-AHD 루프(EoH/ReEvo 연결, `ahd_stub.py` 확장).
