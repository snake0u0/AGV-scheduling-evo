---
citekey: evodr2026
title: "EvoDR: Evolving Dispatching Rules via Large Language Model for Dynamic Flexible Assembly Flow Shop Scheduling"
year: 2026
venue: arXiv:2601.15738
source: abstract
role: 경쟁/계보 (LLM 진화 디스패칭 룰, 머신숍)
---

## 문제정의
동적 유연 조립 흐름공정(kitting 공급 + 기계 유연성, 다제품 납품). GP 디스패칭 룰은 **고정 terminal set + 약한 해석성** 한계.

## 방법
LLM의 의미이해·생성으로 알고리즘설계와 스케줄링지식을 융합한 **EvoDR**. 조립공급 결정을 heterogeneous graph 위 directed edge 우선순위 정렬로 모델링, **dual-expert co-evolution**.

## 도메인
**조립 흐름공정(기계 스케줄링)** — AGV/차량 아님.

## ★ 우리와 차별
- 같은 패러다임(LLM이 디스패칭 룰 진화)이지만 **도메인이 머신/조립숍**. AGV의 vehicle-task-path 결합·배터리·충돌·deadhead **없음**.
- 시사: "LLM이 고정 terminal set 한계를 넘는다"는 논리는 우리도 차용 가능하나, **AGV 고유 terminal/feature 설계**가 우리 신규성.
