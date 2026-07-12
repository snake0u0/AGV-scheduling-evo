# 보고서 - 오픈소스 벤치마크 데이터셋 후보 비교 (소/중/대규모 실험용)

작성 2026-07-12. **업데이트 2026-07-12(같은 날, 2차 조사)**: 논문 5편을 추가로 확인해 문헌 계보를 끝까지
추적, 최초 버전의 결론(Aihong-Sun GitHub 리포 채택)을 **더 나은 1차 출처로 대체**함. 최초 버전 내용은 §1에 보존.

## 결론 (한눈에)
- **최종 결론(2차 조사 반영): GitHub 리포(Aihong-Sun) 대신 문헌 1차 출처를 직접 쓴다.** 5개 논문을 추적한 결과
  Homayouni & Fontes 그룹이 운영하는 **`fastmanufacturingproject.wordpress.com/2019/04/11/fjspt-instances/`**
  페이지 하나에서 **소·중·대규모 전체 5개 데이터셋의 원본(job/기계/travel matrix)을 직접 다운로드**할 수 있음을
  확인함(7개 PDF 파일, 전부 HTTP 200 + 실제 PDF로 검증). 이게 §1에서 채택했던 Aihong-Sun 리포(라이선스 불명,
  pickle 포맷, README 내용 일부 실체 없음)보다 훨씬 신뢰도 높은 1차 출처임.
- **5개 데이터셋의 완전한 문헌 계보**:
  | 데이터셋 | 규모 | 원출처 | 우리가 확보한 다운로드 |
  |---|---|---|---|
  | Dataset1 (FJSPT1-10) | 소 | **Deroussi & Norre (2010)** = Bilge&Ulusoy(1995) 10job×4layout, 기계 2배 복제 | `fjspt_instances_deroussinorre2010-1.pdf` |
  | Dataset2 (EX/EXF-series, ~40개) | 소 | **Kumar, Janardhana, Rao (2011)** = 같은 Bilge&Ulusoy job×layout, 기계 3배. **job set 3/6/10은 원논문 오타로 제외** | `fjspt_kumar2011.pdf` |
  | Dataset3 (SFJS/MFJS, MFJST) | 소·중 | **Homayouni & Fontes (2020/2021)** = Fattahi et al.(2007) FJSP + 여러 문헌 layout 이식 | `2to8machines_layouts.pdf`, `4to18machines_layouts-1.pdf`, `fjspt_hf2020.pdf` |
  | Dataset4 (MK/MKT01-10) | 대 | **Homayouni & Fontes (2020)** = Brandimarte(1993) + 임의생성 travel time(2~10) | `brandimarte1993-2.pdf` |
  | Dataset5 (mt10/setb4/seti5-t, 21개) | 대 | **Homayouni & Fontes (2020)** = Chambers&Barnes(1996) + 임의생성 travel time(2~10) | `chambersbarnes1996-1.pdf` |
- **AGV 대수는 이 문헌 계보 전체에서 2대 고정**(Karimi 2017만 예외). 즉 이 데이터들은 job/machine/operation
  규모 다양성(소→대)은 주지만, **우리 40-50 AGV 목표는 문헌 어디에도 없음** - 이건 여전히 우리 자체 기여.
- 5편의 논문(Kumar 2011, Ham 2020, Han 2024, Meng 2025, Homayouni 2023 BRKGA)을 Zotero(`agv-llm-heuristic`)에
  아카이빙 + `docs/research/cards/`에 요약카드 작성 완료(파일명은 §관련 파일 참고).
- §1(최초 조사, GitHub 리포 3개 + movingai.com + Young Jae Jang 팔로업)의 결론은 **이제 참고용**으로만 남김 -
  Aihong-Sun 리포는 더 이상 채택 안 함.

---

## §2. 2차 조사 - 문헌 1차 출처 추적 (2026-07-12, 최종 채택)

### 처음 목적 / 왜
§1에서 채택했던 Aihong-Sun GitHub 리포는 라이선스 불명·README 주장과 실제 파일 불일치(로더 스크립트 부재,
`small_scale` 1개뿐)라는 약점이 있었음. 우연히 "EX"/"MKT" 같은 인스턴스 명명 체계가 반복 등장하는 걸 보고,
이들의 진짜 학술 출처(누가 언제 만들었는지, 원본을 어디서 받는지)를 논문 자체에서 추적하기로 함.

### 무엇을 어떻게 했나
1. 사용자가 제공한 PDF들을 순서대로 읽으며 인용 사슬을 역추적:
   `Meng et al. 2025 TSMC(Novel CP Models...)` → 참고문헌에서 원저자 확인 → `Kumar et al. 2011`,
   `Ham 2020`, `Han et al. 2024(DCGA)` 확보 → Han(2024) 본문에서 **"모든 데이터셋(가공시간+운반시간 포함)은
   fastmanufacturingproject.wordpress.com에서 다운로드 가능"** 이라는 명시적 문장 발견.
