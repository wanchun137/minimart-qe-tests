"""R-4.15：結帳 preview 完整計價順序（openapi postCheckoutPreview）。"""

from __future__ import annotations

from tests.api.helpers.client import MiniMartApiClient
from tests.api.helpers.coupons import require_unused_coupon
from tests.api.helpers.pricing import assert_preview_amounts, assert_pricing_order

COUPON_SAVE300 = "SAVE300"
COUPON_PCT15 = "PCT15"
COUPON_FREESHIP = "FREESHIP"


def test_咖啡濾杯兩件_PRD_範例_1(authed_api: MiniMartApiClient) -> None:
    """R-5.6 範例 1：小計 960、運費 60、應付 1,020。"""
    product = authed_api.product_by_name("手沖咖啡濾杯")
    authed_api.add_to_cart(product["id"], 2)
    preview = authed_api.checkout_preview()
    assert_pricing_order(preview)
    assert_preview_amounts(
        preview,
        subtotal=960,
        bulk_discount=0,
        coupon_discount=0,
        shipping=60,
        payable=1020,
    )


def test_機械式鍵盤_PRD_範例_2_滿額折扣與免運(authed_api: MiniMartApiClient) -> None:
    """R-4.2、R-5.6 範例 2：小計 3,180、滿額 −159、運費 0、應付 3,021。"""
    product = authed_api.product_by_name("機械式鍵盤")
    authed_api.add_to_cart(product["id"], 1)
    preview = authed_api.checkout_preview()
    assert_pricing_order(preview)
    assert_preview_amounts(
        preview,
        subtotal=3180,
        bulk_discount=159,
        coupon_discount=0,
        shipping=0,
        payable=3021,
    )


def test_機械式鍵盤加滿三千折三百券_PRD_範例_3(authed_api: MiniMartApiClient) -> None:
    """R-4.8、R-5.6 範例 3：滿額 −159、券折 300、應付 2,721。"""
    require_unused_coupon(authed_api, COUPON_SAVE300)
    product = authed_api.product_by_name("機械式鍵盤")
    authed_api.add_to_cart(product["id"], 1)
    preview = authed_api.checkout_preview(COUPON_SAVE300)
    assert_pricing_order(preview)
    assert_preview_amounts(
        preview,
        subtotal=3180,
        bulk_discount=159,
        coupon_discount=300,
        shipping=0,
        payable=2721,
    )


def test_藍牙耳機_PRD_範例_4_百分比四捨五入(authed_api: MiniMartApiClient) -> None:
    """R-2.3、R-5.6 範例 4：2,150 × 5% = 108，應付 2,042。"""
    product = authed_api.product_by_name("無線藍牙耳機")
    authed_api.add_to_cart(product["id"], 1)
    preview = authed_api.checkout_preview()
    assert_pricing_order(preview)
    assert_preview_amounts(
        preview,
        subtotal=2150,
        bulk_discount=108,
        coupon_discount=0,
        shipping=0,
        payable=2042,
    )


def test_七步計價順序恆等式成立(authed_api: MiniMartApiClient) -> None:
    """R-4.15／R-2.6／R-5.1：多種組合下七步重算（含折扣上限與運費級距）成立。"""
    keyboard = authed_api.product_by_name("機械式鍵盤")
    mug = authed_api.product_by_name("手沖咖啡濾杯")
    scenarios = [
        (mug["id"], 1, None, False),
        (mug["id"], 2, None, False),
        (keyboard["id"], 1, None, False),
        (keyboard["id"], 1, COUPON_SAVE300, False),
        (mug["id"], 1, COUPON_FREESHIP, True),
    ]
    for product_id, qty, coupon, free_ship in scenarios:
        authed_api.clear_cart()
        authed_api.add_to_cart(product_id, qty)
        preview = authed_api.checkout_preview(coupon)
        assert_pricing_order(preview, free_shipping_coupon=free_ship)


def test_折扣總額不超過小計_折扣後不為負(authed_api: MiniMartApiClient) -> None:
    """R-2.6：滿額＋券折合計不得使折扣後商品金額為負。"""
    require_unused_coupon(authed_api, COUPON_SAVE300)
    product = authed_api.product_by_name("機械式鍵盤")
    authed_api.add_to_cart(product["id"], 1)
    preview = authed_api.checkout_preview(COUPON_SAVE300)
    discount_total = preview["bulkDiscount"] + preview["couponDiscount"]
    assert discount_total <= preview["subtotal"]
    assert preview["payable"] - preview["shipping"] >= 0
    assert_pricing_order(preview)
