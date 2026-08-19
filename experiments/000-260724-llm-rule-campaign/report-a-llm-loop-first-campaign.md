# 보고서 - LLM 규칙 진화 루프 연결 + 첫 캠페인 (결과는 결론적이지 않음)

> **[RETIRED]** GA 시대 실험이다. 방법(GA/LNS)은 은퇴했고 이 폴더의 스크립트는
> `archive/ga-era/`의 공용 모듈에 의존해 지금은 돌지 않는다. 결과 수치는
> `tests/test_reported_numbers.py`가 계속 지킨다.

작성 2026-07-24. 선행: `2026-07-24-decode-ga-skeleton.md`.
원칙 유지: 데이터 변형 금지. **결과를 부풀리지 않는다.**

## 결론 (한눈에)

- **전체 파이프라인이 연결됐다**: 파서 -> decode -> GA -> 진화 루프 -> **실제 `claude` CLI proposer**.
  실제 Claude가 유효한 AGV 규칙을 제안하고, GA로 평가되고, ReEvo 신호로 다음 세대를 낸다. 동작 확인.
- **첫 캠페인 결과는 결론적이지 않다(정직하게)**. 진화된 규칙 `-arrival - wait/(remaining_ops+1)`은
  - train(3인스턴스)에서 D1/D2를 이김: 6952 vs D1 7043, D2 7102 (약 1.3%).
  - **하지만 held-out test(15인스턴스)에서는 평균만 근소하게 앞서고**(P=6330.6 vs D2=6336.6 vs D1=6355.9,
    D2 대비 0.09%), **인스턴스별 best-of(D1,D2)에는 3승 12패로 짐**(평균 +41.6, 즉 더 나쁨).
- 해석: **train 개선(1.3%)이 test로 거의 일반화되지 않았다.** 단일 진화 규칙이 각 고정 규칙을 평균으로는
  아주 조금 앞서지만, 노이즈 수준이고, "인스턴스마다 D1/D2 중 좋은 걸 고르는" 오라클을 못 이긴다.
- **이건 실패가 아니라 예상된 소규모 데모 결과다**. 예산이 매우 작았고(아래 §3) 진짜 캠페인이 아니다.
  인프라가 정직한 수치를 내놨다는 것 자체가 이 단계의 성과다.

## 1. 연결한 것

```
fjspt/
  llm.py          # B안 proposer: ClaudeCliLLM(_complete) 재사용 + 단일 규칙/makespan 프롬프트
                  #   - ClaudeRuleProposer: 실제 claude CLI (--tools "" 검증본 재사용)
                  #   - LocalProposer: CLI 없이 루프 기계 테스트용 mock
  experiment.py   # evaluate_rule / evolve(ReEvo 루프) / compare / train-test 분할
```

- **`ahd/llm.py`(A안)는 건드리지 않았다.** 검증된 `_complete`(CLI 호출, tool-contamination 수정본)만
  상속으로 재사용하고, B안 전용 프롬프트/특징/단일 규칙 형식을 얹었다.
- 규칙 genome = 단일 표현식 문자열. D1/D2가 같은 공간의 두 점이라 자동으로 ablation이 된다.

## 2. 실제 CLI 동작 확인

1회 vary 호출로 유효한 B안 규칙 3개 생성(예: `-arrival/(machine_free+1) - 0.001*agv_cum_travel`,
비율·부하분산 등 구조적으로 다양). 호출당 약 $0.05, `--tools ""`로 순수 텍스트 생성. fails=0.

## 3. 첫 캠페인 (의도적으로 작은 예산 - 기계 검증용)

| 항목 | 값 |
|---|---|
| train | 01a, 07a, 13a @ 2veh (기계 5/8/10 각 하나) |
| 진화 예산 | pop 12 x 4세대, 내부 GA 30x30, 시드 1개 |
| CLI 호출 | 4회, $0.11, fails=0, 175초 |
| test | 나머지 15인스턴스 @ 2veh, GA 50x50, 시드 2개, 211초 |

