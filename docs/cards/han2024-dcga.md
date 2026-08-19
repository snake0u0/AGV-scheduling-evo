---
citekey: han2024dualpopulation
title: "A dual population collaborative genetic algorithm for solving flexible job shop scheduling problem with AGV"
authors: Xiaoqing Han, Weiyao Cheng, Leilei Meng, Biao Zhang, Kaizhou Gao, Chaoyong Zhang, Peng Duan
year: 2024
venue: Swarm and Evolutionary Computation, 86:101538, doi:10.1016/j.swevo.2024.101538
source: fulltext (Zotero NFDFTRS3)
---

## 문제정의 (problem)
FJSP-AGV(기계선택+AGV선택+연산순서 3개 서브문제) makespan 최소화. MILP(소규모 최적) + DCGA(전체규모 근사).

## 방법 (method/approach)
2계층 인코딩(OS+MS) + **이중 population**(각각 다른 AGV 디코딩 규칙 Decoding1/Decoding2 사용, 해공간 다양화) + population collaboration 연산(POX crossover로 두 population 간 우수해 교환). MILP은 CPLEX로 소규모 최적성 검증.

## 데이터·벤치마크 (data)
**5개 데이터셋 전부 사용, 원본 다운로드 링크 명시**(`fastmanufacturingproject.wordpress.com/2019/04/11/fjspt-instances/`):
1. Data set1 = **SFJS/MFJS01-10**(Homayouni&Fontes 제안, Fattahi et al. 2007 기반)
2. Data set2 = **EX-series 57개**(Kumar et al. 2011)
3. Data set3 = **MFJST01-10**
4. Data set4 = **MK01-10**(Homayouni&Fontes, Brandimarte 1993 + 운반시간)
5. Data set5 = **mt10/setb4/seti5-t 21개**(Homayouni&Fontes, Chambers&Barnes 1996 + 운반시간)
- Data set3-5의 원 출처 = **Ref[31] Homayouni & Fontes(2021), J Glob Optim**.

## 핵심결과 (findings)
DCGA가 기존 SOTA(LAHC/BRKGA/GATS/PGA/IGA/MILP) 대비 **18개 인스턴스의 current best solution 갱신**(Data set3: 2개, Data set4: 8개, Data set5: 8개). Table 6-11에 5개 데이터셋 전체 알고리즘 교차비교 makespan 표.

## 컨트리뷰션 (contribution)
Dual-population(이질적 디코딩) + collaboration 연산 설계, MILP 신규모델, 18개 벤치마크 신기록.

## 한계 (limitations)
makespan 단일목적, AGV 2대 고정, 혼잡/충돌 모델 없음(자유이동 가정), non-LLM 메타휴리스틱(해석불가 - 파라미터화된 GA 인코딩).

## 우리 프로젝트 관련성
**MKT/Dataset5 실제 데이터의 진짜 원출처가 Homayouni & Fontes(2021)임을 확정**, 그리고 **모든 데이터의 실제 다운로드 링크를 논문 텍스트에서 직접 확보**(2026-07-12 데이터셋 비교 보고서 참고). Leilei Meng 그룹(=`archive/a-track/execution_roadmap.md` 앵커 Meng 2023과 동일 계보)의 non-LLM SOTA joint FJSP-AGV 알고리즘 - `novelty_sweep.md`에 "왜 LLM-AHD가 필요한가"의 비교대상(해석성 없는 파라미터화 GA)으로 인용 가치.
