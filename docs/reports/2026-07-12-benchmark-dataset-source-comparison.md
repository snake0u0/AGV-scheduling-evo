# 보고서 - 오픈소스 벤치마크 데이터셋 후보 비교 (소/중/대규모 실험용)

작성 2026-07-12.

## 결론 (한눈에)
- 후보 4개(+연구자 1명 팔로업) 중 실제로 쓸 것은 **2개뿐**:
  - **소규모(문헌 정확 재현)**: `GA-heuristic-approach_to_simultaneous_-scheduling_or_AGV_and_machine`
    (github.com/Aihong-Sun) 의 `Instance/Bilge_Ulusoy/{C1,C2}` — travel matrix 포함 + 문헌 makespan 비교표 있음.
  - **중·대규모(스케일링 곡선)**: `FJSP_AGV-Machine_Instances`(github.com/Aihong-Sun) 의 `middle_scale/`,
    `large_scale/` 폴더 — travel matrix 포함, 자체생성(문헌값 없음).
- **스킵**: 같은 리포의 `Data_Set1/*`(Barnes/Brandimarte/Fattahi) — **직접 unpickle해서 확인한 결과 AGV/travel
  matrix 필드가 전혀 없는, 순수 FJSP 문헌 데이터의 재포장본**이라 우리 joint 연구엔 무의미, `SchedulingLab/
  fjsp-instances`와 내용이 겹침. `SchedulingLab/fjsp-instances`(MIT, 336개 표준 인스턴스) 자체도 AGV가 없어서
  메인 실험표에서 제외(machine-only ablation을 별도로 하고 싶을 때만 보조자료). `movingai.com` MAPF 벤치마크는
  job/기계 구조가 아예 없는 순수 경로탐색 데이터라 실험표에 못 들어감(대규모 congestion 레이아웃 소스로만 잠재
  활용 가능, 채택 안 함).
- 부수 조사: KAIST Young Jae Jang 교수(AGV/AMR/OHT 전문)의 논문들도 훑었으나, 전부 **상용 시뮬레이터(Applied
  Materials AutoMod)나 실제 팹 데이터(1000+대, 산업기밀)** 로 검증돼 있어 재사용 가능한 오픈 데이터셋은 없음.
  유일한 오픈 리드는 그의 MAPF/deadlock 논문이 인용한 movingai.com 맵.

## 처음 목적 / 왜
- `research_plan.md`/`execution_roadmap.md`가 지목한 **"소규모 문헌 수치 재현(follow-up, 미착수)"** 갭을 메우고,
  KIIE/SCIE 논문에 넣을 **소·중·대규모 + 다양한 데이터셋** 실험 매트릭스를 구성하기 위해, 기성 오픈소스 FJSP+AGV
  벤치마크가 있는지 조사(GitHub 검색 + 특정 연구자 팔로업).

## 무엇을 어떻게 했나
1. GitHub에서 FJSP+AGV joint 인스턴스를 공개한 리포 탐색 → `Aihong-Sun/FJSP_AGV-Machine_Instances`,
   `Aihong-Sun/GA-heuristic-approach_...`, `SchedulingLab/fjsp-instances` 3개 확보.
2. KAIST Young Jae Jang 교수(AGV/AMR/OHT 연구자) Google Scholar 프로필 확인 → 논문 목록에서 관련 데이터셋 유무
   확인(`movingai.com` MAPF 벤치마크가 그의 논문에서 재사용된 것 발견).
