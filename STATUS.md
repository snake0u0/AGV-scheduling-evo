# START HERE - 여기서 이어서 (resume point)

최종 업데이트 **2026-07-23**. 새 세션에서 "이제 뭘 하면 돼?" -> 이 파일부터.

## 한 줄 현황

**방향을 B안(정적 벤치마크)으로 확정**하고, 문헌 벤치마크 데이터/해/travel matrix를 모두 확보한 상태.
방법론 뼈대(2계층 공진화 + 비분리성 입증)도 정리됨. **다음 = 파서/evaluator/replay 검증 구현.**
LLM 루프는 뭘 진화시킬지 확정된 뒤에 재가동.

## 방향 결정 (2026-07-23 확정)

| | 내용 | 상태 |
|---|---|---|
| **B안** | 정적 문헌 벤치마크(Deroussi&Norre 등) + GA 뼈대, makespan | **유효** |
| A안 | 동적 FJSP, mean tardiness, 자체생성 40-50 AGV + 혼잡 | **보류** |

- A안 문서(`PLAN.md`, `docs/research/research_plan.md`)는 **superseded 표시만** 하고 보존. `sim/` `ahd/` 코드도 삭제하지 않음.
- B안 근거: 문헌과 직접 수치 비교 가능, 공개 best-known 해로 evaluator 검증 가능, DCGA/CP와 같은 링에서 싸울 수 있음.
- B안 약점(인지하고 있음): 이 계보는 **AGV 2대 고정**이고 소규모. 그래서 정적은 **검증용**으로 쓰고, 성능 주장은 동적/불확실 환경에서 한다(아래 링 분리).

### AGV 규모 결정 (2026-07-23 재확정)

**KIIE 스코프에서 40-50 AGV 타깃을 철회.** B안(공개 벤치마크·SOTA 비교)과 정면 충돌하기 때문 -
문헌 어디에도 6대를 넘는 FJSP-AGV 인스턴스가 없어(전부 확인함: Deroussi/Kumar/Homayouni-Fontes=2대,
Berterottière 자체 확장=2·4·6대 최대), 40-50대에서는 비교할 SOTA/best-known 자체가 존재하지 않는다.
비교 불가능한 규모를 고수하면 B안을 택한 이유(검증 가능성)가 사라짐.

- **새 스코프**: AGV 2·4·6대(Berterottière의 `Berterottiere/dpp{2,4,6}veh/` 확장 그대로 재사용).
  같은 job 데이터를 대수만 바꿔 실험한 문헌 결과가 이미 있어 스케일링 곡선(대수↑ → 성능/이득 변화)을
  **전부 문헌 앵커 위에서** 그릴 수 있음 - 손해가 아니라 오히려 깔끔한 실험 축.
- 40-50 AGV(A안 산물)는 **이번 논문과 완전히 분리**, SCIE 확장이든 별도 컨트리뷰션(우리가 새 벤치마크를
  만들어 오픈소스)이든 나중에 독립적으로 재검토. 지금 당장 되살릴 필요 없음.

## 지금 뭘 하면 되나 (우선순위)

**2026-07-23 갱신**: 1번 완료, 3번은 데이터 문제로 계획 수정.
설계 = `docs/reports/2026-07-23-skeleton-evaluator-design.md`,
결과 = `docs/reports/2026-07-23-evaluator-implementation-and-replay.md`.

1. **[완료] 파서 3종 + 타이밍 코어** - `fjspt/` 패키지. 포맷 A/B/C 전부 동작.
   **타이밍 코어는 Berterottière(2024) 논문의 워크드 예제로 검증 통과**(Cmax 13, 중간 시각까지 일치).
2. **[완료] decode + rules + GA** - `2026-07-24-decode-ga-skeleton.md`. decode 자기검증 180/180 일치.
   GA가 문헌 Table 8과 같은 자릿수(+13~43%, 뼈대 GA vs 600초 tabu라 예상된 격차). D1/D2 비지배성 재현.
   재현: `python -m fjspt.test_paper_example` / `test_ga_operators` / `test_decode_selfcheck`
3. **~~replay 검증~~ - 이 데이터셋에서는 불가능**. 공개 해 파일의 M/V 시퀀스가 헤더 Cmax와 모순
   (2대 케이스는 적재이동 합만으로 Cmax 초과 - 시뮬레이터와 무관한 산술). 54/54 불일치.
   **-> 레포 해 파일 헤더의 Cmax는 인용 금지. 논문 Table 8(data set 1은 Table 4) 값만 인용.**
   fjsp1 -> 134도 이동시간 행렬 미확보로 여전히 막힘(가설 8종 전수 실패, Deroussi&Norre 2010 원문 필요).
