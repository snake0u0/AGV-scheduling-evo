# research-agent — 연구 자동화 파이프라인 (MVP) 계획

> 목적: 논문을 **많이 찾아오고 → 리뷰 후보를 추리고 → Zotero에 쉽게 아카이빙하고 → AI가 전문을 읽어 트렌드·연구흐름·방법론·컨트리뷰션을 정리**하는 개인용 파이프라인.
> 철학: **MVP**. 오버엔지니어링/과도한 도구 설치 금지. 새 코드는 최소화하고, 이미 가진 자산(MCP + 이미 클론한 skill repo)을 조합한다.

---

## 0. 한 줄 요약

`Claude Code(오케스트레이터) + zotero-mcp(로컬) + paper-lookup 스킬`을 **stable spine**으로, Google Scholar MCP는 **보조(optional)**로 두고
**6단계 + 1체크포인트** 워크플로를 돈다. 무거운 코드는 안 짠다. AutoResearchClaw·skill repo에서는 *코드가 아니라 패턴/프롬프트만* 빌려온다.

---

## 1. 목표와 범위

### 하는 것 (v1)
- 키워드 → 여러 소스에서 후보 100~300편 수집 + 중복 제거
- 관련성/품질 점수로 리뷰 후보 추리기 (**여기서 내가 한 번 확인 = 체크포인트**)
- 승인된 것만 Zotero(로컬)에 저장 + OA PDF 첨부
- AI가 Zotero 전문(PDF full-text)을 읽고 논문별 **knowledge card** 생성
- 카드들을 종합해 **트렌드/방법론 family/컨트리뷰션/연구 gap** 리포트 생성

### 안 하는 것 (의도적 제외 — 나중에)
- 실험 자동실행·코드생성·LaTeX 작성 (AutoResearchClaw의 Stage 9~22) — 무관
- 23-stage 상태머신, HITL 6모드, knowledge graph, MetaClaw 학습 — MVP 과잉
- 자체 MCP 서버 구축 — 우리는 MCP를 *소비*만 한다
- citation 존재성 검증(verify.py 류)·semantic full-text index — v2 후보 (§9)

---

## 2. 확정된 결정사항

| 항목 | 결정 | 파이프라인에 주는 영향 |
|---|---|---|
| **연구 분야** | AGV/AMR/OHT scheduling, 물류, SCM, 강화학습, 최적화 | arXiv(cs.RO/cs.LG/cs.AI/math.OC/eess.SY) + IEEE/OR 저널 + 프로시딩 비중↑. paywall(IEEE/Elsevier)·conference 비중이 커서 **Scholar 발견 + Zotero Connector 수동저장** 경로가 중요 |
| **Zotero** | 로컬 데스크톱 앱 | zotero-mcp **로컬 API**로 붙여 **PDF 전문 직접 읽기** 가능 → Stage 5(전문 리뷰)에 최적. Better BibTeX로 citekey 안정화 |
| **자동화 수준** | **체크포인트** | 수집→후보추림까지 자동, **shortlist 승인 게이트**에서 내가 확인 후 archiving/리뷰 진행. 쓰레기 논문 대량 저장 방지 |

---

## 3. 도구 스택 (최소 구성)

### 핵심 spine (2종, load-bearing — 둘 다 안정적)
| 도구 | 역할 | 비고 |
|---|---|---|
| **zotero-mcp** (54yyyu) — 로컬 | 아카이빙 + **전문 읽기** + 라이브러리 검색/노트 | 파이프라인 중심. semantic/pdf extra 설치 |
| **paper-lookup 스킬** (scientific-agent-skills) | **발견 + citation graph + OA PDF 링크** 한 방 | OpenAlex·Semantic Scholar·arXiv·Crossref·CORE·Unpaywall(10 DB) REST. **이미 로컬 클론됨**, 키 거의 불필요, 서버 X. S2 **인용/피인용 그래프·recommendation·Unpaywall OA링크**까지 포함 |

### 보조 (1종, optional — 있으면 좋고 없어도 됨)
| 도구 | 역할 | 비고 |
|---|---|---|
| **Google Scholar MCP** (JackKuo666) | 최신·grey literature·빠진 논문 보조 발견 | 스크래핑이라 불안정·ToS 주의. **파이프라인이 여기 의존하지 않음** — 막히면 paper-lookup이 전부 커버 |

