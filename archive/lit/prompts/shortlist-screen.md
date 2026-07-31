# Stage 3 — 리뷰 후보 추리기 프롬프트 (체크포인트)

역할: 수집된 후보를 2단계로 걸러 리뷰 shortlist를 만들고, **사용자 승인 전에 멈춘다.**

입력: `runs/<slug>/candidates.jsonl`, 주제 "{TOPIC}"
출력: `runs/<slug>/shortlist.md`

## 할 일
1. **싼 pre-filter**: 토픽 키워드(§ search-strategy 키워드 뱅크)와 title/abstract 겹침이 0이면 drop.
2. 남은 논문에 LLM 채점:
   - `relevance` (1-5): 주제 적합도
   - `quality` (1-5): 피인용 수 + venue tier 고려
   - `keep_reason`: 1줄
3. `relevance >= 3` 을 기본 Keep 후보로 둔다. **shortlist는 최소 15편 보장** (모자라면 기준 완화).
4. 아래 표를 출력한 뒤 **멈추고 사용자 승인을 기다린다.** 임의로 Stage 4(아카이빙)로 넘어가지 말 것.

## shortlist.md 출력 형식
```
# <topic> — shortlist (YYYY-MM-DD)  [N candidates → M kept]

| # | Title | Year | Venue | Approach | Key result | Citations | Code? | Rel | Qual | Keep | Reason |
|---|-------|------|-------|----------|-----------|-----------|-------|-----|------|------|--------|
| 1 | ...   | 2023 | RA-L  | MARL     | ...       | 42        | Y     | 5   | 4    | Y    | ...    |

승인 대기: Keep 컬럼을 확정/수정해 주세요. 확정되면 Stage 4로 진행합니다.
```

근거 규칙: Approach/Key result는 abstract에서 확인 가능한 내용만. 추측이면 "(불명)" 표기.
다음 단계: 사용자가 Keep 확정 → Stage 4 (zotero-mcp로 승인분만 저장).
