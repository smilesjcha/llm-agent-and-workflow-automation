"""실습 후 비교할 참고 구현. pytest 결과와 diff를 먼저 확인합니다."""


def checkout_total(price: int, quantity: int, coupon: int = 0) -> int:
    """음수 입력 및 수량 0을 거부하고, 쿠폰 할인 후 결제액을 0 이상으로 제한."""
    if price < 0 or quantity < 1 or coupon < 0:
        raise ValueError("INVALID_CHECKOUT_INPUT")
    return max(0, price * quantity - coupon)
