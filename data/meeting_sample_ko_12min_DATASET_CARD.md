# Synthetic K-Work Meeting 001

## 용도

한국어 회의 기반 STT·Prompt Engineering·LLM 구조화 출력·Tool Calling·LangGraph 사람 승인·LangSmith 평가를 하나의 사례로 연결하기 위한 교육용 합성 데이터다.

## 파일

- meeting_sample_ko_12min.txt: 화자와 타임스탬프가 포함된 상세 transcript
- meeting_sample_ko_12min.wav: 로컬 TTS로 생성하는 비식별 회의 음성
- meeting_sample_ko_12min_expected.json: 결정·Action Item·근거·승인 정책의 기준 결과

## 생성 원칙

- 실제 회사·고객·회의를 복제하지 않은 완전 합성 사례
- 실명 대신 가상 이름과 역할 사용
- 전화번호·이메일·주문번호·계약 금액 등 개인정보와 영업 비밀 없음
- 정상 정보와 함께 상대 날짜, 정정 발언, 근거 누락 위험, 승인 조건을 포함

## 학습 포인트

- 마지막 발언만 읽지 않고 정정 전후 evidence를 연결한다.
- “다음 주 중”을 임의 날짜로 바꾸지 않고 null과 needs_review로 남긴다.
- Prompt에 역할·입력·출력 schema·금지 행동·근거 요구를 넣는다.
- Codex/LLM의 결과는 CI·Golden Dataset·사람 검토로 확인한다.

## 제한

- 합성 음성은 실제 다자간 회의의 겹침 발화, 잡음, 억양을 완전히 재현하지 않는다.
- TTS 음성은 STT 파이프라인 연결을 확인하는 데 사용하고, 실제 환경 성능을 주장하는 자료로 쓰지 않는다.
- expected JSON은 유일한 문장 정답이 아니라 필수 사실과 정책의 기준선이다.
