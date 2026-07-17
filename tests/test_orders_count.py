"""R-14.2：訂單列表「商品件數」應為各品項數量加總。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart


def test_單一品項購買_3_件時列表顯示_3_件(page: Page) -> None:
    login(page)
    clear_cart(page)

    add_product_from_list(page, "手沖咖啡濾杯")
    add_product_from_list(page, "手沖咖啡濾杯")
    add_product_from_list(page, "手沖咖啡濾杯")

    page.goto("/cart", wait_until="domcontentloaded")
    page.get_by_role("button", name="前往結帳").click()
    page.wait_for_url(re.compile(r".*/checkout"))
    page.fill("#checkout-name", "件數測試")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市測試路 3 號")
    page.get_by_role("button", name="送出訂單").click()
    page.wait_for_url(re.compile(r".*/orders/.+/complete"), timeout=60_000)

    page.goto("/orders", wait_until="domcontentloaded")
    target = page.locator(".order-row").filter(has_text="手沖咖啡濾杯").first
    expect(target).to_contain_text(re.compile(r"3\s*件"))
