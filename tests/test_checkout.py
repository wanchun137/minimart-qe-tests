"""結帳主路徑（R-12、R-13）。"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import go_to_checkout


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


def test_結帳頁區塊順序與付款方式(page: Page) -> None:
    """R-12.1／R-12.7：收件→優惠券→金額摘要→付款方式；付款固定為貨到付款。"""
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)

    layout = page.locator(".checkout-page, main").first.inner_text()
    markers = {
        "收件資訊": layout.find("收件資訊"),
        "優惠券": layout.find("優惠券"),
        "商品小計": layout.find("商品小計"),
        "付款方式": layout.find("付款方式"),
    }
    missing = [name for name, idx in markers.items() if idx == -1]
    assert not missing, f"結帳頁缺少區塊：{missing}"

    recipient, coupon, subtotal, payment = (
        markers["收件資訊"],
        markers["優惠券"],
        markers["商品小計"],
        markers["付款方式"],
    )
    assert recipient < coupon < subtotal < payment, (
        "R-12.1 區塊順序應為收件資訊→優惠券→金額摘要→付款方式，"
        f"索引 {markers}"
    )

    payment_section = page.locator("section.checkout-section").filter(
        has=page.get_by_role("heading", name="付款方式")
    )
    expect(payment_section).to_contain_text("貨到付款")
    expect(page.get_by_role("button", name="送出訂單")).to_be_visible()
