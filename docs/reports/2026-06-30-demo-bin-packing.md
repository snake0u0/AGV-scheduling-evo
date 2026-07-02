# 보고서 — LLM-AHD 데모: Online Bin Packing (쉬운 벤치마크)

작성 2026-06-30. (교수님 요청: 쉬운 문제로 LLM 기반 진화 탐색 방법론 데모)

## 결론 (한눈에)
- **방법론이 표준 쉬운 벤치마크(Online Bin Packing, FunSearch/EoH 정석 문제)에서 end-to-end로 작동**함을 데모로 보였다: LLM이 scoring 표현식을 제안 → 평가 → fitness+reflection 진화 → train/valid/test 분리로 보고. AGV 프로젝트의 기계(`policy_from_expr`, `ClaudeCliLLM`)를 그대로 재사용.
- **LLM이 비자명·해석가능 규칙을 자율 발견**: Weibull판에서 모듈러/양자화 규칙(잔여용량을 1/8·1/3에 정렬 — FunSearch 계열 insight)을 찾아 **train에선 Best-Fit을 이김**.
- **단, held-out test에선 두 설정 모두 Best-Fit과 tie**(작은 인스턴스·예산 탓; 강건히 이기려면 FunSearch급 스케일 필요). 데모 목적엔 충분. 상세는 아래 두 실행(균등/Weibull).

## 처음 목적 / 왜
- 교수님이 "쉬운 문제 데모"를 요청. 목적은 SOTA가 아니라 **방법론이 표준 문제에 이식되어 돈다**는 것을 보이는 것. OBP는 LLM-AHD의 정석 데모(FunSearch 대표 예제)라 방어가 쉽다.

## 무엇을 어떻게 했나 (`demo/bpp.py`)
- **문제**: 온라인 빈패킹(용량 1.0). 아이템이 순차 도착 → 열린 bin마다 `score(item, remaining, capacity, num_bins)` → 최고점 feasible bin에 배치, 없으면 새 bin. 목적=최소 bin 수.
- **재사용**: `sim.rule.policy_from_expr`(표현식 컴파일), `ahd.llm.ClaudeCliLLM`(claude CLI proposer)+`_valid`/`_extract_json`. 진화 루프·seed·ReEvo식 reflection 프롬프트는 OBP용으로 축약.
- **baseline**: Best-Fit(`-remaining`), Worst-Fit(`remaining`). **분리**: 12 train / 4 valid / 4 test 인스턴스. budget: 6세대·pop 12.

## 결과 (test bins/LB, 낮을수록 좋음)
| 방법 | bins/LB |
|---|---|
| Best-Fit | 1.0727 |
| Worst-Fit | 1.1952 |
| LLM-진화 `(item-0.4)*remaining` | 1.0778 (−0.5% vs BF) |

sanity: Best-Fit < Worst-Fit(정상). LLM=6콜, fails=0, ~$1.10.

## 왜 Best-Fit을 못 이겼나 (정직)
1. **균등분포[0.10–0.70]에선 Best-Fit이 거의 최적** → 개선 여지 작음. FunSearch가 이긴 건 **Weibull 분포**(작은 아이템 다수, bin당 여러 개 → 조합 여지 큼) 설정.
2. **작은 예산**(6세대·12 train) — FunSearch는 수천 평가.
3. 진화 규칙이 train에선 앞섰으나(1.0792) test 일반화 부족(약간 과적합).

## Weibull 업그레이드 (2차 실행)
`gen_items`를 **Weibull 분포**(FunSearch식)로 바꾸고 16 train·10세대로 확대해 재실행:

| 방법 | bins/LB (test) |
|---|---|
| Best-Fit | 1.0451 |
| LLM (train-best) | **1.0433** (train에선 이김) |
| LLM (valid 선택 → test) | 1.0451 (**+0.0%, tie**) |

- **주목할 발견**: LLM이 `-abs((remaining-item) % (0.125*capacity)) - 0.5*abs((remaining-item) % (0.3333*capacity))` 같은 **모듈러/양자화 규칙**을 자율 발견 — 잔여용량을 bin 분수(1/8, 1/3)에 정렬. **FunSearch가 보고한 것과 같은 계열의 구조적 insight.** (10콜, fails=0, ~$2.1)
- 그러나 train(1.0433)→test(1.0451) **일반화 격차**: valid/test 인스턴스가 4개뿐이라 선택이 노이지 + Best-Fit이 강해 test에서 tie.

## 정직한 결론 + 개선안
- **데모로서 성공**: 방법론이 표준 문제에서 작동하고, **비자명·해석가능 규칙을 자율 발견**하며, train에선 Best-Fit을 이김. held-out test는 tie(작은 인스턴스·예산 탓).
- 강건히 이기려면(FunSearch급): **valid/test 인스턴스 대폭 확대**(안정적 선택) + 예산(세대·pop) 확대 + 다중 반복. 이건 compute 무거움 → 데모 목적엔 현재로 충분, 필요시 스케일업.

## 관련 파일
- 코드: `demo/bpp.py` (자체완결). 실행: `python -m demo.bpp` (claude 자동, `DEMO_LLM=0`=mock).
- 재사용: `sim/rule.py`, `ahd/llm.py`.
