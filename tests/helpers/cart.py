"""購物車相關 UI 輔助函式。"""

from __future__ import annotations

from playwright.sync_api import Locator, Page, expect


def clear_cart(page: Page) -> None:
    """清空購物車，避免殘留資料干擾件數與金額斷言。"""
    response = page.request.get("/api/cart")
    if response.ok:
        for item in response.json().get("items", []):
            page.request.delete(f"/api/cart/items/{item['productId']}")

    page.goto("/cart", wait_until="domcontentloaded")
    if page.get_by_text("購物車是空的").count():
        expect(page.get_by_text("購物車是空的")).to_be_visible(timeout=5_000)


def add_product_from_list(page: Page, product_name: str) -> None:
    """在商品列表把指定名稱的商品加入購物車（預設數量 1）。"""
    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_selector(".product-grid", timeout=15_000)
    card = page.locator(".product-card", has_text=product_name).first
    card.get_by_role("button", name="加入購物車").click()
    try:
        page.get_by_text("已加入購物車").wait_for(state="visible", timeout=3_000)
    except Exception:
        pass


def add_product_with_quantity(page: Page, product_name: str, quantity: int) -> None:
    """在商品詳情頁以指定數量加入購物車。"""
    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_selector(".product-grid", timeout=15_000)
    page.locator(".product-card", has_text=product_name).locator("a.product-card-link").click()
    page.wait_for_selector(".product-detail-page", timeout=15_000)
    picker = page.locator(".quantity-picker")
    plus = picker.get_by_role("button", name="增加數量")
    current = int(picker.locator(".quantity-picker-value").inner_text())
    for _ in range(quantity - current):
        plus.click()
    page.locator(".add-to-cart-btn").click()
    try:
        page.get_by_text("已加入購物車").wait_for(state="visible", timeout=3_000)
    except Exception:
        pass


def cart_badge(page: Page) -> Locator:
    return page.get_by_test_id("cart-badge")