4. **[완료] experiment.py + LLM 루프 연결** - `2026-07-24-llm-loop-first-campaign.md`.
   전체 파이프라인(파서->decode->GA->진화->실제 claude CLI) 동작. `fjspt/llm.py`(B안 proposer,
   ahd/llm.py의 _complete 재사용), `fjspt/experiment.py`(evolve/compare/train-test 분할).
   **첫 캠페인 결과는 결론적이지 않음(정직하게)**: 진화 규칙 `-arrival - wait/(remaining_ops+1)`이
   train에서 D1/D2 이김(1.3%)이나 test에서 평균만 0.09% 앞서고 인스턴스별 best-of(D1,D2)엔 3승12패.
   예산이 데모 수준(pop12x4세대, GA30x30, 시드1). **본 캠페인 필요**(pop20x8~10세대, GA60x60, 시드3,
   2/4/6대, ~$1-2, 1-2h) + Wilcoxon 유의성 검정. 이길지는 미지수 = 그게 진짜 실험.

## 코드 자산 (B안, 2026-07-24 완성)

`fjspt/` 패키지 (A안 `sim/`·`ahd/`와 분리, 둘 다 안 건드림):
- `instance.py` 파서 3종 + 데이터셋 레지스트리 | `solution.py` 해 모델+파일파서
- `timing.py` 타이밍 코어(논문 예제 검증) | `evaluator.py` decode(자기검증 180/180)
- `rules.py` D1/D2+표현식 컴파일 | `ga.py` GA(DCGA 구조, 단위테스트)
- `llm.py` B안 proposer(실제 claude CLI) | `experiment.py` evolve/compare/분할
- `replay.py` (데이터 모순으로 게이트 불가, §3 참고)
- 테스트: `python -m fjspt.test_paper_example` / `test_ga_operators` / `test_decode_selfcheck`

## 신뢰하면 안 되는 것

- **6/30 캠페인 수치 전부(P +1.7%, ReEvo 비교, B5/B6)**: tool-contamination 수정(commit `3a8ad01`, 7/4) **이전**에 생성됨.
  재실행 전까지 인용 금지. 보고서 `docs/reports/2026-06-30-campaign-L1.md`에 결론으로 박혀 있으니 주의.
- 게다가 그 수치는 A안(동적/tardiness) 세팅이라 B안과 직접 연결되지 않음.

## 방법론 뼈대 (2026-07-23 정리)

**빈틈**: FJSP-AGV는 하위문제가 4개(기계배정 / 기계순서 / AGV배정 / AGV순서)인데,
- 메타휴리스틱(Han 2024 DCGA, Meng 2025, Homayouni BRKGA)은 **앞의 2개만 진화**시키고 AGV측 2개는 **고정 디코딩 규칙**에 위임.
  Han은 Decoding1/Decoding2 중 우열을 못 가려 이중 집단으로 회피함(논문이 스스로 인정: MFJS04에서 1152 vs 1144, 다른 예제는 1643 vs 1688로 역전).
- RL/NCO(Cheng 2025, Li 2025 TSMC, Wang 2025)는 **사람이 만든 규칙 풀에서 선택하거나 가중치만 조정**. 전역 최적화가 아니라 구성적 디코더 학습.
- 즉 **양 계보가 같은 자리를 비워뒀고, 거기가 우리 자리**.

**제안 구조 (2계층 공진화)**: 해 수준 GA(OS/MS) x 규칙 수준 LLM(AGV 배정/순서 규칙 동시 진화).
DCGA와 같은 인코딩/벤치마크/목적함수를 쓰므로 비교가 공정하고, Decoding1/2가 그대로 ablation이 됨.

**수학적 입증 경로**:
- disjunctive graph로 통합 정식화. 핵심: **기계 배정 하나가 노드 가중치(`pt`)와 아크 가중치(`Tr`)를 동시에 바꿈**(일반 FJSP는 노드만). 이게 분리 불가의 근거.
- 비분리성 명제 + 반례 인스턴스(2 job x 2 op, 2 machine, 2 AGV면 충분). 순차 최적화가 임의로 나빠질 수 있음을 travel time 파라미터로 보이면 강화됨.
- 실증 뒷받침: arXiv 2604.24117 (joint vs modular coordination gap, 2026-04). 단 **병목 상황에서 joint 이점이 줄어든다**고 하므로 우리 결과 해석 프레임으로도 필요.

**링 분리** (성능/해석성/강건성 동시 달성):
- 정적 벤치마크 = **검증용**. "DCGA-CP는 600초(해 파일 헤더에 `time: 600.1`로 박혀 있음), 우리는 밀리초에 X% 이내" 프레이밍. 여기서 이기려 하지 않음.
- 동적/불확실 = **주장하는 링**. 상대는 GA/CP가 아니라 규칙선택형 RL. 분포 이동(도착률/고장률/AGV대수) 하에서 성능 저하폭 비교 = 강건성.

## 데이터 자산 (2026-07-22 확보)

`docs/data/instances/fjspt-lucasberter/` (github.com/lucasberter/FJSPT 전체)

