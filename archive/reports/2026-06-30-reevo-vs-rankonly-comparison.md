# 보고서 — ReEvo(fitness+reflection) vs rank-only 비교 (L1, 40 AGV)

작성 2026-06-30.

## 결론 (한눈에)
- 유효한 1:1 비교에서 **ReEvo가 rank-only보다 좋고(test +1.8% vs +1.0%) 동시에 더 쌌다**(출력토큰 1/3, $0.65 vs $1.28).
- **그러나 run-to-run 분산이 두 방식의 차이보다 커서, 1회씩 비교로는 "ReEvo가 낫다"를 단정할 수 없다.** 경향상 ReEvo가 더 *일관적*(좁은 범위)이고 rank-only는 변동이 큼.
- **결정**: ReEvo를 기본값으로 유지(원리적으로 더 많은 정보 + 관측상 우세하거나 동등). 엄밀한 ablation은 캠페인 단계에서 다회 반복(≥3 run/조건)으로 수행.

## 처음 목적 / 왜
- LLM proposer에 **fitness 값 + reflection**(ReEvo)을 주는 것이 **순위만**(rank-only) 주는 것보다 LLM-AHD 이득을 키우는지 정량화하려고. (이전엔 vary에 순위만 줬던 게 가장 약한 신호였음.)

## 무엇을 어떻게 바꿨나
- `ahd/llm.py`에 `reevo` 토글 추가: True=elite의 mean_tardiness 제시 + reflection 요청, False=순위만(기존).
- 동일 조건 비교: regime **L1(40 AGV 운반병목)**, 동일 train/valid/test seed, 동일 budget(8세대·8 train seed), `python -m ahd.run` env `AHD_REEVO=0/1`.
- **1차 비교는 무효였다**: 두 런을 연달아 돌리자 RUN B(ReEvo)의 claude 호출이 **전부 throttle로 실패**(8콜 토큰 0)했는데, `_complete`가 에러를 조용히 삼켜 "진화 실패"가 "개선 없음"처럼 보였다. → `_complete`에 **에러 표면화**(stderr + `fails` 카운터) 추가하고, 두 런 사이 **120초 간격**을 두어 재실행.

## 결과 (수치 / 비교)
유효 재실행(v2, baseline NV+EDD test=370.93):

| 방식 | test tardiness | vs baseline | LLM 호출 | 출력토큰 | 비용 | fails |
|---|---|---|---|---|---|---|
| rank-only | 367.25 | +1.0% | 8 | 50,227 | $1.28 | 0 |
| **ReEvo** | **364.32** | **+1.8%** | 8 | 15,498 | $0.65 | 0 |

분산 참고(여러 L1 런에 걸친 test 개선폭):
- rank-only: **+1.0% ~ +3.5%** (변동 큼)
- ReEvo: **+1.8% ~ +2.1%** (좁음, 더 일관적)

진화된 규칙(ReEvo, v2): AGV `-travel_time/(abs(slack)+1)`, machine `-(slack/(proc_time+1))` — 간결·해석가능.

## 한계 / 다음
- **단정 불가(분산 지배)**: 결론을 내려면 조건당 ≥3 반복으로 분포 비교 필요. 캠페인이 다seed로 돌므로 자연 해결.
- **출력 verbose 비용**: rank-only가 50k 토큰/$1.28로 비쌈(모델이 JSON-only 지시에도 장황). 캠페인 전 프롬프트 추가 억제 또는 모델 검토 권장.
- 다음: 이 비교에 매달리지 말고 **M2/M3로 전진** — B1 고전 joint 선택 + B2 GP baseline → 캠페인(P vs B1/B2/B5/B6)에서 다seed로 ReEvo 효과까지 함께 정량화.

## 관련 파일
- 코드: `ahd/llm.py`(reevo 토글 + `_complete` 에러 가시화), `ahd/run.py`(env AHD_REEVO)
- 로그: `$CLAUDE_JOB_DIR/tmp/cmp2_{rankonly,reevo}.log`
