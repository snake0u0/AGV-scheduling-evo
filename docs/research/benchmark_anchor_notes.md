# 벤치마크 앵커 노트 — FJSPT 인스턴스 구조 (S2 생성기용)

작성 2026-06-29. 출처: Berterottière, Dauzère-Pérès & Yugma (2024) EJOR 312(3) 890–909,
doi:10.1016/j.ejor.2023.07.036 (Zotero `3XNMDN47`, 전문 정독). 이 노트 = S2(대규모 인스턴스 생성기)가
"추정"이 아니라 **문헌 구조에 박히도록** 하는 근거.

## 1. FJSPT 벤치마크 혈통 (data sets)
FJSPT(Flexible Job-shop Scheduling with Transportation) 문헌의 표준 벤치마크 계보:
- **Data set 1** — Deroussi & Norre (2010), ← **Bilge & Ulusoy (1995)** JSPT 인스턴스 기반.
  **8 기계, 기계 유연도 2**(각 연산은 2개 대체기계 중 1택, 처리시간 동일), 차량 **2–6대**. *FJSPT에서 가장 널리 쓰임.*
- **Data set 2** — Ham (2020), ← Hurink et al. (1994) FJSP + **3개 기계 레이아웃**.
- **Data set 3** — Homayouni & Fontes (2021), ← Brandimarte (1993) FJSP.
- (4번째 data set도 존재; 1번이 joint 기계+AGV의 정통 앵커.)
- Berterottière(2024) 자신도 신규 벤치마크 인스턴스 제안(§7.3).

## 2. FJSPT 인스턴스를 정의하는 것 (생성기 스펙)
하나의 인스턴스 = 다음의 조합:
- **Jobs × operations**: 각 job은 연산 시퀀스. **각 연산은 적격 기계 집합**(유연성)과 기계별 처리시간.
- **레이아웃**: 기계 위치 → **기계-간 travel time 행렬**. (기계 배정이 바뀌면 운반 travel time도 바뀜.)
- **Fleet**: 차량 K대. LU(load/unload) 스테이션.
- 4개 하위문제: 연산-기계 배정 / 운반-차량 배정 / 기계 시퀀싱 / 차량 라우팅.

## 3. 규모 — "기성 대규모 벤치마크 없음" 확증
문헌 인스턴스는 **소규모**: 기계 ~5–8, 차량 **2–6**. 40–50 차량 FJSP+AGV 인스턴스는 **존재하지 않음**.
→ 우리는 **이 구조를 유지한 채 스케일업**(많은 job·큰 레이아웃·40–50 차량) + **혼잡-지연**.

## 4. 혼잡 — 우리의 빈칸/동기 (논문에 직접 인용)
- 인용①: *"a fleet with too many vehicles might lead to significant congestion in the transportation
  network"* — 그러나 **그들은 혼잡을 모델링하지 않고 fleet 크기를 제한**해 회피.
- 인용②: *"the number of vehicles can have a significant impact on the makespan, in particular when the
  number of machines is large; 2→4 improves, 4→6 not necessarily."* — fleet 수확체감.
→ **우리 동기**: "선행연구는 대규모 fleet의 혼잡을 인지하나 모델링을 회피(fleet 제한)한다. 우리는 혼잡을
  명시 모델링하고, 40–50 AGV에서 혼잡을 완화하는 joint 규칙을 진화시킨다." (N1 + 대규모 + 혼잡)

## 5. 현재 sim과의 갭 (S2에서 메울 것)
- **유연성 없음**: 현 `agv_fms.py::_gen_jobs`는 연산당 기계 1개 고정(`randrange`) = **JSP+AGV**. 앵커(유연도 2)에
  맞추려면 **연산별 적격기계 집합 + 기계별 처리시간**으로 바꿔 **진짜 FJSP**로. (제목이 FJSP이므로 정합성에도 필요.)
- **혼잡 없음**: travel time이 거리만 의존, AGV 간 무간섭(50대 util 0.26). → S1 혼잡-지연.

## 6. 검증 전략 (리뷰어 방어)
1. **소규모 재현**: Bilge-Ulusoy/Deroussi data set 1을 우리 sim에 넣어 **문헌 makespan 재현**(혼잡 off, 차량 2–6).
   → "우리 시뮬은 표준 벤치마크에서 문헌과 일치" 근거.
2. 거기서 **스케일업 + 혼잡 on** → 40–50 AGV. 생성기·seed·혼잡모델 전부 오픈소스.

## 7. 인용 키
- 앵커: Bilge-Ulusoy 1995 (`GP6HQQSG`), Deroussi & Norre 2010, Berterottière/Dauzère-Pérès 2024 (`3XNMDN47`),
  Meng 2023 Multi-AGV FJSP (`2JMVT7DP`), Hurink 1994, Brandimarte 1993.
- 혼잡: AMHS congestion-aware routing, C&IE 2014 (doi:10.1016/j.cie.2014.02.002).
