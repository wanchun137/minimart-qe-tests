"""R-3.5、R-3.7：下單扣庫存；取消／退款後回補（對應 D-09～D-11）。"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout
from tests.helpers.orders import (
    apply_return,
    cancel_order,
    confirm_receipt,
    open_order,
    seller_review,
    ship_order,
)
from tests.helpers.products import (
    parse_remaining_stock,
    product_stock_text_on_list,
    product_stock_via_api,
)

# 純棉素色 T 恤：初始庫存較高，適合 before/after
PRODUCT_NAME = "純棉素色 T 恤"
PRODUCT_ID = 5


def test_下單後商品列表庫存應立即減少(page: Page) -> None:
    """R-3.5／R-12.9：訂單成立後庫存減去購買數量（UI 重新載入可見）。"""
    login(page)
    clear_cart(page)
    before_api = product_stock_via_api(page, PRODUCT_ID)
    before_ui = parse_remaining_stock(product_stock_text_on_list(page, PRODUCT_NAME))
    assert before_ui == before_api, f"UI/API 庫存不一致：UI={before_ui} API={before_api}"

    add_product_from_list(page, PRODUCT_NAME)
    go_to_checkout(page)
    fill_and_submit_checkout(page, name="庫存扣減測試")

    after_api = product_stock_via_api(page, PRODUCT_ID)
    after_ui = parse_remaining_stock(product_stock_text_on_list(page, PRODUCT_NAME))
    assert after_api == before_api - 1, (
        f"API 庫存未扣減：下單前 {before_api}，下單後 {after_api}"
    )
    assert after_ui == before_ui - 1, (
        f"UI 庫存未扣減：下單前 {before_ui}，下單後 {after_ui}"
    )
    expect(page.locator(".product-card", has_text=PRODUCT_NAME)).to_contain_text(
        re.compile(rf"剩餘\s*{before_ui - 1}\s*件")
    )


def test_取消訂單後庫存應回補(page: Page) -> None:
    """R-3.7／R-6.5：取消成功後庫存加回購買數量。"""
    login(page)
    clear_cart(page)
    before = product_stock_via_api(page, PRODUCT_ID)

    add_product_from_list(page, PRODUCT_NAME)
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="庫存回補取消")

    mid = product_stock_via_api(page, PRODUCT_ID)
    assert mid == before - 1, (
        f"取消前回補前提失敗（疑似未扣庫存 D-09）：下單前 {before}，下單後 {mid}"
    )

    open_order(page, order_id)
    if page.get_by_role("button", name="取消訂單").count() == 0:
        probe = page.request.post(f"/api/orders/{order_id}/cancel")
        if probe.status == 404:
            pytest.skip("此環境未實作取消訂單 UI/API，無法驗證庫存回補")
    cancel_order(page, order_id)

    after = product_stock_via_api(page, PRODUCT_ID)
    after_ui = parse_remaining_stock(product_stock_text_on_list(page, PRODUCT_NAME))
    assert after == before, f"取消後 API 庫存應回補至 {before}，實際 {after}"
    assert after_ui == before, f"取消後 UI 庫存應回補至 {before}，實際 {after_ui}"


def test_退款完成後庫存應回補(page: Page) -> None:
    """R-3.7／R-7.9：退款完成後庫存加回購買數量。"""
    login(page)
    clear_cart(page)
    before = product_stock_via_api(page, PRODUCT_ID)

    add_product_from_list(page, PRODUCT_NAME)
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="庫存回補退款")

    mid = product_stock_via_api(page, PRODUCT_ID)
    assert mid == before - 1, (
        f"退款前回補前提失敗（疑似未扣庫存 D-09）：下單前 {before}，下單後 {mid}"
    )

    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "商品有瑕疵想退貨")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已退款", timeout=30_000)

    after = product_stock_via_api(page, PRODUCT_ID)
    after_ui = parse_remaining_stock(product_stock_text_on_list(page, PRODUCT_NAME))
    assert after == before, f"退款後 API 庫存應回補至 {before}，實際 {after}"
    assert after_ui == before, f"退款後 UI 庫存應回補至 {before}，實際 {after_ui}"
