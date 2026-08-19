# 실행 로드맵 (execution runbook) — 지금 → KIIE 투고

작성 2026-06-29 (개정: 스케일 40–50 AGV 확정 반영). **이 문서 = "내가 앞으로 뭘, 어떤 순서로, 어떤 명령으로 돌려서, 어떤 논문 산출물을 만드나".**
학술 설계(무엇을·왜)는 `research_plan.md §5`가 마스터. 이 문서는 그걸 **실제 실행**으로 매핑.

---

## 0. 현 위치 (마일스톤 `research_plan.md §7` 기준)

| 마일스톤 | 상태 | 비고 |
|---|---|---|
| **M1** LLM-AHD 루프 동작 | ✅ 완료 | 실제 `claude` CLI 루프(`ahd/`), train/valid/test 분리, salabim crosscheck |
| **M1.5 시뮬 대규모화** | ⬜ **신규·임계경로** | 혼잡-지연 + 40–50 AGV 인스턴스 생성기 (아래 §2) |
| **M2** baseline 셋 | 🔸 부분 | B1 재료만. B2 GP·B5·B6 빌드 필요. B3/B4 DRL=SCIE |
| **M3** regime·전이·ablation | ⬜ | config 있음, 캠페인 미실행 |
| **M4** 집필 | ⬜ | |

---

## 1. 스케일·시뮬 결정 (이 로드맵의 핵심 변경) ★

**확정(2026-06-29, 사용자)**: KIIE부터 **40–50 AGV 대규모**. (k≤6은 루프 검증용 연습이었음.) 이전 문서가 "40–50=SCIE 스트레치"로 적은 건 오기 — 정정.

세 가지 설계 결정 + 근거(문헌 조사 결과):
1. **혼잡-지연 모델**: AGV 밀집도/공유구간 부하에 따라 travel_time 증가. → 대수가 많을수록 병목이 생기는, "AGV 병목 완화"라는 컨트리뷰션 훅과 직결. **발명 아님** — AMHS 혼잡 문헌에 앵커: *"Congestion-aware dynamic routing in AMHS"* (C&IE 2014, doi:10.1016/j.cie.2014.02.002), AGV scheduling/routing 서베이(로컬 `0.Review`), 충돌없는 라우팅 PDF(로컬).
2. **벤치마크 앵커 = FJSP+운반 벤치마크 확장**: 기성 40–50대 FJSP+AGV 벤치마크는 **없음**(대규모 fleet은 fab AMHS 문헌에만 존재, 그쪽은 joint 시퀀싱 약함 → N1 훼손). 그래서 **고전 joint 벤치마크를 앵커로 쓰고 우리가 스케일업**:
   - **Bilge & Ulusoy (1995)** Zotero `GP6HQQSG` — 기계+MHS 동시 스케줄링 고전 벤치마크(레이아웃·job set·travel matrix). **N1의 정통 앵커.** (PDF 없음 → 서베이/후속논문으로 구조 확보)
   - **Berterottière, Dauzère-Pérès & Yugma (2024)** Zotero `3XNMDN47` (PDF 있음) — 현대 FJSP+transport 인스턴스. 스케일업 기준.
   - **Meng et al. (2023) Multi-AGV FJSP** Zotero `2JMVT7DP` / doi:10.3390/s23083815 — multi-AGV 인스턴스.
   - 우리 기여 = **(스케일업 40–50 + 혼잡-지연) 위에서 joint LLM-AHD.** 혈통은 추적가능, 대규모·혼잡·joint진화가 신규.
3. **프레이밍 유지**: joint 기계+AGV FJSP(N1) 그대로. 제목에 "large-scale/congested" 추가는 추후 검토(설정 미변경).

**리스크(정직)**: 자체 스케일업 인스턴스라 리뷰어 방어가 약할 수 있음 → 완화: ① 고전 벤치마크 혈통 명시 인용, ② 인스턴스 생성기+seed+혼잡모델 전부 오픈소스, ③ 소규모(Bilge-Ulusoy 원본)에서 우리 시뮬이 문헌 결과 재현됨을 보이고 거기서 스케일업.

---

## 2. 빌드 항목

