"""購物車相關 UI 輔助函式。"""

from __future__ import annotations

from playwright.sync_api import Locator, Page


def clear_cart(page: Page) -> None:
    """清空購物車，避免殘留資料干擾件數斷言。"""
    page.goto("/cart", wait_until="domcontentloaded")
    page.wait_for_timeout(500)

    if page.get_by_text("購物車是空的").is_visible():
        return

    for _ in range(20):
        remove_btn = page.get_by_role("button", name="移除").first
        if not remove_btn.is_visible():
            break
        page.once("dialog", lambda dialog: dialog.accept())
        remove_btn.click()
        page.wait_for_timeout(400)


def add_product_from_list(page: Page, product_name: str) -> None:
    """在商品列表把指定名稱的商品加入購物車（預設數量 1）。"""
    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_selector(".product-grid")
    card = page.locator(".product-card", has_text=product_name).first
    card.get_by_role("button", name="加入購物車").click()
    try:
        page.get_by_text("已加入購物車").wait_for(state="visible", timeout=10_000)
    except Exception:
        pass


def cart_badge(page: Page) -> Locator:
    return page.get_by_test_id("cart-badge")
