"""쿠폰과 할인 후 상품 금액을 기준으로 결제 예정액을 계산한다."""


def _validate_money(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("MONEY_INTEGER_REQUIRED")
    if value < 0:
        raise ValueError("MONEY_NON_NEGATIVE_REQUIRED")


def payable(total_won: int, coupon_won: int) -> int:
    _validate_money(total_won)
    _validate_money(coupon_won)
    return total_won - min(total_won, coupon_won)


def calculate_checkout(total_won: int, coupon_won: int) -> dict[str, int]:
    payment = payable(total_won, coupon_won)
    coupon_applied = total_won - payment
    shipping = 0 if payment >= 50_000 else 3_000
    return {
        "total_won": total_won,
        "coupon_applied_won": coupon_applied,
        "shipping_won": shipping,
        "payable_won": payment + shipping,
    }
