// Additions for the existing Day 4 renderer. No model calls or remote writes.
const table = (title, headers, rows, note, phase = 'theory') =>
  ({type: 'table', title, headers, rows, note, phase});
const code = (title, code, explain, note, phase = 'lab') =>
  ({type: 'code', title, code, explain, note, phase});
const task = (title, steps, file, check, note) =>
  ({type: 'task', title, steps, file, check, note, phase: 'lab'});

export const PR_WALKTHROUGH = [
  {
    period: 0,
    after: '합성 PR 로딩',
    slides: [
      code('Notebook 실행 위치',
`print("Python:", sys.executable)
print("프로젝트:", ROOT)
print("실행 위치:", Path.cwd())
print((ROOT / "requirements-day4.txt").is_file())`,
        ['Notebook 준비 셀 실행 후 새 코드 셀에 입력',
         '마지막 값 True · ROOT 아래 labs 폴더 확인'],
        'Notebook 준비 셀에서 정의한 sys, ROOT, Path를 사용한다. 실행 위치가 materials/day4여도 준비 셀이 상위 프로젝트 폴더를 찾으므로 반드시 잘못된 상태는 아니다. ROOT는 requirements-day4.txt와 labs가 있는 폴더다. NameError는 준비 셀 미실행을, ModuleNotFoundError는 커널과 설치 환경을 먼저 확인한다. 학생이 설치를 반복하기 전에 출력된 Python 경로와 선택 커널을 대조하게 한다.',
        'demo'),
    ],
  },
  {
    period: 0,
    after: '대상 정보 확인',
    slides: [
      code('PR 번호 검사의 수정',
`def my_target_matches(pr, repo, number):
    return (
        pr["repo"].lower() == repo.lower()
        and pr["number"] == number
    )
assert my_target_matches(snapshot, snapshot["repo"], 42)
assert not my_target_matches(snapshot, snapshot["repo"], 43)`,
        ['and 행 제거 시 PR 43 검사 실패',
         '조건 복구 후 같은 셀의 두 assert 통과'],
        '제공 함수는 이미 정상이다. 학습을 위해 return 식에서 and pr[\'number\'] == number만 잠시 제거한다. 새 검사 줄은 assert not my_target_matches(snapshot, snapshot["repo"], 43)이다. 번호 조건을 뺐을 때 이 assert가 실패해야 한다. 원래 조건을 복구하면 PR42는 True, PR43은 False다. 검사 기대값을 True로 바꾸는 것은 복구가 아니다. validate_snapshot 함수와 pr.json 원본은 수정하지 않는다.'),
    ],
  },
  {
    period: 0,
    after: '다른 저장소의 차단',
    slides: [
      code('SHA 입력의 오류 복구',
`bad = deepcopy(snapshot)
bad["head_sha"] = "최신버전"
target = dict(expected_repo=snapshot["repo"], expected_pr=42)
try:
    validate_snapshot(bad, **target)
except LabError as error:
    print(error.code)
bad["head_sha"] = snapshot["head_sha"]
assert validate_snapshot(bad, **target) is bad`,
        ['INVALID_SHA 출력 후 마지막 assert 통과',
         '형식 복구 실험 · 최신 버전 조회는 별도'],
        'Notebook 1차시 아래 새 셀에 입력한다. deepcopy와 LabError는 준비된 import를 사용한다. 잘못된 값을 일부러 넣어 안정적인 오류 코드를 확인하고, 복사본의 값을 원본 SHA로 복구한다. 마지막 assert는 예외 없이 끝나면 통과다. 이것은 로컬 입력 형식 실험이며 원격 PR의 최신 SHA를 조회한 증거가 아니다. snapshot 원본은 변경하지 않는다.'),
    ],
  },
  {
    period: 0,
    after: '로컬 작업 폴더 생성',
    slides: [
      table('실습 파일의 역할',
        ['파일', '열어서 확인할 내용', '수정 기준'],
        [
          ['checkout.py', 'checkout_total 함수\n실제 결제 계산', '기능 수정 대상'],
          ['test_checkout.py', '입력과 assert 기대값\nValueError 검사', '기존 검사 유지\n새 검사 추가'],
          ['reference_solution.py', '참고 구현\n비교용 정답 코드', '필요할 때 비교\n자동 복사 기본 꺼짐'],
          ['checkout_before.py', '쿠폰 추가 이전 코드\n변경 배경', '읽기 전용 비교'],
        ],
        '네 파일은 EXERCISE 아래에 생성된다. labs/day4/pr_review_lab/fixtures 안의 원본 파일과 혼동하지 않는다. VS Code의 빠른 열기에 Notebook이 출력한 checkout.py 전체 경로를 붙여 넣는다. reference_solution.py는 학생의 현재 코드가 아니며 checkout_before.py는 쿠폰 기능 추가 이전 버전이다. 수정 전후 diff 실습에서는 쿠폰 버그가 있는 fixture checkout.py와 내 수정본을 비교한다.'),
      task('생성 셀의 재실행 오류',
        ['실습 폴더 생성 셀을 같은 RUN에서 다시 실행',
         'EXERCISE_EXISTS와 기존 파일 보존 확인',
         '생성 셀을 건너뛰고 현재 EXERCISE 경로 확인',
         '아래 check_exercise 셀에서 기존 수정본 검사'],
        'Notebook 1차시 · prepare_exercise / check_exercise',
        '기존 코드 유지 · 검사 셀만 재실행',
        '이 오류는 설치 실패가 아니다. prepare_exercise가 기존 수정 파일을 덮지 않도록 막은 결과다. 앞서 성공한 EXERCISE 변수는 그대로 남아 있으므로 이후 검사 셀을 실행할 수 있다. 커널까지 초기화했다면 저장해 둔 기존 전체 경로로 EXERCISE = Path("...")를 복구하고 준비 import를 먼저 실행한다. 처음 셀부터 Run All을 하면 새로운 RUN과 새 실습 코드가 생긴다는 점도 구분한다. 기존 폴더 삭제로 해결하지 않는다.'),
    ],
  },
  {
    period: 1,
    after: '실패 테스트 읽기',
    slides: [
      table('pytest 메시지의 구분',
        ['표시', '뜻', '다음 수정'],
        [
          ['assert -4000 == 0', '실제 계산값과\n기대값 불일치', 'checkout.py\n최종 금액 확인'],
          ['DID NOT RAISE', '거절해야 할 입력을\n함수가 그대로 처리', 'checkout.py\n입력 검사 추가'],
          ['IndentationError', 'Python 들여쓰기 오류\n기능 검사 전 중단', '같은 함수 안에서\n공백 깊이 정렬'],
          ['ModuleNotFoundError', '실행 Python에서\n모듈을 찾지 못함', '커널·설치·경로 확인\n기대값 수정 금지'],
        ],
        '맨 아래 FAILED 개수만 보지 않고 첫 실패의 오류 종류와 파일 줄을 읽는다. 처음 두 행은 업무 동작의 문제이고 뒤 두 행은 실행 준비 또는 문법 문제다. test_checkout.py의 assert를 지우면 숫자는 줄어도 기능은 복구되지 않는다. 수업 기본 코드에서 나타나는 네 실패는 초과 쿠폰 하나와 잘못된 입력 세 경우다.',
        'check'),
    ],
  },
  {
    period: 1,
    after: '최소 수정 예시',
    slides: [
      task('수정 파일과 저장 상태',
        ['Notebook이 출력한 EXERCISE/checkout.py 열기',
         'checkout_total 함수 안에 검사·반환식 수정',
         'Ctrl+S 또는 ⌘S로 저장하고 수정 표시 확인',
         'current_test 셀만 다시 실행해 새 결과 확인'],
        '내 실습 폴더/checkout.py · Notebook current_test 셀',
        '기본 제공 5개 테스트 모두 통과',
        '같은 이름의 fixture 파일을 고치거나 편집 탭을 저장하지 않는 실수를 먼저 잡는다. 파일 경로 전체가 EXERCISE와 일치해야 한다. current_test는 subprocess로 pytest를 새로 실행하므로 저장한 파일을 읽는다. 생성 셀부터 다시 실행하면 기존 수정본과 다른 폴더를 검사할 수 있다. 테스트를 이미 추가했다면 통과 개수는 5보다 많아질 수 있다.'),
      code('정상 계산의 회귀 검사',
`command = [
    sys.executable, "-m", "pytest", "-q",
    "test_checkout.py", "-k", "normal_coupon",
]
normal = subprocess.run(
    command, cwd=EXERCISE, capture_output=True, text=True
)
print(normal.stdout)
assert normal.returncode == 0`,
        ['기본 샘플: 1 passed, 4 deselected',
         '회귀 검사: 수정 전 정상 기능의 유지 확인'],
        'Notebook 2차시의 새 코드 셀에서 실행한다. -k normal_coupon은 해당 이름의 테스트만 선택한다. 정상 케이스는 가격12000, 수량2, 쿠폰3000의 결과21000을 검사한다. deselected는 실패가 아니라 선택하지 않은 테스트다. 이 한 건이 통과했다고 초과 쿠폰과 잘못된 입력 검사가 끝난 것은 아니므로 다음에는 check_exercise 전체 검사를 유지한다.'),
    ],
  },
  {
    period: 1,
    after: '수정 Diff의 재검토',
    slides: [
      code('수정 전후의 파일 비교',
`from difflib import unified_diff
source = ROOT / "labs/day4/pr_review_lab/fixtures/checkout.py"
old = source.read_text(encoding="utf-8").splitlines()
new = (EXERCISE / "checkout.py").read_text(encoding="utf-8")
diff = unified_diff(
    old, new.splitlines(), fromfile="before", tofile="my-checkout",
    lineterm=""
)
print("\\n".join(diff))`,
        ['+ 입력 검사 · + 0원 하한의 추가 확인',
         '로컬 파일 비교 · GitHub PR 갱신과 별개'],
        'Notebook 2차시에서 새 코드 셀로 실행한다. 비교 기준은 버그가 있는 공개 fixture checkout.py이며, checkout_before.py와 비교하는 것이 아니다. 기존 반환식 제거와 새 입력 검사, 새 반환식 추가가 보인다. diff가 비어 있으면 현재 EXERCISE 경로와 저장 여부를 확인한다. 이 비교는 Git 설치 없이 작동한다. GitHub 원격 코드나 commit SHA는 바뀌지 않는다.'),
    ],
  },
  {
    period: 1,
    after: '게시 전 미리보기',
    slides: [
      code('수정 결과의 HTML 저장',
`current_test = check_exercise(ROOT, EXERCISE)
folder = RUN / "pr" / ("report-" + uuid.uuid4().hex[:6])
files = render_outputs(
    ROOT, folder, snapshot, review,
    test_result=current_test
)
file_link(files["review.html"])`,
        ['새 HTML의 현재 로컬 테스트 결과 확인',
         '원본 PR 리뷰는 유지 · 게시 상태는 확인 대기'],
        'Notebook 준비 셀의 uuid와 file_link를 사용한다. 새 이름의 결과 폴더로 저장하여 이전 화면을 보존한다. 브라우저에서 새 review.html을 열고 02 현재 로컬 작업 코드의 테스트 영역을 확인한다. 원본 fixture PR diff와 원본 리뷰 문장은 그대로이며 이를 수정 후 PR의 최신 리뷰라고 소개하지 않는다. preview 인수를 생략했으므로 승인 완료가 아니라 AWAITING_HUMAN_REVIEW다. HTML과 review.md는 로컬 파일이며 게시나 서비스 배포를 하지 않는다.'),
    ],
  },
  {
    period: 2,
    after: '테스트 한 건 추가',
    slides: [
      code('쿠폰 경계값 테스트',
`@pytest.mark.parametrize("coupon, expected", [
    (0, 1000),
    (1000, 0),
])
def test_zero_or_exact_coupon(coupon, expected):
    assert checkout_total(1000, 1, coupon) == expected`,
        ['test_checkout.py 맨 아래에 추가 후 저장',
         '쿠폰 없음과 총액만큼의 쿠폰: 두 경우 검사'],
        'Notebook 코드 셀이 아닌 EXERCISE/test_checkout.py에 추가하는 완전한 테스트 함수다. 기존 파일 상단에 pytest와 checkout_total import가 있으므로 재사용한다. decorator 아래 함수 앞에 빈 들여쓰기를 넣지 않는다. 함수 이름은 한 번만 추가한다. 파라미터 두 줄은 같은 검사를 서로 다른 입력으로 두 번 실행한다. 기존 테스트5개를 보존하면 전체는7개다. coupon=1000은 최종0, coupon=0은 최종1000을 확인한다.'),
      code('추가 테스트의 선택 실행',
`command = [
    sys.executable, "-m", "pytest", "-q",
    "test_checkout.py", "-k", "zero_or_exact_coupon",
]
extra = subprocess.run(
    command, cwd=EXERCISE, capture_output=True, text=True
)
print(extra.stdout)
assert extra.returncode == 0`,
        ['Notebook 새 셀: 2 passed, 5 deselected',
         '그다음 check_exercise 전체 결과 7 passed'],
        '제공 테스트5개에 바로 앞 함수의 입력2개만 추가한 상태를 기준으로 설명한다. 테스트 함수를 다른 파일이나 다른 실습 폴더에 저장하면 선택된 테스트가 없다는 결과가 나올 수 있다. 수량0 또는 음수 가격 검사를 추가한 학생은 전체 개수가 달라도 된다. 선택 실행 다음에는 기존 check_exercise(ROOT, EXERCISE) 셀을 실행하여 모든 테스트를 확인한다.'),
    ],
  },
  {
    period: 2,
    after: 'CI 파일 구성',
    slides: [
      table('개인 저장소의 파일 배치',
        ['복사할 파일', '개인 저장소의 위치', '연결되는 설정'],
        [
          ['내 checkout.py', 'exercise/checkout.py', '검사할 기능 코드'],
          ['내 test_checkout.py', 'exercise/test_checkout.py', 'pytest가 읽는\n테스트 파일'],
          ['제공 workflow.yml', '.github/workflows/\nday4-checkout-tests.yml', 'working-directory:\nexercise'],
          ['로컬 실행 위치', '터미널에서\nexercise 폴더', 'python -m pytest -q\ntest_checkout.py'],
        ],
        '선택 GitHub 실습의 개인 저장소 배치다. 먼저 별도 로컬 연습 폴더에 파일 두 개와 전체 workflow 템플릿을 복사하여 같은 pytest 명령을 실행한다. Notebook EXERCISE의 길고 매번 달라지는 경로를 workflow에 붙여 넣지 않는다. 원격 활성화는 학생이 본인 저장소와 diff를 확인하고 올렸을 때만 진행한다. 이 강의 저장소의 .github/workflows를 직접 수정하지 않는다. GitHub 계정이 없으면 로컬 배치와 실행까지 진행했다고 기록한다.',
        'lab'),
    ],
  },
  {
    period: 2,
    after: '중복 리뷰의 차단',
    slides: [
      code('리뷰 수정과 이전 승인',
`findings = deepcopy(review["findings"])
findings[0]["suggestion"] += " 정상 입력도 함께 검사합니다."
revised = build_review(snapshot, findings, provider="human")
expected_failure("이전 승인", lambda: preview_publication(
    snapshot, revised, simulated_approval,
    current_head_sha=snapshot["head_sha"]),
    "APPROVAL_MISMATCH")`,
        ['같은 PR·같은 commit이어도 내용 변경은 재확인',
         '테스트용 승인 객체 · 원격 전송 없음'],
        'Notebook 3차시의 simulated_approval 생성 셀 이후 새 셀에서 실행한다. review 원본을 직접 수정하지 않고 findings 복사본의 수정 제안 문장을 고친 뒤 build_review로 새 문서와 해시를 만든다. provider human은 이 예제의 출처 라벨이며 실제 인증 정보가 아니다. 이전 승인의 review_sha256과 새 문서 해시가 다르므로 APPROVAL_MISMATCH가 맞는 결과다. 해시를 강제로 같게 만들거나 승인 검사를 없애지 않는다.'),
      task('수정 리뷰의 재확인',
        ['display(Markdown(revised["markdown"]))로 새 문서 확인',
         '추가한 제안·위치·재현 조건을 원본과 대조',
         '실제 검토 후 승인 예시의 review를 revised로 변경',
         '새 approval과 revised로 미리보기 셀 재실행'],
        'Notebook 3차시 · revised / approve_preview',
        '사람 확인 후 PREVIEW_ONLY · GitHub 게시 없음',
        '승인 코드는 앞의 게시 전 미리보기 장표와 동일하다. approve_preview(snapshot, revised, approved=True, reviewer="student")로 새 approval을 받고 preview_publication(snapshot, revised, approval, current_head_sha=snapshot["head_sha"])를 실행한다. 강사 또는 학생이 새 문서를 읽은 뒤 직접 선택하는 단계이며 테스트용 simulated_approval을 실제 승인처럼 재사용하지 않는다. 확인하지 않을 경우 승인 셀은 실행하지 않고 문서만 보관한다. 자동 merge 또는 외부 POST를 추가하지 않는다.'),
    ],
  },
];
