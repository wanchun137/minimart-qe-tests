"""R-6.3～R-6.5：取消、出貨、確認收貨等訂單狀態轉換。"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout
from tests.helpers.orders import (
    assert_cancel_order_available,
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
    assert_cancel_order_available(page)
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


def test_取消訂單時跳出正確確認文案(page: Page) -> None:
    """R-6.5：取消訂單確認框文案固定為「確定要取消這筆訂單嗎？」。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="取消確認文案測試")
    open_order(page, order_id)
    assert_cancel_order_available(page)

    message = {"text": ""}

    def accept_dialog(dialog) -> None:
        message["text"] = dialog.message
        dialog.accept()

    page.once("dialog", accept_dialog)
    page.get_by_role("button", name="取消訂單").click()
    expect(page.locator("main")).to_contain_text("已取消", timeout=15_000)
    assert message["text"] == "確定要取消這筆訂單嗎？"


def test_超過十分鐘的待出貨訂單不提供取消按鈕(page: Page) -> None:
    """R-6.5：待出貨超過 10 分鐘後不再顯示取消訂單。"""
    login(page)
    response = page.request.get("/api/orders")
    assert response.ok, response.text()
    now = datetime.now(ZoneInfo("Asia/Taipei")).replace(tzinfo=None)
    candidates = [
        order["id"]
        for order in response.json()
        if order.get("status") == "待出貨"
        and datetime.strptime(order["createdAt"], "%Y-%m-%d %H:%M") <= now - timedelta(minutes=10)
    ]
    if not candidates:
        pytest.skip("找不到超過 10 分鐘的待出貨訂單")
    open_order(page, candidates[0])
    expect(page.get_by_role("button", name="取消訂單")).to_have_count(0)
