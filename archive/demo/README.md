# demo — FunSearch식 LLM 프로그램 탐색 (Online Bin Packing)

FunSearch(Nature 2024)의 온라인 빈패킹 실험을 **그들의 실제 evaluator/skeleton/데이터**로 재현하고,
그 위에서 **LLM(claude CLI)이 `priority` 함수를 진화**시키는 데모.

## 파일
- `bpp.py` — 데모 전체(평가기·골격·baseline·LLM 진화 루프). FunSearch `bin_packing.ipynb` 코드 이식.
- `funsearch_data.json` — FunSearch 실제 데이터(OR3, Weibull 5k) + L1 하한. 출처: google-deepmind/funsearch (CC-BY).
- 원논문(FunSearch, Nature 2024)은 Zotero `FIPSC9PH`에 있습니다. (중복 사본은 2026-07-23 삭제)

## 실행
```bash
python -m demo.bpp                                              # 비교표 재현 (LLM 없이, 무료)
DEMO_EVOLVE=1 DEMO_MODEL=sonnet DEMO_GEN=10 python -m demo.bpp  # LLM으로 priority 진화 (claude CLI)
DEMO_LLM=0 python -m demo.bpp                                   # mock (LLM 없이 루프만)
```

## 핵심 결과
숫자 = **초과율**(실제 사용한 상자 수가 이론상 최소치보다 몇 % 더 썼는지). **낮을수록 좋음.**
| heuristic | OR3 | Weibull 5k |
|---|---|---|
| Best-Fit | 5.37% | 3.98% |
| FunSearch OR-discovered | 3.11% | 3.03% |
| FunSearch Weibull-discovered | 12.77% | 0.68% |
| Ours: LLM-evolved (Sonnet) | 4.20% | 2.87% |

→ 우리 평가기가 논문 Table 1을 재현하고(검증), 우리 LLM 규칙이 Best-Fit을 능가.

## 발표용 종합 설명
아키텍처·I/O·skeleton·prompt·evaluator·진화된 priority·분산시스템: **`archive/reports/2026-07-04-demo-presentation.md`**