2. 그 페이지에 직접 접속(HTTP 200 확인) → 페이지 HTML에서 `<a href>` 전부 추출 → 실제 첨부파일(PDF) 7개의
   `wp-content/uploads/...` 직접 링크를 찾아냄. 페이지 본문 텍스트에서 각 데이터셋의 **정확한 문헌 계보 서술**을
   확인(Deroussi&Norre 2010 / Kumar et al. 2011 / Fattahi et al. 2007 / Brandimarte 1993 / Chambers&Barnes 1996
   각각이 무엇을 어떻게 변형했는지).
3. 7개 파일 전부 `curl`로 다운로드해 **HTTP 200뿐 아니라 `file` 명령으로 실제 PDF 시그니처·페이지수까지 검증**
   (README/링크 텍스트만 믿지 않고 바이트 단위 확인 - §1에서 얻은 교훈 적용).
4. 사용자가 같은 파일들을 직접 받아 재확인 요청 → 파일 크기·페이지수 바이트 단위로 대조, 전부 일치 확인.
   추가로 `Homayouni, Fontes & Gonçalves (2023) ITOR`(BRKGA 원논문)도 함께 확보됨.
5. 5개 논문(Kumar 2011 / Ham 2020 / Han 2024 / Meng 2025 / Homayouni 2023) 전문을 읽고 Zotero collection
   `agv-llm-heuristic`(JIREF4BS)에 아카이빙 + 메타데이터 정리(DOI/저자/권호 보정) + `docs/research/cards/`에
   요약카드 5개 작성.

### 결과 - 확보한 원본 다운로드 링크
출처 페이지: `https://fastmanufacturingproject.wordpress.com/2019/04/11/fjspt-instances/`

| 파일 | 데이터셋 | 크기 | 페이지 |
|---|---|---|---|
| `wp-content/uploads/2019/04/fjspt_instances_deroussinorre2010-1.pdf` | Dataset1 | 245KB | 2p |
| `wp-content/uploads/2020/05/fjspt_kumar2011.pdf` | Dataset2 | 178KB | 3p |
| `wp-content/uploads/2020/05/2to8machines_layouts.pdf` | Dataset3 (layout) | 84KB | 2p |
| `wp-content/uploads/2020/05/4to18machines_layouts-1.pdf` | Dataset3 (layout) | 253KB | 7p |
| `wp-content/uploads/2020/05/fjspt_hf2020.pdf` | Dataset3 (job set) | 383KB | 12p |
| `wp-content/uploads/2020/05/brandimarte1993-2.pdf` | Dataset4 | 37KB | 5p |
| `wp-content/uploads/2020/05/chambersbarnes1996-1.pdf` | Dataset5 | 163KB | 10p |

포맷: 각 파일 첫 줄 = `n_jobs n_machines (평균기계수)`, 이후 job별 1행 = `n_ops [기계수 (기계,가공시간)쌍...]` -
파싱 규칙이 페이지에 명시돼 있어 `sim/` 로더 작성이 어렵지 않음.

### 읽은 5개 논문 중 향후 레퍼런스로 삼을 것
| 논문 | 읽을 가치 | 이유 |
|---|---|---|
| **Kumar et al. 2011** | ★★★ 계속 참조 | Table 4(원본 job set)+Fig 3(travel matrix)를 직접 전사할 1차 데이터 소스. `docs/research/cards/kumar2011-fjsp-agv-alt-routing.md` |
| **Han et al. 2024 (DCGA)** | ★★★ 계속 참조 | 데이터 다운로드처를 알려준 논문 + non-LLM SOTA 성능표(5개 데이터셋 전체) + 우리 `research_plan.md` 앵커 저자(Meng)와 동일 계보. `docs/research/cards/han2024-dcga.md` |
| **Meng et al. 2025 (TSMC)** | ★★☆ 관련연구용 | 최신 CP+메타휴리스틱 SOTA, 단 objective가 makespan(우리는 tardiness 주목적)이라 직접 수치비교는 주의. `docs/research/cards/meng2025-cp-dcga-cp.md` |
| **Ham 2020** | ★★☆ 방법 참고용 | FJSPT1-10 진짜 원출처 확인 + "고전 FJSP + 자체 travel matrix 생성" 전략의 선례(T/P 비율 설계 참고 가능). `docs/research/cards/ham2020-transbot-cp.md` |
| **Homayouni et al. 2023 (BRKGA)** | ⬜ 아직 전문 미독 | Dataset3/4/5의 진짜 원저자 그룹 논문으로 추정되나, 이번 세션엔 서지 확인만 함 - **다음 세션에서 전문 읽기 우선순위 높음**(Dataset3 MFJST의 정확한 생성 규칙 확인 필요). `docs/research/cards/homayouni2023-brkga.md` |

### 한계 / 다음
- 7개 데이터 PDF는 아직 우리 `sim/` 포맷으로 전사 안 됨 - 다음 세션 작업.
- Homayouni 2023 BRKGA 논문 전문 미독 - Dataset3(MFJST) 생성 규칙 확인 필요.
- WordPress 블로그 첨부파일이라 링크 영속성 보장 안 됨 - 로컬에 파일 확보해뒀으므로 리스크는 낮으나, 정식 인용 시
  원 논문(Deroussi&Norre 2010, Kumar 2011, Fattahi 2007, Brandimarte 1993, Chambers&Barnes 1996, Homayouni&Fontes
  2020/2021)을 인용하고 이 블로그는 "데이터 접근 경로"로만 각주 처리할 것.
