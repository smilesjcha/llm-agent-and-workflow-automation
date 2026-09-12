// Student-facing content. Instructor timing and prompts remain in notes.
import {insertLessonAdditions} from './day4_plan.mjs';
import {PR_WALKTHROUGH} from './day4_pr_walkthrough.mjs';
import {OFFICE_WALKTHROUGH} from './day4_office_walkthrough.mjs';
import {PROJECT_ENRICHMENT} from './day4_project_catalog.mjs';
const table=(title,headers,rows,note,phase='theory')=>({type:'table',title,headers,rows,note,phase});
const points=(title,points,note,phase='theory')=>({type:'points',title,points,note,phase});
const code=(title,code,explain,note,phase='demo')=>({type:'code',title,code,explain,note,phase});
const prompt=(title,prompt,check,note,phase='lab')=>({type:'prompt',title,prompt,check,note,phase});
const task=(title,steps,file,check,note)=>({type:'task',title,steps,file,check,note,phase:'lab'});
const image=(title,asset,caption,note,phase='demo')=>({type:'image',title,asset,caption,note,phase});
const check=(title,rows,note)=>table(title,['확인 항목','확인 방법'],rows,note,'check');
const ref=d=>({...d,reference:true});
export const PERIODS=[
 {time:'09:00–09:50',title:'PR 대상과 변경 코드',theory:12,demo:8,lab:25,check:5,goal:'저장소·PR·commit 구분과 변경 코드 검증',files:'pr.json · changes.diff · review.html'},
 {time:'09:50–10:40',title:'리뷰 초안과 코드 수정',theory:12,demo:8,lab:25,check:5,goal:'Codex 리뷰 요청, 결제 코드 수정, 게시 전 확인',files:'checkout.py · test_checkout.py · review.md'},
 {time:'10:40–11:30',title:'테스트와 GitHub 연동',theory:12,demo:8,lab:25,check:5,goal:'실패 테스트 복구와 CI·재실행 안전 설계',files:'workflow.yml · publication_preview.json'},
 {time:'13:00–13:50',title:'Excel WBS와 간트 차트',theory:12,demo:8,lab:25,check:5,goal:'입력·수식·조건부서식으로 작동하는 일정표',files:'wbs_tasks.json · WBS_Gantt.xlsx'},
 {time:'13:50–14:40',title:'자동 채점과 문항 분석',theory:12,demo:8,lab:25,check:5,goal:'정답 변경·입력 오류·동점 순위의 일관된 처리',files:'exam_sample.json · Exam_Grading.xlsx'},
 {time:'15:00–15:50',title:'Word 이력서와 사실 검증',theory:12,demo:8,lab:25,check:5,goal:'경력 사실을 보존한 문장 개선과 Word 생성',files:'career_facts.json · Resume_After.docx'},
 {time:'15:50–16:40',title:'데이터 기반 PPT 제작',theory:12,demo:8,lab:25,check:5,goal:'같은 프로젝트 데이터로 보고서 생성·수정·검수',files:'project_brief.json · Project_Brief.pptx'},
 {time:'16:40–17:30',title:'업무 도구 통합과 개인 프로젝트',theory:10,demo:10,lab:25,check:5,goal:'반복 실행 가능한 패키지와 다음 주 제작 범위',files:'README.md · improvement.md · 실행 결과 폴더'},
];
export const OPENING=[
 {type:'cover',title:'PR 리뷰 · 문서 자동화',subtitle:'GitHub · Excel · Word · PowerPoint'},
 table('4주차 학습 경로',['앞선 수업','오늘의 확장','다음 주'],[['1·2주차\n도구 호출·회의 기록','검증 가능한 입력과 파일','업무 서비스 통합'],['3주차\n코드 리뷰 Agent','PR 연동·테스트·사람 확인','개인 기능 개선'],['문서 활용 경험','수식·템플릿·생성 코드','3시간 개인 미니 프로젝트']],'앞선 수업을 다시 강의하지 않는다. 이번 주에는 실제 파일의 수정 전후를 보여 주며, AI가 초안을 만들고 소프트웨어가 계산과 검증을 맡는 차이를 연결한다.'),
 table('하루 시간표',['수업 시간 (쉬는 시간)','차시','함께 챙길 내용'],[['09:00–12:00\n(11:30–12:00)','1·2·3차시','PR 대상·리뷰·테스트'],['12:00–13:00','점심시간','13시 수업 시작'],['13:00–15:00\n(14:40–15:00)','4·5차시','WBS·자동 채점'],['15:00–18:00\n(17:30–18:00)','6·7·8차시','Word·PPT·통합\n마지막 30분: 휴식·Q&A']],'4주차는 일반 점심시간 12~13시다. 학습 400분, 휴식 및 Q&A 80분이다. 휴식은 각 연강 구간의 끝에 둔다. 마지막 Q&A 참여는 선택이다.'),
 table('실습 환경',['필수 준비','확인','선택 연결'],[['Python 3.12·VS Code','Notebook 커널 선택','Codex 로컬 프로젝트'],['제공 저장소 또는 ZIP','requirements-day4.txt 설치','Claude Code 로컬 폴더'],['파일을 열 수 있는 도구','XLSX·DOCX·PPTX·브라우저','개인 GitHub·Google 계정'],['합성 데이터','실제 고객·성적·키 미포함','계정 제한 시 로컬 경로']],'기본 코드는 AI API나 로그인 없이 실행한다. Codex·Claude의 실시간 생성은 별도 계정 조건이 적용된다. 무료 LibreOffice 또는 사용 가능한 Office로 결과를 연다. 회사 자료를 업로드하지 않는다.'),
 code('Notebook 시작','python -m pip install -r requirements-day4.txt\npython -m jupyter lab', ['materials/day4/day4_pr_document_automation.ipynb','저장소 루트에서 실행 · 커널 확인'],'Mac은 python3 또는 가상환경 Python을 사용한다. Notebook 첫 셀은 현재 커널에 필요한 패키지를 설치한다. 오래된 실행본이 아니라 새 Notebook을 열고 위에서부터 진행한다.'),
 table('도구별 작업 공간',['도구','작업 방식','이번 수업의 용도'],[['Codex 로컬 프로젝트','폴더·코드·터미널·diff','함수 수정과 테스트 실행'],['Claude Code 로컬 환경','허용한 폴더의 파일·명령','동일 과제의 다른 구현'],['ChatGPT·Claude 대화','첨부한 파일·사용 가능 도구','문장·문서 초안과 비교'],['Python·Node 코드','정해진 입력과 규칙','계산·반복 생성·자동 검사']],'일반 대화창 로그인만으로 PC 전체 파일 접근이나 GitHub 쓰기가 생기는 것은 아니다. 이번 기본 과정은 Python 코드이며, 로컬 Codex/Claude Code는 학생이 가진 환경을 연결한다. 공식 제품 문서 확인 2026-09-12.', 'theory'),
 {type:'architecture',title:'입력에서 결과 파일까지',note:'세 갈래가 서로 다른 일을 한다. PR은 AI 리뷰 초안과 테스트를 연결하고, Excel/PPT는 정해진 계산을 공유하며, Word는 경력 사실과 문장 개선을 비교한다. 모든 경로에 입력 검사와 사람 확인을 두지만 검증 기준은 같지 않다. 원격 전송은 이 그림 밖의 별도 승인 단계다.'},
];

