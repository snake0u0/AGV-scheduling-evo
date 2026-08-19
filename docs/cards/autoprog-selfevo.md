---
citekey: huang2024autoprog
title: "Automatic programming via LLM with population self-evolution for dynamic job shop scheduling (+ fuzzy variant, SeEvo)"
year: 2024-2026
venue: arXiv:2410.22657 ; fuzzy variant IEEE T-Fuzzy Systems 10.1109/tfuzz.2025.3650586
source: abstract
role: 계보 (LLM+EA self-evolution, 머신숍) — DSevolve가 SeEvo로 인용
---

## 문제정의
동적 job shop(DJSSP)의 HDR은 시나리오 의존적. GP/GEP는 탐색 randomness↑·일반화↓로 새 시나리오 전이 약함.

## 방법
LLM+진화알고리즘의 **population self-evolution**(individual co-evolution + self-evolution + collective evolution)으로 디스패칭 룰 자동 생성·일반화 강화. fuzzy job shop 변형 = SeEvo(IEEE TFS).

## 도메인
**job shop / fuzzy job shop (기계)** — AGV 아님.

## ★ 우리와 차별
- self-evolution 메커니즘은 **탐색 전략으로 차용 검토 가능**하나 도메인·feature가 머신숍.
- DSevolve가 이 라인을 SeEvo로 인용 → AHD-머신숍 계보가 두텁다는 증거. **AGV 이전 + AGV-aware feature가 우리 차별점**.
