---
citekey: ham2020transferrobot
title: "Transfer-robot task scheduling in flexible job shop"
authors: Andy Ham
year: 2020
venue: Journal of Intelligent Manufacturing, doi:10.1007/s10845-020-01537-6
source: fulltext (Zotero UM9J4B5A)
---

## 문제정의 (problem)
로봇 모바일 이행 시스템(RMFS) 환경의 FJSP+transbot(=AGV) 동시 스케줄링(SSMT). makespan 최소화. CP(제약계획) 최초 적용.

## 방법 (method/approach)
IBM CP Optimizer 기반 2개 CP 모델: CP1(pickup/dropoff 분리 태스크), CP2(하나로 병합, 성능 우위). 중간규모엔 warm-start(CP0로 부분해 생성 후 CP1/CP2 투입) 2단계 접근.

## 데이터·벤치마크 (data)
- **소규모**: Deroussi & Norre(2010) 제안 **FJSPT1-10**(=Bilge&Ulusoy 1995 10 job set×4 layout에서 기계 2배 복제) 재사용. Table 2에 M/J/O 크기 + Zhang et al.(2012) GA+TS / Homayouni&Fontes(2019) MIP / CP1 / CP2 문헌 makespan 비교(전부 최적 증명, Bold=optimal).
- **중규모(이 논문의 신규 기여)**: **HUdata(Hurink et al. 1994)** 4세트(sdata/edata/rdata/vdata, 각 40개 la01~40) 기반, **자체 생성한 travel time**(layout1: U[20,40] T/P≈0.6, layout2: U[200,400] T/P≈6, layout3: U[2000,4000] T/P≈60) 부여. Table 3에 CP1/CP1WS/CP2/CP2WS 평균 makespan+gap.
- **전체 인스턴스+상세 CP 스케줄 다운로드**: 논문에 Google Drive 링크 명시(`drive.google.com/open?id=1-yegwDyBnoDDXnN51EZLy7vrXI0jB6lp`, 유효성 미확인).

## 핵심결과 (findings)
CP2가 FJSPT1-10 전부 최초로 최적 증명(FJSPT1 제외 CP1도 최적). HUdata 확장 중간규모에서는 CP2/CP2WS가 CP1/CP1WS 압도(평균 gap 0.4%/5.8% vs 46.8%/34.7%), 단 어느 것도 시간제한 내 최적수렴 실패.

## 컨트리뷰션 (contribution)
FJSP+transbot CP 정식화 최초, 문헌 벤치마크 최적해 다수 증명, HUdata 기반 신규 중간/대규모 벤치마크 제공(travel time 생성 규칙 공개).

## 한계 (limitations)
AGV 2대 고정, 혼잡/충돌 모델 없음(자유이동 가정), 대규모(HUdata)는 최적성 미증명.

## 우리 프로젝트 관련성
**FJSPT1-10(Dataset1)의 진짜 원출처 확인** - Deroussi&Norre(2010)이지 Ham 본인이 아님. **"고전 FJSP 벤치마크(HUdata/Hurink) + 자체 travel matrix 생성" 전략의 선례** - 우리가 Brandimarte/Barnes에 자체 운반시간을 얹는 fallback을 검토할 때 이 논문의 3-layout T/P 비율 설계(0.6/6/60)를 그대로 참고 가능.
