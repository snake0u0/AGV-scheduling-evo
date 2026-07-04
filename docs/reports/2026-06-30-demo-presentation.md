# 발표용 정리 — FunSearch식 LLM 프로그램 탐색 데모 (Online Bin Packing)

작성 2026-06-30. 교수님 발표용 종합 문서. 코드=`demo/bpp.py`, 데이터=`demo/funsearch_data.json`.
원논문: Romera-Paredes et al., *Mathematical discoveries from program search with LLMs*, Nature 625 (2024).
원 저장소: github.com/google-deepmind/funsearch.

---
## 1. 한눈에 (무엇을 만들었나)
- FunSearch의 **온라인 빈패킹 실험**을, 그들의 **실제 평가기·골격·데이터로** 재현하고, 그 위에서 **우리 LLM(claude CLI)이 규칙(Python 함수)을 진화**시키는 데모.
- **검증**: 우리 harness가 논문 **Table 1을 소수점까지 재현** → 평가 파이프라인이 FunSearch와 동일함을 입증.
- **우리 결과**: LLM(Sonnet)이 Best-Fit에서 출발해 10세대 만에 Best-Fit을 능가하는 해석가능 규칙을 진화.

---
## 2. 아키텍처 (전체 루프)
```
   ┌──────────────────────────── 진화 루프 (1세대) ────────────────────────────┐
   │                                                                            │
   │   ① Programs DB(elite pool)                                                │
   │        │  best-shot: 상위 2개 프로그램 + 각 excess%                          │
   │        ▼                                                                    │
   │   ② SAMPLER  ── 프롬프트 ──▶  LLM(claude CLI, Sonnet)  ── k개 priority 함수 ─┐│
   │        ▲                                                                   ││
   │        │                                                                   ▼│
   │   ④ 점수와 함께 DB에 저장                                          ③ EVALUATOR │
   │        │                                                    (compile→online_ │
   │        └──────── (elite 재선정, 하위 폐기) ◀──── excess% ────  binpack→count) │
   └────────────────────────────────────────────────────────────────────────────┘
   반복 N세대 → 최종: valid로 elite 선택 → test로 보고
```
- **진화 대상 = `priority` 함수 하나.** 나머지(패킹 루프·평가·argmax)는 **고정 골격**.
- FunSearch 핵심 아이디어: **해가 아니라 "해를 만드는 프로그램"을 탐색**하고, **검증 가능한 evaluator**로 선택 → 해석가능·환각내성·스케일.

---
## 3. 입력 / 출력 (Input / Output)
**Input**
- 문제 인스턴스: `items`(도착 아이템 크기 리스트) + `capacity`(bin 용량). 데이터셋 = FunSearch 실제 **OR3**(20인스턴스, 용량 150, 500 items) + **Weibull 5k**(5인스턴스, 용량 100, 5000 items).
- 초기 프로그램(skeleton) = Best-Fit `priority` (§5.1).

**Output**
- 진화된 `priority` **Python 함수**(§5.4) + 성능 지표 **excess%**(= (사용 bin 수 − 하한)/하한, 낮을수록 좋음).

---
## 4. 결과
### 4.1 검증 — 논문 Table 1 재현 (우리 평가기 == FunSearch)
| heuristic (그들 evaluator + 데이터) | OR3 | Weibull 5k |
|---|---|---|
| Best-Fit | 5.37% | 3.98% |
| Worst-Fit | 148.51% | 151.53% |
| FunSearch OR-discovered | **3.11%** | 3.03% |
| FunSearch Weibull-discovered | 12.77% | **0.68%** |
| **Ours: LLM-evolved (Sonnet, OR3)** | **4.20%** | **2.87%** |

- 굵은 FunSearch 수치가 논문 Table 1과 **정확히 일치** → harness 동일 검증.
- **우리 규칙**: 전체 OR3에서 4.20%(Best-Fit 5.37% 대비 **+21.8%**), Weibull에서도 2.87%(학습 안 했는데 3.98%보다 좋음, **전이 성공**). 단 FunSearch의 데이터셋-특화 규칙(OR 3.11%, Weibull 0.68%)엔 못 미침(그들은 10^6 샘플).
- 교차: 규칙은 **분포 특이적** — Weibull 규칙을 OR3에 쓰면 12.77%(Best-Fit보다 나쁨).

### 4.2 진화 과정 (Sonnet, OR3, 10세대)
- train 최고 excess: 6.03% → 5.04% → 4.87% → **4.83%** (세대마다 개선).
- test(4 인스턴스) 초과율 **2.758%** vs Best-Fit 4.001% (+31.1%; 작은 split이라 전체 수치 4.20%보다 낙관적).

---
## 5. 구성요소 상세

### 5.1 초기 skeleton (진화 대상 `priority`의 시작점 = Best-Fit)
```python
def priority(item, bins):
    """Returns priority with which we want to add item to each bin.
    Args:  item: Size of item to be added to the bin.
           bins: Array of capacities for each bin.
    Return: Array of same size as bins with priority score of each bin."""
    return -(bins - item)                # Best-Fit: 남는 용량이 가장 작은 bin 선호
```
+ 고정 골격: `get_valid_bin_indices` / `online_binpack` / `evaluate` (§5.3). LLM은 **`priority` 본문만** 바꿈.