폴더가 **입력(인스턴스)과 출력(해)** 두 종류로 갈리는데 README에 설명이 없으니 주의:
- 인스턴스: `DeroussiNorre/`(10) `fattahi/`(20) `Dauzere_Data/Text/`(18x2) `Homayouni_Brandimarte/`(대문자 B)
- **해(결과)**: `Deroussi/` `Homayouni_brandimarte/`(소문자 b) `Homayouni_fattahi/` `Berterottiere/dpp{2,4,6}veh/`
- travel matrix: `BerterottiereTravelTimes/layout{5,8,10}.txt` - **(m+1)x(m+1) 비대칭**. 행=출발, 열=도착. 인덱스 0 = L/U.

포맷 3종:
- **A. Bilge-Ulusoy 계보**(`DeroussiNorre/`): `nJob nMachine 유연도` / op당 `대체기계수 m m 공통시간`. 대체기계 2개의 **처리시간이 같고** 기계가 (1,2)(3,4)... 로 짝지어짐.
- **B. 표준 FJS**(`Dauzere_Data/`, `Homayouni_Brandimarte/`): `nJob nMachine 평균` / op당 `적격기계수 (기계,시간)...`. op마다 적격기계수와 시간이 다름.
- **C. Fattahi**(`fattahi/`): `총op수 선행관계수 기계수` / 선행쌍 리스트 / op당 `적격기계수 (기계,시간)...`. **job 경계가 선행관계로 표현됨.**
- **해 파일**: 헤더에 `#vehicles / Cmax / iterations / time`, 그 아래 `M1 ...`(기계별 연산순서) `V1 T..`(차량별 운반순서). **전체 시퀀스가 다 있음** -> replay 검증 가능.

### 주의: 확인된 문제 2가지
1. **`Homayouni_Brandimarte/setb4xxx.txt`와 `seti5xxx.txt`가 바이트 단위로 동일** (업스트림 레포 파일 착오로 보임).
   둘 다 헤더 `15 18 1`인데, seti5(15job x 15기계 +3)는 18이 맞지만 setb4(15 x 11 +3)는 14가 나와야 함.
   **둘을 별개 인스턴스로 실험에 넣고 보고하면 논문 레벨 오류.** 사용 전 원 출처에서 setb4xxx를 다시 받을 것.
2. **Data set 1(Bilge-Ulusoy 계보)용 travel matrix가 레포에 없음.** `BerterottiereTravelTimes/`는 Dauzere용(5/8/10 기계).
   `DeroussiNorre/`에 맞는 4기계 레이아웃(5x5)은 Bilge & Ulusoy 1995 논문(Zotero `GP6HQQSG`) 또는 Kumar 2011(`KQK9HJMJ`) Fig 3에서 **직접 전사**해야 함.
   -> 착수는 travel matrix가 이미 있는 **Dauzere 계보가 더 빠름**.

`docs/data/papers/` - 정독용 PDF 5편(Ham2020, Han2024, Homayouni2023, Kumar2011, Meng2025).

## 읽는 순서 (Zotero `agv-llm-heuristic` = JIREF4BS, 91편)

우선순위 최상위 3편:
1. **Bilge & Ulusoy 1995** `GP6HQQSG` - 문제 원전 + travel matrix 출처
2. **Zhou, Yang & Zheng 2019** `P584GSG3` - 기계배정+공정순서 **공진화** GP. 우리 joint의 방법론적 선조. "2019년에 이미 했잖아"에 답하려면 필독
3. **arXiv 2604.24117** joint vs modular coordination gap - **아직 Zotero에 없음, 추가 필요**

그 다음: Medikondu&Rao 2017 `NV3DRCFI`(디스패칭룰 통합), Zhang Min 2023 `5HFVPVZ6`(운반부족 동적 FJSP),
Homayouni BRKGA `I5P4WGSW`(카드에 미확인 항목 많음 - 전문 읽기 필요), MRE `R6EF89RJ`(차별 문장용, 전문 미확보).

**Zotero에 없어서 채워야 할 원전**: Deroussi&Norre 2010, Fattahi 2007, Dauzere-Peres&Paulli 1997, Hurink 1994,
Berterottiere 2026(total travel time, hal-05409040), arXiv 2604.24117.

## 재개 검증 (코드 살아있는지)

```
cd ~/project/research-agent
python sim/run_eval.py     # A안 시뮬 sanity (보류 상태지만 동작 확인용)
```

## 핵심 사실 캐시

- **타깃**: KIIE 학술대회 -> SCIE 저널.
- **Zotero**: 컬렉션 `agv-llm-heuristic` (key `JIREF4BS`, **91편**). 2026-07-23 중복 6쌍 정리 완료(메모 있는 사본 유지).
  주의: 6/8 배치로 넣은 항목 상당수가 **`linked_url`(파일 없음)** -> 로컬 PDF `docs/research/pdfs/`가 유일본.
- **위협 1순위**: HUST(Gao Liang / Li Xinyu) 그룹 - `Z8A3C7S9`, `Z33PYZZ7`, DSevolve. 속도로 선점.
- **A안 자산(보류, 삭제 안 함)**: `sim/`(DES + salabim 트윈 + crosscheck), `ahd/`(LLM 루프 + campaign + gp).
- **프로젝트 가이드**: `CLAUDE.md`(헌법), agent `novelty-watch`, skill `ahd-loop`.