export const LESSONS=[
[
 points('리뷰 결과의 목적지',['같은 코드라도 저장소와 PR이 다르면 다른 작업','commit SHA: 리뷰가 기준으로 삼은 코드 버전','좋은 리뷰 문장보다 먼저 확인할 대상 정보'],'택배 주소 비유로 repo/PR/SHA를 구분한다. PR 제목만 같아도 같은 작업이 아니다. 원격 게시 전 검증해야 할 값을 세 가지로 제한해 설명한다.'),
 table('PR 구성',['항목','예시','의미'],[['Repository','training-example/checkout-demo','합성 연습 저장소'],['PR number','42','변경 묶음의 번호'],['head SHA','40자리 commit 식별값','리뷰 대상 코드 버전'],['diff','checkout.py 변경 줄','추가·삭제된 코드']],'합성 PR임을 명확히 말한다. 실제 GitHub 화면의 실행 증거가 아니다. 숫자 42와 SHA는 서로 대체할 수 없다.'),
 table('AI와 코드의 Role',['작업','AI의 Role','코드의 Role'],[['변경 코드 이해','사용자 영향 추론','경로·줄 번호 검사'],['리뷰 내용','설명과 수정 제안','형식·대상 일치 검사'],['승인 이후','판단 근거 보조','버전·중복·권한 검사']],'한 모델에게 모든 검사를 부탁하면 문장은 그럴듯해도 대상 불일치가 남을 수 있다. 실패 조건이 명확한 부분은 코드로 고정한다.'),
 code('Diff 읽기','- return price * quantity\n+ return price * quantity - coupon', ['− 삭제한 코드 / + 추가한 코드','새 쿠폰 인자와 음수 결제 가능성'],'원래 정상적인 수량 계산이 쿠폰 추가로 어떻게 바뀌는지 직접 1000×1−5000을 계산한다. 줄 번호는 새 파일의 RIGHT 기준임을 연결한다.','theory'),
 table('입력 검증의 순서',['먼저 확인','그다음 확인','문제 발생 시'],[['저장소·PR 번호','예상한 대상과 일치','다른 PR 처리 중단'],['SHA 40자리 형식','최신 head SHA와 일치','새 diff 수집'],['파일 경로','작업 폴더 안쪽','접근 차단'],['변경 줄','리뷰 줄의 실제 존재','의견 수정 요청']],'SHA 형식이 맞는 것과 최신 버전이 일치하는 것은 다르다. 경로는 resolve 후 루트 아래인지 확인한다.'),
 image('PR 리뷰 작업대','assets/components/day4/pr-review-workbench.png','합성 PR · 로컬 실행 화면 · 실제 GitHub 게시 없음','브라우저 화면에서 변경 코드와 pytest 실패를 짚는다. 빨간 테스트는 준비 실패가 아니라 학생이 고칠 결함이다. 아래 리뷰 초안은 수업용 fixture라고 정확히 구분한다.'),
 code('합성 PR 로딩','from labs.day4.pr_review_lab import (\n    load_fixture, validate_snapshot\n)\nsnapshot = load_fixture()\nvalidate_snapshot(snapshot,\n    expected_repo=snapshot["repo"], expected_pr=42)',['코드: labs/day4/pr_review_lab/','Notebook: 1차시'],'실제 키 이름을 pr.json에서 같이 찾고 출력한다. 실패가 있으면 import 경로와 커널의 현재 폴더부터 확인한다.'),
 task('대상 정보 확인',['Notebook 1차시에서 합성 PR 로딩','저장소·번호·SHA를 각각 출력','changes.diff와 checkout.py 변경 줄 비교'],'labs/day4/pr_review_lab/fixtures/pr.json','세 값의 의미를 구분하고 해당 변경 파일을 열기','첫 작업은 JSON 산출이 아니라 실제 변경 코드를 읽는 준비다. 화면과 파일의 연결을 한 명씩 발표시키지 않고 채팅 질문으로만 받는다.'),
 task('잘못된 대상의 차단',['deepcopy로 snapshot 복사','repo를 another/repository로 변경','expected_repo를 원본으로 주고 검증 실행'],'Notebook · 1차시 실패 입력','REPO_MISMATCH 확인 · 원본 fixture 보존','오류를 단순 실패로 보지 않는다. 잘못된 대상에 리뷰를 남기지 않았다는 성공 기준이다. 학생은 try/except에서 code를 확인한다.'),
 code('다른 저장소의 차단','from copy import deepcopy\nbroken = deepcopy(snapshot)\nbroken["repo"] = "another/repository"\nvalidate_snapshot(broken,\n    expected_repo=snapshot["repo"], expected_pr=42)', ['예상 오류: REPO_MISMATCH','Notebook의 예외 처리 함수로 확인'],'이 조각은 오류를 보여 주기 위한 추가 실습이다. try/except LabError 또는 Notebook expected_failure 함수로 확인한다.','lab'),
 task('로컬 작업 폴더 생성',['prepare_exercise로 새 폴더 생성','checkout.py와 test_checkout.py 열기','check_exercise로 현재 테스트 실행'],'Notebook에 출력된 EXERCISE 경로','4 failed, 1 passed · 기존 파일 덮어쓰기 없음','Notebook은 실행마다 새 RUN 폴더를 만든다. 터미널 경로를 고정해 붙이지 말고 출력된 EXERCISE 경로를 사용한다. 5개 테스트 중 정상 쿠폰 케이스는 통과한다.'),
 table('입력과 실행의 구분',['입력','취급','기본 정책'],[['PR 제목·설명','외부 사람이 쓴 자료','명령으로 실행하지 않음'],['PR 변경 코드','검토할 자료','자동 checkout·실행 금지'],['수업용 checkout.py','확인된 합성 코드','로컬 테스트 실행'],['계정 키·고객 파일','실습 대상 아님','읽기·캡처·커밋 제외']],'Prompt Injection은 코드 주석에 정책을 무시하라는 문장이 섞이는 경우로 설명한다. 읽기용 자료와 실행 권한은 다른 문제다.'),
 check('1차시 확인',[['대상 구분','저장소·PR·SHA를 각각 설명'],['실제 파일','checkout.py와 test_checkout.py 열기'],['실패 처리','다른 repo 입력의 차단 확인'],['테스트 출발점','4 failed, 1 passed 출력 보관']],'학생이 모두 완료했는지 체크박스로 자가 점검한다. 발표는 없다. 빠른 학생은 아래 참고의 경로 검사로 확장한다.'),
 ref(table('API 응답의 누락',['상황','피해야 할 처리','필요한 처리'],[['binary 변경','없는 diff를 정상으로 간주','검토 불가 표시'],['페이지 수 초과','앞부분만 보고 완료 표시','범위 초과 중단'],['읽는 중 새 commit','서로 다른 버전 혼합','SHA 재확인']],'원격 API의 페이지네이션은 데이터를 끝까지 받았는지의 문제다. 이 실습 adapter는 범위를 제한하고 누락을 조용히 넘기지 않는다.')),
 ref(points('Context의 우선순위',['제품 규칙과 변경 목적','관련 함수·테스트·호출 위치','리뷰 범위를 넘는 자료는 제외'],'Context가 많다는 사실보다 관련성이 중요하다. 오전 시간을 남기면 리뷰 대상 외 파일을 추가했을 때 오히려 초점이 흐려지는 예를 구두로 제시한다.')),
],
[
 table('리뷰 의견의 구성',['항목','초과 쿠폰 예시'],[['위치','checkout.py:6'],['사용자 영향','결제액이 −4,000원으로 계산'],['재현 입력','가격 1,000 · 수량 1 · 쿠폰 5,000'],['최소 수정','입력 검사 후 결제액 0원 하한'],['검증','초과 쿠폰과 기존 정상 케이스 테스트']],'스타일 취향보다 사용자 영향이 있는 finding을 먼저 다룬다. P1/P2는 수업 예시의 우선순위이며 조직별 정책에 따라 정의가 필요하다.'),
 table('그럴듯한 의견과 유용한 의견',['비교','모호한 의견','실행 가능한 의견'],[['문제','예외 처리가 부족함','수량 0이 주문으로 처리됨'],['수정','클린 코드 적용','quantity < 1 검사 추가'],['검증','잘 동작하는지 확인','ValueError 테스트 통과']],'친절한 문장과 행동 가능한 리뷰를 구분한다. 재현 가능한 입력이 있으면 작성자와 리뷰어가 같은 문제를 볼 수 있다.'),
 points('추론 결과의 확인',['모델의 설명은 가설과 제안','재현 테스트는 관찰 가능한 증거','제품 규칙은 사람이 정한 기준'],'LLM이 확신 있게 말해도 테스트를 실행하지 않았다면 실행 증거가 아니다. 코드 리뷰는 사실·예측·취향을 분리해 읽는 훈련이다.'),
 table('리뷰 요청의 Context',['필수 자료','이번 파일','선택 이유'],[['업무 규칙','review_policy.md','무엇이 버그인지 판단'],['구현 코드','checkout.py','어디를 바꿀지 확인'],['테스트','test_checkout.py','기존 동작 보존'],['금지 행동','수정·게시 전 확인','범위 확장 방지']],'모델명만 바꿔도 문제가 해결된다는 인상을 주지 않는다. 자료와 지시, 검증 코드가 한 묶음으로 작동한다.'),
 prompt('Codex 리뷰 요청','review_policy.md와 내 실습 폴더의 checkout.py, test_checkout.py를 읽어 줘. 실패 입력과 사용자 영향을 먼저 설명해 줘. 파일 수정과 GitHub 게시는 아직 하지 마. 의견은 위치·재현 조건·최소 수정·관련 테스트 순서로 써 줘.','재현 입력 · 수정 범위 · 실행 여부','강사는 실제 로컬 프로젝트 대화에 이 요청을 입력한다. 연결이 없으면 제공 fixture를 검토하고 학생이 직접 코드를 수정한다. 실제 모델 출력인 척하지 않는다.','demo'),
 image('실제 Codex 리뷰 응답','assets/components/day4/codex-live-review.png','실제 CLI 응답의 브라우저 보기 · Desktop 대화 UI 아님','2026-09-12 codex-cli 0.151.0, gpt-5.6-sol, read-only로 지정한 세 파일만 읽었다. 실제 응답은 근거 있는 두 결함을 찾았지만 줄 번호를 5로 잘못 썼다. 다음 장표에서 원본과 비교한다. 테스트는 이 모델 호출에서는 미실행이다.'),
 table('모델 의견과 코드 근거',['항목','실제 모델 응답','사람 확인'],[['초과 쿠폰','−4,000원 가능','계산식과 일치'],['입력 검사','수량 0·음수 거절','제품 규칙과 일치'],['문제 위치','checkout.py:5','계산식은 6행'],['실행 여부','테스트 미실행','별도 pytest 필요']],'그럴듯한 리뷰가 있어도 줄 번호와 실행 여부는 확인해야 한다. 모델 원문은 수정하지 않고 별도 사람 검증 기록을 남겼다. Codex_실행사례_및_검증.md 참고.','theory'),
 code('초과 쿠폰의 재현','from checkout import checkout_total\nprint(checkout_total(1000, 1, 5000))\n# 수정 전: -4000\n# 요구사항: 0', ['실습 폴더 안에서 import','정상 가격·수량 계산은 유지'],'Notebook은 준비한 실습 폴더의 테스트를 subprocess로 실행한다. 이 짧은 예시는 함수의 잘못된 계산만 설명한다.'),
 table('결제 입력 규칙',['입력','허용','거절'],[['가격','0 이상의 값','음수 가격'],['수량','1 이상의 값','0 또는 음수'],['쿠폰','0 이상의 값','음수 쿠폰'],['최종 결제액','0원 이상','음수 결과']],'금융 기능을 실제 배포하는 코드가 아니라 기초 검증을 익히는 합성 예제다. 데이터형과 통화 소수점은 참고 심화에서 다룬다.'),
 task('실패 테스트 읽기',['check_exercise 실행','assert의 실제값과 기대값 비교','실패한 입력을 제품 규칙과 연결'],'내 실습 폴더/test_checkout.py','실패 네 건의 원인 구분','오류 로그 전체를 외우지 않는다. -4000과 0의 차이, DID NOT RAISE 두 종류부터 짚는다.'),
 task('결제 코드 수정',['가격·수량·쿠폰 입력 검사 추가','음수 결제액을 0으로 제한','같은 테스트 명령으로 재실행'],'내 실습 폴더/checkout.py','5 passed · 테스트 기대값 변경 금지','학생이 직접 타이핑하거나 Codex에 최소 수정 요청 후 diff를 읽는다. solution 복사만으로 끝내지 않도록 각 조건을 설명하고 잘못된 입력을 직접 바꿔본다.'),
 code('최소 수정 예시','if price < 0 or quantity < 1 or coupon < 0:\n    raise ValueError("INVALID_CHECKOUT_INPUT")\nreturn max(0, price * quantity - coupon)', ['기존 함수 안의 수정','정상 입력 + 초과 쿠폰 + 잘못된 입력'],'완전한 함수는 준비된 solution에 있다. 먼저 학생이 해본 뒤 필요한 경우에만 공개한다.','lab'),
 prompt('수정 Diff의 재검토','내가 수정한 checkout.py의 diff를 리뷰해 줘. 정상 쿠폰 계산이 유지되는지, 잘못된 입력이 거절되는지, 테스트를 약하게 바꾸지 않았는지 확인해 줘. 불필요한 라이브러리와 추상화는 추가하지 마.','기존 기능 · 입력 오류 · 테스트 보존','리뷰 피드백의 자동 생성과 수용은 다른 단계다. 두 번째 모델을 쓰더라도 사람이 같은 재현 입력을 확인해야 한다.'),
 table('승인의 범위',['확인 대상','고정할 값'],[['어디에','저장소와 PR 번호'],['어떤 코드에','head SHA'],['어떤 내용을','리뷰 본문의 해시'],['누가 확인했는지','검토자 식별값']],'승인을 일반적인 신뢰 선언이 아니라 특정 대상과 내용의 확인으로 설명한다. 로컬 승인 객체는 실제 서비스의 인증·전자서명 구현이 아니다.'),
 code('게시 전 미리보기','approval = approve_preview(\n    snapshot, review,\n    approved=True, reviewer="student")\npreview = preview_publication(\n    snapshot, review, approval,\n    current_head_sha=snapshot["head_sha"])',['본문을 읽은 뒤 approved=True 선택','PREVIEW_ONLY · 원격 게시 없음'],'Notebook은 리뷰 내용을 먼저 보여준다. Run All은 실제 게시하지 않는다. 이 코드는 승인 시뮬레이션이며 GitHub POST가 아니다.','demo'),
 check('2차시 확인',[['수정 결과','5 passed · 변경 diff 확인'],['리뷰 문서','재현 조건과 최소 수정 포함'],['게시 구분','preview는 전송 기록이 아님'],['사람 검토','초안의 내용과 대상을 직접 확인']],'리뷰 품질과 코드 품질을 분리해 체크한다. 리뷰가 예쁘게 나와도 테스트가 실패하면 수정 완료가 아니다.'),
 ref(table('리뷰 품질 평가',['기준','좋은 상태','나쁜 상태'],[['정확성','재현 가능한 결함','없는 문제의 지적'],['관련성','이번 변경의 영향','전체 구조 재작성'],['실행 가능성','작은 수정과 테스트','추상적 개선 요구'],['노이즈','중요한 의견만 유지','유사 의견의 반복']],'정답 개수보다 잘못된 경고가 개발 시간을 얼마나 쓰게 하는지 토론할 수 있다. 수치 평가를 하려면 사람이 검토한 기준 사례가 필요하다.')),
 ref(points('금액 처리의 확장',['정수 단위 또는 Decimal의 명시','반올림·세금·할인 순서의 제품 규칙','데이터형과 최대 금액의 추가 테스트'],'기초 수업 코드를 실서비스 결제 로직이라고 소개하지 않는다. 실무에서는 bool/int, 소수점, 과대값, 통화 규칙을 별도로 정의해야 한다.')),
],
[
 table('자동 검사와 AI 리뷰',['구분','자동 검사·CI','AI 리뷰'],[['질문','정한 규칙을 통과하는가','놓친 위험이 있는가'],['결과','명확한 pass/fail','설명과 판단 보조'],['반복 실행','같은 조건의 재현성','출력의 변동 가능성'],['최종 결정','테스트 증거','사람의 merge 판단']],'테스트가 통과했다고 모든 요구사항을 충족하는 것은 아니며 AI 리뷰가 좋다고 테스트를 생략할 수도 없다.'),
 table('GitHub 연동 구조',['순서','작업','이번 기본 실습'],[['1','PR 정보·diff 읽기','합성 PR / 선택 공개 PR'],['2','리뷰와 테스트 준비','로컬 파일·pytest'],['3','게시 내용·대상 확인','사람 확인 미리보기'],['4','외부 전달','기본 경로에서 미실행']],'자동 리뷰 서비스를 확장할 여지는 남기되 실제로 구현하지 않은 게시를 구현했다고 말하지 않는다. 모든 학생이 무료·로컬 경로로 핵심 구조를 배운다.'),
 points('재실행의 두 가지 위험',['리뷰 이후 코드가 바뀌는 상황','네트워크 재시도로 같은 의견을 두 번 쓰는 상황','새 버전 확인과 중복 확인의 별도 처리'],'오래된 SHA와 중복은 같은 문제가 아니다. 새로운 코드에는 새 리뷰가 필요하고, 같은 리뷰 재전송에는 이력 확인이 필요하다.'),
 code('통과 테스트의 확인','result = check_exercise(ROOT, EXERCISE)\nprint(result["status"])\nprint(result["output"])',['수정 완료 후: PASSED / 5 passed','EXERCISE는 Notebook이 만든 실습 폴더'],'터미널은 Notebook에 출력된 경로를 --exercise-dir로 지정한다. 로컬 수정 결과를 합성 PR의 원격 CI 통과로 표현하지 않는다.'),
 image('참고 구현의 테스트 결과','assets/components/day4/notebook-tests.png','실행된 Notebook의 HTML 보기 · 별도 참고 구현 5 passed','원본을 고치지 않은 학생 상태와 참고 구현의 통과 결과를 분리한다. 화면은 실제 실행된 Notebook의 HTML 렌더를 브라우저에서 캡처한 것이다.'),
 code('Actions의 최소 구성','on: [pull_request]\npermissions:\n  contents: read\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      # 제공 템플릿의 checkout·setup 단계\n      - run: python -m pytest -q exercise', ['전체 파일: templates/workflow.yml','축약 설명 · 실행은 완전한 템플릿 사용'],'학생에게 축약 YAML을 그대로 붙여 넣으라고 하지 않는다. 제공 전체 템플릿에는 pin된 checkout/setup, 의존성 설치가 들어 있다.','theory'),
 table('권한의 최소 범위',['필요 기능','필요 권한','이번 선택'],[['코드 읽기','contents: read','허용'],['테스트 실행','로컬·CI runner','허용'],['PR 댓글 쓰기','추가 쓰기 권한','기본 제외'],['자동 merge','저장소 변경 권한','금지']],'pull_request_target에서 신뢰하지 않는 PR 코드를 실행하는 위험을 연결한다. 예제 workflow를 공유 저장소에 임의 활성화하지 않는다.'),
 task('테스트 한 건 추가',['기존 정상 쿠폰 테스트 확인','본인이 고른 입력 한 가지 추가','실패 조건과 통과 조건을 비교'],'내 실습 폴더/test_checkout.py','단순 실행 외에 테스트 코드 직접 작성','추가할 만한 입력으로 coupon=0, 정확히 총액과 같은 쿠폰을 제시한다. 애매한 소수점 정책은 별도 요구사항으로 남긴다.'),
 task('CI 파일 구성',['workflow.yml을 별도 연습 폴더로 복사','trigger·permissions·pytest 단계 찾기','내 exercise 경로와 실행 명령 확인'],'labs/day4/pr_review_lab/templates/workflow.yml','전체 YAML과 실제 폴더 경로의 일치','GitHub 계정이 없는 학생은 파일 작성과 로컬 동일 명령 실행으로 완료한다. 계정이 있는 학생만 개인 저장소에 복사한다.'),
 code('오래된 코드의 차단','preview_publication(\n    snapshot, review, simulated_approval,\n    current_head_sha="3" * 40\n)',['예상 결과: STALE_HEAD_SHA','Notebook 3차시 expected_failure 셀 사용'],'Notebook이 만든 테스트용 simulated_approval을 사용한다. 사람의 실제 승인으로 기록하지 않는다. 새 diff → 새 리뷰 → 다시 확인 순서를 설명한다.'),
 task('중복 리뷰의 차단',['같은 리뷰 표식으로 이력 구성','Notebook 중복 검사 셀 실행','새 리뷰와 재전송 상황 비교'],'Notebook · 3차시 안전 검사','DUPLICATE_REVIEW · 두 번째 전송 없음','미리보기는 원자적 분산락 구현이 아니다. 실제 서비스에서는 동시 요청과 불확실 응답도 추가 설계해야 함을 노트에서 보충한다.'),
 prompt('GitHub 연결 요청','내 개인 연습 저장소에서만 진행해 줘. 변경 파일과 테스트 결과를 정리하고 PR 설명 초안을 만들어 줘. push와 PR 생성은 대상 저장소·브랜치·공개 범위를 보여 준 뒤 내 확인을 기다려 줘. merge는 하지 마.','저장소 · 브랜치 · diff · 테스트 결과','원격 작업은 개인 저장소에서 학생이 직접 확인한다. 회사 저장소나 수업 공유 저장소를 작업 대상으로 잡지 않는다.'),
 table('개인 PR의 확인 위치',['화면','확인 내용'],[['Files changed','의도한 파일만 변경'],['Checks','같은 테스트 명령의 통과'],['Conversation','목적·수정 범위·주의점'],['Merge 전','사람의 최종 확인']],'웹사이트 보기만 실습으로 세지 않는다. 앞에서 만든 코드·YAML을 실제 개인 PR에 올린 학생만 Checks 실행을 비교한다.'),
 check('3차시 확인',[['테스트','내가 추가한 테스트 포함 통과'],['CI 파일','경로·권한·실행 명령 확인'],['버전 변경','STALE_HEAD_SHA 차단'],['재실행','DUPLICATE_REVIEW 차단']],'오전 학습의 체크로 마무리한다. 다음 장표를 넘기기 전에 파일 저장과 쉬는 시간을 안내한다.'),
 ref(table('운영 확장 · 네트워크 오류',['응답','처리 방향'],[['401·403','인증·권한·요청 제한 확인'],['429','제한 확인 후 정해진 횟수만 대기'],['5xx·timeout','읽기는 제한 재시도, 쓰기는 이력 확인'],['알 수 없는 전송 결과','재전송 전에 실제 게시 이력 조회']],'제공 adapter는 GH_READ_FAILED 공통 오류이며 이 재시도 정책을 구현한 운영 서비스가 아니다. 쓰기 timeout 뒤 무조건 재시도하면 중복 알림이 생길 수 있다.')),
 ref(points('CI의 공급망 위험',['Action 버전을 전체 commit SHA로 고정','PR에서 온 스크립트와 secret의 분리','검사 도구 업데이트도 변경 이력으로 관리'],'GitHub 공식 secure-use 문서를 설계 근거로 제시한다. pin된 SHA라도 공급자를 검토해야 하며 영구적으로 안전하다는 의미는 아니다.')),
],
[
 image('일정 데이터와 간트 차트','outputs/day4-document-automation/wbs_gantt.png','WBS_Gantt.xlsx · 날짜·진척률에 반응하는 조건부서식','완성 파일의 간트 부분을 먼저 보여준다. 그림을 붙인 것이 아니라 입력을 바꾸면 셀 색이 다시 계산되는 표라는 점을 실제 변경으로 증명한다.'),
 table('WBS의 최소 단위',['항목','예시','용도'],[['업무','PR diff 수집','끝낼 작업의 범위'],['Role','Backend','업무 담당 역할'],['시작·종료','09/16–09/18','기간 계산'],['선행 ID','W01','먼저 끝나야 할 업무'],['진척률','0.8 → 80%','현재 진행 정도']],'WBS는 큰 프로젝트를 관리 가능한 작업으로 나눈 표다. 역할명만으로 실제 개인 배정이 된 것은 아니므로 개인 서비스에선 담당자 열을 추가할 수 있다.'),
 table('AI 초안과 계산의 분리',['일','AI 도움','코드·수식'],[['업무 분해','누락 후보와 순서 제안','필수 열·ID 검사'],['일정 산정','가정과 위험 설명','업무일 계산'],['상태 표시','지연 원인 문장 초안','날짜·진척률 조건'],['보고','읽기 쉬운 설명','같은 입력의 수치 재사용']],'날짜나 완료 개수를 모델이 기억해서 쓰게 하지 않는다. 설명할 수치는 검증한 계산 결과에서 가져온다.'),
 code('업무일 계산','=NETWORKDAYS(D9,E9)\n\n# 시작일과 종료일 포함\n# 토요일·일요일 제외\n# 공휴일 목록은 별도 추가',['H열: 업무일','샘플: 대한민국 공휴일 미반영'],'샘플의 2026년 실제 공휴일을 반영했다는 오해를 피한다. 휴일 범위를 세 번째 인수로 주는 확장은 선택 과제다.','theory'),
 table('셀 참조의 방향',['참조','고정되는 부분','간트에서의 역할'],[['L$8','날짜가 있는 8행','가로 이동 시 다음 날짜'],['$D9','시작일 D열','세로 이동 시 다음 업무'],['$E9','종료일 E열','업무별 기간 비교'],['$B$4','기준일 셀 전체','모든 업무의 같은 기준일']],'달러 기호를 돈으로 읽지 않고 복사 방향을 제한하는 표시로 설명한다. L9에서 M10으로 복사할 때 각각 어떻게 바뀌는지 학생에게 직접 예상하게 한다.'),
 code('간트 표시 조건','=AND(\n  L$8 >= $D9,\n  L$8 <= $E9,\n  WEEKDAY(L$8,2) < 6\n)', ['기간 안쪽 + 평일','실제 파일은 입력 검증·상태 조건도 포함'],'단순 핵심 식을 먼저 설명한 후 실제 파일의 완료·지연·진행 중 세 규칙을 본다. 색은 장식이 아니라 상태를 읽는 보조 수단이다.','theory'),
 image('입력 열과 계산 열','outputs/day4-document-automation/wbs_table.png','입력 A:G · 계산 H:K · 기준일 B4 · 간트 L:AM','한 화면에 전체 열을 억지로 넣지 않고 표와 간트를 나누어 확대한다. F12가 W04 진척률이며 상태는 I12임을 가리킨다.'),
 code('WBS 데이터 로딩','from labs.day4.office_lab.sheets.student_excel import (\n    load_sample, calculate_wbs\n)\ntasks = load_sample("wbs_tasks.json")\nrows = calculate_wbs(tasks, "2026-09-25")',['Notebook 4차시','원본 JSON 대신 복사본 수정'],'모듈 import 줄은 Notebook에 준비되어 있다. 모델 호출 없이 같은 계산을 재현하는 Python 기준값을 만든다.'),
 task('진척률 변경',['W04의 progress를 0.8에서 1로 변경','calculate_wbs 다시 실행','새 XLSX 복사본을 생성해 열기'],'wbs_tasks.json → 내 WBS 복사본','W04 지연 → 완료 · 완료 개수 변화','원본 데이터 파일을 직접 덮지 않고 Notebook deepcopy를 이용한다. Python은 상태가 바뀌었는데 Excel 화면이 그대로라면 파일 재계산과 열린 파일 버전을 확인한다.'),
 task('일정 변경과 차트 확인',['새 복사본에서 B4 기준일 변경','D:E 시작·종료일 변경','I 상태와 L:AM 간트 이동 확인'],'WBS_Gantt.xlsx · 복사본','입력 변화와 차트 변화의 일치','모든 날짜를 바꾸지 말고 한 업무부터 바꾼다. 종료일이 선행 업무보다 앞서는 상황까지 비교한다.'),
 task('선행 일정의 오류',['업무의 시작일을 선행 종료일 이전으로 변경','validate_wbs와 J열 메시지 확인','일정을 복구하고 재검증'],'Notebook 4차시 · WBS J열','선행 일정 충돌 표시 · 복구 후 해제','예외 처리 실습은 실제 화면에서 오류를 보이게 하는 것이다. 무조건 0이나 빈칸을 넣어 감추지 않는다.'),
 prompt('Codex의 WBS 확장','WBS 코드와 테스트를 읽어 줘. 공휴일 목록을 선택 입력으로 추가하고 싶어. 기존 기본 결과는 유지하고, 휴일이 있는 경우와 없는 경우의 테스트를 먼저 제안해 줘. 원본 XLSX는 덮어쓰지 마.','기존 동작 · 추가 입력 · 테스트 두 종류','빠른 학생의 추가 실습이다. AI가 기능을 한꺼번에 늘리지 않도록 공휴일 하나에 범위를 한정한다.'),
 table('수식 결과의 검증',['검증','방법'],[['계산 정확성','작은 날짜 구간을 손으로 계산'],['재계산','입력 한 셀 변경 후 상태 확인'],['서식','같은 조건의 업무는 같은 표시'],['호환성','사용 중인 Excel·LibreOffice에서 열기']],'파일 생성 성공과 파일 사용 성공은 다르다. 수식 캐시는 도구마다 다를 수 있어 실제 사용 앱에서 재계산을 확인한다.'),
 check('4차시 확인',[['코드 수정','W04 진척률 변경과 새 파일 생성'],['동적 표','날짜 변경 후 상태·간트 갱신'],['잘못된 입력','선행 일정 충돌 확인'],['원본 보존','다른 이름의 XLSX 저장']],'학생이 직접 변경한 파일을 남겼는지 확인한다. 단순 다운로드만 한 경우는 아직 코드 실습이 아니다.'),
 ref(table('WBS의 확장 기준',['기능','먼저 필요한 정의'],[['담당자별 부하','하루 가용 시간·병행 업무'],['비용 산정','단가·기간·수량의 단위'],['의존성 자동 조정','변경 전파와 예외 허용'],['휴일 처리','국가·조직·근무요일']],'기능을 넣기 전에 업무 규칙부터 정의한다. AI가 그럴듯한 일정을 만든 것과 실제 자원 계획은 다른 수준이다.')),
 ref(points('템플릿과 생성 코드',['안정된 레이아웃은 템플릿으로 유지','반복 입력과 계산은 코드로 분리','양식 변경도 버전과 테스트로 관리'],'학생용 공개 코드에서는 제공한 XLSX 템플릿을 openpyxl로 복사·수정한다. 수식을 새로 계산하는 엔진은 아니므로 Excel/LibreOffice의 재계산을 안내한다.')),
],
[
 image('40문항 자동 채점','outputs/day4-document-automation/exam_inputs.png','28명 합성 응답 · 실제 학생 성적과 개인정보 미포함','사용자 제시 화면의 구조를 참고해 새로운 합성 데이터로 만든 예다. 원본 파일의 수식이나 학생 데이터를 복제했다는 주장은 하지 않는다.'),
 table('채점 정책',['상태','점수','집계'],[['정상 응답','정답 1점·오답 0점','포함'],['미응답','해당 문항 0점','포함'],['잘못된 입력','점수 확정 보류','행 제외'],['결시','0점과 별도 관리','제외'],['정답 미등록','전체 채점 보류','정답 확인 후 재계산']],'점수보다 먼저 규칙을 정한다. 빈칸과 결시를 같은 0으로 처리하면 평균과 문항 정답률이 왜곡될 수 있다.'),
 table('채점 시트의 위치',['위치','내용','변경 여부'],[['D8:AQ8','40개 정답','교수자 입력'],['D10:AQ37','응시자 답안','학생 응답 입력'],['AR:AS','총점·동점 등수','수식 계산'],['AT:AX','보류·미응답·오류 집계','검증 결과'],['43행','문항별 정답률','분모를 확인할 지표']],'엑셀 열 이름을 실제 파일에서 찾게 한다. 마지막 컬럼을 별도의 파란 강조로 꾸미지 않는다. 전체 체계를 한 표로 설명한다.'),
 code('정답 색의 조건','=AND(\n  $C10="응시", D$45="등록",\n  ISNUMBER(D10),\n  D10=D$8,\n  D10>=1, D10<=4\n)', ['적용 범위 D10:AQ37','유효한 정답 등록 + 같은 열의 8행과 비교'],'45행에서 정수 1~4의 정답 등록 여부를 검사한다. 잘못된 소수 정답과 응답이 같아도 정답 색이 되지 않는다. 색 외에도 처리 상태와 채점내역 텍스트를 함께 둔다.','theory'),
 table('동점 순위와 정답률',['지표','규칙','예시'],[['동점 순위','나보다 높은 점수 인원 +1','30·30·28 → 1·1·3'],['정답률 분자','집계 대상 중 해당 문항 정답자','정답자 수'],['정답률 분모','입력 오류 없는 응시자','미응답 포함·결시 제외'],['분모 0','집계 보류','0%로 오해 방지']],'동점 처리 방식을 먼저 합의한다. rank 평균 방식도 있지만 이번 파일은 공동 순위 후 건너뛰기다. 정답률은 분모 정책에 따라 달라진다.'),
 image('총점과 보류 상태','outputs/day4-document-automation/exam_results.png','총점 /40 · 등수 · 처리 상태 · 미응답 · 입력 오류','25번째 학생 미응답, 26번째 학생의 9 입력, 28번째 결시 사례를 비교한다. 번호는 합성 행의 위치이지 실제 학생 식별정보가 아니다.'),
 code('Python 기준값','from labs.day4.office_lab.sheets.student_excel import (\n    load_sample, grade_exam\n)\nexam = load_sample("exam_sample.json")\nreport = grade_exam(exam)',['Excel 결과와 독립적으로 비교','기본 집계 대상 26명'],'XLSX 수식과 Python 계산이 같은 정책을 따르는지 교차검증한다. 두 구현 모두 틀릴 수 있어 작은 손계산 예제도 함께 확인한다.'),
 task('정답 변경의 영향',['원본을 deepcopy로 복사','첫 문항 정답을 1에서 2로 변경','Python 보고서와 새 XLSX의 총점 비교'],'Notebook 5차시 · D8','총점·순위·정답률의 동시 갱신','총점만 바뀌고 순위가 안 바뀌는 문제를 찾는 실습이다. 최초 값으로 복구해서 가역성도 확인한다.'),
 task('입력 오류의 복구',['L35의 9 입력 확인','1~4의 유효한 답안으로 수정','집계 대상 인원과 평균 재확인'],'Exam_Grading.xlsx · L35','집계 대상 26 → 27명','오류 학생에게 0점을 줘버리는 대신 채점 보류가 해제되는 흐름이다. 모델이 정답을 추측해서 고치는 방식은 사용하지 않는다.'),
 task('예외 입력 테스트',['정답 한 칸을 비워 채점 보류 확인','답안에 글자 또는 9 입력','정답·답안을 복구하고 재계산'],'Notebook 5차시 · 별도 복사본','오류는 보류 · 복구 후 정상 계산','원본 정답을 지우지 않는다. 각 테스트마다 deepcopy를 사용한다. 결시와 미응답 차이를 눈으로 보며 규칙을 다시 확인한다.'),
 image('문항 분석','outputs/day4-document-automation/exam_question_analysis.png','정답률만이 아닌 정답자 수·집계 대상·미응답 수','정답률이 낮다고 바로 문제를 잘못 출제했다고 단정하지 않는다. 수업 범위, 모호한 표현, 응답 누락을 함께 보아야 한다.'),
 table('Google Sheets 적용',['순서','내 연습 파일에서의 작업'],[['1','합성 XLSX 업로드 → Google Sheets 사본'],['2','빈 문서는 제공 Code.gs로 합성 시트 생성'],['3','D10:AQ37 → 서식 → 조건부서식'],['4','맞춤 수식과 범위 확인'],['5','정답·오답·빈칸을 바꿔 실제 결과 비교']],'원본 성적표는 만지지 않는다. 빈 네이티브 문서에서는 Code.gs의 createDay4GradingPractice를 확인 후 실행한다. Office 편집 모드와 네이티브 Google Sheets는 다르다. 계정이 없으면 로컬 XLSX 경로로 필수 실습을 마친다.'),
 prompt('채점 규칙 개선 요청','합성 채점 코드에 대해 입력 오류, 미응답, 결시, 동점 처리 규칙을 표로 설명해 줘. 정답을 추측해서 바꾸지 마. 문항별 배점을 추가한다면 기존 1점 기본값을 유지하고 관련 테스트부터 제안해 줘.','점수 정책 · 기존 결과 · 추가 테스트','자동 채점은 수식·코드가 맡고 AI는 규칙 설명과 구현 보조를 맡는다. 실제 성적 데이터를 개인 AI 계정에 업로드하지 않는다.'),
 check('5차시 확인',[['정답 변경','총점·순위·정답률 갱신'],['오류 처리','잘못된 답안은 채점 보류'],['분모','결시·입력 오류 제외 규칙'],['결과 파일','수정된 XLSX·CSV 열기']],'엑셀은 보기 좋은 색보다 올바른 분모와 보류 상태가 중요하다고 한 문장으로 연결한다. 이 표는 확인 시간이며 앞선 내용을 반복 강의하지 않는다.'),
 ref(image('맞춤 수식의 공식 안내','assets/components/day4/google-sheets-custom-formula-reference.png','Google 공식 도움말 · 실제 브라우저 캡처','공식 참고 화면이며 수업용 계정에서 Apps Script를 실제 실행한 증거가 아니다. 웹 페이지 구경은 실습 시간에 포함하지 않는다.')),
 ref(table('Apps Script 확장',['기능','안전한 범위'],[['수식·조건부서식 일괄 배치','새 합성 연습 시트만 생성'],['반복 실행','기존 동일 이름 시트 덮어쓰기 금지'],['권한','현재 문서만 접근'],['검증','생성 후 직접 정답·오류 입력 변경']],'제공 스크립트는 선택 확장이다. 설치형 trigger, 이메일 전송, 실제 성적 접근은 넣지 않는다. 네이티브 Google 실행은 계정에서 사용자가 확인한다.')),
],
[
 image('Word 이력서 개선 전','outputs/day4-document-automation/render/before-final/page-1.png','동일한 경력 사실 · 긴 문장 중심의 원본 예시','강사 제공 산업 경험을 익명 교육용으로 정리한 자료다. 실존 회사의 성과나 숫자를 검증한 외부 자료가 아니라 본인 제공 내용임을 구분한다.'),
 table('경력 문장의 구성',['요소','질문','예시'],[['상황','어떤 업무 문제였나','수작업 말하기·글쓰기 평가'],['Role','어떤 일을 맡았나','AI 개발·운영 총괄'],['실행','무엇을 만들었나','평가 시스템과 운영 흐름'],['결과','무엇이 달라졌나','처리시간 단축'],['근거','어떤 사실에 기반하나','career_facts.json의 ID']],'성과 문장은 형용사가 아니라 상황·역할·실행·결과의 연결이다. 근거 없는 수치와 과장된 직함은 생성하지 않는다.'),
 table('개선과 사실 변경',['작업','허용','확인 필요'],[['문장 정리','중복 제거·명사 통일','의미가 달라진 표현'],['성과 강조','제공한 수치 재사용','새 수치·비율'],['업무 범위','제공한 Role 설명','참여를 총괄로 변경'],['경력 구조','산업별 묶음','새 재직 기간·직함']],'숫자만 보존한다고 사실이 보존되는 것은 아니다. 지원·참여를 책임자로 바꾸는 과장도 사람 검토 대상이다.'),
 table('Fact map',['항목','용도'],[['fact_id','문장을 원래 사실에 연결'],['원문','사용자가 제공한 경력'],['개선안','더 읽기 쉬운 설명'],['검사 결과','새 숫자·누락된 근거 탐지'],['사람 확인','의미·범위·톤앤매너 검토']],'Fact map은 작은 데이터 구조일 뿐 특수한 AI 제품이 아니다. 입력 사실과 출력 문장을 매핑해 사람이 비교할 수 있게 한다.'),
 prompt('이력서 개선 요청','career_facts.json의 사실만 사용해 Word 이력서를 개선해 줘. 새로운 숫자·직함·재직 기간은 만들지 마. 산업별 경험은 문제·Role·실행·결과 순서로 정리하고, 바뀐 문장마다 근거 fact_id를 함께 보여 줘.','사실 연결 · 새 주장 여부 · 읽기 흐름','일반 ChatGPT/Claude에는 익명 파일을 첨부한다. 로컬 Codex/Claude Code에서는 지정된 폴더만 읽도록 한다. 실제 연락처와 고객정보는 제외한다.','demo'),
 image('Word 이력서 개선 후','outputs/day4-document-automation/render/after-final/page-1.png','동일 사실의 구조 개선 · 편집 가능한 DOCX','강조가 많아서 좋아진 것이 아니라 산업 흐름과 Role을 빠르게 찾을 수 있어야 한다. 처음과 끝의 사실 목록을 비교한다.'),
 code('Word 생성 코드','python -m labs.day4.office_lab.documents.resume_lab \\\n  --variant after \\\n  --output outputs/day4-student/Resume_Mine.docx',['python-docx · API key 불필요','출력 폴더는 작업 공간 내부'],'커맨드는 저장소 루트에서 실행한다. 기존 파일이 있으면 새 이름을 선택한다. Word를 먼저 열지 않은 상태에서도 docx 생성이 가능하다.'),
 task('경력 문장 한 개 개선',['Fact map에서 문장 하나 선택','의미는 유지하고 길이·순서 개선','audit_rewrite로 자동 검사'],'career_facts.json · Notebook 6차시','fact_id 유지 · 새 숫자 없음','전체 이력서를 한 번에 고치지 않는다. 한 문장에서 개선 기준을 익힌 후 범위를 넓힌다.'),
 task('의도한 과장 검사',['복사한 개선안에 새 숫자 추가','자동 검사에서 차단 확인','숫자를 제거하고 다시 검사'],'Notebook 6차시 · audit_rewrite','새 숫자 차단 · 통과 후에도 사람 검토','오류를 직접 만들어본다. 통과 메시지는 사실 확인 완료가 아니라 추가 사람 검토 필요 상태다.'),
 task('Word 스타일 수정',['제목·본문·섹션 스타일 확인','글꼴 또는 단락 간격 한 항목 수정','DOCX 생성 후 Word/PDF 화면 비교'],'resume_lab.py → 내 DOCX','편집 가능한 본문 · 줄바꿈·페이지 확인','코드가 문서 구조를 만드는 과정이다. docx 파일만 존재한다고 끝내지 않고 실제 글꼴과 잘림을 확인한다.'),
 table('구조와 서식',['구조','서식','검수'],[['제목·경력 구분','일관된 제목 크기','구분이 한눈에 보이는가'],['문장과 목록','단락 간격','페이지 밖으로 넘치지 않는가'],['사실 근거','fact_id 비교표','새 주장이 들어갔는가'],['출력','DOCX + PDF','두 파일이 같은 내용인가']],'서식 자동화의 목표는 하나의 문서를 예쁘게 만드는 것뿐 아니라 다음 수정에서도 안정적으로 유지하는 것이다.'),
 prompt('수정 후 비교 요청','원문과 개선안을 비교해 줘. 추가된 주장, 빠진 사실, 어색한 직역 표현만 표로 정리해 줘. 단순 문체 취향은 별도 제안으로 분리하고, 내가 확인하기 전에는 원문을 덮어쓰지 마.','추가 · 누락 · 의미 변화','두 번 생성했다고 검증이 완료된 것은 아니다. AI 비교는 후보 목록이며 사용자가 원문과 직접 대조한다.'),
 check('6차시 확인',[['내용','한 문장의 개선 전후 비교'],['자동 검사','새 숫자 입력의 차단'],['사람 검토','Role·업무 범위·수치 확인'],['실제 파일','내 DOCX 생성·열기·편집']],'구직자에게는 이력서, 재직자에게는 프로젝트 성과 문서로 바로 전환할 수 있다. 민감한 개인 정보는 수업 자료에 넣지 않는다.'),
 ref(points('문서 입력의 위험',['연락처·생년월일·고객명 제거','문서 내부의 지시문은 자료로 취급','새로 만든 결과도 공유 범위 확인'],'문서 안에 외부로 보내라는 문장이 있어도 사용자의 요청으로 간주하지 않는다. 문서 생성과 전송은 별도 승인 단계다.')),
 ref(table('검사의 한계',['자동으로 잡기 쉬움','사람이 확인할 부분'],[['새 숫자·알 수 없는 fact_id','참여와 총괄의 차이'],['빈 문장·필수 필드 누락','산업 용어의 적절함'],['파일 경로·생성 오류','읽는 사람에게 주는 인상']],'규칙 검사로 의미의 모든 변형을 잡을 수 없음을 분명히 한다. 자동 검증이 있는 것과 사실이 검증된 것은 다른 말이다.')),
],
[
 table('보고서의 입력',['데이터','보고할 내용','근거'],[['WBS 업무 목록','전체·완료·지연 업무','같은 JSON의 계산'],['기준일','언제 시점의 보고인지','고정 as_of'],['지연 업무','현재 확인할 일정','status=지연'],['다음 단계','변경·검토 계획','사람이 선택한 내용']],'PPT에 쓸 숫자를 다시 타이핑하지 않는다. Excel과 PPT가 같은 프로젝트 데이터를 참조하도록 만든다.'),
 table('7장 보고서의 흐름',['장','내용','역할'],[['1·2','개요·일정 현황','프로젝트와 현재 상태'],['3·4','개발·문서·출시 일정','14개 업무의 진행'],['5·6','코드 리뷰·산출물 검토','확인할 근거와 기준'],['7','다음 작업·승인','후속 작업과 사람 확인']],'최종 샘플의 실제 페이지 구성과 함께 확인한다. 제목 개수를 맞추기 위한 반복 요약은 넣지 않는다. 슬라이드별로 다른 질문에 답한다.'),
 points('좋은 생성 요청의 조건',['독자와 회의 목적','사용할 데이터와 금지할 추정','페이지별 질문과 편집 가능 형식'],'예쁘게 만들어줘만으로는 중요한 수치의 근거와 레이아웃 기준이 빠진다. 누구에게 무엇을 결정받을 문서인지 먼저 적는다.'),
 table('자동화 방식의 차이',['방식','장점','확인할 점'],[['대화형 파일 생성','초안과 구조를 빠르게 비교','계정 도구·실행 결과 확인'],['템플릿 채우기','일관된 양식 반복','필드 길이와 넘침'],['코드 기반 생성','같은 입력으로 재생성','글꼴·표·시각 검수']],'일반 대화와 로컬 프로그램을 혼동하지 않는다. 이번 기본 실습은 공개 코드 생성이며 Codex/Claude는 코드와 구조 개선을 돕는다.'),
 code('프로젝트 데이터 준비','python -m labs.day4.office_lab.presentations.brief_data \\\n  --as-of 2026-09-25 \\\n  --output outputs/day4-student/brief.json',['WBS와 같은 기준일','검증된 계산 → 보고서 입력'],'brief_data.py는 WBS 계산 함수를 재사용한다. JSON 자체가 완성 결과가 아니라 뒤의 PPT 생성기에 넘기는 입력이다.'),
 code('학생용 PPT 생성','npm install --prefix labs/day4/office_lab/presentations\nnode labs/day4/office_lab/presentations/student_ppt.mjs \\\n  outputs/day4-student/brief.json \\\n  outputs/day4-student/Project_Brief.pptx',['저장소 루트에서 실행 · Node.js 필요','같은 파일명 재사용 시 새 이름 선택'],'공개 라이브러리 경로를 확인한다. npm install은 인터넷이 필요하다. 준비되지 않은 학생에게는 제공 PPT를 열고 구조·수치 검수 후 코드 경로를 나중에 이어가게 한다.'),
 image('프로젝트 보고서 예시','outputs/day4-document-automation/render/ppt-final/slide-2.png','Project_Brief.pptx · 편집 가능한 표와 수치','PPT 생성 결과를 실제 열어 보여준다. 웹 페이지 스크린샷으로 PPT 파일 생성을 대체하지 않는다. 폰트와 숫자를 함께 확인한다.'),
 task('보고서 재생성',['W04 진척률을 바꾼 tasks 준비','write_brief로 새 보고서 입력 생성','student_ppt.mjs로 새 PPT 생성'],'Notebook 7차시 · brief.json → PPTX','전체·완료·지연 수치의 변경 반영','같은 입력을 Excel과 보고서로 표현하는 작업이다. 입력을 한 번 바꾸고 두 파일의 숫자가 맞는지 확인한다.'),
 task('편집 가능한 표 확인',['생성 PPT를 PowerPoint/LibreOffice로 열기','표의 업무명 셀 직접 수정','본문과 표가 이미지가 아닌지 확인'],'내 Project_Brief.pptx','문자와 표 셀의 직접 편집','모든 것을 큰 이미지 한 장으로 만들어놓으면 다음 사람이 수정하기 어렵다. 화면 캡처는 참고 이미지로만 사용한다.'),
 prompt('Codex의 레이아웃 수정','student_ppt.mjs를 읽고 본문 글씨를 더 크게 조정해 줘. 수치와 문장은 brief.json을 유지해 줘. 표를 이미지로 바꾸지 말고, 긴 업무명이 넘칠 때는 행 높이 또는 열 너비를 조정해 줘. 수정 전후를 렌더해서 비교해 줘.','내용 유지 · 글자 크기 · 실제 화면','제작 방법에 대한 요청을 학생용 PPT에 슬로건으로 넣지 않는다. 코드의 스타일 설정을 바꾸고 결과 파일을 비교한다.'),
 task('PDF와 화면 검수',['PPT를 PDF로 내보내기 또는 인쇄 저장','모든 페이지의 글꼴·잘림 확인','한 오류를 수정하고 다시 생성'],'PPTX + PDF · 내 출력 폴더','같은 내용 · 읽을 수 있는 글꼴','PDF는 결과를 확인하기 위한 고정 레이아웃이다. 편집 가능한 PPT와 함께 보관하며 PDF만으로 완성했다고 하지 않는다.'),
 table('숫자·레이아웃 검증',['검사','비교 대상'],[['전체 업무','WBS 데이터의 행 수'],['완료·지연','동일 as_of의 계산 결과'],['긴 제목','줄바꿈과 표 높이'],['글꼴','다른 PC와 PDF 출력'],['파일 열기','PPTX 실제 편집 가능 여부']],'좋은 보고서의 첫 검수는 색상이 아니라 숫자와 기준일이다. 과장된 시각화나 근거 없는 숫자 추가를 막는다.'),
 check('7차시 확인',[['코드 실행','새 입력으로 새 PPT 생성'],['데이터 연결','WBS와 보고서의 숫자 일치'],['편집 가능','본문·표 셀 직접 수정'],['화면 검수','PDF의 잘림·글꼴 확인']],'설치가 늦은 학생은 원본 PPT 검수와 입력 생성까지만 완료하고, 배포한 실행 가이드로 생성 단계를 이어갈 수 있다. 이를 실행 완료와 구분해서 기록한다.'),
 ref(table('반복 보고의 구조',['분리할 것','예시'],[['Data','프로젝트·업무·기준일'],['Content','독자·핵심 질문·설명'],['Style','글꼴·색·간격·표'],['Validation','숫자·필수 페이지·렌더']],'표준화를 한다고 모든 장표의 레이아웃이 같아야 하는 것은 아니다. 입력과 스타일의 분리로 다양한 구조를 안정적으로 유지한다.')),
 ref(points('배포 전 확인',['개인정보와 비공개 프로젝트명 제거','버전·기준일·출처의 표시','메일·Drive 업로드는 별도 사람 확인'],'파일 생성은 로컬 작업이다. 외부로 배포하는 권한을 자동으로 얻는 것은 아니다. 대상과 공개 범위를 다시 확인한다.')),
],
[
 table('업무 자동화의 공통 구조',['단계','이번 예제','확인 기준'],[['입력','PR·WBS·답안·경력','범위와 필수 값'],['처리','리뷰·계산·문장 개선','역할별 함수'],['검증','테스트·수식·사실 비교','기대한 변화와 오류'],['출력','HTML·XLSX·DOCX·PPTX','실제 열기·편집'],['전달','개인 저장·선택 공유','사람이 대상 확인']],'하루의 마지막에만 공통 구조를 정리한다. 오전에 한 말을 반복하기보다 학생이 만든 서로 다른 결과가 같은 구조를 갖는다는 것을 보여준다.'),
 table('서비스와 일회성 파일',['구분','일회성 생성','반복 가능한 도구'],[['입력','대화마다 다시 설명','정해진 필드·양식'],['실행','작성자만 방법을 앎','실행 명령·Notebook'],['오류','대충 수정 후 진행','메시지·복구 방법'],['검증','한 번 눈으로 확인','테스트 + 사람 확인'],['전달','파일만 공유','코드·안내·샘플 함께']],'모든 것을 웹서비스로 배포할 필요는 없다. 동료가 자기 PC에서 다시 쓸 수 있는 도구도 충분한 서비스 결과다.'),
 points('Agent가 필요한 지점',['고정된 계산과 생성은 코드','자료 탐색과 수정 제안은 AI','필요한 도구 선택·반복·확인을 묶는 작업 흐름'],'단순 템플릿 채우기를 자율 Agent라고 과장하지 않는다. Codex/Claude Code가 정책과 파일을 읽고 도구를 선택하여 수정·테스트를 반복하는 부분을 구분한다.'),
 table('완성 패키지',['파일','다른 사용자가 이해할 내용'],[['README.md','시작 명령·입력·결과'],['requirements / package','설치할 라이브러리'],['sample + code','안전한 연습 데이터와 구현'],['tests','지켜야 할 정상·오류 규칙'],['improvement.md','수정 전후와 남은 제한']],'README를 지저분한 파일 목록이 아니라 학생이 실제로 실행할 경로로 작성한다. private 데이터나 .env는 패키지에 넣지 않는다.'),
 code('필수 검증 실행','python -m pytest -q \\\n  tests/test_day4_pr_review_lab.py \\\n  tests/test_day4_excel_lab.py \\\n  tests/test_day4_document_lab.py',['네트워크·유료 API 없는 기본 검증','학생 수정 코드는 해당 실습 폴더에서 별도 검사'],'전체 예제의 테스트와 학생이 수정한 checkout 테스트를 구분한다. 초록색 숫자만 보고 어떤 코드가 검증됐는지 잊지 않도록 한다.'),
 image('Notebook의 결과 파일','assets/components/day4/notebook-results.png','한 번의 실제 실행에서 생성한 파일 목록 · 로컬 HTML','HTML의 파일 링크가 실제 생성한 XLSX·DOCX·PPTX를 가리키는지 확인한다. 원격 게시나 배포 웹서비스가 아니라 로컬 결과 탐색 화면이다.'),
 table('다음 주 3시간 제작',['시간','개인 작업','작업 범위'],[['15:00–15:20','문제·입력·완료 기준','기능 하나 선택'],['15:20–16:00','기본 기능 구현','샘플로 실제 실행'],['16:00–16:40','오류·테스트·개선','수정 전후 비교'],['16:40–17:10','화면·파일·사용 안내','다른 사람이 실행'],['17:10–17:30','패키지·개선 기록','미완료와 한계 구분'],['17:30–18:00','쉬는 시간·Q&A','선택 공유·실습 복구']],'150분 실제 제작 +30분 휴식/Q&A다. 발표는 의무가 아니다. 남은 시간을 모두 개발 시간이라고 안내하지 않는다.'),
 table('개인 프로젝트 선택',['주제','최소 기능','확인할 개선'],[['WBS 도우미','날짜·상태·간트','공휴일·선행 업무'],['채점 도구','점수·오류·통계','배점·입력 검증'],['이력서 편집기','사실 기반 DOCX','문장 비교·과장 검사'],['PR 리뷰 작업대','diff·테스트·리뷰','근거·중복·버전'],['보고서 생성기','같은 데이터의 PPT','수치 일치·긴 문장']],'프로젝트를 선택했다고 여러 파일 형식을 모두 구현할 필요는 없다. 3시간에는 입력 한 종류, 결과 한 종류, 오류 두 가지 정도로 범위를 좁힌다.'),
 task('개인 과제의 범위',['다음 주 만들고 싶은 도구 하나 선택','사용자·입력·결과를 README에 작성','정상 사례 1개·실패 사례 2개 정의'],'materials/day5/미니프로젝트_사전안내.md','무엇이 실행되면 완료인지 명확한 문장','이 활동은 Ideation과 문서 작성이다. 코드 실습과 구분하여 안내하고 이어지는 테스트/함수 작성이 실제 구현 시간이다.'),
 prompt('ChatGPT·Claude의 제작 요청','나는 비개발자 동료에게 쓸 수 있는 [도구]를 선물하려고 해. 입력은 [샘플 파일], 결과는 [형식]이야. 먼저 흐름과 완료 기준을 설명하고, 한 기능씩 구현·실행·오류 테스트를 진행해 줘. 외부 배포와 원본 덮어쓰기는 내 확인 전 금지야.','업무 흐름 · 실행 방법 · 실패 대응','대괄호를 구체적으로 채운다. 일반 대화에서는 파일을 첨부하고 로컬 프로젝트에서는 허용 폴더를 지정한다. 양쪽의 파일 접근 방식은 다르다.','demo'),
 task('개선 기능의 첫 구현',['이번 코드에서 작은 기능 한 가지 선택','Codex에 함수·테스트의 수정 계획 요청','코드를 수정하고 해당 테스트 실행'],'내 개인 연습 폴더','실제 변경 diff와 실행 결과','여기부터 소프트웨어 제작 실습이다. 시간이 짧으면 README만 완성했다고 개발 완료로 기록하지 않고 구현 예정 상태로 남긴다.'),
 task('실행 안내의 검증',['README의 명령을 그대로 복사','새 출력 폴더에 결과 생성','다른 파일을 덮지 않는지 확인'],'README.md + 새 출력 폴더','설명 없이 명령만으로 재실행 가능','학생 자신이 5분 뒤 다시 읽어도 이해할 수 있는 안내를 목표로 한다. 타인의 기기에 실제 배포한 것처럼 표현하지 않는다.'),
 table('개선 기록',['항목','작성 내용'],[['Before','기존의 불편과 재현 입력'],['Change','바꾼 함수·수식·문장'],['Evidence','테스트 출력·결과 화면'],['After','확인한 변화'],['Limit','아직 못한 일과 사용 조건']],'성공을 선언하는 홍보 문서가 아니라 검증 가능한 작은 변화의 기록이다. 시간 절감 수치를 측정하지 않았으면 예상과 측정을 분리한다.'),
 check('하루의 최종 확인',[['PR','코드 수정·테스트·게시 미리보기'],['Excel','입력 변경·재계산·오류 복구'],['Word·PPT','실제 파일 생성·내용·화면 확인'],['다음 주','한 기능의 개인 과제와 테스트 초안']],'마지막 정리 한 번만 한다. 완료하지 못한 작업은 실패가 아니라 복구 경로와 함께 기록한다. 17:30부터 휴식·질문으로 전환한다.'),
 ref(table('작은 도구의 운영',['상황','다음 개선'],[['입력 형식 변경','버전 표시·변환 함수'],['다른 PC에서 실패','설치·폰트·경로 검사'],['반복 오류','에러 코드·재현 샘플'],['여러 명 사용','권한·동시 실행·개인정보'],['배포 요청','사람 확인·되돌리기 방법']],'오늘의 코드가 곧바로 기업 운영 수준이라고 표현하지 않는다. 운영 요구가 추가되면 별도 설계가 필요하다.')),
 ref(points('추가 학습 경로',['GitHub: 테스트와 리뷰의 자동 실행','Google Sheets: 수식·Apps Script·입력 검증','문서 도구: 구조·스타일·렌더 검증'],'공식 출처와 제공 코드를 학습 경로로 연결한다. 사이트 방문 자체를 실습 완료로 세지 않는다.')),
],
];

