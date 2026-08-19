# 실험 노트

**한 실험 = 한 폴더.** 이름은 `NNN-YYMMDD-<슬러그>` (NNN = 실행 순서, YYMMDD = 실행일).
그 실험의 스크립트·결과 JSON·그림·보고서가 전부 그 폴더 안에 있다.
폴더를 새로 만드는 규칙과 파일 이름 규약은 `docs/experiment_protocol.md` §5.

같은 날 같은 계열의 후속 실행은 새 폴더가 아니라 **같은 폴더의 새 파일**이다
(`run_nohint.py`, `result_full_resumed2.json`, `report-b-….md`).

| # | 폴더 | 물은 것 | 답 | 상태 |
|---|---|---|---|---|
| 000 | `000-260724-llm-rule-campaign` | LLM이 진화시킨 배차 규칙이 문헌 손규칙 D1/D2를 이기나 | pop70에서는 이겼다. 그런데 003이 이 결론을 무효화했다 | RETIRED |
| 001 | `001-260729-literature-gap` | 문헌 최고기록과 우리 격차가 실제로 얼마인가 | 65%. 병목은 AGV 배차가 아니라 **기계 선택** | 유효 |
| 002 | `002-260731-budget-and-population-diagnosis` | 그 격차가 예산 문제인가 구조 문제인가 | 둘 다 아니었다. **population 크기**였다 (94.5% → 24.1%) | RETIRED |
| 003 | `003-260801-ga-tuning-and-rule-retest` | population을 제대로 맞추면 무엇이 남나 | population은 U자 곡선이고, **튜닝된 solver에서는 규칙 우위가 사라진다** | RETIRED |
| 004 | `004-260806-rule-effect-vs-budget` | 규칙은 저예산일수록 중요한가 | 아니다. **훈련된 체제에서만** 유리하다 | RETIRED |
| 005 | `005-260807-constructive-baseline` | 탐색 없는 4슬롯 구성형 기준선은 얼마나 가나 | 예상보다 훨씬 강하다 | 유효 |
| 006 | `006-260810-slot-expansion-and-lns-gate` | 슬롯을 5개로 늘리고 solver를 LNS로 바꿀까 | 확장은 통과, **LNS는 게이트에서 기각** | RETIRED |
| 007 | `007-260813-bundle-evolution` | 4슬롯을 문헌 규모 예산(65세대)으로 동시 진화시키면 | held-out 45.2%, 손규칙 전부 이김. **41~65세대에서 과적합** | 유효 |

`RETIRED` = GA/LNS 시대 실험. 스크립트가 `archive/ga-era/`의 공용 모듈에 의존해 지금은 돌지 않는다.
코드는 그때 돌린 그대로 두었다. 수치는 `tests/test_reported_numbers.py`가 계속 지킨다.

## 공용 파일

| 파일 | 무엇 |
|---|---|
| `common.py` | 문헌 기준값·격차·짝지은 검정·프로토콜 상수·병렬 러너. **실험마다 다시 쓰지 않는다** |
| `plots.py` | 간트차트·수렴곡선·격차 막대. 기본 출력은 실행한 폴더의 `figures/` |

## 새 실험을 시작할 때

```
mkdir experiments/008-YYMMDD-<슬러그>
```
스크립트는 `run.py`, 결과는 `result.json`, 보고서는 `report.md`.
끝나면 `python -m tests.run_all` (게이트 5종) 통과를 확인한다.
