"""R-18.4：手機須為 09 開頭共 10 碼；11 碼應被擋下。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart


def test_11_碼手機號碼不可成功下單(page: Page) -> None:
    login(page)
    clear_cart(page)
    add_product_from_list(page, "手沖咖啡濾杯")

    page.goto("/cart", wait_until="domcontentloaded")
    page.get_by_role("button", name="前往結帳").click()
    page.wait_for_url(re.compile(r".*/checkout"))

    page.fill("#checkout-name", "手機驗證")
    page.fill("#checkout-phone", "09123456789")  # 11 碼
    page.fill("#checkout-address", "台北市測試路 11 號")
    page.get_by_role("button", name="送出訂單").click()

    expect(page).not_to_have_url(re.compile(r".*/orders/.+/complete"), timeout=5_000)
