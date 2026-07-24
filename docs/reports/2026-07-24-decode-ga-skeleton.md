# 보고서 - decode / rules / GA 뼈대 구현 완료

작성 2026-07-24. 선행: `2026-07-23-evaluator-implementation-and-replay.md`(타이밍 코어).
원칙 유지: **데이터 변형 금지.**

## 결론 (한눈에)

- **파서 -> decode -> GA 전 과정이 end-to-end로 동작**한다. 실제 Dauzere 인스턴스에서 GA가 문헌
  Table 8과 **같은 자릿수**의 Cmax를 낸다(+13~43%, 아래 §3). 우리 GA는 평범한 뼈대이고 문헌은 최대
  600초 tabu search이므로 이 격차는 예상된 것이며, **파이프라인이 정상 동작한다는 확인**이 목적이다.
- **decode의 자기검증이 완벽하다**: decode가 만든 스케줄을 타이밍 코어에 재투입하면 makespan이
  **180/180 케이스 전부 정확히 일치**. 두 프론트엔드(decode / replay)가 하나의 코어로 묶여 있다는
  강한 회귀 테스트가 상시 작동한다.
- **D1/D2 비지배성을 우리 코드로 재현**했다(§4). Han 2024가 "두 디코딩 중 어느 것도 항상 우월하지
  않다"고 인정한 지점을 우리 실험에서도 확인 - **LLM이 더 나은 규칙을 찾을 여지가 실재함**을 뒷받침.
- GA 연산자는 단위 테스트로 검증. 특히 **POX**(어제 본 Aihong-Sun 저장소에서 결과를 버리고 부모를
  반환하던 죽은 코드)를 제대로 구현하고, "자식이 부모와 다르고 job별 공정 수가 보존됨"을 200케이스로 확인.

## 구현물

```
fjspt/
  rules.py               # AGV 선택 규칙: D1/D2 baseline + 진화 규칙 컴파일(rule_from_expr)
  evaluator.py           # decode(inst, OS, MS, rule) -> (Solution, Schedule) + self_check
  ga.py                  # GA (DCGA 구조: POX/균등교차/swap·insert·inversion/재배정, 토너먼트+엘리트)
  test_decode_selfcheck  # decode==timing 회귀 테스트 (180 케이스, 통과)
  test_ga_operators      # POX/교차/변이 단위 테스트 (통과)
```

## 1. decode 설계 요점

- 입력: OS(job id 반복 순열, k번째 등장 = job의 k번째 공정) + MS(공정 canonical 순서별 적격기계 인덱스)
  + rule(AGV 선택). 출력: 완전 지정된 `Solution` + Cmax.
- **타이밍 코어와 동일한 점화식을 증분 계산**한다. 그래서 decode 결과를 `timing.simulate`에 재투입하면
  같은 값이 나와야 하고(자기검증), 실제로 180/180 일치.
- 기계 순서 = OS에서 공정이 처리되는 순서(append). 차량 = rule이 후보 중 최고 점수를 그리디 선택.
- 같은 기계로 이어지는 공정은 운반 없음(§ 확정 규약) - decode에도 반영.

## 2. rules 인터페이스 (LLM 진입점)

규칙은 후보 차량 하나의 특징 dict를 받아 점수를 반환하고, 디스패처가 최고점을 고른다.
특징: `empty_travel, loaded_travel, arrival, wait, agv_free, agv_cum_travel, machine_free, remaining_ops`.

**두 baseline이 같은 공간의 두 점으로 표현된다**(설계 §8.2 그대로):
- `D1 = -arrival` (가장 이른 도착, 동점은 차량 인덱스)
- `D2 = -arrival - eps*agv_cum_travel` (동점은 누적이동 최소)

`rule_from_expr`로 LLM이 낸 문자열 규칙을 같은 인터페이스로 컴파일한다(A안 `sim/rule.py`의 제한 eval
재사용). 즉 LLM 규칙과 baseline 비교가 "다른 알고리즘 비교"가 아니라 **같은 공간 안 ablation**이 된다.

