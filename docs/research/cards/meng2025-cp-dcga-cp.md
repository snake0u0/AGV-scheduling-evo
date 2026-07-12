---
citekey: meng2025novel
title: "Novel CP Models and CP-Assisted Meta-Heuristic Algorithm for Flexible Job Shop Scheduling Benchmark Problem With Multi-AGV"
authors: Leilei Meng, Weiyao Cheng, Chaoyong Zhang, Kaizhou Gao, Biao Zhang, Yaping Ren
year: 2025
venue: IEEE Transactions on Systems, Man, and Cybernetics: Systems, 55(11):8455-8468, doi:10.1109/TSMC.2025.3604355
source: fulltext (Zotero GFEHG82C)
---

## 문제정의 (problem)
FJSP-AGV makespan 최소화. 기존 CP 모델[Han 2024]의 한계(같은 job의 연속 2개 연산이 같은 기계에서 처리되는 MPTCOJ 케이스 처리 불가)를 해결하는 신규 CP 모델 + CP-보조 메타휴리스틱(DCGA-CP).

## 방법 (method/approach)
신규 CP 정식화(redundant + symmetry-breaking 제약 추가) + 2단계 프레임워크: 1단계 메타휴리스틱(DCGA, Han 2024와 동일 계보)으로 좋은 초기해 탐색 → 2단계 그 해를 CP의 시작점(warm start)으로 주입해 최적성 보완. CPLEX 사용.

## 데이터·벤치마크 (data)
Han(2024)와 동일한 **5개 데이터셋**(FJSPT1-10[Ham 2020]/EX-series 57개[Kumar 2011]/MFJST01-10/MKT01-10[Brandimarte+운반]/mt10·setb4·seti5-t 21개[Barnes+운반]) + **실제 생산현장 케이스 4건**(Table XIII, Fig.6 workshop layout, 원출처 Yao et al. 2025 ref[20], 5/10/15/20 job). 데이터 자체는 논문에 없고 저자 GitHub(`github.com/mengleilei/FJSP-AGV`)에 **개선된 best-known 해 값만**(docx) 공개, 원본 인스턴스 파일 없음.

## 핵심결과 (findings)
CP모델+DCGA-CP가 **35개 신규 최적해 증명 + 32개 best-known 해 개선**(Data set2에서 13개 신규최적, Data set3 3개, Data set4 8개, Data set5 14/21개 개선). Table III-XII에 CP-N/R/B/RB(제약조합별) + DCGA-CP + 기존 알고리즘(LAHC/BRKGA/PGA/IGA/DCGA/MILP1/MILP2) 전체 교차비교.

## 컨트리뷰션 (contribution)
MPTCOJ 처리 가능한 신규 CP 모델, redundant/symmetry-breaking 제약 효과 실증, CP+메타휴리스틱 결합 프레임워크, 35+32개 벤치마크 신기록.

## 한계 (limitations)
makespan 단일목적(에너지·setup time 등 미고려, 결론에서 향후연구로 명시), AGV 2대 고정, non-LLM(CP+GA 결합), 실제 생산케이스 데이터는 비공개(ref [20] 의존).

## 우리 프로젝트 관련성
저자 **Leilei Meng = execution_roadmap.md 앵커 "Meng 2023 Multi-AGV FJSP"와 동일 인물** - 이 팀이 joint FJSP-AGV의 exact/metaheuristic SOTA를 계속 갱신 중인 최전선 그룹. **objective가 makespan(우리는 mean tardiness 주목적, makespan 보조지표)이라 직접 수치비교엔 주의 필요.** non-LLM 최상위 baseline 인용처로 최적(B1 성능 하한선 감각 확인용). 5개 데이터셋의 원본 다운로드처(fastmanufacturingproject.wordpress.com)는 이 논문이 아니라 Han(2024)에 명시돼 있었음(2026-07-12 발견).
