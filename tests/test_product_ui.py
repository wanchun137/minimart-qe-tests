"""R-3.1、R-3.3、R-9、R-10.5、R-10.6：商品列表／詳情欄位與售完行為。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.products import (
    parse_remaining_stock,
    product_by_name_via_api,
    product_stock_text_on_list,
    product_stock_via_api,
)


def test_香氛蠟燭禮盒商品圖片正常載入(page: Page) -> None:
    """R-9.2 / D-02：香氛蠟燭禮盒卡片圖片應可正常載入（naturalWidth > 0）。"""
    login(page)
    product = product_by_name_via_api(page, "香氛蠟燭禮盒")
    image_url = product.get("imageUrl", "")
    assert image_url, "API 應提供 imageUrl"

    img_resp = page.request.get(image_url)
    content_type = (img_resp.headers.get("content-type") or "").lower()
    body_prefix = img_resp.text()[:80].lstrip()
    assert img_resp.ok, f"imageUrl 應可存取：{image_url} → {img_resp.status}"
    assert "image/svg" in content_type or body_prefix.startswith("<svg"), (
        f"imageUrl 應回傳 SVG 圖片（D-02），"
        f"status={img_resp.status}，content-type={content_type!r}，"
        f"body={body_prefix[:60]!r}"
    )

    page.goto("/", wait_until="domcontentloaded")
    card = page.locator(".product-card", has_text="香氛蠟燭禮盒").first
    expect(card).to_be_visible()
    img = card.locator(".product-image, img").first
    expect(img).to_be_visible()
    page.wait_for_timeout(1_000)
    natural_width = img.evaluate("el => el.naturalWidth")
    assert natural_width > 0, (
        f"香氛蠟燭禮盒圖片應正常載入（D-02），"
        f"naturalWidth={natural_width}，imageUrl={image_url}"
    )


def test_商品卡片與詳情顯示必要欄位(page: Page) -> None:
    """R-3.1／R-9.2／R-10.1：列表卡與詳情含名稱、分類、單價、庫存文字。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    card = page.locator(".product-card", has_text="手沖咖啡濾杯").first
    expect(card).to_contain_text("手沖咖啡濾杯")
    expect(card).to_contain_text("廚房")
    expect(card).to_contain_text("NT$480")
    expect(card).to_contain_text(re.compile(r"剩餘\s*\d+\s*件"))
    expect(card.locator("img")).to_be_visible()

    card.locator("a.product-card-link").first.click()
    page.wait_for_selector(".product-detail-page", timeout=15_000)
    main = page.locator(".product-detail-page")
    expect(main).to_contain_text("手沖咖啡濾杯")
    expect(main).to_contain_text("廚房")
    expect(main).to_contain_text("NT$480")
    expect(main.locator(".product-detail-stock")).to_be_visible()
    expect(main.locator(".quantity-picker")).to_be_visible()
    expect(main.locator(".add-to-cart-btn")).to_be_visible()


def test_商品列表卡片商品具描述欄位(page: Page) -> None:
    """R-3.1：列表上的商品在 API 資料中須含非空 description。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    card = page.locator(".product-card", has_text="手沖咖啡濾杯").first
    expect(card).to_be_visible()

    product = product_by_name_via_api(page, "手沖咖啡濾杯")
    description = product.get("description", "").strip()
    assert description, "API 商品描述不可為空（R-3.1）"

    desc_el = card.locator(
        ".product-card-description, .product-description, [data-testid='product-description']"
    )
    if desc_el.count() > 0:
        expect(desc_el.first).to_contain_text(description)


def test_商品詳情顯示商品描述(page: Page) -> None:
    """R-10.1：詳情頁須顯示商品描述（與 API 一致）。"""
    login(page)
    product = product_by_name_via_api(page, "手沖咖啡濾杯")
    description = product.get("description", "").strip()
    assert description, "API 商品描述不可為空"

    page.goto("/", wait_until="domcontentloaded")
    page.locator(".product-card", has_text="手沖咖啡濾杯").locator("a.product-card-link").click()
    page.wait_for_selector(".product-detail-page", timeout=15_000)

    detail = page.locator(".product-detail-page")
    desc = detail.locator(
        ".product-detail-description, .product-description, [data-testid='product-description']"
    )
    if desc.count() > 0:
        expect(desc.first).to_contain_text(description)
    else:
        expect(detail).to_contain_text(description)


def test_加入購物車不改變庫存數量(page: Page) -> None:
    """R-3.3：加車只是暫存，不扣庫存。"""
    login(page)
    clear_cart(page)
    before_api = product_stock_via_api(page, 5)
    before_ui = parse_remaining_stock(product_stock_text_on_list(page, "純棉素色 T 恤"))
    add_product_from_list(page, "純棉素色 T 恤")
    after_api = product_stock_via_api(page, 5)
    after_ui = parse_remaining_stock(product_stock_text_on_list(page, "純棉素色 T 恤"))
    assert after_api == before_api
    assert after_ui == before_ui


def test_已售完商品詳情選擇器與加入按鈕停用(page: Page) -> None:
    """R-10.5：庫存 0 時詳情數量選擇器與加入購物車皆停用。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    page.locator(".product-card", has_text="陶瓷馬克杯").locator("a.product-card-link").click()
    page.wait_for_selector(".product-detail-page", timeout=15_000)
    expect(page.locator(".product-detail-stock")).to_contain_text("已售完")
    expect(page.locator(".add-to-cart-btn")).to_be_disabled()
    picker = page.locator(".quantity-picker")
    expect(picker.get_by_role("button", name="增加數量")).to_be_disabled()
    expect(picker.get_by_role("button", name="減少數量")).to_be_disabled()


def test_商品詳情可回商品列表(page: Page) -> None:
    """R-10.6：點「回商品列表」回到列表。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    page.locator(".product-card", has_text="手沖咖啡濾杯").locator("a.product-card-link").click()
    page.wait_for_selector(".product-detail-page", timeout=15_000)
    page.get_by_role("link", name=re.compile(r"回商品列表")).click()
    expect(page.locator(".product-grid")).to_be_visible(timeout=15_000)
