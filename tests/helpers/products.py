"""商品庫存讀取輔助（UI／API）。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect


def product_stock_via_api(page: Page, product_id: int) -> int:
    response = page.request.get(f"/api/products/{product_id}")
    assert response.ok, f"讀取商品失敗：{response.status} {response.text()}"
    return int(response.json()["stock"])


def product_stock_text_on_list(page: Page, product_name: str) -> str:
    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_selector(".product-grid", timeout=15_000)
    card = page.locator(".product-card", has_text=product_name).first
    expect(card).to_be_visible()
    return card.inner_text()


def product_by_name_via_api(page: Page, product_name: str) -> dict:
    """依商品名稱從 /api/products 取得完整商品資料（含 description）。"""
    response = page.request.get("/api/products")
    assert response.ok, f"讀取商品列表失敗：{response.status} {response.text()}"
    for product in response.json():
        if product.get("name") == product_name:
            return product
    raise AssertionError(f"找不到商品：{product_name}")


def parse_remaining_stock(text: str) -> int | None:
    """從「剩餘 N 件」解析庫存；已售完回傳 0。"""
    if "已售完" in text:
        return 0
    match = re.search(r"剩餘\s*(\d+)\s*件", text)
    return int(match.group(1)) if match else None
