# Stage 6 — 종합 / 트렌드 분석 프롬프트 (최종 산출물)

역할: 논문 카드 전체를 종합해 연구 흐름·방법론·컨트리뷰션·gap 리포트를 만든다.

입력: `runs/<slug>/cards/*.md` (+ 필요시 candidates/shortlist)
출력: `runs/<slug>/synthesis.md`

## 할 일 (연도순 종합)
1. **문제정의 변화**: 시간에 따라 다루는 문제가 어떻게 이동했는지
2. **데이터셋·벤치마크 변화**: 무엇으로 평가해 왔는지, 표준이 있는지
3. **방법론 family clustering (≤5개)**: 각 family 정의
4. **family별 대표 논문 + contribution**
5. **최근 2년 논문이 주장하는 한계**
6. **내가 시도할 수 있는 contribution 후보 5개 + 연구 gap**

## 출력 규칙 (anti-hallucination)
- **모든 주장에 근거**: `(저자year, §섹션)` 형식으로 출처 표기.
- 카드에 없는 숫자/주장은 쓰지 않는다. 추론이면 "추론:" 으로 명시.
- 가능한 한 표로 정리.

## synthesis.md 권장 구조
```
# <topic> — synthesis (YYYY-MM-DD)  [N papers]

## 1. 문제정의 변화 (timeline)
## 2. 데이터셋·벤치마크
## 3. 방법론 family (≤5)
| Family | 정의 | 대표 논문 | 핵심 contribution |
## 4. 최근 2년 한계
## 5. 내 contribution 후보 5 + gap
| # | gap/아이디어 | 근거(어느 논문이 한계라 했나) | 시도 방법 |
```

다음 단계: (선택) related-work 초안은 phd-skills `paper-writing` 으로.
