# iusztinpaul/designing-real-world-ai-agents-workshop 활용성 검토

**날짜** 2026-07-23 · **대상** https://github.com/iusztinpaul/designing-real-world-ai-agents-workshop
(MIT, Python, 478★, 최종 push 2026-06-03)

## 결론

**이 연구에는 쓸 게 거의 없다. 도입 권장하지 않음.**
겹치는 건 이름("research agent")뿐이고, 실제 내용물은 *Gemini + Google Search grounding으로
리서치 브리프를 뽑아 LinkedIn 포스트를 써주는 MCP 서버 2개* 짜리 교육용 워크샵이다.
최적화도, 휴리스틱 진화도, 스케줄링도 없다.

가져올 만한 건 코드가 아니라 **패턴 2개**뿐이고, 그마저도 우리 `ahd/`에 이미
동등하거나 더 나은 형태로 있다(아래 §3).

## 1. 레포 실체

| 구성 | 내용 |
|---|---|
| `src/research/` | MCP 서버. `deep_research`(Gemini + Google Search grounding) / `analyze_youtube_video` / `compile_research` 3개 툴 -> `research.md` |
| `src/writing/` | MCP 서버. research.md -> LinkedIn 포스트 생성 -> `[review -> edit] x N` 루프 -> 이미지 생성 |
| `src/writing/evals/` | Opik 기반 LLM-as-judge (pass/fail 이진 라벨 + critique) |
| `.agents/skills/` | research / write-post 스킬. 대부분은 무관한 Streamlit 스킬 번들 |
| `datasets/` | 저자 본인의 LinkedIn 포스트 코퍼스 |

의존: **Google Gemini API 키 필수**, FastMCP, Opik, Streamlit.

## 2. 우리 연구와의 거리

현재 확정 방향(STATUS.md 2026-07-23, B안)은 *정적 FJSP-AGV 벤치마크 + 2계층 공진화
(해 수준 GA x 규칙 수준 LLM), makespan, DCGA 대비 비교*다. 당장 할 일은 파서 3종 /
evaluator / replay 검증(`DeroussiNorre/fjsp1.txt` -> 134)이다.

- 이 레포에는 **적합도 함수도, 시뮬레이터도, 탐색 알고리즘도 없다**. 기여할 지점 자체가 없음.
- 레포의 "evaluator-optimizer loop"는 **LLM 리뷰어가 텍스트를 고치는** 루프다.
  우리 루프는 시뮬레이터가 내는 수치 적합도로 선택압을 준다. 신호 품질이 다른 층위라
  차용할 게 아니라 우리 쪽이 이미 강한 쪽이다.
- 문헌 조사 용도로도 밀린다: 저쪽은 Gemini의 Google Search grounding 한 겹인데,
  우리는 `paper-lookup`(10개 학술 DB, provenance 재현 가능) + `literature-review` +
  Zotero MCP를 이미 쓰고 있다. 논문 인용에는 grounding 검색 결과를 쓸 수 없다.

## 3. 그나마 눈여겨볼 패턴 2개 (그리고 왜 안 가져와도 되는지)

**(a) 구조화 출력 강제** - `response_schema=<Pydantic model>`로 Gemini가 JSON을 반환하도록
강제 (`src/research/utils/llm.py:32`). 우리 `ClaudeCliLLM`은 자유 텍스트에서 표현식을
파싱하고 실패 시 `""` 반환 -> elite로 패딩한다(`ahd/llm.py`). 개념적으로는 스키마 강제가
더 견고하지만, 우리는 **API 키 없이 로그인된 `claude` CLI**를 쓰기로 한 결정이 있어
`response_schema`를 그대로 쓸 수 없다. 현행 파싱+패딩으로 충분.

**(b) 툴 호출 예산 하드캡** - `.memory/`에 호출 수를 영속화해서 프롬프트를 무시해도
초과 못 하게 막음 (`exploration_budget.py`). 우리는 `max_calls` + `AHD_GEN`/population으로
이미 상한이 잡혀 있고, 실패 카운트(`fails/calls`)까지 usage에 찍어 런 유효성을 판정한다.

**Opik 트레이싱**은 실험 로깅에 쓸 수 있지만, LLM 제안 로그를 남기려고 SaaS 관측 스택을
붙일 이유가 없다(현재 CLI usage 봉투에서 토큰/비용을 직접 받고 있음).

## 4. 권고

도입/포크하지 않는다. 필요하면 나중에 "LLM 호출 스키마 강제" 논의 때 (a)만 참고.
지금 우선순위는 STATUS.md §"지금 뭘 하면 되나"의 1-3번(파서 -> evaluator -> replay 134 검증).