## 3. GA end-to-end 결과 (문헌 Table 8과 대조, 100 pop x 100 gen, 시드 0)

| 인스턴스 | 우리 D1 | 우리 D2 | 문헌 Table 8 | gap% | 초 |
|---|---|---|---|---|---|
| 01a 2veh | 3797 | 3940 | 3029 | +25.4 | 10 |
| 01a 4veh | 3170 | 3188 | 2812 | +12.7 | 13 |
| 01a 6veh | 3126 | 3271 | 2756 | +13.4 | 16 |
| 07a 2veh | 6010 | 5852 | 4157 | +40.8 | 17 |
| 07a 4veh | 3636 | 3845 | 2860 | +27.1 | 22 |
| 07a 6veh | 3353 | 3388 | 2758 | +21.6 | 27 |
| 13a 2veh | 9322 | 9069 | 6332 | +43.2 | 26 |
| 13a 4veh | 4736 | 4957 | 3471 | +36.4 | 33 |
| 13a 6veh | 3964 | 3819 | 2900 | +31.7 | 39 |

- 비교 기준은 **논문 Table 8**(레포 해 파일 헤더 아님 - 어제 내부 모순 확인). 이 원칙 유지.
- 격차의 의미: 우리는 뼈대 GA(특화 이웃탐색 없음, 10~40초), 문헌은 disjunctive-graph 이웃 tabu search
  (최대 600초). **자릿수가 맞다(10배씩 벌어지지 않음)는 것이 이 단계의 통과 기준**이고, 충족했다.
- 격차를 줄이는 것은 (a) GA 강화, (b) **LLM 규칙 진화**의 몫. 특히 규칙은 우리 연구의 핵심 기여 지점.

## 4. D1/D2 비지배성 재현 (연구 전제의 실증)

위 표에서 D1이 이기는 경우(01a 전부, 07a 4·6veh)와 D2가 이기는 경우(07a 2veh, 13a 2·6veh)가 섞여 있다.
어느 고정 규칙도 항상 우월하지 않다 - **Han 2024의 핵심 관찰을 우리 파이프라인이 재현**했다.
이는 "고정 규칙 2개 사이 어딘가에 더 나은 규칙이 있다"는 우리 연구의 전제가 공허하지 않음을 보여준다.
LLM이 채울 자리가 실제로 존재한다.

## 5. 다음 단계

```
[완료] 파서 3종 + 타이밍 코어(논문 예제 검증) + decode(자기검증) + rules(D1/D2) + GA(단위테스트)
다음:
  1. experiment.py - train/test 분할, 다회 반복, 통계, 결과표 (설계 §9)
  2. LLM 루프 연결 - ahd/llm.py(ClaudeCliLLM, tool-contamination 수정본) 재사용.
     규칙 문자열 제안 -> rule_from_expr -> GA로 평가 -> ReEvo 신호로 다음 세대.
     train에서 D1/D2 초과하는 규칙을 찾고 test에서 유지되는지 검증.
  3. (병렬) Deroussi&Norre 2010 원문 확보 -> data set 1 이동시간 행렬 -> fjsp1 replay 재시도.
```

## 검증 재현 커맨드

```
python -m fjspt.test_paper_example      # 타이밍 코어: 논문 예제 Cmax 13 일치
python -m fjspt.test_ga_operators       # POX/교차/변이 단위 테스트
python -m fjspt.test_decode_selfcheck   # decode==timing 180케이스 일치
```

## 관련 파일

- 구현: `fjspt/rules.py`, `fjspt/evaluator.py`, `fjspt/ga.py`
- GA 실행 대조 스크립트(임시): `$CLAUDE_JOB_DIR/tmp/test_ga_run.py`
- 설계 근거: `docs/reports/2026-07-23-skeleton-evaluator-design.md`