- AGV 대수 확장(2→40-50)은 이 문헌 어디에도 없음 - 여전히 우리 자체 컨트리뷰션 영역.

---

## §1. 1차 조사 (2026-07-12, 오전 - 이제 참고용, GitHub 리포 채택은 철회됨)

### 무엇을 어떻게 했나
1. GitHub에서 FJSP+AGV joint 인스턴스를 공개한 리포 탐색 → `Aihong-Sun/FJSP_AGV-Machine_Instances`,
   `Aihong-Sun/GA-heuristic-approach_...`, `SchedulingLab/fjsp-instances` 3개 확보.
2. KAIST Young Jae Jang 교수(AGV/AMR/OHT 연구자) Google Scholar 프로필 확인 → 논문 목록에서 관련 데이터셋 유무
   확인(`movingai.com` MAPF 벤치마크가 그의 논문에서 재사용된 것 발견).
3. **각 리포의 README 주장을 그대로 믿지 않고, 실제 파일을 다운로드해 unpickle하여 필드 구조를 직접 검증**:
   - `Data_Set1/FJSP_Brandimarte/Mk01.pkl` → `{n, m, processing_time, Processing machine, Jobs_Onum}` (AGV 필드 없음)
   - `Data_Set1/FJSP_Fattahi/Fattahi1.pkl` → 동일 구조 (AGV 필드 없음)
   - `Data_Set1/FJSP_Barnes/mt10c1.pkl` → 동일 구조 (AGV 필드 없음, 3개 서브폴더 전부 확인 완료)
   - `GA-heuristic-approach/Instance/Bilge_Ulusoy/C1/E11.pkl` → `(n=5, m=4, agv=2, processing_time, machine_seq, travel_matrix[5x5])` (AGV 있음) - **§2에서 이게 Kumar 2011의 EX11과 동일 인스턴스임을 확인**
   - `FJSP_AGV-Machine_Instances/middle_scale/n30_m8_agv3.pkl` → `{n, m, agv_num, processing_time, Processing_machine, travle_Matrix}` (AGV 있음, 문헌값 없는 자체생성)
   - `FJSP_AGV-Machine_Instances`의 git tree 전체를 재귀 조회 → README가 언급한 로더 파일(`fjspT.py`,
     `Generator_FJSPT.py`, `EX.py`)이 **실제로는 존재하지 않음**, `small_scale/`도 README가 주장한 12개가 아니라
     **1개 파일뿐**임을 확인.

### 당시 결론 (철회됨 - §2 참고)
~~소규모=`GA-heuristic-approach/Instance/Bilge_Ulusoy`, 중·대규모=`FJSP_AGV-Machine_Instances/middle_scale`+
`large_scale` 채택~~ → **§2의 1차 문헌 출처(fastmanufacturingproject.wordpress.com)로 대체**. `SchedulingLab/
fjsp-instances`(MIT, AGV 없는 순수 FJSP 336개) 및 `movingai.com`(MAPF 전용, job/기계 구조 없음)에 대한 평가는
유효: 메인 실험표 제외, 각각 machine-only ablation·대규모 레이아웃 참고용으로만 보류. Young Jae Jang(KAIST)
계열은 여전히 재사용 가능한 오픈 데이터 없음(상용 시뮬레이터/실팹 데이터, 비공개).

---

## 관련 파일
- **1차 출처(§2, 최종 채택)**: `https://fastmanufacturingproject.wordpress.com/2019/04/11/fjspt-instances/`
  (7개 PDF, 위 표 참고)
- **읽은 논문 5편(Zotero `agv-llm-heuristic`/JIREF4BS에 아카이빙, 키는 카드 참고)**:
  `docs/research/cards/kumar2011-fjsp-agv-alt-routing.md`, `docs/research/cards/ham2020-transbot-cp.md`,
  `docs/research/cards/han2024-dcga.md`, `docs/research/cards/meng2025-cp-dcga-cp.md`,
  `docs/research/cards/homayouni2023-brkga.md`
- **§1 GitHub 리포(더 이상 채택 안 함, 참고용)**: github.com/Aihong-Sun/GA-heuristic-approach_to_simultaneous_-scheduling_or_AGV_and_machine,
  github.com/Aihong-Sun/FJSP_AGV-Machine_Instances, github.com/SchedulingLab/fjsp-instances
- 참고(미채택): movingai.com/benchmarks/mapf.html
- 검증에 쓴 임시 스크립트/다운로드 파일: `$CLAUDE_JOB_DIR/tmp/` (세션 종료 시 정리됨, 저장소에 커밋 안 함).
  PDF 원본은 `docs/research/pdfs/`에 두지 않음(gitignore 대상, Zotero가 원문 저장소 역할).
- 관련 이전 보고서: `docs/reports/2026-07-10-project-status-and-problem-design-review.md`(소규모 문헌 재현
  갭을 최초 지목)
