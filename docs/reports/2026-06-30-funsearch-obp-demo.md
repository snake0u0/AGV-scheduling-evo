# 보고서 — FunSearch식 LLM 프로그램 탐색 데모: Online Bin Packing (평가·수정·결과)

작성 2026-06-30. 대상: Romera-Paredes et al., *Mathematical discoveries from program search with LLMs*,
Nature 625 (2024), "Bin packing" 절 + Fig 1/2b/6, Table 1. 오픈소스: google-deepmind/funsearch.

## 결론 (한눈에)
- 초기 구현의 **평가기(skeleton)에 결정적 버그**가 있었다: heuristic에 **빈 bin을 후보로 주지 않아** "새 bin을 여는 선택"을 아예 못했다 → 어떤 모델도 Best-Fit을 못 넘음. FunSearch(논문 Fig 2b + OSS)는 사전할당된 bins 배열로 **빈 bin(용량 C)까지 후보에 포함**한다. **이를 수정**(매 스텝 신선한 빈 bin을 후보에 추가) + docstring/skeleton 프롬프트 보강.
- 수정 후: **Sonnet이 Best-Fit을 +24.6% 능가**(test 초과율 3.274%→2.468%)하고 **논문 Fig 6의 핵심 전략("매우 tight할 때만 tight bin, 아니면 여유를 남김")을 자율 재발견**. **Haiku는 수정 후에도 tie**(모델 역량 병목).
- 교훈: **평가기/골격의 충실성이 결과를 좌우**하며(버그면 아무리 좋은 모델도 못 이김), 그 위에서 **모델 역량이 discovery를 가름**.
- **FunSearch 공개 heuristic(Fig 6) 직접 비교**: 우리 평가기에 이식하니 5.490%로 **Best-Fit보다 나쁨** — Fig-6은 OR 정수-용량에 튜닝돼 우리 정규화 [0,1] Weibull에선 항이 반대로 작동(스케일 특이성). → **heuristic은 타깃 분포에서 진화시켜야** 함(우리 Sonnet 규칙이 그 예).

## 6하원칙
- **누가**: 연구자(오케스트레이션) + LLM(로그인 `claude` CLI, Haiku·Sonnet)이 heuristic 프로그램 생성자.
- **무엇을**: 온라인 빈패킹 heuristic을 LLM 프로그램 탐색으로 진화 + 초기 구현을 논문·OSS와 대조·수정.
- **언제**: 2026-06-30. **어디서**: `demo/bpp.py`.
- **왜**: 교수님 요청 — 쉬운 표준 문제로 방법론 데모 + skeleton/프롬프트/평가기가 제대로 됐는지 논문·OSS로 평가·수정.
- **어떻게**: 아래 아키텍처 + 평가 + 수정.

## 전체 루프 (아키텍처)
```
 [seed: Best-Fit 프로그램(+docstring)]
        │
        ▼
   ┌─────────┐ best-shot(상위2개+excess%) ┌──────────┐  heuristic 프로그램들  ┌───────────────┐
   │ elite   │ ─────────────────────────▶ │ LLM       │ ──(def heuristic ...)─▶│ 안전 exec      │
   │ pool    │                            │(claude CLI)│                        │ (numpy만 노출) │
   └─────────┘ ◀── fitness로 재정렬 ────── └──────────┘                        └───────────────┘
        ▲                                                                            │ valid만
        │        ┌───────────────────────────────────────────────────────────────────▼──────────┐
        └────────│ EVALUATE(온라인 패킹): item마다 후보 = [들어가는 열린 bin들] + [신선한 빈 bin] │
                 │  → heuristic argmax에 배치(마지막=빈 bin이면 새 bin 개설). 목적=초과율(사용/하한−1)│
                 └──────────────────────────────────────────────────────────────────────────────┘
   선택: train(12×200)로 진화 → valid로 elite 선택 → **test(4×500, 더 큼)로만 보고**(일반화)
```
- 진화 대상 = `heuristic` 함수만(FunSearch와 동일). 골격(패킹 루프·argmax·평가)은 고정.

## 평가 (논문 + OSS 대비) — 발견한 3가지
1. **[치명적] 빈 bin이 heuristic 후보에서 누락.** 초기 `pack()`은 "이미 열린·들어가는 bin"만 넘기고, 다 안 맞을 때만 새 bin 개설 → heuristic이 **새 bin 여는 선택 불가**. FunSearch(Fig 2b)는 `bins=problem.bins`(사전할당) + `get_valid_bin_indices`로 **빈 bin(용량 C)까지 후보**. Fig 6 전략("여유 남기기/새 bin")을 표현하려면 필수. **→ 이게 Best-Fit을 못 넘은 구조적 원인.**
2. **skeleton·docstring 부재.** FunSearch는 진화 함수에 docstring, LLM엔 전체 골격 노출. 초기 프롬프트는 산문 설명·docstring 없음.
3. **(경미) 용량 스케일.** FunSearch는 정수 용량(OR3=150, Weibull=100). 본 데모는 정규화 [0,1](등가).

## 수정 내용 (`demo/bpp.py`)
- **①**: `pack()`이 매 스텝 **신선한 빈 bin(용량 1.0)을 후보 배열의 마지막에 포함**. heuristic이 이를 최고점 주면 새 bin 개설. (검증: Worst-Fit이 3.3%→302%로 폭발 = 이제 새 bin을 매번 여는 게 표현됨 → 수정이 작동. Best-Fit은 3.274% 불변.)
- **②**: seed/baseline에 docstring 추가, `_SYSTEM`에 **고정 골격(후보=열린bin+신선빈bin, argmax)** 명시.
- **③**: 정규화 스케일 명시.

