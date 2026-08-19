# 보고서 — FunSearch OSS의 evaluator/skeleton/데이터로 데모 교체 + Table 1 재현

작성 2026-07-04. 저장소: github.com/google-deepmind/funsearch (`bin_packing/bin_packing.ipynb`).

## 결론 (한눈에)
- FunSearch OSS를 **직접 다운로드**해서, 우리 데모의 자체 evaluator/skeleton/데이터를 **그들의 실제 코드·데이터로 교체**했다.
- 그 결과 우리 harness가 **FunSearch의 발표 수치(논문 Table 1)를 소수점까지 재현**한다: Best-Fit OR3=**5.37%**·Weibull5k=**3.98%**, FunSearch OR-discovered OR3=**3.11%**, FunSearch Weibull-discovered Weibull5k=**0.68%** — 모두 Table 1과 일치. → **우리 평가 파이프라인이 논문과 동일함이 검증됨.**
- 부수 확인: 그들의 discovered 규칙조차 **분포 특이적** — Weibull 규칙을 OR3에 쓰면 12.77%(Best-Fit보다 나쁨), OR 규칙을 Weibull에 쓰면 3.03%.

## 무엇을 했나 (6하: 무엇/어떻게)
1. `git clone google-deepmind/funsearch` → `bin_packing/bin_packing.ipynb`의 코드 셀 추출.
2. **evaluator/skeleton 교체** (verbatim 이식) into `demo/bpp.py`:
   - `get_valid_bin_indices`, `online_binpack`, `evaluate` — 그들 코드 그대로.
   - 진화 대상 `priority(item, bins)` 초기값 = **Best-Fit + 논문 docstring**(그들의 seed).
   - 그들의 **discovered 규칙**(OR용 step-function, Weibull용 max_bin_cap 식) 두 개를 verbatim baseline으로.
3. **데이터 교체**: 그들의 실제 **OR3·Weibull 5k 인스턴스 + L1 하한(opt_num_bins)** 를 `demo/funsearch_data.json`로 추출(CC-BY, 출처 명기).
4. **프롬프트 교체**: LLM에 우리 산문이 아니라 **실제 skeleton(get_valid_bin_indices/online_binpack/priority-docstring)** 을 보여주고 `priority`만 재작성하게.

## 이전 우리 자체 구현 대비 무엇이 달랐나 (왜 교체가 필요했나)
| 항목 | 우리 이전 자체판 | FunSearch 실제(교체 후) |
|---|---|---|
| 빈 bin 후보 | 신선 bin **1개**만 후보 | `[capacity]*num_items` **사전할당**(빈 bin 다수) — Weibull 규칙의 `max(bins)`·`score[1:]-=score[:-1]` 가 이 구조에 의존 |
| 초기 skeleton | docstring 없음, 산문 프롬프트 | 논문 docstring + 실제 골격 노출 |
| 데이터 | 우리 정규화[0,1] Weibull(자작) | 그들 실제 OR3(정수 용량150)/Weibull5k(용량100) |
| 하한/메트릭 | 연속 sum/cap | 그들 **opt_num_bins**(L1) 그대로 |
| 스케일 | [0,1] | 정수 용량(그들 규칙이 native로 동작) |

→ 특히 **스케일·빈-bin 구조** 차이로, 이전엔 그들 규칙이 우리 harness에서 misfire(예: Fig-6가 5.49%)했음. 교체 후엔 그들 규칙이 native 수치(0.68% 등)를 정확히 냄.

## 결과 (그들 evaluator + 그들 데이터, 초과율 %)
| heuristic | OR3 | Weibull 5k |
|---|---|---|
| Best-Fit (seed) | 5.37% | 3.98% |
| Worst-Fit | 148.51% | 151.53% |
| FunSearch OR-discovered | **3.11%** | 3.03% |
| FunSearch Weibull-discovered | 12.77% | **0.68%** |

논문 Table 1: Best-Fit OR3 5.37 / Weibull 3.98; FunSearch OR3 3.11 / Weibull 0.68 → **완전 일치.**

## 의미 / 다음
- 이제 **우리 실험 harness가 FunSearch와 동일**함이 검증됨. 이 위에서 우리 LLM 루프(claude CLI)를 돌리면 **공정한(같은 평가기) 비교**가 됨.
- **다음(선택)**: `DEMO_EVOLVE=1 DEMO_MODEL=sonnet python -m demo.bpp` — 그들 evaluator 위에서 우리 LLM이 OR3의 `priority`를 Best-Fit에서 진화(train12/valid4/test4)시켜 Best-Fit(OR3 5.37%)을 넘는지 확인. (LLM 비용 발생)
- 이 데모가 강한 이유: 단순 재구현이 아니라 **원 저장소의 evaluator/데이터로 우리 파이프라인을 검증**했고 발표 수치를 재현함.

## 관련 파일
- `demo/bpp.py`(FunSearch 실제 evaluator/skeleton 이식), `demo/funsearch_data.json`(그들 OR3/Weibull5k 데이터, CC-BY).
- 원본: github.com/google-deepmind/funsearch, 논문 `demo/02. Mathematical discoveries ...pdf`.
- 이전 단계 기록: `docs/reports/2026-07-02-funsearch-obp-demo.md`(자체 evaluator판·수정·Fig6 비교).
