---
citekey: huang2026dsevolve
title: "DSevolve: Enabling Real-Time Adaptive Scheduling on Dynamic Shop Floor with LLM-Evolved Heuristic Portfolios"
authors: Jin Huang, Jie Yang, XinLei Zhou, Qihao Liu, Liang Gao, Xinyu Li (HUST)
year: 2026
venue: arXiv:2603.27628 (cs.AI, 2026-03-29)
source: fulltext
---

## 문제정의 (problem)
동적 제조환경(기계고장·신규주문)에서 최적 디스패칭 전략이 계속 바뀜. 기존 LLM-AHD는 **단일 elite 룰**로 수렴해 적응 불가. 또 LLM 진화는 비싼 오프라인 과정이라 온라인 배치와 단절. (Intro §1, §2.2)

## 방법 (method/approach) — 3단계
1. **Multi-Persona Seeding**: K=7 직교 페르소나 프롬프트(Extreme Greedy, Load Balancer, Global Planner, Deadline Chaser, Contrarian, Formula Synthesizer, Hybrid Hierarchical)로 초기 모집단을 behavioral feature space 전역에 분산. (§3.1.2)
2. **Topology-Aware Diversity Evolution**: 3D behavioral feature space F=[load skewness, waiting ratio, diversity] 위 MAP-Elites archive. distance-maximization crossover(가장 먼 셀 부모 결합) + dual-track mutation(elitist 미세개선 + contrastive 반대특성 생성)로 조기수렴 방지. (§3.2)
3. **Probe-Based Rapid Scheduling**: 교란 발생 시 6D probe fingerprint(빠른 SPT 시뮬로 추출) → 오프라인 KB에서 top-k 유사 케이스 검색 → 후보 룰들 look-ahead 시뮬 → 최소 makespan 룰 선택. 초 단위 응답. (§3.3, eq.5-8)

## 데이터·벤치마크 (data)
실산업 기반 **500+ dynamic FJSP** 인스턴스. evolution(5)/case library(100)/test(500, Easy70·Med240·Hard190) 분할. LLM 3종(Qwen-Plus, DeepSeek-V3, GPT-4o-mini). (§4.1)

## 핵심결과 (findings)
AHD(EoH/ReEvo/HSEvo)·고전 HDR(SPT/LPT/SRM/SSO/LSO)·GP·DRL 전부 능가. S3 Hard makespan: DSevolve 3139.4 < EoH 3172.6 < DRL 3380.4 < GP 3404.9 < SPT 3968.7 (Table1-2). Probe 검색이 Top선택 대비 makespan 41.6↓ (Table3). 페르소나 시딩 제거 시 성능 저하 가장 큼(ablation Table4).

## 컨트리뷰션 (contribution)
(1) 7-페르소나 시딩, (2) topology-aware 진화연산자(거리최대 crossover + contrastive mutation), (3) probe 기반 인스턴스 핑거프린팅으로 오프라인 룰진화↔온라인배치 연결. (Intro 기여 1-3)

## 한계 (limitations)
(1) feature space가 수작업 3차원 — 자동학습 필요. (2) 오프라인 KB 구축이 archive×instance에 선형 비용(LSH 등 필요). (3) makespan 단일목표(다목표 미해결). (4) 물리 라인 검증 미수행. (§6)

## AGV 관점 메모
DSevolve와 인용된 모든 AHD(FunSearch/EoH/ReEvo/HSEvo/NeRM/SeEvo/LLM4DRD/LLM-AMA)는 **job/flow/assembly shop의 기계 스케줄링** 대상. **AGV(차량) 스케줄링·디스패칭에 적용한 사례는 references에 없음** → 본 졸논의 빈틈. DSevolve의 DRL/GP 베이스라인 세팅(Appendix D, DEAP GP·PPO)은 비교실험 참고용으로 유용.
