# 보고서 - 폴더 개편 + Deroussi&Norre 데이터셋 개방 (replay 10/10)

작성 2026-07-31.

## 결론

1. **한 달 넘게 막혀 있던 replay 검증 게이트가 통과했다. fjsp1-10 전부 공표 makespan을 정확히 재현한다(10/10).**
   막혔던 이유는 시뮬레이터가 아니라 **잘못된 전제**였다. 이 인스턴스들의 기계 수를 4대로 알고 5x5 이동시간
   행렬을 재구성하려 했는데, 실제로는 **8대**이고 행렬은 9x9다. 유연도 2는 기계가 (M1;M2)(M3;M4)(M5;M6)(M7;M8)로
   **짝지어져** 나오는 것이지 기계가 4대여서가 아니었다. 전제가 틀렸으므로 이전 가설 8종은 전부 실패할 수밖에
   없었다.
2. 행렬은 추측이 아니라 **원출처에서 전사**했다. Han et al. (2024)이 본문에 적어둔 데이터셋 페이지에
   Deroussi&Norre 2010 인스턴스 PDF가 올라와 있고, 그 Table 5가 레이아웃과 이동시간 행렬 전체다.
3. **폴더 구조를 역할 기준으로 개편했다**(`simulator/` `model/` `experiments/` `data/` `docs/` `archive/`).
   기존 회귀 테스트 3종이 전부 통과하는 것을 완료 판정으로 삼았고, 통과했다.
4. **"5개 데이터셋 전부"는 아직 미해결.** 이 페이지는 data set 1 전용이었다. Kumar EX-series 57개와
   Homayouni&Fontes 계열(fattahi / Brandimarte)의 이동시간은 다른 출처가 필요하다.

## 1. Deroussi&Norre 데이터셋 개방

### 출처

- 페이지: `fastmanufacturingproject.wordpress.com/2019/04/11/fjspt-instances/`
  (Han et al. 2024 본문이 지목한 다운로드처)
- 파일: `.../wp-content/uploads/2019/04/fjspt_instances_deroussinorre2010-1.pdf` (2쪽)
  - **Table 4** = job set 10개 (가공시간·대체기계)
  - **Table 5** = 레이아웃 그림 + **이동시간 행렬 9x9 (LU + M1..M8), 비대칭**
- 전사본: `data/instances/fjspt-lucasberter/DeroussiNorreTravelTimes/layout8.txt`
  근거·주의사항: 같은 폴더 `SOURCE.md`

### 교차 확인

Table 4의 Job Set 1과 우리 파서 결과가 일치한다.

| | Table 4 | `parse_format_a` 결과 |
|---|---|---|
| J1 | M1;M2(16) M3;M4(32) M7;M8(24) | `[[(1,16),(2,16)],[(3,32),(4,32)],[(7,24),(8,24)]]` |
| J2 | M1;M2(40) M5;M6(20) M3;M4(36) | 일치 |
| J3 | M5;M6(24) M7;M8(16) M1;M2(30) | 일치 |

### replay 결과 (하드 게이트)

공표 해 파일의 기계·차량 시퀀스를 그대로 타이밍 코어에 넣고, 그 파일 헤더가 주장하는 makespan이
나오는지 본다.

| 인스턴스 | 기계 | 공정 | 공표 Cmax | replay | 판정 | (부수) TTT |
|---|---|---|---|---|---|---|
| fjsp1 | 8 | 19 | 134 | 134 | 일치 | 200 |
| fjsp2 | 8 | 15 | 114 | 114 | 일치 | 150 |
| fjsp3 | 8 | 16 | 120 | 120 | 일치 | 132 |
| fjsp4 | 8 | 19 | 114 | 114 | 일치 | 182 |
| fjsp5 | 8 | 13 | 94 | 94 | 일치 | 124 |
| fjsp6 | 8 | 18 | 138 | 138 | 일치 | 182 |
| fjsp7 | 8 | 19 | 112 | 112 | 일치 | 174 |
| fjsp8 | 8 | 20 | 178 | 178 | 일치 | 238 |
| fjsp9 | 8 | 17 | 144 | 144 | 일치 | 188 |
| fjsp10 | 8 | 21 | 174 | 174 | 일치 | 210 |

**10/10.** 회귀 테스트로 고정: `python -m simulator.test_replay_deroussi`

### 부수 검증 (TTT) - 참고용, 확정 아님

Berterottière et al. (2026) EJOR 332 Table 1이 같은 인스턴스의 총이동시간(TTT)을 준다.
위 표의 TTT는 이번 세션에서 임시 계산한 값이며 아직 코드에 넣지 않았다.

- fjsp1 = 200 -> Table 1 "First" 200과 **정확히 일치**
- fjsp7 = 174 -> Table 1 "Best" 174와 **정확히 일치**
- 8/10이 Table 1의 [Best, Worst] 구간 안에 들어옴
- **불일치 2건**: fjsp4는 182로 Table 1 Best(188)보다 낮고, fjsp5는 124로 Worst(122)보다 높다.
  TTT 정의의 세부(마지막 배송 후 공차 처리 등)가 아직 문헌과 완전히 맞춰지지 않았다는 뜻이다.

