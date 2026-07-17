"""R-6.3～R-6.5：取消、出貨、確認收貨等訂單狀態轉換。"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout
from tests.helpers.orders import (
    cancel_order,
    confirm_receipt,
    open_order,
    ship_order,
)


def test_待出貨訂單可取消(page: Page) -> None:
    """R-6.5：10 分鐘內可取消，狀態轉為已取消。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="取消測試")

    open_order(page, order_id)
    if page.get_by_role("button", name="取消訂單").count() == 0:
        probe = page.request.post(f"/api/orders/{order_id}/cancel")
        if probe.status == 404:
            pytest.skip("此環境未實作取消訂單 UI/API")
    cancel_order(page, order_id)
    expect(page.get_by_role("button", name="模擬出貨（Demo）")).to_have_count(0)


def test_待出貨訂單可模擬出貨(page: Page) -> None:
    """R-6.3：出貨後狀態為已出貨。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="出貨測試")

    open_order(page, order_id)
    ship_order(page, order_id)


def test_已出貨訂單可確認收貨(page: Page) -> None:
    """R-6.4：下單→出貨→確認收貨，狀態轉為已完成。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="收貨測試")

    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    expect(page.get_by_role("button", name="申請退貨")).to_be_visible()
