# 보고서 - 4슬롯 조인트 진화 루프, 첫 실행

작성 2026-08-13. 코드 `model/llm.py`(`ClaudeBundleProposer`)·`model/experiment.py`(`evolve_bundle`,
`evaluate_bundle`) - 둘 다 2026-08-12에 작성됐고 커밋 전이었으며, 이번이 **첫 실행**이었다(그 전엔
스모크 테스트조차 없었음). 실행 전 `LocalBundleProposer`(LLM 없음)로 구조만 먼저 확인, 에러 없음.
결과 `data/results/2026-08-13-bundle_evolution_result.json`. LLM 호출 6회(세대당 1회),
`claude -p --model sonnet`, 총 비용 $2.06, 실패 0/6.

## 결론

1. **루프가 처음으로 끝까지 돌았다, 에러 없이.**
2. 학습 3개 인스턴스(01a/07a/13a, AGV 2대)에서 세대 0(최선의 시드 = MIX) 7122.0 ->
   세대 6 5953.7, **16.4% 개선**.
3. **held-out 15개 인스턴스(진화 중 전혀 안 본 데이터)에서 evolved가 BALANCED/HAND/MIX
   전부를 15/15 이겼다.** 문헌(Berterottière 2024 Table 8) 대비 평균 격차:
   BALANCED 115.8% -> **evolved 46.2%**.
4. 그래도 **문헌 자체를 이긴 건 아니다** (46.2%는 여전히 문헌 best-known보다 나쁘다는 뜻).
5. 이건 **단일 실행(n=1)**이다. 이 프로젝트는 "처음엔 좋아 보였다가 재검정에서 무너지는" 패턴을
   반복해서 겪었다(2026-07-24 재현성 캠페인 -> 2026-08-01b 재검정에서 뒤집힘). 재현 확인 전까지는
   잠정 결과로 취급할 것.

## 1. 설정

- Train: 01a/07a/13a (AGV 2대) - `default_split()`
- Test (held-out, 15개): 02a~18a 중 train 제외 나머지, AGV 2대
- `pop_size=20`, `n_gens=6`, elite = `pop_size // 4` = 5
- 시드 population: `_SEEDS_BUNDLE`(BALANCED/HAND/MIX) 3개를 20개로 반복 패딩
- 진화 LLM: ReEvo 스타일(적합도 + 1문장 반성 -> 제안), 시스템 프롬프트에 "부하분산이 손규칙 조합을
  이긴다"는 2026-08-07 실측 사실이 힌트로 명시돼 있음 (`model/llm.py::_SYSTEM_BUNDLE`)

## 2. 세대별 진행 (train, mean Cmax)

| 세대 | best Cmax | 비고 |
|---|---|---|
| 0 (시드) | 7122.0 | 최선의 시드 = MIX 그대로 |
| 1 | 6818.7 | op/task_sequence에 `remaining_ops`/`remaining_proc` 항 추가 |
| 2 | 6691.3 | |
| 3 | 6691.3 | 정체 |
| 4 | 6269.7 | 같은 항의 가중치 확대(0.02 -> 0.05) |
| 5 | 6005.7 | machine_select/vehicle_select에도 항 추가(`travel_to`, `empty_travel`) |
| 6 | 5953.7 | 최종 |

최종 번들:

```
machine_select: -queue_len + 0.01*remaining_ops - 0.003*travel_to
op_sequence:    -arrival + 0.045*remaining_ops + 0.01*wait + 0.005*idle
vehicle_select: -queue_len - 0.003*empty_travel
task_sequence:  -arrival + 0.045*remaining_proc + 0.01*wait
```

**관찰**: LLM은 구조를 뒤엎지 않았다. 부하분산(`-queue_len`/`-arrival`) 뼈대는 6세대 내내
유지됐고, 그 위에 작은 가중치(0.003~0.05)로 부차 신호를 얹는 미세조정만 했다. 세대 0의 최선이
이미 MIX(=`queue_len`+`arrival` 조합)였다는 점과 맞물려, "부하분산이 이긴다"는 시스템 프롬프트의
힌트를 그대로 따라간 모양새다 - 아래 4절 참고.

## 3. Held-out 평가 (15개 인스턴스, 진화 중 미접근)

| 번들 | mean Cmax | 문헌 대비 평균 격차 | evolved가 이긴 인스턴스 수 |
|---|---|---|---|
| **evolved** | **4806.1** | **46.2%** | - |
| BALANCED | 7011.6 | 115.8% | 15/15 |
| MIX | 6670.7 | 105.2% | 15/15 |
| HAND | 9939.2 | 205.8% | 15/15 |

15개 인스턴스 전부에서 `evolved < BALANCED, MIX, HAND` (개별 인스턴스 값은
`data/results/2026-08-13-bundle_evolution_result.json`에 전부 있음).

## 4. 해석

- train(3개)에서 test(15개)로 갈 때 우위가 줄지 않고 오히려 커졌다 - 단순 과적합 징후는
  안 보인다. 다만 인스턴스별 격차 값의 절대 스케일이 서로 다르므로(문헌 격차 %는 인스턴스마다
  분모가 다름), "격차%가 크게 줄었다"는 문장을 과대해석하지 않도록 주의.
- 46.2%는 이 프로젝트가 이 계열(Dauzère, 구성형·무탐색)에서 낸 수치 중 가장 낮다
  (BALANCED의 76.6%/115.8%보다 낮음). 그래도 "문헌을 이겼다"는 아니다 - 여전히 양수.

## 5. 주의 (다음 세션이 읽기 전 필수)

- **n=1.** 독립 재실행으로 "부하분산 뼈대 유지 + 미세조정"이라는 질적 통찰이 재현되는지
  확인되지 않았다. 2026-07-24 캠페인은 반드시 3회 반복 후 결론 냈다 - 이번은 그 절차를
  아직 안 밟았다.
- 시스템 프롬프트(`_SYSTEM_BUNDLE`)에 "부하분산이 이긴다"는 사실이 이미 힌트로 박혀 있다.
  LLM이 그걸 스스로 재발견한 것인지, 그냥 받아쓴 것인지 이 실행만으로는 구분 안 된다 -
  그 문장을 뺀 ablation이 필요하다.
- AGV 2대 스코프만 봤다(`default_split()`). 4·6대에서도 같은 패턴인지 미확인.
- **`vary()`는 매 세대 LLM 호출 1회로 k개 자식을 한 번에 받는 구조다.** STATUS.md의
  "다음 계획" 1번 항목이 명시한 "교차 = 슬롯 단위 재조합(LLM 불필요, 항상 유효)" 연산자는
  구현되지 않았다 - 지금은 변이(LLM)만 있고 별도 결정적 교차 연산자는 없다. 계획과 구현이
  이 지점에서 다르다는 걸 인지하고 넘어갈 것.
- 비용 $2.06/6콜. 세대를 늘리면(예: 6 -> 20) 선형으로 비용 증가.

## 관련 파일

- `model/llm.py` (`ClaudeBundleProposer`, `_SEEDS_BUNDLE`, `_SYSTEM_BUNDLE`) - 미커밋
- `model/experiment.py` (`evolve_bundle`, `evaluate_bundle`) - 미커밋
- `data/results/2026-08-13-bundle_evolution_result.json` - 세대별 전체 로그
  (부모/프롬프트/응답/반성/거부된 후보 포함)
