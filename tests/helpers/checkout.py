"""結帳頁金額摘要與下單共用工具。"""

from __future__ import annotations

import re
from typing import Any

from playwright.sync_api import Locator, Page, expect

COUPON_CODES = {
    "新人小禮券": "NEWBIE20",
    "滿千折百券": "SAVE100",
    "滿三千折三百券": "SAVE300",
    "全站 85 折券": "PCT15",
    "免運券": "FREESHIP",
}


def format_nt(amount: int, *, as_discount: bool = False) -> str:
    """將整數金額格式化成畫面顯示字串。"""
    if amount == 0:
        return "NT$0"
    if as_discount:
        return f"−NT${amount:,}"
    return f"NT${amount:,}"


def go_to_checkout(page: Page) -> None:
    """從購物車進入結帳頁。"""
    page.goto("/cart", wait_until="domcontentloaded")
    page.get_by_role("button", name="前往結帳").click()
    page.wait_for_url(re.compile(r".*/checkout"), timeout=15_000)
    expect(page.locator(".checkout-sidebar")).to_be_visible(timeout=15_000)


def summary_row_value(page: Page, label: str) -> Locator:
    """取得結帳側欄指定標籤列的金額值。"""
    row = page.locator(".summary-row").filter(
        has=page.locator(".summary-row-label", has_text=label)
    )
    return row.locator(".summary-row-value")


def fetch_checkout_preview(page: Page, coupon_code: str | None = None) -> dict[str, Any]:
    """呼叫 checkout preview API 取得 PRD 計價結果。"""
    response = page.request.post("/api/checkout/preview", data={"couponCode": coupon_code})
    assert response.ok, f"preview 失敗：{response.status} {response.text()}"
    return response.json()


def expect_summary_matches_preview(page: Page, *, coupon_code: str | None = None) -> dict[str, Any]:
    """以 preview API 為基準，驗證結帳頁 UI 關鍵金額欄位。"""
    preview = fetch_checkout_preview(page, coupon_code)
    expect(summary_row_value(page, "商品小計")).to_have_text(format_nt(preview["subtotal"]))
    expect(summary_row_value(page, "運費")).to_have_text(format_nt(preview["shipping"]))
    expect(summary_row_value(page, "應付金額")).to_have_text(format_nt(preview["payable"]))
    return preview


def assert_preview_amounts(preview: dict[str, Any], **expected: int) -> None:
    """直接斷言 preview API 回傳的 PRD 金額。"""
    mapping = {
        "subtotal": "subtotal",
        "bulk_discount": "bulkDiscount",
        "coupon_discount": "couponDiscount",
        "shipping": "shipping",
        "payable": "payable",
    }
    for key, value in expected.items():
        assert preview[mapping[key]] == value, f"{key} 預期 {value}，實際 {preview[mapping[key]]}"


def select_coupon(page: Page, name: str) -> None:
    """點選結帳頁優惠券選項（依券名稱）。"""
    option = page.locator("label.coupon-option", has_text=name).first
    expect(option).to_be_visible(timeout=10_000)
    option.click()


def fill_and_submit_checkout(
    page: Page,
    *,
    name: str = "測試買家",
    phone: str = "0912345678",
    address: str = "台北市中山區測試路 1 號",
    note: str | None = None,
) -> str:
    """填寫收件資訊（可選訂單備註）並送出，回傳訂單編號。"""
    page.fill("#checkout-name", name)
    page.fill("#checkout-phone", phone)
    page.fill("#checkout-address", address)
    if note is not None:
        page.fill("#checkout-note", note)
    page.get_by_role("button", name="送出訂單").click()
    page.wait_for_url(re.compile(r".*/orders/.+/complete"), timeout=30_000)
    match = re.search(r"/orders/(MM-[^/]+)/complete", page.url)
    if not match:
        raise AssertionError(f"無法從完成頁解析訂單編號：{page.url}")
    return match.group(1)
