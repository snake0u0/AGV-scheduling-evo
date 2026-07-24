# 이 데이터에 대한 우리 메모 (업스트림 README에 없는 것)

출처: https://github.com/lucasberter/FJSPT (Berterottiere, Dauzere-Peres & Yugma 2024 EJOR 동반자료)
받은 날짜: 2026-07-22. **아래 내용은 우리가 직접 파일을 열어 확인한 것.**

## 1. 폴더가 입력과 출력 두 종류로 갈림 (업스트림 README에 설명 없음)

| 폴더 | 정체 |
|---|---|
| `DeroussiNorre/` (10) | **인스턴스** - Bilge-Ulusoy 계보, 8기계·유연도2 |
| `fattahi/` (20) | **인스턴스** - Fattahi 2007, sfjs01-10 / mfjs01-10 |
| `Dauzere_Data/Text/` (18x2) | **인스턴스** - Dauzere-Peres & Paulli. `.txt`와 `.fjs`는 내용 동일 |
| `Homayouni_Brandimarte/` (대문자 B) | **인스턴스** - Brandimarte Mk + Hurink seti/setb/mt10 계열 |
| `BerterottiereTravelTimes/` (3) | **travel matrix** - layout5/8/10 |
| `Deroussi/` (10) | **해(결과)** |
| `Homayouni_brandimarte/` (소문자 b) | **해(결과)** |
| `Homayouni_fattahi/` (10) | **해(결과)** |
| `Berterottiere/dpp{2,4,6}veh/` (54) | **해(결과)** - Dauzere 인스턴스 x 차량 2/4/6대 |

주의: `Homayouni_Brandimarte`(대)와 `Homayouni_brandimarte`(소)는 **파일명까지 같은데 하나는 입력, 하나는 출력**.
리눅스에서만 공존 가능하고 Windows/macOS에서 clone하면 충돌함.

## 2. 확인된 문제

### (a) setb4xxx.txt == seti5xxx.txt (바이트 동일)
`Homayouni_Brandimarte/setb4xxx.txt`와 `seti5xxx.txt`가 **완전히 같은 파일**임(md5 일치).
둘 다 헤더가 `15 18 1`인데, seti5(15job x 15기계 + 3 복제)는 18이 타당하지만
setb4(15job x 11기계 + 3)는 14가 나와야 함. -> **`setb4xxx.txt`에 seti5 데이터가 잘못 들어간 것으로 추정.**

**영향**: 둘을 별개 인스턴스로 실험에 넣고 결과를 보고하면 논문 레벨 오류.
**조치**: 사용 전 원 출처(`fastmanufacturingproject.wordpress.com/2019/04/11/fjspt-instances/`)에서 setb4 계열 재확인.

### (b) Data set 1용 travel matrix가 없음
`BerterottiereTravelTimes/`의 layout5/8/10은 **Dauzere 인스턴스용**(5/8/10 기계).
`DeroussiNorre/` 인스턴스에 맞는 4기계 레이아웃(5x5)은 이 레포에 없음.
-> Bilge & Ulusoy 1995 (Zotero `GP6HQQSG`) 또는 Kumar 2011 (`KQK9HJMJ`) Fig 3에서 직접 전사해야 함.
-> **착수는 travel matrix가 이미 있는 Dauzere 계보가 빠름.**

### (c) 해 파일에 없는 가정
loading/unloading 시간, 빈차(deadhead) 재배치 규칙은 데이터에 없음.
Berterottiere 2024 논문 3절에서 읽어야 하고, **이 가정 하나 때문에 replay Cmax가 안 맞을 수 있음.**

## 3. 우리가 이 데이터로 하려는 것

**replay 검증**: 해 파일의 `M*`(기계별 연산순서) / `V*`(차량별 운반순서)를 그대로 evaluator에 먹여
헤더의 Cmax와 일치하는지 확인. 정책이 개입하지 않으므로 **시간계산 로직만 순수 검증**됨.
목표: `DeroussiNorre/fjsp1.txt` -> Cmax **134**.

포맷 상세(3종)와 파싱 방침은 `STATUS.md §데이터 자산` 참고.
**해 인코딩은 데이터셋과 무관하게 하나로 통일** (파서만 포맷별로 3개).
