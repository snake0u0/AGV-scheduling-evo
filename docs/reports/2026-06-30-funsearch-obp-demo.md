# 보고서 — FunSearch식 LLM 프로그램 탐색 데모: Online Bin Packing

작성 2026-06-30. 대상 논문: Romera-Paredes et al., *Mathematical discoveries from program search
with large language models*, Nature 625 (2024) — "Bin packing" 절 + Fig 1/2b/6, Table 1.

## 결론 (한눈에)
- FunSearch의 OBP 실험을 **faithful하게(간소화) 재구현**했다: LLM이 **Python 프로그램**(`heuristic(item, bins)` numpy 함수)을 진화, best-fit에서 출발, **하한 대비 초과 bin 비율(%)** 로 평가. (이전 데모는 단일행 표현식이라 논문의 "프로그램 진화" 핵심을 놓쳤음 → 이번에 수정.)
- **결과(Haiku)**: 아키텍처는 정상 작동(세대당 valid 프로그램 8개 생성, fails=0)했으나 **Best-Fit을 못 넘음**(test 초과율 3.274% = best-fit, +0.0%). 10세대 내내 정체.
- **해석**: 방법·아키텍처는 재현됐고, 미달의 원인은 **모델 역량(Haiku ≪ FunSearch의 Codey) + 소규모 예산**. FunSearch는 N=5,000+ 인스턴스 + ~10^6 샘플 + island 모델로 best-fit을 크게 이겼음(Table 1: Weibull에서 0.68% vs best-fit 3.98%).

## 6하원칙
- **누가(Who)**: 연구자(오케스트레이션) + LLM(**Haiku**, 로그인된 `claude` CLI로 호출; API 키 없음)이 heuristic 프로그램 생성자.
- **무엇을(What)**: 온라인 빈패킹 heuristic을 LLM 프로그램 탐색으로 진화시키는 데모.
- **언제(When)**: 2026-06-30.
- **어디서(Where)**: `demo/bpp.py` (자체완결). 기존 프로젝트 기계(`ahd.llm.ClaudeCliLLM`) 재사용.
- **왜(Why)**: 교수님 요청 — 쉽고 표준적인 문제로 LLM-AHD 방법론을 데모하고 원논문과 대조. OBP는 FunSearch의 대표 예제라 방어가 쉽다.
- **어떻게(How)**: 아래 아키텍처.

## 전체 루프 (아키텍처)
```
        ┌─────────────────────────── 진화 루프 (evolve_bpp) ───────────────────────────┐
        │                                                                               │
 [seed: best-fit 프로그램]                                                               │
        │                                                                               │
        ▼                                                                               │
   ┌─────────┐   best-shot 프롬프트    ┌──────────────┐   heuristic 프로그램들   ┌─────────────┐
   │ elite   │ ───(상위 2개 프로그램 + │  LLM         │ ──(def heuristic(item,  │ compile +   │
   │ pool    │    각자 excess%)───────▶│ (claude CLI, │    bins): ... 8개)──────▶│ 안전 exec   │
   │ (top-k) │                         │  Haiku)      │                          │ (numpy만)   │
   └─────────┘                         └──────────────┘                          └─────────────┘
        ▲                                                                               │ valid 프로그램
        │                                                                               ▼
        │                              ┌──────────────────────────────────────────────────────┐
        │   fitness로 재정렬            │ EVALUATE: 각 프로그램으로 온라인 패킹                   │
        └──────────────────────────────│  - item마다: fit되는 bin들 중 heuristic 최고점에 배치  │
                                        │  - 없으면 새 bin. 목적 = (사용bin/하한 − 1) 평균 (낮을수록↑)│
                                        └──────────────────────────────────────────────────────┘
  선택: train으로 진화 → valid로 elite 선택 → **test(더 큰 인스턴스)로만 보고** (일반화)
```
- **Specification**: `evaluate` = 초과 bin 비율; `solve` = "fit되는 bin 중 heuristic argmax"(고정 골격); **진화 대상 = `heuristic` 함수만** (FunSearch와 동일 개념).
- **표현**: 다중행 numpy 프로그램(단일 표현식 아님). `heuristic(item, bins_array)->scores_array` — 전역 bin 배열을 보고 "가장 tight한 bin을 찾아 특별처리" 같은 로직 표현 가능.
- **안전 실행**: `exec`를 `__builtins__` 제거 + numpy/min/max/abs/len/range/sum만 노출한 네임스페이스에서. 컴파일·스모크테스트 실패 시 폐기.

