# AGV × LLM/Agent 휴리스틱 스케줄링 — search strategy (2026-06-08)

주제(학부 졸논, ~3개월): **AI Agent 기반 AGV 스케줄링 휴리스틱 룰 생성·결정**
앵커 논문: **DSevolve** (arXiv:2603.27628, 2026) — LLM-evolved 디스패칭 룰 포트폴리오 + MAP-Elites + online 룰 선택. DFJSP 대상.

## 각도 (contribution 가설)
DSevolve류 AHD(Automatic Heuristic Design)는 주로 **job shop(DFJSP)** 에 적용됨. **AGV/AMR 스케줄링**에 LLM 기반 휴리스틱 생성·동적 선택을 적용한 연구는 상대적으로 희소 → 여기가 학부 수준에서 노릴 gap. 리뷰 목표 = (1) AHD/LLM-휴리스틱 계보, (2) AGV 스케줄링·디스패칭·DRL 현황, (3) 두 흐름의 교차점/빈틈 확인.

## 파라미터
- year_min: 2016 (GP/디스패칭 기반은 과거, AHD/LLM은 2023+)
- seminal(연도무관): FunSearch(Nature 2024), Evolution of Heuristics(EoH), 고전 dispatching rule 리뷰
- 기계 입력: `queries.txt` (collect.py가 읽음)

## 소스
- 1차: OpenAlex (arXiv·저널·proceedings 통합 인덱스, 피인용/abstract 제공) + DSevolve 참고문헌 확장
- 보조(수동/후속): arXiv 최신 프리프린트, Google Scholar (빠진 논문)

## target venues (필터 참고)
NeurIPS/ICML/ICLR (AHD/LLM), Nature (FunSearch), GECCO (GP/QD), IEEE T-ASE, RA-L, ICRA/IROS/CASE, IEEE T-ITS, Int. J. Production Research, Computers & OR, EJOR, IISE Trans, Robotics & CIM.

## 쿼리 그룹 (요약 — 전체는 queries.txt)
1. AHD/LLM 휴리스틱 생성 계보
2. quality-diversity / 유전프로그래밍 룰 생성
3. AGV/AMR 스케줄링·디스패칭·DRL
4. 동적 FJSP / 실시간 룰 선택 (DSevolve 도메인)
