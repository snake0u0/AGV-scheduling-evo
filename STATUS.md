# ▶ START HERE — 여기서 이어서 (resume point)
최종 업데이트 2026-06-09. 새 세션에서 "이제 뭘 하면 돼?" → **이 파일을 읽으면 방향이 잡힘.** (메모도 자동 로드됨)

## 한 줄 현황
주제·컨트리뷰션 **확정(B+N1)**, 시뮬 v0 + 실제 LLM-AHD 루프(`claude` CLI) **동작·검증 완료(M1)**. **스케일 40–50 AGV가 KIIE 타깃으로 확정(2026-06-29)** → **다음 = 시뮬 대규모화(혼잡+앵커 생성기, M1.5, 임계경로).** 전체 흐름은 `execution_roadmap.md`.

## 지금 뭘 하면 되나 (우선순위)
1. **★ 시뮬 대규모화 (M1.5 — 임계경로, 진행중)** — KIIE부터 **40–50 AGV**(k≤6은 연습이었음). 진행:
   - ✅ **S1 혼잡-지연**: `agv_fms.py::_cong_factor` (config `congestion_alpha`, 기본0=무회귀). 50대서 alpha↑→util/tard 상승 확인.
   - ✅ **S2a FJSP화**: 연산별 적격기계 집합(config `flex`, 기본1=비트동일) + 고정 최소부하 배정룰(`_assign`). flex2/3서 부하분산 개선 확인.
   - ✅ **S2b 대규모 regime**: `sim/configs.py::LARGE_REGIMES` (L1=40AGV 운반병목, L3=50AGV 균형; flex2·혼잡on; <0.5s/run). 수치는 S3에서 보정.
   - 🔸 **S3 검증**: (b) ✅ salabim에 혼잡+flex 포팅 후 재-crosscheck **3/3 순위 일치**(congested-fjsp 포함; 절대값 3–7%차=혼잡 타이밍 민감도). (a) ✅ 정성 검증(차량수↑→makespan↓ 수확체감, flex·혼잡 효과 문헌 패턴 재현). ⬜ BU 정확 number-matching은 정적모드+explicit travel matrix+인스턴스 데이터 필요 → follow-up.
   - 구조 근거·인용=`benchmark_anchor_notes.md`. 상세·순서=`execution_roadmap.md` §1–3.
2. **LLM 루프(동작함, 대규모 검증됨)** — `ahd/llm.py::ClaudeCliLLM`가 로그인 `claude` CLI 헤드리스 호출(키 불필요, Sonnet). `ahd/run.py`는 env `AHD_REGIME`/`AHD_GEN`/`AHD_TRAIN_N`로 regime·버짓 선택.
   - **L1(40 AGV) 실런**(8세대·8seed·~$1): baseline 370.9 → **test 362.99 (+2.1%)**. train 364→360 꾸준 개선. 진화 AGV규칙이 `congestion` feature 활용(`-downstream_load/(congestion+1)`) = **혼잡 인지 디스패칭**. R3(+1.7%)보다 큼(어려운 regime일수록 이득↑ 가설 일치).
   - ✅ **ReEvo 강화**: `loop`이 elite를 fitness와 함께 `vary`에 전달 → `_ExprProposer.vary`가 mean_tardiness 값 제시 + reflection 요청(`ahd/llm.py`). 검증됨(1콜 4규칙, ~$0.11). 남은 것: **L1에서 old vs ReEvo 비교 런으로 이득 정량화**, 버짓↑.
3. **캠페인/베이스라인 ✅**: `ahd/campaign.py`(B1·B2·B5·B6·P, test 표→`docs/research/results/`), `ahd/gp.py`(B2 GP). **L1 결과: P joint +1.7% > B5 +0.9% > B2 GP +0.2% ≈ B6 0% ≈ B1 −0.1%.** 두 주장 입증: ①N1 joint 필요성, ②**P > 전통 GP(B2): 성능+해석성(26자 vs 207자) 이중 우위**. (단일런·작은 magnitude.) 보고서 `docs/reports/2026-06-30-campaign-L1.md`.
4. **다음(통계·집필)**: 조건당 ≥3 반복·Wilcoxon + 다regime(L3·R) + 해석성 표 → KIIE 초록/발표.
5. **P1 논문 수동 다운로드**: `manual_download_list.md` (특히 **MRE 전문** — 차별 문장용).
6. **투고 직전**: novelty sweep 재확인 → `novelty_sweep.md §잔여리스크` (agent `novelty-watch`).

