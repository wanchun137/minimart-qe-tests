"""R-11.4、R-11.6、R-11.7、R-11.9：購物車上限、移除、空車與金額欄位。"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart


def test_同一商品購物車數量上限為_5(page: Page) -> None:
    """R-11.4：同品累加上限 5；再加入仍維持 5、無錯誤提示。"""
    login(page)
    clear_cart(page)
    for _ in range(6):
        add_product_from_list(page, "純棉素色 T 恤")
    page.goto("/cart", wait_until="domcontentloaded")
    row = page.locator(".cart-row", has_text="純棉素色 T 恤")
    expect(row.locator(".quantity-picker-value")).to_have_text("5")
    expect(page.get_by_text("錯誤")).to_have_count(0)


def test_移除商品需確認後列消失(page: Page) -> None:
    """R-11.6：移除確認「確定要移除〈商品〉嗎？」確認後列消失。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    page.goto("/cart", wait_until="domcontentloaded")
    page.once("dialog", lambda d: d.accept())
    page.locator(".cart-row", has_text="純棉素色 T 恤").get_by_role("button", name="移除").click()
    expect(page.get_by_text("購物車是空的")).to_be_visible(timeout=10_000)


def test_空購物車顯示文案且結帳停用(page: Page) -> None:
    """R-11.9：空車顯示「購物車是空的」與「去逛逛」；前往結帳停用。"""
    login(page)
    clear_cart(page)
    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.get_by_text("購物車是空的")).to_be_visible()
    expect(page.get_by_role("link", name="去逛逛")).to_be_visible()
    expect(page.get_by_role("button", name="前往結帳")).to_be_disabled()


def test_購物車頁只顯示商品小計(page: Page) -> None:
    """R-11.7：購物車僅商品小計，不顯示滿額／券／運費／應付。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.get_by_text("商品小計")).to_be_visible()
    expect(page.get_by_text("滿額折扣")).to_have_count(0)
    expect(page.get_by_text("優惠券折抵")).to_have_count(0)
    expect(page.get_by_text("運費")).to_have_count(0)
    expect(page.get_by_text("應付金額")).to_have_count(0)
