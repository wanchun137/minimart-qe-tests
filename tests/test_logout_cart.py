"""R-1.7 / R-11.1：登出清空購物車；重新整理／切換畫面後內容保留。"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.helpers.auth import login, logout
from tests.helpers.cart import add_product_from_list, cart_badge, clear_cart


def test_登出後再登入購物車應為空(page: Page) -> None:
    """R-1.7／R-11.1：登出清空購物車；再次登入為空。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "手沖咖啡濾杯")
    page.goto("/cart", wait_until="domcontentloaded")
    expect(cart_badge(page)).to_have_text("1")

    logout(page)
    login(page)
    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.get_by_text("購物車是空的")).to_be_visible()
    expect(cart_badge(page)).to_have_count(0)


def test_切換畫面與重新整理後購物車內容保留(page: Page) -> None:
    """R-11.1：購物車綁定帳號；切換畫面、重新整理後內容不變。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    add_product_from_list(page, "手沖咖啡濾杯")

    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.locator(".cart-row", has_text="純棉素色 T 恤")).to_be_visible()
    expect(page.locator(".cart-row", has_text="手沖咖啡濾杯")).to_be_visible()
    expect(cart_badge(page)).to_have_text("2")

    page.goto("/", wait_until="domcontentloaded")
    page.goto("/orders", wait_until="domcontentloaded")
    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.locator(".cart-row", has_text="純棉素色 T 恤")).to_be_visible()
    expect(page.locator(".cart-row", has_text="手沖咖啡濾杯")).to_be_visible()
    expect(cart_badge(page)).to_have_text("2")

    page.reload(wait_until="domcontentloaded")
    expect(page.locator(".cart-row", has_text="純棉素色 T 恤")).to_be_visible()
    expect(page.locator(".cart-row", has_text="手沖咖啡濾杯")).to_be_visible()
    expect(cart_badge(page)).to_have_text("2")
