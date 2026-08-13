# 문헌 기준값 - 출처

우리 격차(gap)를 재는 자다. **코드에 절대 하드코딩하지 않는다** - 2026-08-07 이전에는
6개 실험 스크립트에 각각 복사돼 있었고, 한 곳의 오타가 조용히 결론을 바꿀 수 있는 상태였다
(당시 검사에서는 6벌 모두 일치했다). 읽는 곳은 `experiments/common.py` 한 곳뿐이다.

---

## `berterottiere2024_table8.tsv`

**Berterottière, Dauzère-Pérès & Yugma (2024), EJOR 312(3), 890-909, Table 8.**
Zotero `3XNMDN47`. 18개 Dauzère-Pérès & Paulli (1997) 인스턴스 x 차량 2/4/6대.

- 값은 **iteration-stop** 기준 makespan이다. 같은 논문에 time-stop 값도 있으므로
  둘을 섞지 않도록 주의한다.
- 인스턴스 파일 = `data/instances/fjspt-lucasberter/Dauzere_Data/Text/{stem}.txt`
- travel matrix = `BerterottiereTravelTimes/layout{5,8,10}.txt` (기계 수에 맞춰 선택)

**주의: `Berterottiere/dpp{2,4,6}veh/`의 해 파일 헤더 Cmax는 인용하지 말 것.**
그 파일들의 M/V 시퀀스가 헤더와 모순된다(54/54 불일치, 2026-07-23 확인).
논문 Table 8 값만 쓴다.

## `deroussi_published.tsv`

**Deroussi & Norre (2010) 인스턴스 fjsp1-10의 공표 makespan.** 차량 2대 고정.

- 생성 방식: `data/instances/fjspt-lucasberter/Deroussi/{stem}.txt` 해 파일 헤더에서 직접 추출
- **우리 시뮬레이터가 이 10개를 전부 정확히 재현한다**(`tests/test_replay_deroussi.py`, 10/10).
  즉 이 값들은 인용된 숫자가 아니라 **우리가 검증한 숫자**다.
- Berterottière et al. (2026) EJOR 332, Table 6의 fjsp1-10 값과도 일치한다:
  134, 114, 120, 114, 94, 138, 112, 178, 144, 174

---

## 아직 없는 것

| 데이터셋 | 상태 |
|---|---|
| fattahi (mfjs, 20개) | 이동시간 행렬 미확보 -> 실험 불가 |
| Homayouni_Brandimarte | 이동시간 행렬 미확보 -> 실험 불가 |
| Kumar EX-series (57개) | 인스턴스 자체 미보유 |

이 셋의 이동시간 출처는 Homayouni & Fontes (2021, J Glob Optim)와 Kumar et al. (2011)이다.
열리면 여기에 TSV를 추가하고 `experiments/common.py`의 `REFERENCES`에 등록한다.
**Han(2024)/Meng(2025)의 5개 데이터셋과 같은 표에서 비교하려면 이게 선행돼야 한다.**
