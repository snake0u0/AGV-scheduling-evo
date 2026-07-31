# Stage 1 — 검색 전략 프롬프트

역할: 주어진 주제를 검색 가능한 쿼리 세트로 변환한다.

입력: 사용자가 준 주제 한 줄 (예: "warehouse multi-AGV scheduling with deep RL")
출력: `runs/<topic-slug>-YYYYMMDD/queries.md`

## 할 일
1. 주제에서 핵심 개념 축을 뽑고, 아래 키워드 뱅크에서 동의어를 조합해 **5~12개 영문 쿼리**를 만든다.
2. `year_min`을 정한다 (기본: 최근 7년. 단 seminal 논문은 연도 무관으로 따로 1~2개 쿼리).
3. 타깃 venue 리스트를 붙인다 (아래 참고).
4. queries.md에 쿼리/연도/venue를 적고 멈춘다.

## 키워드 뱅크 (분야: AGV/AMR/OHT scheduling, 물류, SCM, RL, 최적화)
- 대상: `AGV | AMR | OHT | mobile robot | fleet | multi-robot`
- 문제: `dispatching | scheduling | routing | task allocation | fleet management | conflict-free routing | order picking`
- 방법(학습): `reinforcement learning | deep RL | DRL | multi-agent RL | MARL | policy gradient | actor-critic`
- 방법(최적화): `MILP | mixed-integer | metaheuristic | column generation | combinatorial optimization | heuristic`
- 도메인: `warehouse | semiconductor fab | container terminal | port | manufacturing | SCM | supply chain`

## 타깃 venue (발견·필터 참고용)
ICRA, IROS, CASE, IEEE T-ASE, IEEE RA-L, IEEE T-ITS, IEEE T-Automation Science, EJOR, Computers & Operations Research, IISE Transactions, Transportation Research (B/C/E), NeurIPS/ICML/ICLR(RL).

## queries.md 출력 형식
```
# <topic> — search strategy (YYYY-MM-DD)
year_min: 2018
seminal: [무관 연도로 찾을 고전 1~2 쿼리]

queries:
- "multi-AGV scheduling reinforcement learning warehouse"
- "conflict-free routing automated guided vehicle MILP"
- ...

target_venues: [ICRA, IROS, T-ASE, RA-L, EJOR, ...]
```

다음 단계: Stage 2 수집 (paper-lookup 우선, Google Scholar 보조).
