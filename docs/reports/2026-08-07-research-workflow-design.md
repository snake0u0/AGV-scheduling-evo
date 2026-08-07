# 연구 워크플로우 설계 - LLM wiki 연결 구조 확정

**결론**: 새 연구 wiki를 만들지 않는다. 기존 `SecondBrain-hub`의 소스 레지스트리를 4개로 확장하고,
`wiki/research/{papers,topics}` 두 폴더를 신설한다. **hub로 들어가는 쓰기 경로는 `/update-wiki`
하나뿐**이다. hub에서 이 명령을 돌리면 소스 4개의 변경분을 스캔해 목록을 보여주고, 내가 고른 것만
압축해 wiki에 넣는다. 연구 프로젝트 쪽 스킬 `/dh-paper-review`(카드 생성)와 `/dh-discuss`(문답
기록)는 hub에 직접 쓰지 않는다. 그저 다음 스캔에 후보로 뜰 재료를 만들 뿐이다.

---

## 1. 최종 구조

```
research-agent  (연구 작업장 - 양 많고 회전 빠름)
  docs/research/cards/     LLM 논문 카드     <- /dh-paper-review
  docs/reports/            실험 보고서
  docs/discussions/        문답 기록          <- /dh-discuss

myblog  (사람이 손으로 쓰는 정독 리뷰)
  content/paper-review/NNN-x.md

MAIN-VT  (원천 볼트)

        |  <- 게이트: /update-wiki 스캔 목록에서 내가 고른 것만
        v

SecondBrain-hub  (LLM wiki)
  wiki/research/current-map.md   지금 연구가 뭔지 (진입점)
  wiki/research/papers/          선별된 논문 지식
  wiki/research/topics/          선별된 주제·교훈
```

역할이 겹치지 않는 이유:
- `cards/`는 **프로젝트 자산**이다. related work 작성과 경쟁논문 포지셔닝에 쓰인다. 회전이 빠르다.
- `discussions/`는 **이해의 작업 기록**이다. 문답 원문을 그대로 남긴다.
- `myblog`는 **사람의 정독 기록**이다. 공개 발행이 목적이다.
- `hub`는 **오래 사는 지식**이다. 이 연구가 끝나도 남는다. 그래서 내가 고른 것만 들어간다.

## 2. 확정된 결정

