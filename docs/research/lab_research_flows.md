# 주도 랩 연구 흐름 (research flows) — LLM-AHD × 스케줄링 × AGV/AMHS
정리: 2026-06-09. 출처=수집 논문 + 웹/OpenAlex 확인. 각 랩: 정체성 → 흐름(시간순) → 현재 트렌드/다음 → 당신과의 관계.

---

## 1. CityU Hong Kong — Qingfu Zhang (Chair Prof., CS) / 핵심학생 Fei Liu  ★방법 본가
- **정체성**: 진화연산(MOEA/D의 그 Zhang) → LLM-AHD 방법론 세계 본가.
- **흐름**: 다목적 진화최적화 → AEL(Algorithm Evolution using LLM, '23) → **EoH**('24, NL 'thought'+code 공진화) → MOEoH(AAAI), **EoH-S**(heuristic *set*), **EvoDR**(디스패칭 룰, 머신숍).
- **트렌드/다음**: AHD를 *효율적·다목적·집합(set)기반·다양성*으로. 점점 **스케줄링**으로 내려옴.
- **당신과 관계**: **방법 출처**(EoH/ReEvo 계열을 그대로 출발점). 인용 필수. 위협도 중간(범용 CO 중심).

## 2. HUST — Liang Gao & Xinyu Li (State Key Lab of Intelligent Manufacturing)  ★최대 경쟁/앵커
- **정체성**: 제조 스케줄링(FJSP) 세계 최선두 → LLM-AHD를 제조로 가장 공격적으로 이식.
- **흐름**: GP/메타휴리스틱 FJSP → DRL 동적 스케줄링 → **LLM4DRD**(조립 흐름공정), **SeEvo/AutoProg**(self-evolution JSP·fuzzy JSP), **DSevolve**(QD 포트폴리오+온라인 probe, DFJSP), **LLM-MILP 멀티로봇 task allocation**, 인간-로봇 LLM 스케줄링.
- **트렌드/다음**: 모든 제조 스케줄링 변형에 LLM-AHD 적용 + **온라인/동적 배치 + 다자원(로봇/운반)**. → **"LLM-AHD for AGV/통합 스케줄링"이 이들의 자연스러운 다음 수**.
- **당신과 관계**: **가장 큰 위협.** 같은 걸 먼저 낼 수 있음. → (a) 빠르게(KIIE), (b) 이들이 안 하는 각도(아래 §종합), (c) 한국 도메인 강점 활용으로 차별. 신작 alert 필수.

## 3. Victoria Univ. of Wellington — Mengjie Zhang·Yi Mei·Fangfang Zhang (ECRG) + Su Nguyen(La Trobe)  ★전통/베이스라인
- **정체성**: 동적 (F)JSP용 **GP 하이퍼휴리스틱**의 세계 표준 그룹.
- **흐름**: GP 디스패칭룰 진화 → feature selection·다목적·surrogate·**전이학습·해석성**·GP+ML 서베이(IEEE TEVC'23).
- **트렌드/다음**: 진화 룰의 *해석성·전이성·다목적*, LLM-assisted GP로 확장 가능성.
- **당신과 관계**: 당신이 주장할 **해석성·전이성이 이들 전통의 핵심** → 반드시 인용·계승. GP 베이스라인 근거.

## 4. KAIST — Jinkyoo Park, SILAB (산업및시스템공학과)  ★한국·방법·1순위
- **정체성**: neural/RL 조합최적화 + LLM hyper-heuristic + 멀티에이전트 RL(스마트팩토리/물류).
- **흐름**: attention/RL for VRP·TSP → **RL4CO**(KDD'25, 벤치마크) → **ReEvo**(NeurIPS'24, LLM hyper-heuristic+reflection) → 시스템/물류 MARL, 반도체 OHT MARL+GNN.
- **트렌드/다음**: RL↔LLM 하이브리드 솔버, 오픈소스 툴링(RL4CO/ReEvo).
- **당신과 관계**: **방법+코드+한국 타깃 1순위.** ReEvo/RL4CO 그대로 출발점, 인용·교류·대학원 후보.

## 5. KAIST — Young Jae Jang, AE Lab / SynusTech-KAIST AI AMHS 센터 (산업및시스템공학과)  ★한국·도메인 본가(OHT/AGV)
- **정체성**: 반도체 팹 **AMHS(OHT·AGV·stocker)** 운영의 한국 최선두. (MIT 기계/OR 박사)
- **흐름**: AMHS 해석모델 → **Q(λ) OHT 동적 라우팅**(IJPR'19) → **MARL+그래프표현학습 OHT 유휴차량 재배치**(IISE Trans'21) → **policy-based RL 팹 디스패칭 룰** → 스마트물류/SCM·무선급전 AMHS.
- **트렌드/다음**: 대규모 RL/MARL AMHS, 산업협력(SynusTech), AI 물류.
- **당신과 관계**: **도메인 앵커.** 당신 분야(AGV/AMR/**OHT**)와 정확히 일치. RL 디스패칭 = 당신의 **강력한 베이스라인·문제정의 근거**. LLM-AHD는 아직 미적용 = 당신 틈. 인용·문제설정·(협력) 핵심.

## 6. Google DeepMind — FunSearch  (시조, 추종 대상 아님)
- LLM이 프로그램 탐색으로 휴리스틱 발견(수학·bin-packing). AHD의 출발점. 인용용.

## 7. PortAgent 그룹 — Tongji Univ.(도로교통공학) + COSCO Shipping Ports + Dalian Maritime Univ.  ★도메인 인접 경쟁(다른 커뮤니티)
- **정체성**: 교통/항만물류 + LLM 에이전트.
- **방법**: Virtual Expert Team(멀티에이전트)+RAG+Reflexion으로 **컨테이너터미널 VDS(AGV 함대 배차) 자동설계·이전**. 진화 아님.
- **당신과 관계**: 도메인 인접(항만 AGV)이나 **다른 학문 커뮤니티(교통공학)·다른 방법(agentic codegen)**. related work에 명시 차별: 제조 AGV-FMS vs 항만, 진화 vs 에이전트.

---

## 종합 시사점 (positioning)
1. **위협 1순위 = HUST(Gao/Li).** 머신숍 LLM-AHD를 다 점령했고 운반/다자원으로 확장 중 → AGV가 그들 다음 수일 수 있음. **속도 + 차별 각도 + 한국 도메인 강점**으로 대응.
2. **최강 각도 = "한국 도메인 본가(장영재, OHT/팹 AMHS) × 방법 본가(박진규/CityU, LLM-AHD)"의 교차.** 둘 다 KAIST IE에 있고, 양쪽 다 *반도체 팹 AMHS에 LLM-AHD*를 아직 안 했다.
   → **정밀화된 틈**: *반도체 팹 AMHS(OHT/AGV) 동적 디스패칭에 진화형 LLM-AHD 적용.* 일반 AGV보다 **(i) 한국 IE/KIIE 적합성↑, (ii) 장영재 랩의 RL 베이스라인·문제설정 재사용, (iii) 혼잡·교착(deadlock)·재배치 등 AMHS 고유구조**로 방법 신규성↑, (iv) PortAgent(항만)·HUST(머신숍)·CityU(범용)와 도메인 충돌 최소.
3. **해석성·전이성 주장은 Victoria Wellington(GP) 전통 계승**으로 정당화.
4. **실행**: KIIE로 빠르게 깃발 → SCIE 확장. 투고 전 HUST·CityU·PortAgent forward-citation sweep.