> **왜 이 구성인가 (Scholar 불안정성 대응):** 발견 spine을 **stable REST(paper-lookup)** 로 두고 Scholar는 보너스로 강등. 이전에 거론된 semantic-scholar / arxiv / paper-distill MCP가 더하려던 가치(인용 그래프·arXiv·멀티소스)는 **paper-lookup이 이미 흡수** → 추가 설치는 중복이라 안 한다. ("도구 더 쓰기"보다 나은 설계.)
> **추가는 trigger 있을 때만:** paper-lookup의 S2 citation 호출이 rate-limit로 자주 막히면 → 그때 dedicated **semantic-scholar MCP**(zongmin-yu, batching·rate-limit 내장) 하나만 추가. arXiv 전문 즉시읽기가 꼭 필요하면 arxiv-mcp. 그 전엔 불필요.

### 보조 스킬 (서버 X, 프롬프트/스크립트 파일일 뿐 — 이미 로컬에 있음)
| 스킬 | 출처(로컬 경로) | 쓰는 단계 |
|---|---|---|
| **pyzotero** | `gh-lab/scientific-agent-skills/scientific-skills/pyzotero/` | Stage 4 (Zotero가 유일하게 네이티브로 지원되는 스킬; zotero-mcp 대안/보강) |
| **literature-review** | `.../scientific-skills/literature-review/` | Stage 3·5·6 백본 (PRISMA 스크리닝 → 주제별 synthesis → gap). `search_databases.py`, `verify_citations.py` 번들 |
| **citation-management** | `.../scientific-skills/citation-management/` | Stage 4·6 (DOI→BibTeX, 메타데이터 정제/dedup) |
| **literature-research** | `gh-lab/phd-skills/plugin/skills/literature-research/` | Stage 2·6 (citation chaining 발견, gap 분석) |
| **paper-writing** | `gh-lab/phd-skills/plugin/skills/paper-writing/` | (선택) related-work 초안 작성 |

> MVP에선 **literature-review 한 개만** 적극 쓰고 나머지는 필요할 때 끌어다 쓴다. "스킬 5개 동시 설치" 같은 건 하지 말 것.

### 구현 형태
별도 Python 앱을 만들지 않는다. 구현 = **이 PLAN + `prompts/` 템플릿을 Claude Code가 따라가는 것**.
반복 사용을 원하면 v1.1에서 이 워크플로를 **단일 오케스트레이터 스킬**(`research-agent/SKILL.md`) 하나로 묶는다. (그 이상은 금지)

---

## 4. 파이프라인 (6단계 + 체크포인트)

```
[1 전략] → [2 수집] → [3 후보추림] ──🛑체크포인트🛑──→ [4 아카이빙] → [5 전문리뷰] → [6 종합]
```

### Stage 1 — 검색 전략
- **입력**: 주제 한 줄 (예: "warehouse multi-AGV scheduling with deep RL")
- **할 일**: 키워드 쿼리 세트 생성(동의어 포함), 연도 범위, 타깃 venue 지정
  - 키워드 뱅크(분야 맞춤): `AGV | AMR | OHT | mobile robot`, `dispatching | scheduling | routing | task allocation | fleet management`, `reinforcement learning | DRL | multi-agent RL | policy`, `MILP | metaheuristic | optimization | combinatorial`, `warehouse | semiconductor fab | container terminal | SCM`
  - 타깃 venue: ICRA, IROS, CASE, **T-ASE, RA-L, IEEE T-ITS**, IEEE T-Automation, **EJOR, Computers & OR, IISE Trans, Transportation Research**, NeurIPS/ICML/ICLR(RL)
- **출력**: `queries.md` (쿼리 리스트 + year_min + venue 리스트)
- **차용**: AutoResearchClaw Stage 3 (`queries.json` + seminal 시드 아이디어)

### Stage 2 — 광역 수집
- **도구**: Google Scholar MCP(넓게) + paper-lookup(OpenAlex/S2/arXiv/Crossref/CORE)
- **할 일**: 쿼리별 검색 → 후보 모으기(title/abstract/year/venue/citations/doi/arxiv_id/url/source) → **중복 제거**
  - dedup 규칙: **DOI > arXiv ID > 정규화 title**, 충돌 시 citation 높은 레코드 채택 (AutoResearchClaw `_deduplicate` 그대로)
- **출력**: `candidates.jsonl` (논문당 1줄, 아래 §5 스키마)
- **목표량**: 100~300편

