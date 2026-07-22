"""R-5.1：運費依折扣後商品金額級距（含邊界與「依折扣後而非小計」）。"""

from __future__ import annotations

import pytest

from tests.api.helpers.client import MiniMartApiClient
from tests.api.helpers.coupons import require_unused_coupon
from tests.api.helpers.pricing import assert_pricing_order, shipping_for_after_discount

COUPON_PCT15 = "PCT15"
COUPON_NEWBIE20 = "NEWBIE20"


@pytest.mark.parametrize(
    "product_name,qty,expected_shipping",
    [
        ("純棉素色 T 恤", 1, 80),  # 400 → <500
        ("手沖咖啡濾杯", 1, 80),  # 480 → <500
        ("不鏽鋼保溫瓶", 1, 60),  # 690 → ≥500、<1000
        ("手沖咖啡濾杯", 2, 60),  # 960 → ≥500、<1000
        ("折疊露營椅", 1, 30),  # 1020 → ≥1000、<2000
        ("極簡皮革錢包", 1, 30),  # 1280 → ≥1000、<2000
        ("機械式鍵盤", 1, 0),  # 3180−159=3021 → ≥2000
    ],
)
def test_運費級距依折扣後金額(
    authed_api: MiniMartApiClient,
    product_name: str,
    qty: int,
    expected_shipping: int,
) -> None:
    """R-5.1：各級距代表商品組合的運費。"""
    product = authed_api.product_by_name(product_name)
    if product["stock"] < qty:
        pytest.skip(f"{product_name} 庫存不足（需 {qty}）")
    authed_api.add_to_cart(product["id"], qty)
    preview = authed_api.checkout_preview()
    assert_pricing_order(preview)
    assert preview["shipping"] == expected_shipping


def test_運費依折扣後金額非商品小計(authed_api: MiniMartApiClient) -> None:
    """R-5.1：小計可 ≥2000，但折扣後 <2000 時運費不應免運。

    無線藍牙耳機小計 2,150（達免運門檻），套 PCT15 後折扣後約 1,719，
    應落在 NT$1,000～未滿 2,000 → 運費 NT$30。
    """
    require_unused_coupon(authed_api, COUPON_PCT15)
    product = authed_api.product_by_name("無線藍牙耳機")
    authed_api.add_to_cart(product["id"], 1)

    without = authed_api.checkout_preview()
    assert without["subtotal"] >= 2000
    assert without["shipping"] == 0

    with_coupon = authed_api.checkout_preview(COUPON_PCT15)
    after = (
        with_coupon["subtotal"]
        - with_coupon["bulkDiscount"]
        - with_coupon["couponDiscount"]
    )
    assert after < 2000, f"預期折扣後未滿 2000 以驗證級距，實際 {after}"
    assert with_coupon["shipping"] == shipping_for_after_discount(after)
    assert with_coupon["shipping"] == 30
    assert_pricing_order(with_coupon)


def test_小計未滿500套小額券後運費仍為80(authed_api: MiniMartApiClient) -> None:
    """R-5.1：折扣後仍 <500 時運費維持 NT$80。"""
    require_unused_coupon(authed_api, COUPON_NEWBIE20)
    product = authed_api.product_by_name("純棉素色 T 恤")
    authed_api.add_to_cart(product["id"], 1)
    preview = authed_api.checkout_preview(COUPON_NEWBIE20)
    after = preview["subtotal"] - preview["bulkDiscount"] - preview["couponDiscount"]
    assert after < 500
    assert preview["shipping"] == 80
    assert_pricing_order(preview)