| ID | 항목 | 현재 | 할 일 | 예상 |
|---|---|---|---|---|
| **S1** | **혼잡-지연 레이어** | AGV 무간섭(util 0.26@50대) | travel_time = base × f(국소밀집도/구간부하). `_features`의 congestion이 이를 반영하게 | 2–3d |
| **S2** | **대규모 인스턴스 생성기** | 단순 grid 랜덤 + 연산당 기계 1개(=JSP) | (a) **연산별 적격기계 집합**으로 진짜 FJSP화(유연도≈2), (b) Bilge-Ulusoy/Dauzère 구조 기반 레이아웃+job set, 40–50 AGV/큰 M/큰 layout, seed 분리. 구조 근거=`benchmark_anchor_notes.md` | 2–3d |
| **S3** | **검증(재현+crosscheck)** | crosscheck v0 | 소규모서 문헌값 재현 + salabim에도 혼잡 포팅 후 재-crosscheck | 2d |
| T1 | method 스위치 (P/B5/B6) | 양쪽 진화 | 한쪽 고정 옵션 | 0.5d |
| T2 | B1 최우수 고전 joint | joint_demo | 고전 쌍 grid 평가→최우수 | 0.5d |
| T3 | B2 GP joint (DEAP) | 없음 | 동일 feature·예산 GP | 2–3d |
| T4 | 캠페인 러너+집계 | 단일 regime | regime×method→CSV 표 | 1d |
| T5 | 통계·해석성 추출 | 없음 | Wilcoxon + 규칙 식·복잡도 | 0.5d |

DRL(B3/B4), 전이, 배터리/고장 = **SCIE**(§5).

---

## 3. 실행 순서 (각 단계 = 빌드 → 실행 → 산출물 → done)

### 단계 0 — 앵커 정독 ✅ 완료
- Berterottière 2024(`3XNMDN47`) 정독 완료 → 구조·규모·혼잡갭·검증전략을 **`benchmark_anchor_notes.md`** 에 정리.
- 핵심: data set 1 = Bilge-Ulusoy(8기계·유연도2·차량2–6); 대규모 벤치마크 없음 확증; 선행연구는 혼잡 인지하나 미모델링(우리 빈칸); 현 sim은 JSP라 FJSP화 필요.

### 단계 1 — 시뮬 대규모화 (S1·S2·S3) [~1.5–2주] ← 임계경로
- 혼잡-지연 + 40–50 AGV 생성기 + 재검증.
- **done**: 50 AGV에서 agv_util·혼잡이 의미있게 반응(병목 재현), 소규모서 문헌 재현, salabim 재-crosscheck 통과.

### 단계 2 — 실험 인프라+해석성 (T1·T2·T4·T5) [~2d]
- regime×method 러너 → `runs/.../results/main_R1.csv` 등.

### 단계 3 — GP baseline (T3) [~2–3d]
- `ahd/gp.py`(DEAP) → 표1 완성(P vs B1·B2·B5·B6).

### 단계 4 — 통계+글쓰기 (M4) [~1주]
- Wilcoxon, 표·그림 → `proposal_kiie.md` 결과 채움 → 초록/슬라이드.
- 투고 직전 `novelty-watch` 1회.

> 합계 ≈ 4–5주 작업분 + 글쓰기. **임계경로는 단계1(시뮬 대규모화)** — 소규모 KIIE보다 무거워졌으나 40–50 타깃엔 필수.

---

## 4. KIIE 산출물 (test seed에서만, 평균±표준편차)
- **표1**: R1(운반병목)·R3에서 **P vs B1·B2·B5·B6** — tardiness(주)·makespan·throughput·**agv_util/혼잡지표**.
- **표/그림2 (해석성)**: P 진화 규칙 식 + 복잡도 + 해석. ← N1 해석가능 기둥.
- **그림3**: 세대별 수렴, **혼잡 vs 대수** 곡선(대규모 효과 가시화).
- 통계: P vs B1 Wilcoxon.

---

## 5. 열린 결정 / 레퍼런스
- **LLM 모델 기록**: Sonnet-4-6 via Claude Code CLI(구독, 키 없음). 논문엔 실제 모델/호출수/토큰/비용으로(러너 자동 로깅). 모든 LLM 방법 동일 모델·예산.
- **레퍼런스(확보)**: 혼잡=C&IE2014(doi:10.1016/j.cie.2014.02.002); 앵커=Bilge-Ulusoy1995(`GP6HQQSG`)·Berterottière2024(`3XNMDN47`,PDF)·Meng2023(`2JMVT7DP`); 로컬 `3_agv_scheduling`에 AGV scheduling/routing 서베이·MAPF 벤치마크·충돌없는 라우팅·LLM-AHD 경쟁자(DSevolve/FunSearch/ReEvo/VRPAgent) 다수.
- **P가 약하면**: ReEvo 강화(`vary`에 fitness값+reflection; skill `ahd-loop`)를 단계2 결과 보고 투입.

---

## 6. SCIE 확장 (KIIE 후)
교란(AGV 고장·배터리·충전), 전이/일반화(unseen layout/fleet, vs DRL 저하폭), DRL/D3QN(B3/B4), 전체 ablation, 다목적, 더 큰 fleet(100+). → C&IE/ESWA/JIM/RCIM/IEEE T-ASE.

---

## 부록 — 현재 동작 명령
```
python -m ahd.run                  # P: joint LLM-AHD (claude CLI 자동, 없으면 mock)
python sim/run_eval.py             # 고전 룰 비교(B1 재료)+sanity
python sim/crosscheck_salabim.py   # 엔진 충실성
python sim/joint_demo.py           # 고전 joint 쌍 데모
```
