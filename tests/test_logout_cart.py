"""R-1.7 / R-11.1：登出應清空購物車。"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.helpers.auth import login, logout
from tests.helpers.cart import add_product_from_list, cart_badge, clear_cart


def test_登出後再登入購物車應為空(page: Page) -> None:
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
