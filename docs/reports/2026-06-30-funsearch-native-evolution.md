# 보고서 — FunSearch native 셋업에서 LLM 규칙 진화 (Sonnet, 10세대)

작성 2026-06-30. 셋업 = FunSearch 실제 evaluator/skeleton/데이터(`2026-06-30-funsearch-native-swap.md` 참조).

## 결론 (한눈에)
- FunSearch의 **실제 평가기·골격·데이터(OR3)** 위에서 **Sonnet**으로 `priority`를 Best-Fit에서 **10세대 진화** → OR3 test 초과율 **2.758% vs Best-Fit 4.001% (+31.1%)**.
- 진화 규칙이 **FunSearch의 핵심 전략을 재발견**: "다음 아이템이 못 들어갈 **죽은 gap(dead space)** 을 페널티 + 정확 fit 보상 + 새 bin 약간 페널티" — 논문 Fig 6/OR 규칙과 같은 통찰.

## 모델 선택: 왜 Sonnet인가 (Haiku 아님)
- 이 과제는 **비자명한 numpy heuristic 프로그램을 합성**하는 것 — 코딩·전략 추론 역량이 결정적.
- **실증 근거**: 앞선 데모에서 **Haiku는 10세대 내내 Best-Fit을 못 넘음**(discovery 실패, tie). 반면 **Sonnet은 개선을 찾고 FunSearch 전략을 재발견**. 이번에도 Sonnet이 +31.1% + 전략 재발견.
- **트레이드오프**: Sonnet은 더 비싸고(≈$1.7/런) 응답이 verbose해 가끔 timeout을 유발. 그럼에도 **discovery 성패를 가르는 게 모델 역량**이라 Sonnet 채택(Haiku는 이 과제에 부적합함이 실증됨). verbose→timeout은 프롬프트 간결화·pop 축소로 완화.

## 셋업
- 평가기/골격/데이터: FunSearch OSS 그대로(OR3, 용량 150, 500 items/instance). `priority` 초기값 = Best-Fit + 논문 docstring.
- 분리: OR3 20인스턴스 → train 12 / valid 4 / test 4. 진화 = train, 선택 = valid, 보고 = **test**.
- 예산: **10세대**, pop 6(호출당 3 offspring), best-shot 프롬프트(상위 2개 + excess%).

## 결과
- train 최고 초과율: 6.030 → 5.036 → 4.871 → **4.829%** (세대 진행하며 개선).
- **OR3 test 초과율 = 2.758%** (Best-Fit 4.001%) → **+31.1%**. 참고로 FunSearch 공개 OR 규칙은 (전체 20인스턴스에서) 3.11% — split이 달라 직접 비교는 주의하나, **구조·성능이 유사한 규칙을 우리 LLM이 재발견**.
- 진화 규칙(해석가능):
```python
def priority(item, bins):
    r = bins - item
    C = np.max(bins)
    dead = (r > 0) & (r < item)          # 다음 아이템(크기 item)이 못 들어가는 '죽은 gap'
    exact = r == 0
    return -r - dead*(r + bins) + exact*C - (bins == C)*item*0.1
    #      best-fit  죽은gap 페널티   정확fit 보상   새 bin 약간 페널티
```
- 비용/신뢰성: Sonnet 10콜 중 **1콜 timeout**(gen5, 420초 초과) → 9세대 생산적. out_tok ~60k, ~$1.7.

## 한계 (정직)
- **작은 test split(4 인스턴스)·단일 런·고분산**: 직전 flaky 런(5/10 timeout)에선 같은 셋업이 +52.8%였음 → 수치 변동 큼. **Table 1(20인스턴스 전체) 주장 아님.** 견고한 수치엔 다중 반복 + 전체 인스턴스 평가 필요.
- **Sonnet verbose → timeout**: 프롬프트 간결화로 1/10까지 줄였으나 잔존. (근본 완화: 출력 토큰 억제 or pop 추가 축소.)
- FunSearch 대비 예산 극소(10세대·~30프로그램 vs ~10^6).

## 관련 파일
- `demo/bpp.py` (FunSearch native evaluator + LLM 진화; `DEMO_EVOLVE=1 DEMO_MODEL=sonnet DEMO_GEN=10`).
- `demo/funsearch_data.json` (OR3/Weibull5k, CC-BY). 로그: `$CLAUDE_JOB_DIR/tmp/bpp_native_evolve2.log`.
