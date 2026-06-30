# INDEX — research-agent 프로젝트 지도

> **새 세션은 여기부터.** 그다음 `STATUS.md`(현재 상태·다음 할 일)를 읽으면 방향이 잡힙니다.

연구 주제: *LLM-Evolved Interpretable Joint Dispatching Rules for Integrated Machine-and-AGV
Dynamic FJSP* — 동적 FJSP에서 기계 시퀀싱 + AGV 디스패칭 규칙을 LLM-AHD로 **동시 진화**. 타깃: KIIE → SCIE.

## 어디에 뭐가 있나

### 길잡이 문서 (루트)
| 파일 | 무엇 |
|---|---|
| **INDEX.md** | 이 지도 |
| **STATUS.md** | 현재 진행 상태 + 바로 다음 할 일 (구 NEXT.md) |
| **CLAUDE.md** | 에이전트 작업 규칙(헌법) |
| **PLAN.md** | 전체 실험계획(개요) — 상세 설계는 `docs/research/research_plan.md`, 실행순서는 `docs/research/execution_roadmap.md` |

### 코드
| 폴더 | 무엇 | 핵심 파일 |
|---|---|---|
| **sim/** | DES 시뮬레이터 + 고전 baseline | `agv_fms.py`(메인 엔진), `agv_fms_salabim.py`(salabim 트윈), `configs.py`(regime·대규모 config), `policies.py`, `rule.py`, `crosscheck_salabim.py`(엔진 교차검증), `viz.py`(시각화), `run_eval.py`(sanity) |
| **ahd/** | LLM-AHD 진화 루프 (핵심 컨트리뷰션) | `loop.py`(진화), `llm.py`(MockLLM + ClaudeCliLLM proposer), `run.py`(실행: `python -m ahd.run`) |

### 연구 문서 / 산출물
| 위치 | 무엇 |
|---|---|
| **docs/reports/** | **결과 보고서**(스텝/실험마다 1개, 두괄식). ← 진행 추적은 여기서 |
| **docs/research/** | 연구 문서: `research_plan.md`(실험설계 마스터), `execution_roadmap.md`(실행 runbook), `benchmark_anchor_notes.md`, `contribution.md`, `novelty_sweep.md`, `simulator_spec.md`, `proposal_kiie.md` + `figures/`(그림) + 문헌데이터(`*.jsonl`, `cards/`, `pdfs/`) |
| **lit/** | 문헌수집 파이프라인: `scripts/`(collect.py 등) + `prompts/`(템플릿) + `pipeline.md`(파이프라인 계획) |
| **.claude/** | agent `novelty-watch`(스쿱 감지), skill `ahd-loop`(실험 절차) |

## 자주 쓰는 명령
```
python -m ahd.run                  # LLM-AHD 루프 (env: AHD_REGIME / AHD_GEN / AHD_TRAIN_N / AHD_REEVO)
python sim/run_eval.py             # 고전 룰 sanity
python sim/crosscheck_salabim.py   # 두 엔진 교차검증
python sim/viz.py                  # 그림 생성 -> docs/research/figures/
```

## 진행 상태 요약 (상세는 STATUS.md)
- ✅ 시뮬 v1: 대규모(40–50 AGV) + 혼잡-지연 + FJSP + 교차검증
- ✅ LLM-AHD 루프: 실제 `claude` CLI proposer, ReEvo 강화, L1에서 +2.1%
- 🔸 진행중: ReEvo old vs new 비교 런
- ⬜ 다음: 캠페인(P vs baselines) → 통계 → 집필