3. **각 리포의 README 주장을 그대로 믿지 않고, 실제 파일을 다운로드해 unpickle하여 필드 구조를 직접 검증**:
   - `Data_Set1/FJSP_Brandimarte/Mk01.pkl` → `{n, m, processing_time, Processing machine, Jobs_Onum}` (AGV 필드 없음)
   - `Data_Set1/FJSP_Fattahi/Fattahi1.pkl` → 동일 구조 (AGV 필드 없음)
   - `GA-heuristic-approach/Instance/Bilge_Ulusoy/C1/E11.pkl` → `(n=5, m=4, agv=2, processing_time, machine_seq, travel_matrix[5x5])` (AGV 있음)
   - `FJSP_AGV-Machine_Instances/middle_scale/n30_m8_agv3.pkl` → `{n, m, agv_num, processing_time, Processing_machine, travle_Matrix}` (AGV 있음)
   - `FJSP_AGV-Machine_Instances`의 git tree 전체를 재귀 조회 → README가 언급한 로더 파일(`fjspT.py`,
     `Generator_FJSPT.py`, `EX.py`)이 **실제로는 존재하지 않음**, `small_scale/`도 README가 주장한 12개가 아니라
     **1개 파일뿐**임을 확인.

## 결과 (비교표)

| 후보 | AGV/travel matrix 있음? | 문헌값 비교 가능? | 라이선스 | 채택 |
|---|---|---|---|---|
| `GA-heuristic-approach/Instance/Bilge_Ulusoy` | ✅ (확인함) | ✅ (README에 EX11~EX104 82개 gap표) | 명시 없음 | **채택(소규모)** |
| `FJSP_AGV-Machine_Instances/middle_scale`, `large_scale` | ✅ (확인함) | ❌ (자체생성) | 명시 없음 | **채택(중·대규모)** |
| `FJSP_AGV-Machine_Instances/Data_Set1/*`, `small_scale`(1개뿐) | ❌ (확인함, AGV 필드 없음 / 파일 사실상 없음) | - | - | 스킵 |
| `SchedulingLab/fjsp-instances` (Barnes/Behnke/Brandimarte/Dauzere/Fattahi/Hurink/Kacem, 336개) | ❌ (AGV 자체가 없는 순수 FJSP) | ✅ (문헌 정리 잘됨) | MIT | 메인 제외, machine-only ablation용 후보로만 보류 |
| `movingai.com/benchmarks/mapf.html` (Sturtevant, 24맵×25시나리오) | 라우팅만 있고 job/기계 구조 없음 | - | 학술 인용 조건 | 미채택(대규모 레이아웃 소스로만 잠재 고려) |
| Young Jae Jang(KAIST) 논문들 | 방법론은 관련 있으나 데이터는 전부 비공개(AutoMod 상용 시뮬/실팹 1000+대) | - | - | 채택 데이터 없음 |

## 한계 / 다음
- 채택한 두 리포(`GA-heuristic-approach`, `FJSP_AGV-Machine_Instances`) 모두 **라이선스 미명시** — 내부 검증·재현
  용도는 문제없으나, 논문에 인스턴스를 그대로 오픈소스로 재배포하려면 원저자 확인 또는 원 문헌(Bilge-Ulusoy 1995)
  직접 인용으로 대체 필요.
- 파일 포맷이 Python pickle(.pkl) — 신뢰 안 되는 소스이므로 로더 작성 시 내용 확인 후 JSON/CSV 등으로 변환 권장.
- 다음 단계: 두 데이터셋을 `sim/` 인터페이스(travel matrix + job/operation 구조)에 맞는 로더로 변환 →
  (1) Bilge-Ulusoy 소규모에서 문헌 makespan 재현 비교, (2) middle/large_scale로 스케일링 곡선 실험.

## 관련 파일
- 원본 리포: github.com/Aihong-Sun/GA-heuristic-approach_to_simultaneous_-scheduling_or_AGV_and_machine,
  github.com/Aihong-Sun/FJSP_AGV-Machine_Instances, github.com/SchedulingLab/fjsp-instances
- 참고(미채택): movingai.com/benchmarks/mapf.html
- 검증에 쓴 임시 스크립트/다운로드 파일: `$CLAUDE_JOB_DIR/tmp/` (세션 종료 시 정리됨, 저장소에 커밋 안 함)
- 관련 이전 보고서: `docs/reports/2026-07-10-project-status-and-problem-design-review.md`(소규모 문헌 재현
  갭을 최초 지목)
