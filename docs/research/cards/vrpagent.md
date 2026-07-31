---
citekey: vrpagent2025
title: "VRPAgent: LLM-Driven Discovery of Heuristic Operators for Vehicle Routing Problems"
authors: ai4co (KAIST 계열)
year: 2025
venue: arXiv:2510.07073
source: abstract + repo 코드 확인 (github.com/ai4co/vrpagent)
---

## 문제정의 (problem)
VRP(CVRP / VRPTW / prize-collecting VRP)용 휴리스틱 설계. LLM 코드생성이 여러 분야에서 가능성을
보였으나 아직 전문가가 손으로 만든 휴리스틱에 못 미친다는 문제의식.

## 방법 (method/approach)
**LLM이 만든 부품을 메타휴리스틱 안에 심고, 그 부품을 유전 탐색으로 정제한다.**
저장소의 실제 생성 코드(`generated_heuristics/cvrp/.../code.cpp`)를 열어 확인한 결과
**진화 대상 슬롯이 정확히 2개**다.

| 슬롯 | 시그니처 | 정체 |
|---|---|---|
| 1 | `std::vector<int> select_by_llm_1(const Solution&)` | **LNS destroy** - 어느 고객을 제거할지. seed 고객 하나 뽑고 근접 이웃으로 확장(= Shaw/related removal 계열), 제거 수는 전체의 2~4%를 10~20 사이로 클램프 |
| 2 | `void sort_by_llm_1(std::vector<int>&, const Instance&)` | **repair 순서** - 제거된 고객을 어떤 순서로 재삽입할지 |

C++ 부품이 기존 고성능 메타휴리스틱 프레임워크 안에 들어간다. 저자 표현:
*"By using the LLM to generate problem-specific operators, embedded within a generic
metaheuristic framework, VRPAgent keeps tasks manageable, **guarantees correctness**,
and still enables the discovery of novel and powerful strategies."*

## 핵심결과 (findings)
CVRP·VRPTW·PCVRP에서 손으로 만든 방법과 최신 학습기반 방법을 모두 능가. **CPU 코어 1개만 사용.**
저자 주장: **LLM 기반 패러다임이 VRP에서 SOTA를 갱신한 최초 사례.**

## 우리 프로젝트 관련성 - 매우 높음. 직접 선례다

**2026-07-31 정정**: `novelty_sweep.md`에 "정적 VRP용 LLM 연산자 + GA"로 적어둔 한 줄은
novelty sweep 중 스친 기록이었고 **부정확했다.** 실제로는 **LNS destroy + repair 순서 연산자**다.

- 우리가 2026-07-31 회의에서 고른 구조(**메타휴리스틱 뼈대 + LLM이 그 안의 연산자를 진화**,
  옵션 D)와 **같은 패러다임**이다. "우리가 짜낸 구조"가 아니라 이미 SOTA를 갱신한 검증된 패러다임이라는
  뜻이므로, 설계 정당화 인용처로 최우선.
- 저자의 "guarantees correctness" 논리 = 우리 **슬롯 고정 스키마**의 논리와 동일.
  파일 전체를 자유 편집(AlphaEvolve식)하지 않고 시그니처를 고정하는 이유가 문헌에 이미 있다.
- Berterottière et al. (2026) EJOR 332 결론이 FJSPT의 다음 수순으로 **LNS(Pisinger & Ropke)**를
  지목하고 "**reconstruction operator**에 특히 주의하라"고 쓴 것과 정확히 맞물린다.
  즉 VRP에서 이미 통한 처방을, FJSPT 쪽 SOTA가 필요하다고 명시한 자리에 적용하는 그림.

### 우리와의 차별 (본문 차별 문단용)
| | VRPAgent | 우리 |
|---|---|---|
| 문제 | VRP (자원 1종: 차량) | **FJSP-AGV (자원 2종: 기계 + AGV, 결합)** |
| 진화 슬롯 | **2개** (destroy, repair 순서) | **5개** (기계선택·공정순서·AGV선택·AGV순서 + destroy) |
| 기계 배정 | 없음 (VRP에 기계가 없음) | **있음. 배정 하나가 노드 가중치(pt)와 아크 가중치(Tr)를 동시에 바꿈** |
| 프롬프트 체계 | 유전 탐색 | EoH(생각+코드) + ReEvo(부모 장단점 반성) 결합 |

**"이미 VRPAgent가 했잖아"에 대한 답**: 하위문제가 4개로 결합된 문제에서 슬롯 5개를 *동시에* 진화시키는
것은 다르다. 특히 기계 배정은 VRP에 대응물이 없고, 이것이 우리 2026-07-29 실측에서 **격차의 주 원인**
으로 지목된 슬롯이다(유연도 2.0 미만 36% vs 이상 84%).

## 한계 (limitations)
- 저장소는 **생성된 휴리스틱과 예시 population만** 공개. 진화 루프 코드는 아직 없음("More to come").
  -> 프레임워크를 가져다 쓸 수는 없고, 설계 참조 + 인용으로 쓴다.
- 초기 population에 `inf.obj`(실행 불가/발산) 개체가 섞여 있음 -> 슬롯 방식에서도 무효 개체가
  나온다는 실증. 우리 쪽 무효 처리(부모 슬롯으로 되돌리기) 설계의 근거로 쓸 수 있음.