## 읽는 순서 (아래 문서는 모두 `docs/research/` 아래)
0. **`execution_roadmap.md`** ← **실행 runbook(지금→KIIE, 스케일·시뮬·순서·레퍼런스). 막히면 여기부터.**
1. **`research_plan.md`** ← 마스터(주제·컨트리뷰션·RQ·실험설계·단계계획)
2. `contribution.md §8` ← 최종 컨트리뷰션·차별표 (※ §1–7은 사고과정 기록, 일부 superseded)
3. `novelty_sweep.md` ← 경쟁논문·빈칸 검증
4. `simulator_spec.md` ← 시뮬 설계
5. `proposal_kiie.md` ← 학술대회 초록형
- 배경(필요시, `docs/research/`): `synthesis.md`, `shortlist.md`, `lab_research_flows.md`, `cards/`. 문헌 파이프라인 계획은 `lit/pipeline.md`.

## 재개 검증 (코드 살아있는지)
```
cd ~/project/research-agent
python sim/run_eval.py     # sanity 전부 PASS여야 정상
python sim/joint_demo.py   # joint 룰이 NV+EDD 베이스라인 능가 확인
```

## 핵심 사실 캐시
- **제목**: LLM-Evolved Interpretable Joint Dispatching Rules for Integrated Machine-and-AGV Dynamic FJSP
- **신규성**: 기계 시퀀싱 룰 + AGV 디스패칭 룰을 **동시(joint) 진화** (기존 AHD는 한쪽만; 통합은 DRL D3QN뿐·비해석)
- **시뮬 인터페이스**: `policy(features)->score` (AGV) + `machine_policy(features)->score` (기계). `sim/agv_fms.py::simulate(cfg, agv_policy, seed, machine_policy=)`
- **엔진 결정(2026-06-29)**: salabim 전진(`sim/agv_fms_salabim.py`, 동일 인터페이스) + custom(`sim/agv_fms.py`) 동결 오라클. `sim/crosscheck_salabim.py`로 충실성 검증(NV/EDD/FIFO 비트동일, 순위 2/2 일치, salabim ~2.5-3x 느림 → 진화 루프는 custom 권장).
- **프로젝트 가이드**: `CLAUDE.md`(헌법) + agent `novelty-watch`(스쿱 감지) + skill `ahd-loop`(joint 실험 절차).
- **Zotero**: 컬렉션 `agv-llm-heuristic` (key JIREF4BS, 40편). zotero MCP는 user scope 등록됨. arXiv는 DOI 아닌 URL로 add.
- **타깃**: KIIE 학술대회(3개월) → SCIE 저널.
- **위협 1순위**: HUST(Gao/Li) — AGV로 확장 가능 → 속도(KIIE 선점).

## 코드/도구
- `sim/` — DES 시뮬·baseline·joint·AHD 하네스 (검증됨) + `agv_fms_salabim.py`(salabim 포팅)·`crosscheck_salabim.py`(엔진 교차검증) + `configs.py`(regime R1–R4·scale grid·train/valid/test seed 분리)
- `ahd/` — LLM-AHD joint 진화 루프 (실제 `claude` CLI proposer + ReEvo, 키 없이 `python -m ahd.run`)
- `lit/scripts/` — collect.py(OpenAlex 수집)·archive_zotero.sh(Zotero)·fetch_pdfs.py(OA PDF)
- 새 주제 돌리려면: `lit/prompts/` + `lit/pipeline.md` 흐름, `queries.txt`만 바꿔 `lit/scripts/collect.py` 실행
