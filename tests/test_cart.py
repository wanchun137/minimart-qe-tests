"""購物車主路徑（R-9.4、R-11.2、R-1.4）。"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, cart_badge, clear_cart


@pytest.fixture(autouse=True)
def _logged_in_empty_cart(page: Page):
    login(page)
    clear_cart(page)


@pytest.mark.smoke
def test_加入商品後購物車頁可見該品項且件數正確(page: Page) -> None:
    add_product_from_list(page, "手沖咖啡濾杯")

    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.locator(".cart-row", has_text="手沖咖啡濾杯").first).to_be_visible()
    expect(cart_badge(page)).to_have_text("1")


def test_同一商品再加入一次件數累加為_2(page: Page) -> None:
    add_product_from_list(page, "手沖咖啡濾杯")
    add_product_from_list(page, "手沖咖啡濾杯")
    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.locator(".cart-row")).to_have_count(1)
    expect(cart_badge(page)).to_have_text("2")
