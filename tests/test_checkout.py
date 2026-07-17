"""結帳主路徑（R-12、R-13）。"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart


@pytest.fixture(autouse=True)
def _logged_in_empty_cart(page: Page):
    login(page)
    clear_cart(page)


@pytest.mark.smoke
def test_從購物車進入結帳並完成下單(page: Page) -> None:
    add_product_from_list(page, "手沖咖啡濾杯")
    page.goto("/cart", wait_until="domcontentloaded")
    page.get_by_role("button", name="前往結帳").click()
    page.wait_for_url(re.compile(r".*/checkout"))

    expect(page.locator(".checkout-sidebar")).to_be_visible()
    expect(page.get_by_text("商品小計")).to_be_visible()
    expect(page.get_by_text("應付金額")).to_be_visible()

    page.fill("#checkout-name", "測試買家")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市中山區測試路 1 號")
    page.get_by_role("button", name="送出訂單").click()

    page.wait_for_url(re.compile(r".*/orders/.+/complete"), timeout=60_000)
    expect(page.get_by_role("heading", name="訂單已成立")).to_be_visible()