### Stage 3 — 리뷰 후보 추리기 🛑(체크포인트)
- **할 일(2단계, 비용 절약)**:
  1. 싼 **키워드 pre-filter**: 토픽 키워드와 겹침 0이면 제거
  2. LLM **relevance_score(1-5) + quality_score + keep_reason** 채점 → 랭킹
  - 최소 보장: shortlist ≥ 15 (AutoResearchClaw `_MIN_SHORTLIST`)
- **출력**: `shortlist.md` 표 — `Title | Year | Venue | Approach | Key result | Citations | Code? | Relevance | Keep | Reason`
- **🛑 게이트**: Claude가 표를 보여주고 멈춘다. **내가 Keep 컬럼을 확정/가지치기**한 뒤에만 Stage 4 진행. (승인된 것만 Zotero로 감)
- **차용**: AutoResearchClaw Stage 5 스크리닝 + phd-skills `literature-research` 분류표

### Stage 4 — Zotero 아카이빙
- **도구**: zotero-mcp (DOI/arXiv/URL로 add) — 로컬
- **할 일**:
  - 승인 논문을 전용 **collection**에 저장 + 태그(`agv`, `rl`, `scheduling`...) 부여
  - OA PDF 자동 첨부: arXiv / Unpaywall / CORE (paper-lookup이 OA 링크 제공)
  - **paywalled(IEEE/Elsevier 등)**: 자동 저장 불가 → `archive_log.md`에 "수동 필요"로 표시 → 학교 VPN + **Zotero Connector**로 직접 저장
- **출력**: Zotero collection + `archive_log.md` (저장됨/수동필요/PDF유무)
- **참고**: AutoResearchClaw엔 Zotero 연동이 **없음** → 이 단계는 zotero-mcp/pyzotero로 새로 구성. `Paper.to_bibtex()`→Zotero import 흐름이 자연스러운 접점

### Stage 5 — AI 전문 리뷰 (논문별 카드)
- **도구**: zotero-mcp 로 로컬 PDF **full-text** 읽기 (로컬 앱이라 가능)
- **할 일**: 논문마다 **knowledge card** 1장 생성 (§8 템플릿)
  - 필드: 문제정의 / 방법 / 데이터·벤치마크 / 지표 / 핵심결과 / **컨트리뷰션** / 한계 / **근거(섹션·페이지)**
- **출력**: `cards/<citekey>.md` (+ 선택: Zotero note로도 저장)
- **차용**: AutoResearchClaw Stage 6 카드 스키마. (단, ARC은 abstract만 읽음 → 우리는 zotero-mcp로 **전문**을 읽어 한 단계 위)

### Stage 6 — 종합 / 트렌드 분석 (최종 산출물)
- **할 일**: 카드 전체를 입력으로 종합 리포트 생성 (§8 synthesis 템플릿)
  - 문제정의 변화(연도순) / 데이터셋·벤치마크 변화 / **방법론 family ≤5 clustering** / family별 대표논문+컨트리뷰션 / 최근 2년 한계 / **내가 시도할 contribution 후보 5개 + 연구 gap**
  - **모든 주장에 논문 title + 섹션 근거** 달기 (anti-hallucination)
- **출력**: `synthesis.md`
- **차용**: AutoResearchClaw Stage 7 (clusters+gaps+opportunities) + literature-review 주제별 synthesis

---

## 5. 폴더 / 산출물 구조

```
research-agent/
  PLAN.md                  ← 이 문서
  prompts/
    search-strategy.md     ← Stage 1 쿼리/venue 생성 (+분야 키워드뱅크)
    shortlist-screen.md    ← Stage 3 채점 프롬프트
    knowledge-card.md      ← Stage 5 카드 프롬프트
    synthesis.md           ← Stage 6 종합 프롬프트
  scripts/
    collect.py             ← Stage 2 수집기 (OpenAlex 멀티쿼리+seed 확장+dedup, stdlib)
  runs/
    <topic-slug>-YYYYMMDD/
      queries.md / queries.txt    ← 전략(사람) / 쿼리(collect.py 입력)
      candidates.jsonl            ← Stage 2 raw
      candidates_filtered.jsonl   ← Stage 3 토픽 pre-filter 통과분
      shortlist.md         ← 체크포인트 산출물
      archive_log.md
      cards/<citekey>.md
      synthesis.md         ← 최종 리포트
```

**candidates.jsonl 한 줄 스키마** (AutoResearchClaw `Paper` 축약):
```json
{"title":"","authors":["..."],"year":0,"venue":"","abstract":"",
 "citation_count":0,"doi":"","arxiv_id":"","url":"","source":"openalex|arxiv|scholar"}
```

