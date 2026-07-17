"""R-4.6：商品小計恰好等於門檻時視為達到門檻。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart


def test_小計恰等於門檻時_PCT15_應可使用(page: Page) -> None:
    """PCT15 門檻 NT$800；純棉素色 T 恤 ×2 若單價 400 則小計恰為 800。"""
    login(page)
    clear_cart(page)

    add_product_from_list(page, "純棉素色 T 恤")
    add_product_from_list(page, "純棉素色 T 恤")

    page.goto("/cart", wait_until="domcontentloaded")
    page.get_by_role("button", name="前往結帳").click()
    page.wait_for_url(re.compile(r".*/checkout"))

    sidebar = page.locator(".checkout-sidebar")
    expect(sidebar.get_by_text("商品小計")).to_be_visible()

    # 券卡片應可點選；若標示「未達使用門檻 NT$800」即為缺陷 D-08
    expect(page.get_by_text("未達使用門檻 NT$800")).to_have_count(0)
    expect(page.get_by_text(re.compile(r"PCT15|85\s*折")).first).to_be_visible()
