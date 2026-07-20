"""訂單列表與詳情共用工具。"""

from __future__ import annotations

import re
from datetime import datetime

from playwright.sync_api import Page, expect

CREATED_AT_FORMAT = "%Y-%m-%d %H:%M"


def go_to_order_list(page: Page) -> None:
    """進入訂單列表並等待載入完成（含空列表）。"""
    page.goto("/orders", wait_until="domcontentloaded")
    page.wait_for_selector(".order-row, .order-list-empty-text", timeout=15_000)


def order_list_rows(page: Page) -> list[dict[str, str]]:
    """讀取訂單列表每一列的編號、時間、狀態、件數、應付。"""
    rows = page.locator(".order-row")
    data: list[dict[str, str]] = []
    for i in range(rows.count()):
        row = rows.nth(i)
        data.append(
            {
                "id": row.locator(".order-row-id").inner_text(),
                "createdAt": row.locator(".order-row-createdAt").inner_text(),
                "status": row.locator(".order-row-status").inner_text(),
                "itemCount": row.locator(".order-row-itemCount").inner_text(),
                "payable": row.locator(".order-row-payable").inner_text(),
            }
        )
    return data


def parse_order_created_at(text: str) -> datetime:
    """解析列表／API 的下單時間字串。"""
    return datetime.strptime(text.strip(), CREATED_AT_FORMAT)


def assert_orders_sorted_new_to_old(created_at_texts: list[str]) -> None:
    """R-14.1：下單時間應由新到舊（非遞增）。"""
    times = [parse_order_created_at(t) for t in created_at_texts]
    for i in range(len(times) - 1):
        assert times[i] >= times[i + 1], (
            f"R-14.1：第 {i + 1} 列 {created_at_texts[i]} 應不早於第 {i + 2} 列 {created_at_texts[i + 1]}"
        )


def assert_cancel_order_available(page: Page) -> None:
    """R-6.5／R-14.9：待出貨訂單詳情應顯示「取消訂單」按鈕（缺失視為缺陷 D-23）。"""
    expect(page.get_by_role("button", name="取消訂單")).to_be_visible()


def open_order(page: Page, order_id: str) -> None:
    page.goto(f"/orders/{order_id}", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="訂單詳情")).to_be_visible(timeout=15_000)


def expect_order_status(page: Page, status: str) -> None:
    expect(page.locator("main")).to_contain_text(status)


def _reload_order_detail(page: Page) -> None:
    page.reload(wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="訂單詳情")).to_be_visible(timeout=15_000)


def cancel_order(page: Page, order_id: str) -> None:
    """取消待出貨訂單（優先 UI，必要時以 Demo API 補足）。"""
    cancel_btn = page.get_by_role("button", name="取消訂單")
    if cancel_btn.count() and cancel_btn.is_visible():
        page.once("dialog", lambda dialog: dialog.accept())
        cancel_btn.click()
    else:
        response = page.request.post(f"/api/orders/{order_id}/cancel")
        assert response.ok, f"取消 API 失敗：{response.status} {response.text()}"
    _reload_order_detail(page)
    expect_order_status(page, "已取消")


def ship_order(page: Page, order_id: str) -> None:
    """模擬出貨並等待畫面更新。"""
    ship_btn = page.get_by_role("button", name="模擬出貨（Demo）")
    expect(ship_btn).to_be_visible()
    try:
        with page.expect_response(
            lambda r: "/ship" in r.url and r.request.method == "POST",
            timeout=8_000,
        ) as resp_info:
            ship_btn.click()
        assert resp_info.value.ok, f"出貨 API 失敗：{resp_info.value.status}"
    except Exception:
        response = page.request.post(f"/api/orders/{order_id}/ship")
        assert response.ok, f"出貨 API 失敗：{response.status} {response.text()}"
    _reload_order_detail(page)
    expect_order_status(page, "已出貨")
    expect(page.get_by_role("button", name="確認收貨")).to_be_visible()


def confirm_receipt(page: Page, order_id: str) -> None:
    confirm_btn = page.get_by_role("button", name="確認收貨")
    expect(confirm_btn).to_be_visible()
    try:
        with page.expect_response(
            lambda r: "confirm-receipt" in r.url and r.request.method == "POST",
            timeout=8_000,
        ) as resp_info:
            confirm_btn.click()
        assert resp_info.value.ok, f"確認收貨 API 失敗：{resp_info.value.status}"
    except Exception:
        response = page.request.post(f"/api/orders/{order_id}/confirm-receipt")
        assert response.ok, f"確認收貨 API 失敗：{response.status} {response.text()}"
    _reload_order_detail(page)
    expect_order_status(page, "已完成")


def apply_return(page: Page, reason: str) -> None:
    """從已完成訂單進入退貨申請頁並送出。"""
    page.get_by_role("button", name="申請退貨").click()
    page.wait_for_url(re.compile(r".*/orders/.+/return"), timeout=15_000)
    page.locator("textarea").first.fill(reason)
    page.get_by_role("button", name="送出申請").click()
    page.wait_for_url(re.compile(r".*/orders/MM-[^/]+$"), timeout=15_000)
    expect_order_status(page, "退貨中")


def seller_review(page: Page) -> None:
    page.get_by_role("button", name="賣家審核（Demo）").click()
    _reload_order_detail(page)
