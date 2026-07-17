"""R-4.7：折扣券折抵以商品小計為基準（非扣滿額折扣後）。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart


def test_PCT15_對機械式鍵盤的折抵應為_477(page: Page) -> None:
    """機械式鍵盤 NT$3,180；PCT15 預期折抵 3180*15%=477。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "機械式鍵盤")

    page.goto("/cart", wait_until="domcontentloaded")
    page.get_by_role("button", name="前往結帳").click()
    page.wait_for_url(re.compile(r".*/checkout"))

    coupon = page.get_by_text(re.compile(r"PCT15|15%|85\s*折")).first
    coupon.click()

    sidebar = page.locator(".checkout-sidebar")
    expect(sidebar.get_by_text("優惠券折抵")).to_be_visible()
    expect(sidebar).to_contain_text(re.compile(r"NT\$\s*477"))