## 논문(FunSearch) 대비 비교
| 항목 | FunSearch | 본 데모(수정 후) |
|---|---|---|
| 진화 대상 | Python 프로그램(heuristic 함수) | 동일 ✓ |
| signature / 배치 | `heuristic(item, bins)->scores`, valid 중 argmax | 동일 ✓ |
| **빈 bin 후보** | 포함(사전할당 배열) | **포함(수정 완료)** ✓ |
| 출발점 | Best-Fit(+docstring) | 동일 ✓ |
| 적합도 | 초과 bin 비율(L2 하한) | 초과 bin 비율(연속 하한 sum/cap) ≈동일 |
| 인스턴스 | OR+Weibull, train-size≠test | Weibull, train200/test500 ✓(축소) |
| 탐색 | island + programs DB, ~10^6 샘플 | elite pool, ~80 프로그램 ✗(축소) |
| 모델 | Codey(PaLM2) | Haiku / Sonnet(claude CLI) |

## 실행 규모 (세대·샘플)
각 검증 런: **10세대 / 10 LLM 호출 / 세대당 8 프로그램 요청**. 총 프로그램 샘플: **Haiku 79개 유효**(fails 0), **Sonnet 70개 유효**(fails 1=gen7 timeout) + 초기 best-fit seed. FunSearch 원논문의 **~10^6 샘플**과 비교하면 극소.

## 결과 (test = Weibull 4×500, 초과율 낮을수록 좋음)
| 방법 (수정된 셋업, 동일 평가기) | 초과율(test) | vs Best-Fit |
|---|---|---|
| Worst-Fit | 302.835% | (참고: 새 bin 남발) |
| Best-Fit (출발점) | 3.274% | — |
| **FunSearch 공개 heuristic (Fig 6)** | **5.490%** | **−67.7% (더 나쁨)** |
| Haiku 진화 | 3.274% | +0.0% (tie) |
| **Sonnet 진화 (ours)** | **2.468%** | **+24.6%** |

### FunSearch 공개 heuristic 직접 비교 (핵심)
FunSearch가 논문 Fig 6(= OSS `google-deepmind/funsearch` bin-packing)에서 공개한 discovered heuristic을
**verbatim으로 가져와 우리 평가기에서 직접 돌렸다**(코드: `demo/bpp.py::FUNSEARCH_PUBLISHED`). 결과 **5.490%로 Best-Fit(3.274%)보다 나쁨.**
- **원인 = 스케일/분포 특이성**: Fig-6 규칙은 **OR 데이터셋(정수 용량 ~100–150)** 에 튜닝됨. 우리 **정규화 [0,1] Weibull** 에선 `score[index] *= item`(item<1)이 best-fit bin 점수를 *낮춰* 그 bin을 회피시키는 등 항들이 반대로 작동(정수 스케일에선 item~50이라 반대로 강화). → **heuristic은 그대로 이식하면 misfire.**
- **교훈**: 진화 heuristic은 **타깃 분포에서 진화**시켜야 한다(FunSearch도 Weibull 테스트엔 Weibull로 학습). 우리 Sonnet 규칙은 우리 분포에서 진화시켜 +24.6%.
- **한계(정직)**: 완전 동일 비교는 FunSearch의 정확한 OR/Weibull 데이터셋(정수 용량)에서 돌려야 함. 그 데이터셋은 노트북에 대용량 JSON으로 임베드돼 자동 web-fetch로 코드셀/데이터 추출 실패 → 여기선 **공개 heuristic을 우리 harness에 이식한 same-harness 비교**(논문 Table 1 재현 아님). 정수-스케일 harness 재현은 후속 과제.

Sonnet이 진화시킨 heuristic (해석가능 + **Fig 6 전략 재발견**):
```python
def heuristic(item, bins):
    """Aim residual at half the item's complement space, matching typical future-item statistics."""
    residual = bins - item
    target = 0.5 * (1.0 - item)            # tightest가 아니라, 미래 아이템용 여유를 남기는 목표 residual
    score = -np.abs(residual - target) * 3.0
    perfect = residual < 0.03
    score = np.where(perfect, 60.0 - residual * 10.0, score)   # 매우 tight할 때만 그 bin을 강하게 선호
    score = np.where(bins == 1.0, score - 0.15, score)         # 새 bin은 약간 페널티
    return score
```
→ 논문 Fig 6("least-capacity bin only if fit is very tight, otherwise leave more space")과 **동일한 통찰**을 6~10세대·소예산으로 재발견. (train 4.491→3.832 개선; Sonnet 10콜 중 1콜 timeout 실패했으나 진화·최종 test 결과는 유효. ~$1.3.)

## 결론적 해석 / 한계
- **평가기·골격의 충실성이 1차 결정 요인**: 빈-bin 버그가 있으면 어떤 모델도 Best-Fit을 못 넘었고, 수정 후 강한 모델은 넘었다.
- **모델 역량이 2차 요인**: 동일한 올바른 셋업에서 Haiku는 tie, Sonnet은 +24.6%.
- 한계: 소규모 예산·인스턴스·단순 elite(island 아님). FunSearch급(10^6 샘플·island·N=5000+)이면 이득이 더 커짐(논문 Table 1 Weibull에서 best-fit 대비 ~5배 개선).
- 잔여: `_complete` timeout(180s)이 Sonnet verbose 응답에서 가끔 걸림 → 필요시 상향.

## 관련 파일
- 코드: `demo/bpp.py`. 실행: `DEMO_MODEL=sonnet python -m demo.bpp` (또는 `haiku`; `DEMO_LLM=0`=mock).
- 논문: `demo/02. Mathematical discoveries ...pdf`. OSS: github.com/google-deepmind/funsearch (bin_packing).
