[checkout.py](<WORKSPACE>/output/day3-redesign/codex-authoring-demo/starter/checkout.py)를 수정했습니다. 테스트 파일과 조건은 변경하지 않았습니다.

수정한 로직:

- 음수 금액은 `MONEY_NON_NEGATIVE_REQUIRED`로 거절
- 소수와 `bool`은 `MONEY_INTEGER_REQUIRED`로 거절
- 쿠폰 할인액을 상품 금액까지만 적용
- 할인 후 상품 금액을 기준으로 배송비 결정
- 영수증에 요청액이 아닌 실제 적용 할인액 기록

실행 결과:

- `python checkout_checks.py`
  - 환경에 `python` 명령이 없어 `command not found`
- `python3 checkout_checks.py` 수정 전
  - 9개 중 7개 실패
- `python3 checkout_checks.py` 수정 후
  - `Ran 9 tests`
  - 전체 통과: `OK`

수정 전후 사례:

- 상품 10,000원, 쿠폰 15,000원
  - 수정 전: 상품 결제액 -5,000원, 할인액 15,000원
  - 수정 후: 실제 할인 10,000원, 배송비 3,000원, 최종 3,000원
- 상품 50,000원, 쿠폰 10,000원
  - 수정 전: 할인 전 금액 기준으로 무료 배송
  - 수정 후: 할인 후 40,000원 기준 배송비 3,000원, 최종 43,000원
- `-100`, `10_000.5`, `True`
  - 수정 전: 유효 금액으로 처리
  - 수정 후: 요구된 오류 코드로 거절