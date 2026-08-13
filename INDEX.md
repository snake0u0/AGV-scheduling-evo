# INDEX - research-agent 프로젝트 지도

> **새 세션은 여기부터.** 그다음 `STATUS.md`(현재 상태·다음 할 일)를 읽으면 방향이 잡힙니다.

연구 주제: **FJSP-AGV(기계+AGV 통합 스케줄링)에서 LLM 기반 자동 휴리스틱 설계(AHD).**
2026-07-23 기준 **B안(정적 문헌 벤치마크 + GA 뼈대)이 유효**, A안(동적/자체생성)은 보류. 상세 = `STATUS.md`.
타깃: KIIE -> SCIE.

## 어디에 뭐가 있나

### 길잡이 문서 (루트)
| 파일 | 무엇 |
|---|---|
| **INDEX.md** | 이 지도 |
| **STATUS.md** | 현재 상태 + 바로 다음 할 일 + 방향 결정 기록. **여기가 핵심** |
| **CLAUDE.md** | 에이전트 작업 규칙(헌법) |
| **docs/research/experiment_protocol.md** | **실험 예산·문헌기준·반복 규칙. "실험 돌려줘" = 이 설정으로** |
| archive/a-track/PLAN.md | A안 실험계획 (보류, 이력 보존용) |

### 코드 (역할 기준)
**`model/`과 `simulator/`에는 지금 방법을 돌리는 데 필요한 것만 둔다.** 방법이 바뀌면
안 쓰는 것은 그때그때 `archive/`로 보낸다(2026-08-13 정리).

| 폴더 | 무엇 |
|---|---|
| **simulator/** | 문제와 평가. 파서 3종·travel matrix·타이밍 코어·4슬롯 구성형 빌더. **model/에 의존하지 않음** |
| **model/** | 방법. 규칙 컴파일러(`rules.py`), 4슬롯 proposer(`llm.py`), CLI 백엔드(`llm_backend.py`), 진화 루프(`experiment.py`) |
| **experiments/** | 캠페인 스크립트(실험 1개 = 파일 1개) + `common.py`(공용 하네스) + `plots.py`(그림·비교표) |
| **archive/** | 은퇴 자산. `a-track/`(동적 A안), `ga-era/`(GA·LNS 시대 + 그 캠페인 11개), `demo/`, `lit/` |

회귀 테스트 4종 - 아무거나 건드린 뒤엔 이걸 돌린다:
```
python -m simulator.test_paper_example      python -m simulator.test_replay_deroussi
python -m simulator.test_dispatch           python -m experiments.test_reported_numbers
```
구성형 진화를 건드렸다면 결정성도 확인한다(같은 번들 -> 같은 Cmax):
`evaluate_bundle(best_bundle, train)` 이 저장된 `best_train_fitness` 와 정확히 일치해야 한다.

### 데이터
| 위치 | 무엇 |
|---|---|
| **data/instances/fjspt-lucasberter/** | FJSPT 벤치마크. 인스턴스 + travel matrix + 공표 해. 포맷 3종·함정 = `STATUS.md §데이터 자산` |
| **data/results/** | 캠페인 결과 json |
| **data/papers/** | 정독용 PDF 5편 (Ham2020, Han2024, Homayouni2023, Kumar2011, Meng2025) |

즉시 실험 가능: **Dauzere 54 케이스**(18 x 차량 2/4/6) + **DeroussiNorre 10 케이스**.
travel matrix가 없어 아직 막힌 계열: fattahi(20), Homayouni_Brandimarte. 미보유: Kumar EX-series 57개.

### 연구 문서
| 위치 | 무엇 |
|---|---|
| **docs/research/han2024_formulation_notes.md** | **MILP 정식화 + 디코딩 절차. evaluator 설계도** |
| docs/research/benchmark_anchor_notes.md | FJSPT 벤치마크 혈통·구조 |
| docs/research/novelty_sweep.md | 경쟁논문·빈칸 검증 (2026-06-09, 재확인 필요) |
| docs/research/cards/ | 논문 요약카드 9편 |
| archive/a-track/research_plan.md | A안 마스터플랜 (보류) |
| docs/research/contribution.md, simulator_spec.md, proposal_kiie.md | A안 계열 문서 (보류) |
| **docs/reports/** | 결과 보고서(스텝마다 1개, 두괄식). 진행 추적은 여기서 |
| docs/discussions/ | `/dh-discuss` 문답 기록. 보고서가 "무엇을 보여줬나"라면 여기는 "내가 어떻게 이해했나" |
| docs/research/pdfs/ | 논문 PDF. **Zotero가 linked_url이라 여기가 유일본** (gitignored) |
| lit/ | 문헌수집 파이프라인(collect.py 등) + 프롬프트 |

## 진행 상태 요약 (상세는 STATUS.md)
- [완료] 문헌 계보 추적 + 벤치마크 원본 확보 + Zotero 91편 정리
- [완료] 파서 3종 + 타이밍 코어 + decode + GA + LLM 루프 + 캠페인 3종 + 2x2 ablation
- [완료] 문헌 격차 실측 (65%, 병목은 AGV가 아니라 기계 선택)
- [완료 2026-07-31] **replay 검증 10/10** (fjsp1=134 포함) + 폴더 개편
- [진행] **설계 개정**: 하위문제 4개 전부 진화(슬롯 5개), solver를 GA -> LNS. `STATUS.md` 참고
- [주의] 6/30 캠페인 수치는 tool-contamination 이전 생성 -> 인용 금지
