"""R-9.5、R-10.3、R-11.5、R-3.4：庫存與數量上限邊界。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout


def test_已售完商品加入按鈕停用(page: Page) -> None:
    """R-9.5：陶瓷馬克杯庫存 0，列表按鈕停用。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    card = page.locator(".product-card", has_text="陶瓷馬克杯").first
    expect(card.get_by_text("已售完")).to_be_visible()
    expect(card.get_by_role("button", name="加入購物車")).to_be_disabled()


def test_商品詳情數量上限為_5_與庫存取小(page: Page) -> None:
    """R-10.3：數量選擇器最大值為 min(5, 庫存)。"""
    login(page)
    clear_cart(page)
    page.goto("/", wait_until="domcontentloaded")
    page.locator(".product-card", has_text="手沖咖啡濾杯").locator("a.product-card-link").click()
    page.wait_for_selector(".product-detail-page", timeout=15_000)
    stock_text = page.locator(".product-detail-stock").inner_text()
    stock = int(re.search(r"(\d+)", stock_text).group(1))
    expected_max = min(5, stock)
    picker = page.locator(".product-detail-page .quantity-picker")
    plus = picker.get_by_role("button", name="增加數量")
    while plus.is_enabled():
        plus.click()
    expect(picker.locator(".quantity-picker-value")).to_have_text(str(expected_max))
    expect(plus).to_be_disabled()


def test_低庫存商品詳情數量上限受庫存限制(page: Page) -> None:
    """R-10.3：折疊露營椅庫存 1，最大只能選 1。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    page.locator(".product-card", has_text="折疊露營椅").locator("a.product-card-link").click()
    page.wait_for_selector(".product-detail-page", timeout=15_000)
    picker = page.locator(".quantity-picker")
    expect(picker.locator(".quantity-picker-value")).to_have_text("1")
    expect(picker.get_by_role("button", name="增加數量")).to_be_disabled()


def test_購物車數量不得超過庫存(page: Page) -> None:
    """R-11.5：折疊露營椅庫存 1，購物車 + 按鈕應停用。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "折疊露營椅")
    page.goto("/cart", wait_until="domcontentloaded")
    row = page.locator(".cart-row", has_text="折疊露營椅")
    expect(row.locator(".quantity-picker-value")).to_have_text("1")
    expect(row.get_by_role("button", name="增加數量")).to_be_disabled()


def test_結帳時超過庫存應顯示錯誤且不成立訂單(page: Page) -> None:
    """R-3.4、R-12.10：購買數量超過庫存時整筆訂單不成立。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "折疊露營椅")
    go_to_checkout(page)
    fill_and_submit_checkout(page, name="庫存邊界測試")

    page.request.post("/api/cart/items", data={"productId": 7, "quantity": 2})
    page.goto("/checkout", wait_until="domcontentloaded")
    page.fill("#checkout-name", "庫存邊界測試")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市中山區測試路 1 號")
    page.get_by_role("button", name="送出訂單").click()
    expect(page.get_by_text(re.compile(r"商品〈折疊露營椅〉庫存不足"))).to_be_visible(timeout=15_000)
    expect(page).to_have_url(re.compile(r".*/checkout"))
