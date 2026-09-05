"""동일한 검증을 초안과 수정본에 실행하는 실제 unittest."""

import unittest

from checkout import calculate_checkout, payable


class CheckoutTests(unittest.TestCase):
    def test_normal_coupon(self):
        self.assertEqual(payable(30_000, 5_000), 25_000)

    def test_coupon_larger_than_total_is_capped(self):
        self.assertEqual(payable(10_000, 15_000), 0)

    def test_negative_total_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "MONEY_NON_NEGATIVE_REQUIRED"):
            payable(-100, 0)

    def test_negative_coupon_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "MONEY_NON_NEGATIVE_REQUIRED"):
            payable(10_000, -100)

    def test_fractional_won_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "MONEY_INTEGER_REQUIRED"):
            payable(10_000.5, 100)

    def test_bool_is_not_money(self):
        with self.assertRaisesRegex(ValueError, "MONEY_INTEGER_REQUIRED"):
            payable(True, 0)

    def test_shipping_uses_discounted_amount(self):
        result = calculate_checkout(50_000, 10_000)
        self.assertEqual(result["shipping_won"], 3_000)
        self.assertEqual(result["payable_won"], 43_000)

    def test_free_shipping_at_threshold(self):
        self.assertEqual(calculate_checkout(55_000, 5_000)["shipping_won"], 0)

    def test_receipt_records_applied_discount(self):
        result = calculate_checkout(10_000, 15_000)
        self.assertEqual(result["coupon_applied_won"], 10_000)
        self.assertEqual(result["payable_won"], 3_000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