---

## 6. 차용한 패턴 (출처 명시)

| 패턴 | 출처 | 우리 단계 |
|---|---|---|
| 멀티소스 검색 + **DOI>arXiv>title dedup** | ARC `literature/search.py::_deduplicate` | Stage 2 |
| 2단계 스크리닝(키워드 pre-filter → LLM 점수) + min-shortlist | ARC Stage 5 `_literature.py:606` | Stage 3 |
| **knowledge-card 스키마**(problem/method/data/metrics/findings/limitations) | ARC Stage 6 `_literature.py:737` | Stage 5 |
| **synthesis**(clusters+gaps+opportunities) | ARC Stage 7 `_synthesis.py` | Stage 6 |
| (v2) citation 존재성 검증 VERIFIED/SUSPICIOUS/HALLUCINATED | ARC `literature/verify.py` | §9 |
| Markdown KB(파일 1개=항목, frontmatter) | ARC `knowledge/base.py` | runs/ 구조 |
| PRISMA 스크리닝·synthesis·gap·citation verify 번들 | scientific-agent-skills `literature-review/` | Stage 3·5·6 |
| Zotero 네이티브 CRUD/PDF/BibTeX | scientific-agent-skills `pyzotero/` | Stage 4 |
| 10 DB 키리스 REST 검색 | scientific-agent-skills `paper-lookup/` | Stage 2 |
| discovery + citation chaining + gap 분석 | phd-skills `literature-research/`, `/gaps` | Stage 2·6 |
| related-work 작성 프로토콜 | phd-skills `paper-writing/` | (선택) |

---

## 7. 셋업 절차 (one-time) — 실제 환경 반영 (WSL2 + Windows Zotero → Web API 모드)

환경: 여기는 **WSL2(NAT)**, Zotero는 **Windows 앱**(`/mnt/c/Users/admin/Zotero/`). 로컬 API(127.0.0.1:23119)는 WSL에서 Windows localhost에 못 닿으므로 **Web API 모드** 채택. (완전 로컬을 원하면 `.wslconfig` networkingMode=mirrored + `wsl --shutdown` 대안)

- [x] **스킬 복사**: `paper-lookup`, `literature-review` → `project/.claude/skills/` (완료)
- [x] **zotero-mcp-server[pdf] 설치**: `uv tool install "zotero-mcp-server[pdf]"` → CLI `zotero-mcp`, `zotero-cli` (완료). 패키지는 54yyyu의 **`zotero-mcp-server`** (PyPI의 `zotero-mcp`는 다른 프로젝트라 주의). semantic(torch/chromadb)은 무거워 제외 → v2
- [x] **Zotero sync 확인**: Web API로 라이브러리 접근 검증됨 (userID `17577554`, 항목 62개·컬렉션 3개)
- [x] **API key 발급**: 발급·검증 완료 (권한 library/files/notes/write 모두 True). 키는 `~/.claude.json`[600]에만 저장
- [x] **Claude Code에 MCP 등록** (user scope): `zotero` = `zotero-mcp serve --transport stdio`, env `ZOTERO_LOCAL=false / TYPE=user / LIBRARY_ID=17577554 / API_KEY`
  ```
  # 재현용 (값 교체):
  claude mcp add zotero -s user -e ZOTERO_LOCAL=false -e ZOTERO_LIBRARY_TYPE=user \
    -e ZOTERO_LIBRARY_ID=<USER_ID> -e ZOTERO_API_KEY=<KEY> \
    -- /home/dohyung/.local/bin/zotero-mcp serve --transport stdio
  ```
- [ ] **남은 단계: 이 세션에서 MCP 연결** — `/mcp` 로 연결하거나 Claude Code 재시작해야 `mcp__zotero__*` 툴이 로드됨 (user scope를 세션 중간에 추가했기 때문)
- **전문 읽기(Stage 5)**: Web API 메타데이터의 attachment key로 `/mnt/c/Users/admin/Zotero/storage/<KEY>/*.pdf` 를 직접 read (full-text sync 여부와 무관하게 동작)
- **아카이빙(Stage 4)**: zotero-mcp의 "add by DOI/URL → 메타데이터 자동 + OA PDF cascade(Unpaywall/arXiv/S2/PMC)" 사용. 단 OA PDF 업로드는 클라우드 storage(무료 300MB) 차감 → 필요시 metadata-only로
- (선택) **Better BibTeX**: citekey 안정화 — MVP 필수 아님
- (선택) **Google Scholar MCP** (JackKuo666): 보조 발견, 원하면 나중에 등록

