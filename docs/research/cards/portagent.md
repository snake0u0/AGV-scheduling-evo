---
citekey: portagent2025
title: "PortAgent: LLM-driven Vehicle Dispatching Agent for Port Terminals"
year: 2025
venue: arXiv:2512.14417
source: abstract+webfetch
role: 최근접 경쟁논문 (AGV/vehicle × LLM)
---

## 문제정의
자동컨테이너터미널(ACT)의 차량배차시스템(VDS)은 터미널 간 **전이성 부족**(전문가 의존·데이터 요구·수동 배포)으로 상용화가 어려움.

## 방법
LLM 기반 에이전트가 VDS 이전 워크플로를 자동화. **Virtual Expert Team(VET)** = Knowledge Retriever·Modeler·Coder·Debugger 4가상에이전트 협업 + RAG few-shot + **Reflexion 자기수정 루프**. → 디스패칭 시스템 코드를 자동 설계/이전. **진화탐색 아님**(에이전트 codegen).

## 도메인
**항만 컨테이너터미널 차량배차**. 정적 시스템 설계/이전(동적 교란·배터리 처리 명시 없음).

## 컨트리뷰션
(1) 전문가 의존 제거, (2) 데이터 요구↓, (3) 빠른 배포.

## ★ 우리(AGV-aware AHD)와 차별
- 도메인: **항만 한정 vs 일반 AGV-FMS**
- 방법: **에이전트 codegen(VET+RAG+Reflexion) vs quality-diverse 진화 LLM-AHD**
- 범위: **정적 시스템 이전 vs 동적 교란(신규작업·차량고장)+배터리·혼잡·충돌 처리**
- AGV 고유 feature space/terminal(혼잡·충돌·SOC·deadhead) **부재** → 우리의 방법론적 delta
→ related work에서 반드시 명시 위치 + 위 3차별점 본문화. ('first LLM for AGV' 주장 금지)
