"""R-17：我的優惠券頁（領取、頁籤、卡片欄位）。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login


def _open_coupons(page: Page) -> None:
    page.goto("/coupons", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="我的優惠券")).to_be_visible(timeout=15_000)


def test_優惠券頁有三頁籤與卡片必要欄位(page: Page) -> None:
    """R-17.5、R-17.6：可使用／已使用／已過期頁籤；卡片含名稱、券碼、面額、門檻、到期日。"""
    login(page)
    _open_coupons(page)

    expect(page.get_by_role("button", name=re.compile(r"^可使用"))).to_be_visible()
    expect(page.get_by_role("button", name=re.compile(r"^已使用"))).to_be_visible()
    expect(page.get_by_role("button", name=re.compile(r"^已過期"))).to_be_visible()

    card = page.get_by_test_id("coupon-card").first
    expect(card).to_be_visible()
    expect(card.locator(".coupon-card-name")).to_be_visible()
    expect(card.locator(".coupon-card-code")).to_contain_text("券碼")
    expect(card.locator(".coupon-card-value")).to_be_visible()
    expect(card.locator(".coupon-card-threshold")).to_be_visible()
    expect(card.locator(".coupon-card-expires")).to_contain_text("到期日")


def test_門檻為零的券顯示無最低消費(page: Page) -> None:
    """R-17.6：門檻 0 顯示「無最低消費」。"""
    login(page)
    _open_coupons(page)
    card = page.get_by_test_id("coupon-card").filter(has_text="新人小禮券")
    expect(card).to_contain_text("無最低消費")


def test_已過期頁籤可見舊版折五十券(page: Page) -> None:
    """R-17.5：已過期頁籤列出過期券。"""
    login(page)
    _open_coupons(page)
    page.get_by_role("button", name=re.compile(r"^已過期")).click()
    expect(page.get_by_test_id("coupon-card").filter(has_text="舊版折五十券")).to_be_visible()


def test_優惠券頁提供折扣碼領取且可領取_WELCOME50(page: Page) -> None:
    """R-17.1／R-17.4：輸入有效折扣碼可領取，提示「已領取〈歡迎折五十券〉」。"""
    login(page)
    _open_coupons(page)

    redeem_input = page.get_by_placeholder(re.compile(r"折扣碼|優惠碼|coupon", re.I))
    if redeem_input.count() == 0:
        redeem_input = page.locator("input[name*='code' i], #coupon-code, #redeem-code")
    expect(redeem_input.first).to_be_visible(timeout=5_000)
    redeem_input.first.fill("WELCOME50")
    page.get_by_role("button", name=re.compile(r"領取")).click()
    expect(page.get_by_text(re.compile(r"已領取〈歡迎折五十券〉"))).to_be_visible(timeout=10_000)


def test_無效折扣碼顯示錯誤訊息(page: Page) -> None:
    """R-17.2：無效碼顯示「折扣碼不存在或已失效」。"""
    login(page)
    _open_coupons(page)
    redeem_input = page.locator(
        "input[placeholder*='折扣'], input[name*='code' i], #coupon-code, #redeem-code"
    )
    expect(redeem_input.first).to_be_visible(timeout=5_000)
    redeem_input.first.fill("NOT-A-REAL-CODE")
    page.get_by_role("button", name=re.compile(r"領取")).click()
    expect(page.get_by_text("折扣碼不存在或已失效")).to_be_visible(timeout=10_000)


def test_我的優惠券頁不可套用優惠券(page: Page) -> None:
    """R-17.9：此頁僅查看／領取，不可套用（無套用到訂單的操作）。"""
    login(page)
    _open_coupons(page)
    expect(page.get_by_role("button", name=re.compile(r"套用|使用優惠券"))).to_have_count(0)