---

## 8. 핵심 프롬프트 템플릿 (초안)

### prompts/shortlist-screen.md (Stage 3)
```
다음 candidates.jsonl 의 각 논문을 평가하라. 주제: "{TOPIC}".
1) 먼저 토픽 키워드와 겹치는 게 없으면 drop.
2) 남은 것에 대해: relevance(1-5), quality(피인용/venue 고려, 1-5), keep_reason(1줄).
표로 출력: Title | Year | Venue | Approach | Key result | Citations | Code? | Relevance | Keep(Y/N) | Reason
relevance>=3 을 기본 Keep 후보로. shortlist 최소 15편 보장. 끝나면 멈추고 내 승인 대기.
```

### prompts/knowledge-card.md (Stage 5)
```
zotero-mcp로 이 논문 전문을 읽고 카드를 작성하라. 추측 금지, 근거는 섹션/페이지로.
- citekey:
- 문제정의(problem):
- 방법(method/approach):
- 데이터·벤치마크(data):
- 평가지표(metrics):
- 핵심결과(findings):
- 컨트리뷰션(contribution):   # 저자가 주장하는 기여, 가능한 한 그대로
- 한계(limitations):
- 근거(evidence): "<주장> — <섹션/페이지>" 형식 목록
```

### prompts/synthesis.md (Stage 6)
```
이 collection의 cards/*.md 를 연도순으로 종합하라.
1. 문제정의가 어떻게 바뀌었는지
2. 사용 데이터셋/벤치마크 변화
3. 방법론 family를 5개 이하로 clustering
4. 각 family 대표 논문과 contribution
5. 최근 2년 논문이 주장하는 한계
6. 내가 시도할 수 있는 contribution 후보 5개 + 연구 gap
표로 정리하고, **각 주장마다 논문 title + 섹션 근거**를 단다.
근거 없는 주장/숫자는 쓰지 말 것.
```

---

## 9. MVP 컷라인 (v1 vs 나중)

**v1 (지금)**: Stage 1~6, 핵심 3도구, literature-review 스킬, 체크포인트 1개, runs/ 산출물.
**v1.1**: 워크플로를 단일 `research-agent/SKILL.md` 오케스트레이터로 묶어 반복 호출.
**v2 (필요해지면)**:
- ARC `verify.py` 패턴으로 **citation 존재성 검증**(가짜 DOI/title 잡기) — related-work 글 쓸 때
- zotero-mcp **semantic full-text index**로 "이 collection에서 X 방법 쓴 논문" 검색
- paper-distill / Scientific-Papers-MCP로 소스 더 넓히기 (지금은 paper-lookup으로 충분)

---

## 10. 리스크 / 한계

- **MCP는 paywall을 못 뚫는다.** IEEE/Elsevier 전문은 학교 VPN + Zotero Connector 수동 저장이 현실. → 파이프라인은 "OA는 자동, paywall은 수동 플래그"로 설계됨(Stage 4).
- **Google Scholar MCP 불안정/ToS.** 스크래핑 계열, rate-limit·차단 가능. **발견 전용**, 실패 시 paper-lookup으로 폴백. 자동 루프에서 과도 호출 금지.
- **분야 특성**: 이 분야 핵심이 conference(ICRA/IROS/CASE)·IEEE에 많아 arXiv보다 OA 비율이 낮음 → Stage 4 수동 비중이 ML 평균보다 높을 수 있음.
- **전문 읽기 품질**은 Zotero에 PDF가 실제로 있어야 보장됨(없으면 abstract 기반으로 degrade). archive_log에서 PDF 유무 추적.

---

## 11. 다음 액션

1. ~~이 PLAN 검토/수정~~ + ~~`prompts/`(4개) + `runs/` 스캐폴딩 생성~~ → **완료**
2. (셋업) Zotero 로컬 API + Better BibTeX 활성화, **zotero-mcp** 등록, **paper-lookup 스킬** 경로 연결 (Scholar MCP는 선택)
3. paper-lookup 스킬을 `research-agent/.claude/skills/`로 복사하거나 스킬 경로 인식시키기
4. 첫 주제로 Stage 1~3 드라이런 → shortlist 체크포인트까지 한 번 돌려보고 감 잡기
```
```