### 진화 로그 (train)
```
gen 0: 7043.0  -arrival                              (= D1)
gen 1: 6967.7  -arrival - agv_cum_travel/(agv_free+1)
gen 2: 6952.0  -arrival - wait/(remaining_ops+1)     <- 최종
gen 3~4: 개선 없음
```

### test 결과 (held-out 15인스턴스)
| 규칙 | test 평균 makespan |
|---|---|
| D1 | 6355.9 |
| D2 | 6336.6 |
| **P(진화)** | **6330.6** |

- 평균으로는 P가 D2를 0.09%, D1을 0.4% 앞섬 - **노이즈 수준**.
- 인스턴스별 best-of(D1,D2) 대비: **3승 0무 12패, 평균 +41.6**(P가 더 나쁨).

## 4. 왜 결론적이지 않은가 (한계, 숨기지 않음)

1. **예산이 진짜 캠페인의 1/10 수준**. 진화 pop 12 x 4세대, 내부 GA 30x30, 시드 1개.
   설계(`2026-07-23-skeleton-evaluator-design.md` §9)가 상정한 규모(pop 20 x 10세대, GA 100x100,
   다중 시드)에 한참 못 미침. 지금은 "루프가 도는가"를 본 것.
2. **차량 2대만**. 2/4/6대 스케일링 축을 아직 안 씀.
3. **GA가 확률적인데 시드가 적다**. train 시드 1개, test 시드 2개. 1.3%~0.09% 개선은 시드 노이즈와
   구분이 안 됨.
4. **train 3인스턴스는 과적합 위험이 큼**. test 일반화 실패(+41.6)가 이를 보여줌.

## 5. 그래서 이 결과가 말해주는 것

- **긍정**: 인프라가 정직하게 동작한다. 진화 규칙이 train에서 baseline을 이기고, test에서 검증되고,
  과적합이 수치로 드러난다. 이게 연구에서 필요한 정직한 측정 장치다.
- **부정(정직하게)**: 이 예산으로는 "LLM이 D1/D2를 유의미하게 이긴다"고 주장할 수 없다. 평균 0.09%는
  주장 못 함. **더 큰 캠페인이 필요**하고, 그때도 이길지는 미지수다 - 그게 진짜 실험이다.

## 6. 다음 단계 (실제 결과를 내려면)

1. **본 캠페인**: train을 6~9인스턴스로, 진화 pop 20 x 8~10세대, 내부 GA 60x60, 시드 3개.
   2/4/6대 전부. 예상 CLI 비용 ~$1~2, 시간 1~2시간. (지금 코드 그대로 파라미터만 키우면 됨.)
2. **통계 검정**: P vs D1/D2를 시드 다수로 돌려 Wilcoxon 등으로 유의성 확인. 평균 비교로는 부족.
3. **평가 지표 재고**: "단일 규칙이 best-of(D1,D2)를 이겨야 한다"가 올바른 기준. 평균만 보면 오해 소지.
4. **GA 강화 검토**: 문헌 대비 **65%** 격차(뼈대 GA, `2026-07-29-literature-gap-measurement.md`).
   규칙 개선 효과가 GA 약함에 묻힐 수 있음.
5. (병렬) Deroussi&Norre 2010 원문 -> data set 1 -> fjsp1 replay.

## 재현 커맨드

```
# 기계 테스트(CLI 없이): LocalProposer로 루프 동작
# 실제 캠페인 스크립트: $CLAUDE_JOB_DIR/tmp/campaign_evolve.py, campaign_test.py
# 결과 JSON: campaign_result.json, campaign_test_result.json
```

## 관련 파일

- 구현: `fjspt/llm.py`, `fjspt/experiment.py`
- 캠페인 스크립트/결과(임시): `$CLAUDE_JOB_DIR/tmp/campaign_*.py`, `campaign_*result.json`
- 설계: `docs/reports/2026-07-23-skeleton-evaluator-design.md` §8~9
