"""R-4.6、R-4.11、R-5.2：優惠券與免運門檻上下邊界。"""

from __future__ import annotations

import pytest

from tests.api.helpers.client import MiniMartApiClient
from tests.api.helpers.pricing import assert_preview_amounts, assert_pricing_order

COUPON_PCT15 = "PCT15"
COUPON_SAVE100 = "SAVE100"
COUPON_FREESHIP = "FREESHIP"


def _tee_subtotal(api: MiniMartApiClient) -> int:
    """純棉素色 T 恤單價（用於門檻邊界）。"""
    return api.product_by_name("純棉素色 T 恤")["unitPrice"]


@pytest.mark.xfail(reason="已知缺陷 D-08：小計恰等於門檻時 PCT15 未生效", strict=True)
def test_PCT15_小計恰等於門檻_800_可折抵(authed_api: MiniMartApiClient) -> None:
    """R-4.6：小計 = 800 時 PCT15 應生效。"""
    unit = _tee_subtotal(authed_api)
    threshold = 800
    if unit == 0 or threshold % unit != 0:
        pytest.skip(f"T 恤單價 {unit} 無法湊出門檻 {threshold}")
    qty = threshold // unit
    product = authed_api.product_by_name("純棉素色 T 恤")
    authed_api.add_to_cart(product["id"], qty)
    preview = authed_api.checkout_preview(COUPON_PCT15)
    assert preview["subtotal"] == threshold
    assert preview["couponDiscount"] > 0


def test_PCT15_小計低於門檻_799_視同無券(authed_api: MiniMartApiClient) -> None:
    """R-4.11：未達門檻時靜默忽略，couponDiscount = 0。"""
    unit = _tee_subtotal(authed_api)
    threshold = 800
    if unit == 0:
        pytest.skip("無法取得 T 恤單價")
    qty = (threshold - 1) // unit
    if qty < 1:
        pytest.skip("單價過高，無法湊出 799 小計")
    product = authed_api.product_by_name("純棉素色 T 恤")
    authed_api.add_to_cart(product["id"], qty)
    preview = authed_api.checkout_preview(COUPON_PCT15)
    assert preview["subtotal"] <= threshold - 1
    assert preview["couponDiscount"] == 0


def test_SAVE100_滿千門檻邊界(authed_api: MiniMartApiClient) -> None:
    """R-4.6：滿千折百券在 999 無折、1000 有折。"""
    mug = authed_api.product_by_name("手沖咖啡濾杯")
    unit = mug["unitPrice"]
    below_qty = 999 // unit
    at_qty = 1000 // unit
    if below_qty < 1 or at_qty < 1 or below_qty == at_qty:
        pytest.skip(f"濾杯單價 {unit} 不適合門檻邊界測試")

    authed_api.add_to_cart(mug["id"], below_qty)
    below = authed_api.checkout_preview(COUPON_SAVE100)
    assert below["couponDiscount"] == 0

    authed_api.clear_cart()
    authed_api.add_to_cart(mug["id"], at_qty)
    at_threshold = authed_api.checkout_preview(COUPON_SAVE100)
    assert at_threshold["subtotal"] >= 1000
    assert at_threshold["couponDiscount"] == 100


def test_免運券不論金額運費為零(authed_api: MiniMartApiClient) -> None:
    """R-5.2：低金額訂單使用免運券，運費 NT$0。"""
    coupons = authed_api.get_coupons()
    free_coupon = next((c for c in coupons if c["code"] == COUPON_FREESHIP), None)
    if not free_coupon or free_coupon["status"] != "未使用":
        pytest.skip("免運券不可用")

    mug = authed_api.product_by_name("手沖咖啡濾杯")
    authed_api.add_to_cart(mug["id"], 1)
    preview = authed_api.checkout_preview(COUPON_FREESHIP)
    assert preview["shipping"] == 0
    assert_preview_amounts(
        preview,
        subtotal=mug["unitPrice"],
        bulk_discount=0,
        coupon_discount=0,
        shipping=0,
        payable=mug["unitPrice"],
    )
    assert_pricing_order(preview, free_shipping_coupon=True)


def test_無效券碼靜默忽略(authed_api: MiniMartApiClient) -> None:
    """R-4.10-4.11：不存在券碼不報錯，金額與無券相同。"""
    mug = authed_api.product_by_name("手沖咖啡濾杯")
    authed_api.add_to_cart(mug["id"], 1)
    baseline = authed_api.checkout_preview()
    with_coupon = authed_api.checkout_preview("NOT_A_REAL_CODE")
    assert with_coupon == baseline
