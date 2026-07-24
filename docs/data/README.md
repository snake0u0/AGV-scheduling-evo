# 연구 인스턴스 데이터 · 논문 (FJSP-AGV)

정리 2026-07-16. 파일은 `instances/`(실제 벤치마크 데이터)와 `papers/`(방법론·SOTA·출처 논문)로 분류.

## instances/ — 벤치마크 데이터 (전부 공개)

원본 다운로드처: fastmanufacturingproject.wordpress.com/2019/04/11/fjspt-instances/
전부 정적(static) · makespan · AGV 2대 기준.

| 파일 | 데이터셋 | 규모 | 원 출처 |
|---|---|---|---|
| Dataset1_DeroussiNorre2010_FJSPT1-10.pdf | FJSPT1-10 (job set + travel matrix) | 소 | Deroussi & Norre 2010 (= Bilge & Ulusoy 1995, 기계 2배 복제) |
| Dataset2_Kumar2011_EX-series.pdf | EX-series | 소 | Kumar et al. 2011 (같은 job set, 대체기계 3개; job set 3/6/10은 오타로 제외) |
| Dataset3_HomayouniFontes_jobsets_SFJS-MFJS.pdf | SFJS/MFJS job set | 소·중 | Homayouni & Fontes (Fattahi 2007 기반) |
| Dataset3_HomayouniFontes_layouts_2-8machines.pdf | Dataset3 layout (2~8 기계) | 소·중 | Homayouni & Fontes |
| Dataset3_HomayouniFontes_layouts_4-18machines.pdf | Dataset3 layout (4~18 기계) | 소·중 | Homayouni & Fontes |
| Dataset4_Brandimarte1993_MK.pdf | MK01-10 (+운반시간) | 대 | Brandimarte 1993 + Homayouni & Fontes 운반 확장 |
| Dataset5_ChambersBarnes1996_Barnes.pdf | mt/setb/seti (+운반시간) | 대 | Chambers & Barnes 1996 + Homayouni & Fontes 운반 확장 |

## papers/ — 방법론 · SOTA · 출처 논문

| 파일 | 저자·연도 | 내용 | 우리 연구에서의 역할 |
|---|---|---|---|
| Kumar2011_IJAMT_FJSP-AGV_DE.pdf | Kumar, Janardhana, Rao 2011 (IJAMT) | 차분진화(DE)로 기계+AGV 동시 스케줄링 | Dataset2 출처 논문, 소규모 문헌값 |
| Ham2020_JIM_transbot_CP.pdf | Ham 2020 (J. Intell. Manuf.) | FJSP+transbot CP 정식화 | Dataset1 최적값·검증 기준, "고전 FJSP + 자체 운반" 선례 |
| HomayouniFontes2023_ITOR_BRKGA.pdf | Homayouni, Fontes, Gonçalves (ITOR) | BRKGA | Dataset3/4/5 원저자 그룹, 비교 알고리즘 |
| Han2024_SwarmEvolComput_DCGA.pdf | Han et al. 2024 (Swarm Evol. Comput.) | 이중 population 유전 알고리즘(DCGA) | 데이터 다운로드처 명시, best-known 18개 갱신 |
| Meng2025_TSMC_CP-DCGA-CP_SOTA.pdf | Meng et al. 2025 (IEEE TSMC) | CP + CP-보조 메타휴리스틱(DCGA-CP) | 현 SOTA (35 신규 최적 + 32 best-known 갱신) |

## 메모
- 각 논문 요약 카드: `docs/research/cards/` (kumar2011, ham2020, han2024, meng2025, homayouni2023)
- 데이터셋 계보·비교 보고서: `docs/reports/2026-07-12-benchmark-dataset-source-comparison.md`
- 정식 인용 시 blog가 아니라 위 "원 출처" 논문을 인용할 것.
