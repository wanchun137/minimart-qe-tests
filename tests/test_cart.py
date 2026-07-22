"""購物車主路徑（R-9.4、R-11.2、R-1.4）。"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, add_product_with_quantity, cart_badge, clear_cart
from tests.helpers.checkout import format_nt


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


def test_購物車列顯示商品圖片與列小計(page: Page) -> None:
    """R-11.2：每列須含商品圖、單價、數量選擇器、列小計（單價 × 數量）。"""
    add_product_with_quantity(page, "手沖咖啡濾杯", 2)
    page.goto("/cart", wait_until="domcontentloaded")

    cart = page.request.get("/api/cart")
    assert cart.ok, cart.text()
    item = next(
        (row for row in cart.json()["items"] if row.get("name") == "手沖咖啡濾杯"),
        None,
    )
    assert item, "API 購物車應含手沖咖啡濾杯"

    row = page.locator(".cart-row", has_text="手沖咖啡濾杯")
    expect(row.locator("img")).to_be_visible()
    img_src = row.locator("img").get_attribute("src") or ""
    image_url = item.get("imageUrl", "")
    if image_url:
        assert image_url in img_src, f"圖片 src 應含 {image_url!r}，實際 {img_src!r}"

    expect(row).to_contain_text(format_nt(item["unitPrice"]))
    expect(row).to_contain_text(format_nt(item["lineTotal"]))
    expect(row.locator(".quantity-picker-value")).to_have_text(str(item["quantity"]))
    expect(row.get_by_role("button", name="移除")).to_be_visible()