| # | 질문 | 결정 | 근거 |
|---|---|---|---|
| Q1 | 새 wiki를 만드나 | **아니오. SecondBrain-hub에 통합** | hub가 이미 LLM wiki. 새로 만들면 연구 맵이 두 개가 되어 어느 쪽을 믿을지 알 수 없어짐 |
| Q0 | hub 헌장을 고치나 | **소스 레지스트리 4개로 확장** | hub의 목적("에이전트가 먼저 읽는 압축 레이어")은 그대로. 입력만 늘림 |
| Q3 | wiki 폴더 구조 | **papers/ + topics/** | 날짜별 digests는 만들지 않는다. 시간순 파일은 검색 가치가 낮고 원본이 이미 살아있다 |
| Q4 | cards 10장 이관하나 | **아니오. 제자리** | LLM 생산물은 프로젝트 안에 머문다는 원칙. 인바운드 링크 27곳도 안 깨짐 |
| Q6 | myblog는 상류/하류 | **상류** | 손으로 쓰는 습관 유지 |
| Q5 | 승격 게이트 | **`/update-wiki`의 스캔 목록에서 사용자가 고름** | 쓰기 경로가 하나여야 hub 규칙이 한 곳에서 강제됨. 문답을 했다고 자동 승격되면 게이트가 아님 |
| Q7 | 문답 주도권 | **LLM이 캐묻는다** | 사람이 주도하면 "모르는 걸 모르는" 문제가 안 잡힘 |
| Q8 | 스킬 배치 | **~/.claude/skills/ 전역, 대상 세션에서 실행** | 대상 문서가 있는 곳에서 도는 게 자연스러움 |
| Q9 | /dh-paper-review 범위 | **카드 생성만** | Zotero 아카이빙은 지금처럼 수동 |
| Q10 | 죽은 current-map.md | **B안으로 갱신, 진입점 유지** | index.md가 3곳에서 링크. 연구 질문의 단일 진입점이 필요 |
| Q11 | 업데이트 명령 통합 | **`/update-wiki`가 `/update-main-vt`를 흡수** | 스캔 로직이 소스마다 동일. ps1은 Windows 단독 실행용으로 남김 |

## 3. 논의 중 뒤집힌 결정 (재논의 방지용 기록)

네 번 뒤집혔다. 왜 뒤집혔는지가 결론보다 중요하다.

**Q1 (새 repo -> 통합)**: 처음엔 "hub는 private 압축층이라 블로그 공개 원고 작성에 안 맞다"를 근거로
새 repo를 지지했다. 그런데 "블로그가 원고 작성처, wiki는 압축본"으로 정하는 순간 그 근거가
사라졌다. 그리고 hub의 `wiki/research/current-map.md`가 이미 죽은 A안을 담고 7주 방치된 것을 발견했다.
새 wiki를 만들면 그 페이지가 고쳐지지 않은 채 **경쟁하는 연구 맵 두 개**가 생긴다.

**Q2 (블로그만 상류 -> LLM 카드도 상류)**: "사람이 쓴 것만 wiki에 넣는다"로 정했으나, `cards/` 10장을
실제로 읽어보니 6장이 `source: fulltext`에 절·표 번호까지 인용한 고밀도 노트였고, 오히려 블로그
리뷰 10편이 Summary/Method가 빈 채로 방치돼 있었다. 논문 읽기가 두 종류(연구용 스캔 / 정독 학습)라는
사실이 데이터로 드러났다. 둘 다 유효한 입력으로 인정했다.

**Q4 (cards 이관 -> 제자리)**: 사용자가 "LLM이 하는 논문 리뷰는 연구 프로젝트 안에서, 내가 선별한
것만 wiki로"라는 원칙을 제시했다. 이관하면 인바운드 링크 27곳이 깨지고 `archive/lit/` 파이프라인
계보도 끊긴다.

**Q5 (문답이 게이트 -> `/update-wiki`가 게이트)**: 처음엔 `/dh-discuss`가 문답 후 hub에 직접
쓰도록 설계했다. 사용자가 "문답했다고 무조건 wiki로 연결하지 말라, hub에서 스킬 하나 돌리면 소스들로부터
갱신되게 하라"고 지시해 바꿨다. 결과적으로 더 낫다 - **쓰기 경로가 하나**가 되어 hub 규칙이 한 곳에서만
강제되고, hub의 `CLAUDE.md`가 로드되지 않는 문제도 사라진다. 선별은 문답이 아니라 스캔 목록에서 한다.
이 게이트 패턴은 `archive/lit/pipeline.md` Stage 3에서 이미 쓰던 것이다.

## 4. 스킬 / 명령 3종

### /dh-paper-review (전역 스킬, 연구 프로젝트에서 실행)

- **입력**: Zotero에 이미 있는 논문 (citekey / 제목 / Zotero 키)
- **동작**: zotero-mcp로 full-text 읽기 -> 카드 1장 생성
- **출력**: `docs/research/cards/<citekey>.md`
- Zotero에 없으면 중단한다. 웹 초록으로 대충 채우면 카드의 가치인 "전문 근거"가 사라진다.
- `novelty_sweep.md`는 건드리지 않는다. 경쟁논문 판단은 사용자 몫이다.
- **카드 스키마**: `archive/lit/prompts/knowledge-card.md`의 옛 스펙이 아니라 **실제 10장의 진화형**.
  옛 스펙의 `평가지표`·`근거` 섹션은 사라졌고, 근거는 본문 인라인(`(§3.1.2)`)으로, 마지막에
  `★ 우리와 차별`이 붙는다.

### /dh-discuss (전역 스킬, 연구 프로젝트에서 실행)

- **입력**: 문서 경로 하나 (카드 / 보고서 / 블로그 글)
- **동작**: LLM이 3~5개 질문을 하나씩 던진다. 대답 못 한 것은 "아직 모르는 것"으로 남긴다.
- **출력**: `docs/discussions/<YYYY-MM-DD>-<슬러그>.md`
- **hub에 쓰지 않는다.** 문답 원문(`## 문답 기록`)은 여기 남긴다. 압축은 나중에 `/update-wiki`가 한다.

### /update-wiki (hub 프로젝트 명령, WSL에서 hub 디렉토리에서 실행)

**hub로 들어가는 유일한 쓰기 경로.**

1. `git pull` 후 `scripts/scan-sources.sh` 실행. 소스 4개의 baseline 이후 변경 .md를 나열
2. `TOTAL: 0`이면 즉시 중단
3. **게이트**: 목록을 `# / Source / File / Lines / 제안(ingest|skip) / 왜` 표로 보여주고 멈춘다.
   curated 소스의 기본 제안은 `skip`. 사용자가 확정할 때까지 진행하지 않는다
4. 확정된 것만 읽고 압축해서 wiki 페이지에 반영 (200줄 미만은 전문, 이상은 헤딩 먼저)
5. **스킵한 것 포함해** 모든 스캔 소스의 baseline을 갱신. 스킵도 결정이다. 그다음 `log.md` 추가 + commit

hub 페이지 형식:

```markdown
## 압축된 이해     질문에 답할 수 있게 된 것
## 내 판단        우리 연구와의 관계, 채택/기각과 이유
## 아직 모르는 것   대답 못 한 질문 = 다음에 읽을 것
```

문답 원문은 hub에 저장하지 않는다. hub 헌장이 *"compression layer, not a search index"*다.

## 5. 구현된 변경사항

### SecondBrain-hub

| 파일 | 변경 |
|---|---|
| `CLAUDE.md` | 역할 문단을 소스 4개 체제로. `/update-wiki`가 유일 쓰기 경로임을 명시. 하드룰에 게이트 규칙과 baseline 갱신 규칙 추가 |
| `sources.md` | 맨 앞에 소스 등급표 신설. `research-agent` 4개 + `myblog` 2개 source id 등록 |
| `docs/hub-architecture.md` | Role 문단 개정. 게이트가 왜 필요한지 명시 |
| `docs/workflows.md` | "Update the wiki from all sources"로 교체. `/update-main-vt`는 Windows 폴백으로 격하 |
| `index.md` | Wiki 섹션에 papers/topics, Query Hints 2줄, Operating에 `/update-wiki` |
| `scripts/scan-sources.sh` | **신설.** bash. 소스 4개를 baseline 대비 스캔. ps1의 제외 규칙과 미커밋 변경분 포함 동작을 이식 |
| `.claude/commands/update-wiki.md` | **신설.** 위 5단계 프로토콜 |
| `wiki/research/papers/README.md` | **신설.** 페이지 형식과 규칙 |
| `wiki/research/topics/README.md` | **신설.** 페이지 형식과 규칙 |

`scan-main-vt-changes.ps1`과 `/update-main-vt`는 지우지 않았다. WSL을 못 쓸 때의 폴백이다.

### 전역 스킬

- `~/.claude/skills/dh-paper-review/SKILL.md`
- `~/.claude/skills/dh-discuss/SKILL.md`

### research-agent

- `docs/discussions/README.md` 신설, `INDEX.md`에 한 줄 추가

## 6. 다음 단계

1. `/dh-discuss docs/reports/2026-08-07-project-review.md` -> 검증: `docs/discussions/`에 문답
   기록이 남고, 대답 못 한 항목이 "아직 모르는 것"에 그대로 남는다
2. hub 디렉토리에서 `/update-wiki` -> 검증: 스캔이 4개 소스를 나열하고 게이트에서 멈춘다.
   1번의 문답 기록을 ingest로 골랐을 때 `wiki/research/current-map.md`가 B안으로 갱신된다
3. `/dh-paper-review` -> 검증: 기존 카드 1장을 재생성해 스키마가 일치한다

첫 `/update-wiki`는 `research-agent`와 `myblog`에 baseline이 없어서 전체 목록이 뜬다. 대부분 skip하고
몇 개만 고르는 게 정상이다. 그 한 번으로 baseline이 잡히면 이후로는 변경분만 뜬다.