## 논문(FunSearch) 대비 비교
| 항목 | FunSearch (논문) | 본 데모 (`demo/bpp.py`) |
|---|---|---|
| 진화 대상 | Python **프로그램**(heuristic 함수) | **동일** (다중행 numpy 함수) ✓ |
| heuristic signature | `heuristic(item, bins:np.ndarray)->np.ndarray` | **동일** ✓ |
| 출발점 | **Best-Fit** | **동일** ✓ |
| 적합도 | 하한 대비 **초과 bin 비율**(L2 lower bound) | 초과 bin 비율(연속 하한 sum/cap) ≈ 동일 |
| 배치 규칙 | fit되는 bin 중 heuristic argmax | **동일** ✓ |
| 인스턴스 | OR-Library + Weibull(5k/10k/100k), train-size≠test-size | Weibull, train 200 / **test 500(더 큼)** ✓(축소) |
| 탐색 구조 | **island 모델** + programs DB, best-shot(k=2) | **단순 elite pool** + best-shot(2) ✗(간소화) |
| 예산 | **~10^6 샘플**, 분산 | ~80개 프로그램(10세대×8) ✗(대폭 축소) |
| 모델 | Codey (PaLM2 코드 파인튜닝) | **Haiku** (claude CLI) ✗(더 약함) |

즉 **문제 정식화·표현·평가·배치·출발점은 논문과 일치**시켰고, **탐색 규모·구조·모델**만 데모 수준으로 축소.

## 결과 (test = Weibull 4×500 items, 초과율 낮을수록 좋음)
| 방법 | 초과율(test) |
|---|---|
| Worst-Fit | 8.498% |
| Best-Fit (baseline·출발점) | 3.274% |
| **LLM(Haiku) 진화 heuristic** | 3.274% (**+0.0%**, best-fit과 동일) |

- 진화 로그: 10세대 내내 train 최고 excess가 4.491%(best-fit)에서 개선 없이 정체. 세대당 valid 프로그램 8개 생성(fails=0), 그러나 어느 것도 best-fit 초과 못함.
- 최종 선택 프로그램 = best-fit(`-(bins - item)`) 그대로.
- 비용: Haiku 10콜, out_tok 86,610(장황), ~$0.51.
- sanity: Best-Fit(3.27%) ≪ Worst-Fit(8.50%) — 논문 Table 1의 best-fit Weibull ~3.8–4%와 동일 수준. 우리 파이프라인·메트릭은 논문과 정합.

## 왜 Best-Fit을 못 넘었나 (정직)
1. **모델 역량**: Best-Fit을 넘으려면 "매우 tight할 때만 tight bin, 아니면 여유 bin에 두어 작은 gap 방지"라는 비자명 로직(논문 Fig 6)을 프로그램으로 합성해야 함. **Haiku는 이를 10세대 내 못 찾음**(약한 모델). Sonnet은 앞선 표현식 데모에서 모듈러 규칙을 찾은 바 있어 더 유망.
2. **소규모 예산·인스턴스**: 논문은 N=5,000+ + ~10^6 샘플 + island 다양성으로 이득이 누적. 우리는 N=200/500 + 80프로그램이라 미세 이득이 노이즈에 묻힘.
3. **island 부재**: 단순 elite pool은 조기 수렴/다양성 부족.

## 한계 / 다음
- **더 강한 데모 원하면**: 모델을 **Sonnet**으로(프로그램 합성력↑, ~$1–2), 세대·pop·인스턴스 확대, (선택) island 모델 근사. 이러면 best-fit 초과 가능성 큼.
- 현재로도 **"방법론·아키텍처가 논문과 정합하게 작동함 + 모델 역량이 discovery의 병목"** 이라는 정직한 데모·발견으로 충분.

## 관련 파일
- 코드: `demo/bpp.py` (FunSearch식). 실행: `DEMO_MODEL=haiku python -m demo.bpp` (또는 `sonnet`; `DEMO_LLM=0`=mock).
- 재사용: `ahd/llm.py::ClaudeCliLLM`. 논문 PDF: `demo/02. Mathematical discoveries ...pdf`.
- 이전(단일표현식) 데모 기록: `docs/reports/2026-06-30-demo-bin-packing.md`.
