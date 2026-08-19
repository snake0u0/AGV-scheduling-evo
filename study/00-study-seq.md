## 코드 볼 순서

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

코드 볼 순서

6) simulator/instance.py
2) simulator/solution.py
8) simulator/dispatch.py
3) simulator/timing.py

1) model/experiment.py
4) model/llm.py
7) model/llm-backend.py
5) model/rule.py



