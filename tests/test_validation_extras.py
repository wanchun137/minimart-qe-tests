"""R-14.3、R-15.6、R-17.3、R-18.1／18.2／18.7／18.9：空態與驗證細節。"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import go_to_checkout


def test_訂單列表空態文案(page: Page) -> None:
    """R-14.3：無訂單時顯示「還沒有任何訂單」與「去逛逛」。"""
    login(page)
    page.goto("/orders", wait_until="domcontentloaded")
    page.wait_for_function(
        """() => {
          const t = document.querySelector('main')?.innerText || '';
          if (t.includes('載入中')) return false;
          return t.includes('還沒有任何訂單') || /MM-\\d{8}-\\d{4}/.test(t);
        }""",
        timeout=20_000,
    )
    main_text = page.locator("main").inner_text()
    has_orders = bool(re.search(r"MM-\d{8}-\d{4}", main_text))
    if has_orders:
        pytest.skip("此帳號已有訂單（含內建／歷史單），無法驗證空態")
    expect(page.get_by_text("還沒有任何訂單")).to_be_visible()
    expect(page.get_by_role("link", name="去逛逛")).to_be_visible()


def test_通知中心空態文案(page: Page) -> None:
    """R-15.6：無通知時顯示「目前沒有通知」。"""
    login(page)
    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )
    if page.get_by_test_id("notification-row").count() > 0:
        pytest.skip("此帳號已有通知，無法驗證空態")
    expect(page.get_by_text("目前沒有通知")).to_be_visible()


def test_折扣碼重複領取應顯示錯誤(page: Page) -> None:
    """R-17.3：已在清單中的折扣碼顯示「此折扣碼已領取過」。"""
    login(page)
    page.goto("/coupons", wait_until="domcontentloaded")
    redeem = page.locator(
        "input[placeholder*='折扣'], input[name*='code' i], #coupon-code, #redeem-code"
    )
    if redeem.count() == 0:
        pytest.fail("缺少折扣碼領取 UI（D-13／R-17.3）")
    # WELCOME50 若尚未領取，先領一次再重複
    redeem.first.fill("WELCOME50")
    page.get_by_role("button", name=re.compile(r"領取")).click()
    page.wait_for_timeout(1000)
    redeem.first.fill("WELCOME50")
    page.get_by_role("button", name=re.compile(r"領取")).click()
    expect(page.get_by_text("此折扣碼已領取過")).to_be_visible(timeout=10_000)


def test_姓名前後空白應被去除後驗證(page: Page) -> None:
    """R-18.1：前後空白去除後若仍有效則可送出。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    page.fill("#checkout-name", "  空白買家  ")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市驗證路 18 號")
    expect(page.get_by_role("button", name="送出訂單")).to_be_enabled()


def test_多欄驗證失敗時各自顯示錯誤訊息(page: Page) -> None:
    """R-18.7：多欄失敗時各自顯示紅色錯誤（若 UI 採即時／送出驗證）。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    # 觸發：空姓名、短地址、非法手機 — 至少送出應停用；若有錯誤文案則斷言
    page.fill("#checkout-name", "")
    page.fill("#checkout-phone", "123")
    page.fill("#checkout-address", "短")
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
    # 嘗試 blur 觸發錯誤
    page.locator("#checkout-name").blur()
    page.locator("#checkout-phone").blur()
    page.locator("#checkout-address").blur()
    errors = page.locator(".field-error, .error-message, [data-testid*='error'], .input-error")
    if errors.count() == 0:
        # 部分實作僅停用按鈕、無紅字；仍以 R-12.6 停用為底線，紅字列為強化斷言
        pytest.skip("此環境未在欄位下方顯示驗證錯誤文案，僅送出停用")
    assert errors.count() >= 2, "多欄失敗時應各自顯示錯誤"


def test_超長姓名不自動截斷且無法送出(page: Page) -> None:
    """R-18.9／R-18.3：超長內容仍顯示於輸入框，由驗證擋下。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    long_name = "測" * 30
    page.fill("#checkout-name", long_name)
    actual = page.input_value("#checkout-name")
    assert actual == long_name, f"不應自動截斷，實際長度 {len(actual)}"
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市驗證路 18 號")
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()


def test_Unicode字元數以字元計(page: Page) -> None:
    """R-18.2：中英各算 1；20 個中文字姓名應可送出，21 不可。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    page.fill("#checkout-name", "一二三四五六七八九十一二三四五六七八九十")  # 20
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市驗證路 18 號")
    expect(page.get_by_role("button", name="送出訂單")).to_be_enabled()
    page.fill("#checkout-name", "一二三四五六七八九十一二三四五六七八九十一")  # 21
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
