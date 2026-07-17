"""UI 與 API 結果交叉驗證（辨識前後端不一致）。"""

from __future__ import annotations

from playwright.sync_api import Page

from tests.api.helpers.pricing import assert_preview_amounts
from tests.helpers.auth import login
from tests.helpers.cart import add_product_with_quantity, clear_cart
from tests.helpers.checkout import (
    expect_summary_matches_preview,
    fetch_checkout_preview,
    fill_and_submit_checkout,
    go_to_checkout,
)


def test_結帳頁金額與_preview_API_一致(page: Page) -> None:
    """R-12.5：同一 session 下 UI 摘要與 checkout preview API 完全相同。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "手沖咖啡濾杯", 2)
    go_to_checkout(page)
    ui_preview = expect_summary_matches_preview(page)
    api_preview = fetch_checkout_preview(page)
    assert ui_preview == api_preview


def test_下單後訂單詳情金額快照與_preview_一致(page: Page) -> None:
    """R-14.4：訂單詳情金額應等於下單前 preview（機械式鍵盤 PRD 範例 2）。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "機械式鍵盤", 1)
    go_to_checkout(page)
    preview = expect_summary_matches_preview(page)
    assert_preview_amounts(
        preview,
        subtotal=3180,
        bulk_discount=159,
        coupon_discount=0,
        shipping=0,
        payable=3021,
    )

    order_id = fill_and_submit_checkout(page, name="交叉驗證")
    response = page.request.get(f"/api/orders/{order_id}")
    assert response.ok, f"訂單詳情失敗：{response.status} {response.text()}"
    detail = response.json()
    assert detail["subtotal"] == preview["subtotal"]
    assert detail["bulkDiscount"] == preview["bulkDiscount"]
    assert detail["couponDiscount"] == preview["couponDiscount"]
    assert detail["shipping"] == preview["shipping"]
    assert detail["payable"] == preview["payable"]
