# Stage 5 — 논문별 knowledge card 프롬프트

역할: Zotero에 저장된 논문 전문(PDF full-text)을 읽고 구조화된 카드 1장을 만든다.

입력: Zotero collection의 논문 (zotero-mcp로 full-text 접근)
출력: `runs/<slug>/cards/<citekey>.md`

## 규칙
- **추측 금지.** 모든 항목은 본문 근거가 있어야 하며, 근거는 섹션/페이지로 명시.
- PDF가 없어 abstract만 있으면, 카드 상단에 `source: abstract-only` 라고 표시하고 알 수 있는 만큼만 채운다.
- 저자가 주장하는 contribution은 가능한 한 원문 표현을 살린다.

## 카드 형식
```
---
citekey: zhang2023marl
title: ...
year: 2023
venue: RA-L
source: fulltext        # 또는 abstract-only
---

## 문제정의 (problem)
...

## 방법 (method/approach)
...

## 데이터·벤치마크 (data)
...

## 평가지표 (metrics)
...

## 핵심결과 (findings)
...

## 컨트리뷰션 (contribution)
- ...

## 한계 (limitations)
- ...

## 근거 (evidence)
- "<주장> — §4.2, p.6"
- ...
```

다음 단계: 카드가 모이면 Stage 6 (synthesis).
