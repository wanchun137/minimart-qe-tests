"""R-14.2：訂單列表「商品件數」應為各品項數量加總。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout


def test_單一品項購買_3_件時列表顯示_3_件(page: Page) -> None:
    login(page)
    clear_cart(page)

    add_product_from_list(page, "手沖咖啡濾杯")
    add_product_from_list(page, "手沖咖啡濾杯")
    add_product_from_list(page, "手沖咖啡濾杯")

    go_to_checkout(page)
    order_id = fill_and_submit_checkout(
        page,
        name="件數測試",
        address="台北市測試路 3 號",
    )

    # R-14.2：列表列顯示訂單編號，不以品名定位（列表本來就不顯示商品名稱）
    page.goto("/orders", wait_until="domcontentloaded")
    target = page.locator(".order-row").filter(has_text=order_id).first
    expect(target).to_be_visible(timeout=15_000)
    expect(target).to_contain_text(re.compile(r"3\s*件"))
