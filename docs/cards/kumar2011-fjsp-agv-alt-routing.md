---
citekey: kumar2011simultaneous
title: "Simultaneous scheduling of machines and vehicles in an FMS environment with alternative routing"
authors: M. V. Satish Kumar, Ranga Janardhana, C. S. P. Rao
year: 2011
venue: The International Journal of Advanced Manufacturing Technology, 53(1-4):339-351, doi:10.1007/s00170-010-2820-2
source: fulltext (Zotero KQK9HJMJ)
---

## 문제정의 (problem)
FMS에서 기계 시퀀싱 + AGV 디스패칭 동시 스케줄링, 대체가능기계(alternative routing) 포함, makespan 최소화. Bilge & Ulusoy(1995)의 10개 job set × 4개 layout을 그대로 재사용(자체 신규 데이터 아님).

## 방법 (method/approach)
차분진화(Differential Evolution) + 자체 개발한 vehicle assignment heuristic(VLT 최소 AGV 선택) + machine selection heuristic(대체기계 중 완료시각 최소인 기계 선택). 두 전략(PDE-1/PDE-2) 비교.

## 데이터·벤치마크 (data)
**Bilge & Ulusoy(1995) 10 job set × 4 layout**(각 layout=5×5 travel time matrix, L/U+M1~M4). t/p>0.25군(1.1~10.4, 40문제)과 t/p≤0.25군(1.10~10.40 + 2.41~7.41)으로 나뉨. Appendix Table 4에 전체 job set 원본 데이터(연산별 대체기계+가공시간), Fig 3에 4개 layout의 travel matrix가 그대로 실려있음 → **직접 전사 가능**.

## 핵심결과 (findings)
Table 5/6에 STW(Ulusoy&Bilge)/UGA(Ulusoy GA)/AGA(Abdelmaguid)/RGA(Reddy&Rao GA)/PDE-1/PDE-2 6개 알고리즘 makespan 교차비교 - **문헌 검증된 ground truth 표**로 그대로 사용 가능.

## 컨트리뷰션 (contribution)
DE 기반 vehicle/machine 배정 휴리스틱 2종, 문헌 대비 성능 우위.

## 한계 (limitations)
소규모(5job×4machine, AGV 2대 고정)만 다룸. 최적성 증명 없음(메타휴리스틱).

## 우리 프로젝트 관련성
**소규모 문헌 정확 재현(execution_roadmap.md가 지목한 갭)의 1차 출처.** "EX"/"EXF" 인스턴스 명명 체계의 뿌리가 이 논문(job set.layout 번호)임을 확인. `fastmanufacturingproject.wordpress.com`의 "Data set2"(Kumar 2011)가 이 논문 job set을 3개 대체기계로 재구성한 버전 - 단, job set 3/6/10은 원 데이터 오타로 그 사이트에서 제외됨. Table 4/Fig 3을 우리 `sim/` 인스턴스 포맷으로 직접 전사하는 게 다음 액션.
