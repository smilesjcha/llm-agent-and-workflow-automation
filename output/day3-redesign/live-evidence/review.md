# 쿠폰 결제 서비스 코드 리뷰

- 실제 사용 Provider: codex_cli
- 모델 선택: codex-default
- 테스트: FAILED · exit code 1
- 대체 실행 사유: 없음

## [P1] 쿠폰 할인액을 상품 금액으로 제한해야 합니다

`checkout.py:5` · `coupon-cap`

- 재현 조건과 영향: 상품 금액보다 큰 쿠폰을 입력하면 할인 후 금액이 음수가 됩니다. 예를 들어 `payable(10_000, 15_000)`이 요구값 0이 아니라 -5,000을 반환합니다.
- 코드 근거: `return total_won - coupon_won`
- 수정 제안: 실제 할인액을 `min(total_won, coupon_won)`으로 제한하고 상품 금액에서 그 값만 차감합니다.

## [P1] 금액 형식과 음수 입력을 검증해야 합니다

`checkout.py:5` · `money-validation`

- 재현 조건과 영향: 음수, 소수, bool 금액이 그대로 계산되어 정책상 유효하지 않은 주문 금액과 영수증이 생성됩니다.
- 코드 근거: `return total_won - coupon_won`
- 수정 제안: 두 인자 모두 bool이 아닌 int인지 먼저 확인해 아니면 `MONEY_INTEGER_REQUIRED`로 거절하고, 0 미만이면 `MONEY_NON_NEGATIVE_REQUIRED`로 거절한 뒤 계산합니다.

## [P1] 배송비 기준에 할인 후 금액을 사용해야 합니다

`checkout.py:10` · `shipping-after-discount`

- 재현 조건과 영향: 할인 전 금액이 50,000원 이상이지만 할인 후에는 미만인 주문에 배송비가 누락됩니다. 예를 들어 50,000원에 10,000원 쿠폰을 적용하면 배송비 3,000원과 최종액 43,000원이어야 하지만 무료 배송으로 계산됩니다.
- 코드 근거: `shipping = 0 if total_won >= 50_000 else 3_000`
- 수정 제안: 검증 및 쿠폰 상한 적용을 마친 할인 후 상품 금액을 기준으로 `50_000` 이상일 때만 배송비를 0으로 설정합니다.

## [P2] 영수증에 요청 쿠폰액이 아닌 실제 할인액을 기록해야 합니다

`checkout.py:13` · `receipt-applied-discount`

- 재현 조건과 영향: 상품 금액보다 큰 쿠폰을 입력하면 실제 적용 가능한 할인보다 큰 금액이 영수증에 표시됩니다. 10,000원 상품과 15,000원 쿠폰에서는 10,000원이 기록되어야 하지만 15,000원이 기록됩니다.
- 코드 근거: `"coupon_applied_won": coupon_won,`
- 수정 제안: 상품 금액으로 제한한 실제 할인액을 별도 변수로 계산하고 `coupon_applied_won`에 그 값을 반환합니다.

## 다음 작업

리뷰 중 수정할 항목을 선택하고 starter/checkout.py를 수정한 뒤 같은 테스트를 다시 실행합니다.