### 5.2 프롬프트 (초기 system + best-shot vary)
- **System 프롬프트**(고정 골격을 그대로 노출 — LLM이 문맥을 정확히 알게):
```
You improve the `priority` function of this FUNSEARCH online bin-packing skeleton:
    def get_valid_bin_indices(item, bins): return np.nonzero((bins - item) >= 0)[0]
    def online_binpack(items, bins):
        for item in items:
            best = valid[np.argmax(priority(item, bins[valid]))]; bins[best] -= item
    # evaluate() minimizes the number of used bins.
def priority(item, bins): -> numpy array of scores; item goes to the HIGHEST-scoring bin.
You may use numpy... Explore NON-OBVIOUS scoring — the best heuristics do not always pick the tightest bin.
```
- **best-shot vary 프롬프트**: "현재 상위 2개 `priority`(+각 excess%)를 보여주고 → 더 적은 bin을 쓰는 개선판 k개를 생성하라"(간결 출력 강제).

### 5.3 자동평가기 (Evaluator) — FunSearch 코드 verbatim
```python
def get_valid_bin_indices(item, bins):
    return np.nonzero((bins - item) >= 0)[0]        # 사전할당 배열 -> 빈 bin(용량 C)도 후보

def online_binpack(items, bins, priority):
    for item in items:
        valid = get_valid_bin_indices(item, bins)
        best_bin = valid[np.argmax(priority(item, bins[valid]))]
        bins[best_bin] -= item

def evaluate(instances, priority):                  # 인스턴스별: bins=[cap]*num_items,
    ...                                             #   사용 bin 수 = (bins != cap).sum()
    return mean(num_bins)                           # 평균 bin 수(최소화). excess=(avg-하한)/하한
```
- 안전장치: LLM 코드는 **제한 exec**(numpy/max/min/abs/len/range/sum만, no builtins/I/O) + compile·스모크테스트 통과분만 채택.

### 5.4 LLM이 진화시킨 `priority` (Sonnet, OR3)
```python
def priority(item, bins):
    r = bins - item
    C = np.max(bins)
    dead  = (r > 0) & (r < item)                    # 다음 아이템(크기 item)이 못 들어가는 '죽은 gap'
    exact = r == 0                                   # 정확히 딱 맞는 fit
    return -r - dead*(r + bins) + exact*C - (bins == C)*item*0.1
    #      best-fit  죽은gap 페널티     정확fit 보상    새 bin 약간 페널티
```
→ **FunSearch가 발견한 것과 같은 통찰**을 자율 재발견: "tight만 좇지 말고, 못 쓰게 될 작은 gap을 피하고, 정확fit을 보상."

### 5.5 분산 시스템 (FunSearch) vs 본 데모
| 항목 | FunSearch (논문) | 본 데모 |
|---|---|---|
| 구조 | **비동기 분산**: 3종 워커 — Programs DB + **Samplers**(LLM 호출) + **Evaluators**(채점) | **단일 프로세스·순차** |
| 병렬 | **15 samplers + 150 CPU evaluators**(LLM은 가속기, 평가는 값싼 CPU) | sampler 1(claude CLI 호출) + inline evaluator |
| Programs DB | **island 모델**(다중 population), 상위·짧은 프로그램 선호 샘플, 주기적 하위 island 폐기 | 단순 **elite pool**(상위 k) |
| 프롬프트 | best-shot(island에서 k=2 샘플) | best-shot(elite 상위 2) |
| 총 샘플 | **~10^6** | **~30**(10세대×3) |
| 목적 | 대규모 병렬로 탐색폭↑·비용↓ (어려운 문제 대응) | 개념 시연(쉬운 문제) |

→ FunSearch의 분산·island·10^6은 **2023년 약한 모델(Codey)의 높은 실패율을 대량 샘플로 보완**하는 성격이 큼. 강한 2026 모델은 샘플당 품질이 높아 **훨씬 적은 샘플로도** 유효(우리 데모가 그 예). 다만 **핵심 아이디어(프로그램탐색+검증 evaluator)** 는 모델이 세질수록 오히려 유용.

---
## 6. 모델 선택 (Haiku vs Sonnet) — 왜 Sonnet
비자명한 numpy 프로그램 합성 과제. **실증: Haiku는 10세대 내내 Best-Fit을 못 넘음(discovery 실패)**, Sonnet만 개선+전략 재발견. → discovery 성패를 가르는 게 모델 역량이라 **Sonnet 채택**(더 비싸고 verbose하지만).

## 7. 정직한 한계
- 소예산(~30 샘플)·**단일 런·작은 test split → 고분산**(같은 셋업 다른 런에서 +52.8% vs +31.1%). Table-1급 강건 수치 아님.
- FunSearch 데이터셋-특화 규칙(0.68%)엔 못 미침(그들 10^6 vs 우리 ~30).
- Sonnet verbose → 가끔 호출 timeout(간결 프롬프트로 완화).

## 8. 실행법
```
python -m demo.bpp                                  # 비교표(재현+우리규칙), LLM 없이·무료
DEMO_EVOLVE=1 DEMO_MODEL=sonnet DEMO_GEN=10 python -m demo.bpp   # LLM 진화 재현
```
관련 상세 보고서: `2026-06-30-funsearch-native-swap.md`(Table1 재현), `2026-06-30-funsearch-native-evolution.md`(진화 상세).
