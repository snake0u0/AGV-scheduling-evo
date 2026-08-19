# INDEX - research-agent 프로젝트 지도

> **새 세션은 여기부터.** 그다음 `STATUS.md`(현재 상태 + 바로 다음 할 일)를 읽으면 방향이 잡힌다.

연구 주제: **FJSP-AGV(기계+AGV 통합 스케줄링)에서 LLM 기반 자동 휴리스틱 설계(AHD).**
2026-07-23 기준 **B안(정적 문헌 벤치마크 + 진화 루프)이 유효**, A안(동적/자체생성)은 보류.
타깃: KIIE -> SCIE.

## 폴더 하나에 역할 하나

| 폴더 | 무엇 | 들어가면 |
|---|---|---|
| **experiments/** | **실험. 1건 = 번호 폴더 1개**(`NNN-YYMMDD-슬러그`) - 코드·결과·그림·보고서가 한 곳 | `experiments/README.md` (실험 8건 요약표) |
| **docs/** | 연구 문서. 프로토콜·정식화·문헌·포지셔닝 | `docs/README.md` |
| **model/** | 방법. 규칙 컴파일러·4슬롯 proposer·CLI 백엔드·진화 루프 | |
| **simulator/** | 문제와 평가. 파서 3종·타이밍 코어·4슬롯 구성형 빌더. **model/에 의존하지 않음** | |
| **tests/** | 게이트 5종. 단위테스트가 아니라 **시뮬레이터 타당성의 증거** | |
| **data/** | 인스턴스·문헌 기준값·PDF | `data/README.md` |
| **study/** | 코드 독해 노트 15편 | |
| **archive/** | 은퇴 자산. 지우지 않고 여기로 보낸다 | 아래 |

`model/`과 `simulator/`에는 **지금 방법을 돌리는 데 필요한 것만** 둔다. 방법이 바뀌면
안 쓰는 것은 그때그때 `archive/`로 보낸다.

## 길잡이 문서

| 파일 | 무엇 |
|---|---|
| **STATUS.md** | 현재 상태 + 바로 다음 할 일 + 방향 결정 기록. **여기가 핵심** |
| **CLAUDE.md** | 에이전트 작업 규칙 |
| **docs/experiment_protocol.md** | **실험 예산·문헌 기준값·실험 폴더 규약. "실험 돌려줘" = 이 설정으로** |
| **docs/han2024_formulation_notes.md** | MILP 정식화 + 디코딩 절차. evaluator 설계도 |
| docs/reports/README.md | 모든 보고서의 시간순 색인 |

## 게이트

무엇이든 건드린 뒤엔 이 한 줄을 돌린다 (결정성 포함 5종):

```
python -m tests.run_all
```

## 데이터

| 위치 | 무엇 |
|---|---|
| **data/instances/fjspt-lucasberter/** | FJSPT 벤치마크. 인스턴스 + travel matrix + 공표 해. 포맷 3종·함정 = `STATUS.md §데이터 자산` |
| **data/literature/** | 문헌 최고기록 표. `experiments/common.py`가 읽는 **단일 출처** |
| **data/papers/** | 정독용 PDF 5편 (gitignored) |

즉시 실험 가능: **Dauzere 54 케이스**(18 x 차량 2/4/6) + **DeroussiNorre 10 케이스**.
travel matrix가 없어 막힌 계열: fattahi(20), Homayouni_Brandimarte. 미보유: Kumar EX-series 57개.

## archive에 무엇이 있나

| 위치 | 무엇 |
|---|---|
| `archive/a-track/` | A안(동적/자체생성) 코드·설계문서·그림. 보류, 삭제 안 함 |
| `archive/ga-era/` | GA·LNS 시대 공용 모듈 (캠페인 스크립트는 `experiments/`의 RETIRED 폴더에) |
| `archive/reports/` | A안·데모 시대 보고서 9편. **06-30 수치 인용 금지** |
| `archive/status-history.md` | STATUS.md에서 덜어낸 옛 진행 로그 |
| `archive/demo/`, `archive/lit/`, `archive/diagrams/` | FunSearch 데모, 문헌 수집 파이프라인, 옛 다이어그램 |

## 진행 상태 요약 (상세는 STATUS.md)

- [완료] 문헌 계보 추적 + 벤치마크 원본 확보 + Zotero 91편 정리
- [완료] 파서 3종 + 타이밍 코어 + decode + **replay 검증 10/10**
- [완료] 4슬롯 구성형 평가기 + LLM 번들 진화 루프
- [완료 2026-08-13] 문헌 규모 예산(65세대) 완주. held-out 45.2%, 손규칙 전부 이김, **41~65세대에서 과적합**
- [주의] GA 시대의 "규칙이 문헌 손규칙을 이긴다"는 결론은 무효 (실험 003이 뒤집음)
- [주의] 06-30 캠페인 수치는 tool-contamination 이전 생성 -> 인용 금지