**따라서 makespan replay만 검증된 것으로 취급한다. TTT는 미확정이며 인용 금지.**
목적함수가 makespan 단일로 확정됐으므로(2026-07-31 설계 회의) 지금은 보조 지표 이상이 아니다.

## 2. 폴더 개편

역할 기준으로 나눴다. **`simulator/`는 `model/`에 의존하지 않는다**(단방향).

| 새 위치 | 내용 | 이전 위치 |
|---|---|---|
| `simulator/` | 파서 3종, travel matrix, 타이밍 코어, decode, replay, 이벤트 구동 엔진 | `fjspt/{instance,timing,solution,evaluator,replay}.py`, `sim/{agv_fms,policies,rule}.py` |
| `model/` | 규칙, GA, LLM proposer, 실험 드라이버 | `fjspt/{rules,ga,llm,experiment}.py`, `ahd/llm.py` -> `model/llm_backend.py` |
| `experiments/` | 캠페인 스크립트 | `docs/data/campaigns/*.py` |
| `data/{instances,results,papers}` | 데이터 | `docs/data/*` |
| `docs/{reports,research,diagrams}` | 문서 | `docs/*`, `diagrams/` |
| `archive/a-track/` | A안(동적) 코드, `PLAN.md`, `research_plan.md` | `sim/*`, `ahd/*` 잔여 |
| `archive/{demo,lit}` | 발표 데모, 문헌수집 파이프라인 | `demo/`, `lit/` |

`src/`는 두지 않았다. `simulator/`와 `model/`이 이미 역할로 갈려 있어 한 겹 더 씌우면 경로만 길어진다.

### 완료 판정 - 회귀 테스트 4종 전부 통과

```
python -m simulator.test_paper_example       # 타이밍 코어 = 논문 워크드 예제 (Cmax 13)
python -m simulator.test_replay_deroussi     # 신규. 공표 해 10/10 재현
python -m model.test_ga_operators            # POX/균등교차/변이 불변식
python -m model.test_decode_selfcheck        # decode <-> replay 180/180 일치
```

`archive/`로 옮긴 코드는 테스트 대상이 아니다.

## 3. 남은 데이터 문제

| 계열 | 인스턴스 | travel matrix | 상태 |
|---|---|---|---|
| Dauzere (18 x {2,4,6} = 54) | 보유 | `BerterottiereTravelTimes/layout{5,8,10}` | 사용 가능 (기존) |
| **DeroussiNorre (10)** | 보유 | **`DeroussiNorreTravelTimes/layout8`** | **사용 가능 (이번 세션)** |
| fattahi (mfjs, 20) | 보유 | 없음 | 막힘 |
| Homayouni_Brandimarte | 보유 | 없음 | 막힘 |
| Kumar EX-series (57) | **미보유** | 없음 | 막힘 |

즉 지금 즉시 실험 가능한 것은 **64 케이스**(Dauzere 54 + Deroussi 10)다.

막힌 3계열의 이동시간 출처는 Homayouni & Fontes (2021, J Glob Optim)와 Kumar et al. (2011) 쪽이다.
Kumar 2011은 PDF를 로컬 보유 중(`data/papers/Kumar2011_IJAMT_FJSP-AGV_DE.pdf`, Table 4 + Fig 3)이라
전사가 가능하지만 57개는 분량이 크다. Homayouni&Fontes는 아직 출처 미확인.

**이번 성공 사례의 교훈**: 행렬을 추측하지 말 것. 원출처를 찾을 것. 8종 가설 실패에 쓴 시간보다
원 데이터셋 페이지를 여는 데 든 시간이 훨씬 적었다.

## 4. 부수 정정

`STATUS.md`의 다음 기술이 틀렸으므로 정정한다.

> "`DeroussiNorre/`에 맞는 4기계 레이아웃(5x5)은 Bilge & Ulusoy 1995 논문 또는 Kumar 2011 Fig 3에서
> 직접 전사해야 한다"

- 4기계가 아니라 **8기계**, 5x5가 아니라 **9x9**다.
- Bilge&Ulusoy / Kumar 논문이 아니라 **Deroussi&Norre 데이터셋 배포 PDF**가 출처다.
  (데이터셋 페이지 설명: 이 인스턴스들은 Bilge&Ulusoy의 job set과 레이아웃을 쓰되
  "all machines have been duplicated"; 그 복제 결과가 8기계다.)

## 관련 파일

- 이동시간 행렬 + 출처: `data/instances/fjspt-lucasberter/DeroussiNorreTravelTimes/{layout8.txt,SOURCE.md}`
- 로더: `simulator/instance.py::load_deroussi`, `DEROUSSI_STEMS`
- 게이트: `simulator/test_replay_deroussi.py`
