## 1. Instance.py 파악

> 정리: 인스턴스 파일 불러오고(각 인스턴스의 job, operation, machine, 대체기계, AGV대수, 이동시간)을 리스트 및 딕셔너리 형태로 저장, 원하는 형태에 맞게 변형. 공백단위로 데이터 토큰화 후 정해진 구조에 맞게 저장. 이동시간 행렬도 있는 것들에서 일단가져옴.

1. @dataclass: 타입 힌트가 붙은 변수 목록을 나열 시 생성자 만들어줌.

2. class Instance: 하나의 FJSP-AGV 인스턴스(테스트 케이스 하나)를 담는 그릇. job수,기계 수, 공정 데이터 정보를 담아두고, 편하게 꺼내 쓰는 데이터 구조. 

3. class Instance에서 name은 인스턴스(파일명), n_jobs는 작업 개수, n_machine은 기계 대수, jobs는 작업들 세부사항, travel은 이동시간 행렬, n_vehicles는 AGV 대수, source는 인스턴스의 출처 경로.

4. source: dict=field(default_factory=dict)는 source dict = {}로 적을 시 딕셔너리 하나가 모든 Instance 객체가 공유하는 단 하나의 딕셔너리가 되는 문제를 피하기 위해서.

5. @property: 메서드인데 괄호 없이 변수처럼 접근할 수 있게 해주는 데코레이터

6. n_ops, gid, job_op, proc_time, eligible, tockens 각각 뭔지 코드와 역할
	: n_ops: 전체 공정 수, jobs는 job들의 리스트. 각 job들은 ops들의 리스트.
	  gid: 전역 공정번호 매기기
	  job_op: gid의 역함수. 전역번호를 (job, operation) 쌍으로 묶음.
	  proc_time: 특정 [job][operation]인 operation을 특정 machine에서 처리하면 몇 분이 걸리는지 시간을 반환. 기계에서 처리 불가능한 공정이면 에러.
	  eligible: 이 공정을 처리할 수 있는 기계 목록. 시간은 안 저장하고 기계 번호만 뽑아서 리스트로 반환.

	  _tockens: 파일을 통째로 읽어서 공백 기준으로 쪼갠 토큰 리스트로 반환하는 내부 유틸. 
			"이름 앞에 _가 있으면 이 모듈 밖에서는 쓰지마라"는 관례

7. parse_format_a(path, name=None): 란 파일 전체를 토큰 리스트로 변환, 

8. def parse_fatmat_a(): 이거 밑에 주석 뭔지 설명해줘.

9. prase_format_a, b, c가 각각 처리하는 데이터셋
	a: DeroussiNorre → 대체기계들이 가공시간 공유
	b: Dauzere_Data, Homayouni_Brandimarti → 기계마다 가공시간이 다름.
	c: fattahi → job 경계가 없고, 선행관계로 복원, 기계번호가 0부터 시작.

10. 데이터 파서: 데이터 파일을 읽고 데이터의 형태 및 구조를 재배열하는 것.

11. load_travel(): 이동시간 행렬 파일을 읽어서 2차원 리스트로 반환. 
    mat[a][b]: a에서 b로 이동하는 시간

12. load_dauzere(), load_deroussi(): 두개의 데이터셋에 대해서만 현재 이동시간 행렬이 존재해서 두개밖에 없음.


후속질문

1. __init__: 생성자. __init__은 클래스가 정의될 때(파이썬이 이 파일을 읽을 때) 딱 한 번 만들어지고, 그 이후 Instance()가 몇 번 호출하든 하나의 __init__ 재사용. 

2. 가변 객체: 리스트나 딕셔너리처럼 내용물을 나중에 바꿀 수 있는 객체. 정수 변수 같은건 불변 객체
클래스를 한 번 정의하면 클래스에 속한 딕셔너리나 리스트, 변수들은 __init__횟 수 만큼 만들어짐. 그래서 Instance같은 class를 호출할 때마다 그 클래스의 새로운 딕셔너리가 생성되는게 아니라 이전에 한 번 정의된 딕셔너리를 불러오게 됨. 따라서 우리는 매번 다른 인스턴스를 불러오는데 그 인스턴스 별로 딕셔너리가 초기화되어야하기 때문에  source: dict = field(default_factory=dict) 이것을 사용하는 것.

3. default_factory=dict에서 default_factory는 공식 매개변수 이름
    field()는 dataclasses 모듈이 제공하는 함수, "이 필드를 어떻게 초기화할지"를 세밀하게 조정할 때 사용함.

4. @property는 def로 만든 것에만 적용, 바로 아래 하나에만 적용. 현재 파일의 경우에는 n_ops() 이것만 적용.

5. 메서드란, 클래스 안에 정의된 함수.

6. 데코레이터(@)란, "함수를 정의하자마자 바로 다른 함수에 감싸는" 작업을 짧게 쓰는 문법.

7. 전역 공정번호 하나의 인스턴스 안에서 모든 job을  operation이 아니라 한 인스턴스 내에서 operation의 번호를 말하는거 맞지?

8. 유틸: 도구, '모듈': .py 파이썬 파일 하나, 통상적으로 _를 함수 이름 앞에 붙이면 다른 모듈(파일)에 갖다 쓰지 말라는 관례적 신호

