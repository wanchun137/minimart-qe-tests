"""R-14.1～R-14.2：訂單列表排序、完整列表與列表列欄位。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout
from tests.helpers.orders import (
    assert_orders_sorted_new_to_old,
    go_to_order_list,
    order_list_rows,
)


def _place_order(page: Page, *, product: str, name: str) -> str:
    clear_cart(page)
    add_product_from_list(page, product)
    go_to_checkout(page)
    return fill_and_submit_checkout(page, name=name, address="台北市列表測試路 14 號")


def test_訂單列表依下單時間由新到舊排序(page: Page) -> None:
    """R-14.1：全部訂單依下單時間由新到舊排列。"""
    login(page)
    go_to_order_list(page)
    rows = order_list_rows(page)
    assert rows, "此帳號應至少有一筆訂單以驗證排序"
    assert_orders_sorted_new_to_old([row["createdAt"] for row in rows])


def test_連續下單後較新訂單應排在較舊訂單上方(page: Page) -> None:
    """R-14.1：新建立的訂單應出現在較早訂單上方。"""
    login(page)
    older_id = _place_order(page, product="手沖咖啡濾杯", name="列表排序較舊")
    newer_id = _place_order(page, product="純棉素色 T 恤", name="列表排序較新")

    go_to_order_list(page)
    ids = [row["id"] for row in order_list_rows(page)]
    assert older_id in ids and newer_id in ids
    assert ids.index(newer_id) < ids.index(older_id), (
        f"較新訂單 {newer_id} 應排在較舊訂單 {older_id} 上方（R-14.1）"
    )


def test_列表顯示帳號全部訂單且不分頁(page: Page) -> None:
    """R-14.1：UI 列出的訂單筆數與 API 一致，且包含全部訂單編號。"""
    login(page)
    api_orders = page.request.get("/api/orders")
    assert api_orders.ok, api_orders.text()
    api_ids = [order["id"] for order in api_orders.json()]

    go_to_order_list(page)
    ui_ids = [row["id"] for row in order_list_rows(page)]
    assert len(ui_ids) == len(api_ids), (
        f"列表應顯示全部 {len(api_ids)} 筆訂單，UI 僅 {len(ui_ids)} 筆（R-14.1）"
    )
    assert ui_ids == api_ids, "UI 順序應與 GET /api/orders 一致"


def test_列表列顯示必要欄位(page: Page) -> None:
    """R-14.2：每列含訂單編號、下單時間、狀態、件數總和、應付金額。"""
    login(page)
    go_to_order_list(page)
    row = page.locator(".order-row").first
    expect(row.locator(".order-row-id")).to_have_text(re.compile(r"MM-\d{8}-\d{4}"))
    expect(row.locator(".order-row-createdAt")).to_have_text(
        re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
    )
    expect(row.locator(".order-row-status")).not_to_be_empty()
    expect(row.locator(".order-row-itemCount")).to_have_text(re.compile(r"\d+\s*件"))
    expect(row.locator(".order-row-payable")).to_have_text(re.compile(r"NT\$[\d,]+"))


def test_點擊列表列進入訂單詳情(page: Page) -> None:
    """R-14.2：點擊任一列進入訂單詳情頁。"""
    login(page)
    go_to_order_list(page)
    first_id = page.locator(".order-row-id").first.inner_text()
    page.locator(".order-row").first.click()
    page.wait_for_url(re.compile(rf".*/orders/{re.escape(first_id)}$"), timeout=15_000)
    expect(page.get_by_role("heading", name="訂單詳情")).to_be_visible()
    expect(page.locator("main")).to_contain_text(first_id)