// Slide-specific crops enlarge real evidence, without replacing or editing its source.
insertLessonAdditions(LESSONS, [...PR_WALKTHROUGH, ...OFFICE_WALKTHROUGH, ...PROJECT_ENRICHMENT]);
for(const title of ['내 채점표의 Google Sheets 사본','조건부서식 메뉴와 시험 입력']) {
 const slide=LESSONS[4].find(item=>item.title===title);
 slide.reference=true;
 slide.activityLabel='선택 파일 작업 · Google Sheets';
}
OPENING[4].explain=['materials/day4/day4_pr_document_automation.ipynb','추가 코드는 해당 차시에 새 코드 셀로 실행'];
LESSONS[0].find(item=>item.title==='실습 파일의 역할').options={widths:[370,390,392]};
LESSONS[1].find(item=>item.title==='pytest 메시지의 구분').options={widths:[370,390,392]};
const referenceTestIndex=LESSONS[2].findIndex(item=>item.title==='참고 구현의 테스트 결과');
LESSONS[2][referenceTestIndex]=code('참고 구현의 테스트 결과',
 'reference_check = check_exercise(ROOT, RUN / "pr/reference-only")\nprint(reference_check["output"])\n# 실제 참고 구현 검증: 5 passed',
 ['내 작업 폴더가 아닌 별도 참고 구현의 결과','Notebook의 참고 구현 준비 셀 실행 후 비교'],
 '화면 캡처에서 작게 보이던 실제 테스트 결과를 편집 가능한 텍스트로 표시한다. 결과는 실제 실행 Notebook의 별도 참고 구현 5 passed에 근거한다. 학생 자신의 checkout.py가 통과한 것과 구분한다. 참고 구현 준비가 선행되어야 이 경로에 테스트 파일이 있다.','demo');
