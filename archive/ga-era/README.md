# archive/ga-era

GA/LNS 시대의 코드와 캠페인 스크립트. **은퇴했지만 기록으로 보존**한다.

## 왜 여기로 왔나

2026-08-12에 방법이 **구성형(constructive) 4슬롯 진화**로 확정되면서, 해 수준 탐색
(GA, LNS)을 쓰지 않게 됐다. 여기 있는 것들은 그 이전 방식의 자산이다.

- **GA**: 규칙 하나(vehicle_select)만 진화시키고 나머지 3개 하위문제는 염색체가 결정.
  튜닝된 GA가 규칙 변화를 1~2%p로 흡수한다는 것이 측정됐다(2026-08-01b).
- **LNS**: 2026-08-10 게이트에서 기각(수용률 0.002%, 8,109회 시도에 개선 0회).

## 무엇이 있나

| 파일 | 무엇 |
|---|---|
| `ga.py` | 유전 알고리즘 (POX/uniform-MS/mutate-OS) |
| `evaluator.py` | (OS, MS, rule) -> Solution 디코딩 |
| `lns.py` | Large Neighbourhood Search (기각됨) |
| `llm_single_rule.py` | 단일 규칙 proposer (`model/llm.py`에서 분리) |
| `replay.py` | Dauzere 계열 replay. 해 파일 헤더가 54/54 불일치라 사용 불가 |
| `test_ga_operators.py`, `test_decode_selfcheck.py` | 위 코드들의 게이트 |
| `2026-*.py` (11개) | 위 코드를 쓰던 캠페인 스크립트 |

## 되살리려면

`ga.py`/`evaluator.py`는 `simulator/`의 현재 코드에 의존하는데, `simulator/`는
그 뒤로 바뀌지 않았으므로 그대로 import 경로만 되돌리면 동작한다.
단, **최종 논문 표에 GA 베이스라인 행이 필요하면 전체를 되살리지 말고
`experiments/plots.py`에 비교용 코드를 따로 쓰는 쪽**이 프로젝트 방침이다.

각 실험의 결과 JSON은 여기가 아니라 `data/results/`에 그대로 있고,
`tests/test_reported_numbers.py`가 그 수치들을 계속 지킨다.
