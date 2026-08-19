## 코드 볼 순서 - 20260810

1) 문제 관련
1. simulator/instance.py    #
2. simulator/solution.py    # Solution이 뭔지 + 남의 파일 읽기  <- 지금 보는 이 파일
3. simulator/timing.py      # Solution -> Cmax

simulator가 model을 전혀 import 하지 않는 구조.

2) 코드 테스트
1. tests/test_paper_example.py  
2. simulator/replay.py
3. tests/test_replay_deroussi.py

3) 우리 방법
1. model/rules.py ⭐
2. simulator/evaluator.py           #  개체 하나 → Solution(decode) 
3. model/test_decode_selfcheck.py
4. model/ga.py                      # 개체군(population) 관리, 세대 진화, 몇 개 남길지
5. model/experiment.py

4) LLM 루프
1. model/llm.py
2. model/llm_backend.py

5) 새 설계
1. simulator/dispatch.py
2. tests/test_dispatch.py

---

## 코드 볼 순서 - 20260819

1) simulator/instance.py - 문제입력
2) simulator/solution.py - 해표현
3) simulator/timing.py - 해(Cmax)
4) model/rules.py- 규칙 표현

5) simulator/dispatch.py - 규칙 4개로 해를 만드는 빌더(디코더)
6) model/llm_backend.py - claude CLI 통신계층
7) model/llm.py - 프롬프트 설계
8) model/experiment.py - 적합도 계산 + 세대 진화 루프

9) experiments/common.py - 문헌 기준값, 격차, 예산 상수 파라미터
10) experiments/007/run.py - 위 전부 호출해서 65세대 실험 하나 완성

---