const dependencyTask=LESSONS[3].find(item=>item.title==='선행 일정의 오류');
dependencyTask.steps=['Python 복사본에서 W04 시작일을 2026-09-18로 변경','validate_wbs(broken_tasks)로 선행 일정 충돌 확인','Excel 복사본 D12도 09/18로 바꾸고 J12 확인','두 입력을 각각 복구하고 다시 확인'];
dependencyTask.check='Excel 수정과 Python 변수 수정은 자동 연동되지 않음';
dependencyTask.note='broken_tasks=deepcopy(tasks)로 시작한 뒤 W04의 start를 바꾼다. 제공 기본 목록에서 W04는 [3] 위치다. 예: broken_tasks[3]["start"]="2026-09-18". validate_wbs로 PREDECESSOR_DATE_CONFLICT 확인. Excel 복사본에서는 D12를 같은 날짜로 바꿔 J12를 확인한다. 두 입력은 별개이므로 각각 원래 날짜 2026-09-21로 복구한다.';
LESSONS[7].find(item=>item.title==='입력 파일의 세 가지 상태').options={widths:[380,420,352]};
const requestIndex=LESSONS[7].findIndex(item=>item.title==='ChatGPT·Claude의 제작 요청');
LESSONS[7][requestIndex]=table('계획과 구현 결과의 구분',['대화 응답','아직 확인할 것','다음 요청'],[
 ['구현 계획만 제시','실제 코드 변경 여부','계획한 함수의 코드 작성'],
 ['코드 블록 제시','저장 위치·호출 방법','파일 저장과 실행 명령'],
 ['테스트 통과 주장','실제 명령과 출력','정상·오류 결과 제시'],
 ['CSV 생성 완료','파일 내용·열 구조','직접 열어 입력과 대조'],
],'바로 앞의 구체적인 제작 요청 이후 어떤 응답이 왔는지 구분한다. 계획 설명이나 코드 블록만으로 PC에 파일이 생긴 것은 아니다. 실행 권한이 없는 대화 환경에서는 학생이 파일을 저장하고 명령을 실행한다. 이미 실행된 기능을 다시 개발시키지 않고 부족한 다음 단계만 요청한다.','demo');
const projectOverview=LESSONS[7].find(slide=>slide.title==='개인 프로젝트 선택');
projectOverview.title='제공 코드의 프로젝트 출발점';
projectOverview.note='이 다섯 가지는 제공 코드로 시작하기 쉬운 예시다. 선택은 제한되지 않는다. 뒤의 9분야·36개 제안 또는 자신의 반복 업무를 선택할 수 있다. 기본 코드, 응용, 새 구현 범위를 구분한다. 3시간에는 입력 한 종류, 결과 한 종류, 오류 두 가지 정도로 범위를 좁힌다.';
OPENING[2].headers[0]='수업 시간\n(쉬는 시간)';
OPENING[2].options={headerH:84,widths:[320,240,592]};
const evidenceLayout={
 'PR 리뷰 작업대':{crop:{left:64,top:462,width:715,height:175},caption:'합성 PR의 함수 변경 확대 · 로컬 화면 · GitHub 게시 없음'},
 '실제 Codex 리뷰 응답':{crop:{left:78,top:252,width:1095,height:390},caption:'실제 CLI 응답 일부 확대 · Desktop 대화 UI 아님'},
 '참고 구현의 테스트 결과':{crop:{left:84,top:629,width:635,height:59},caption:'실행 Notebook의 출력 확대 · 별도 참고 구현 5 passed'},
 '입력 열과 계산 열':{asset:'outputs/day4-document-automation/wbs_inputs_zoom.png',caption:'입력 A:F 확대 · 전체 파일의 계산 H:K · 간트 L:AM'},
 '총점과 보류 상태':{asset:'outputs/day4-document-automation/exam_status_zoom.png',headerAsset:'outputs/day4-document-automation/exam_status_header.png',caption:'합성 학생 24–28번 · 총점·등수·미응답·입력 오류 비교'},
 'Word 이력서 개선 전':{crop:{left:110,top:105,width:1190,height:450},caption:'개선 전 상단 확대 · 같은 경력 사실의 긴 문장·중복 표현'},
 'Word 이력서 개선 후':{crop:{left:110,top:105,width:1190,height:430},caption:'개선 후 상단 확대 · 전체 내용은 편집 가능한 DOCX 제공'},
 'Notebook의 결과 파일':{crop:{left:185,top:246,width:600,height:330},caption:'생성 파일 목록 일부 확대 · 전체 결과는 index.html에서 확인'},
 '일정 데이터와 간트 차트':{crop:{left:0,top:80,width:1275,height:460},caption:'9/14~9/28 구간 확대 · 첫 8개 업무 · 전체 일정은 XLSX'},
 '40문항 자동 채점':{crop:{left:0,top:394,width:1316,height:360},caption:'합성 응답 일부 확대 · 정답행과 1~8번 답안 · 실제 성적 미포함'},
};
for(const lesson of LESSONS)for(const slide of lesson)if(evidenceLayout[slide.title])Object.assign(slide,evidenceLayout[slide.title]);
LESSONS[7].find(slide=>slide.title==='개인 과제의 범위').activityLabel='Ideation · 작업 정의';

export const SOURCES={
 github:'https://docs.github.com/en/actions/reference/security/secure-use',
 reviews:'https://docs.github.com/en/rest/pulls/reviews',
 codex:'https://learn.chatgpt.com/docs/projects',
 claude:'https://code.claude.com/docs/en/desktop',
 claudeFiles:'https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude',
 networkdays:'https://support.microsoft.com/en-us/excel/functions/networkdays-function',
 formatting:'https://support.microsoft.com/en-us/excel/use-conditional-formatting-to-highlight-information-in-excel',
 sheets:'https://support.google.com/docs/answer/78413?hl=ko',
 appsScript:'https://developers.google.com/apps-script/reference/spreadsheet/conditional-format-rule-builder',
};
