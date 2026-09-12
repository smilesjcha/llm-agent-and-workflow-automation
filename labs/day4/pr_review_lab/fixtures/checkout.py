"""수강생이 직접 수정하는 합성 쇼핑몰 결제 코드. 고객 데이터 없음."""


def checkout_total(price: int, quantity: int, coupon: int = 0) -> int:
    """상품 가격 × 수량 - 쿠폰. 잘못된 입력과 초과 쿠폰을 확인하세요."""
    return price * quantity - coupon
