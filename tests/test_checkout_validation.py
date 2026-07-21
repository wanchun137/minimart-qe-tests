"""R-12.6、R-18：結帳收件欄位驗證與送出按鈕狀態。"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import go_to_checkout


def _prepare_checkout(page: Page) -> None:
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)


def test_收件欄位未填時送出訂單停用(page: Page) -> None:
    """R-12.6：任一必填未填或格式不符時「送出訂單」停用。"""
    _prepare_checkout(page)
    submit = page.get_by_role("button", name="送出訂單")
    expect(submit).to_be_disabled()

    page.fill("#checkout-name", "驗證買家")
    expect(submit).to_be_disabled()
    page.fill("#checkout-phone", "0912345678")
    expect(submit).to_be_disabled()
    page.fill("#checkout-address", "台北市驗證路 5 號")
    expect(submit).to_be_enabled()


def test_姓名空白不可啟用送出(page: Page) -> None:
    """R-18.3：姓名必填（去除空白後 1～20 字）。"""
    _prepare_checkout(page)
    page.fill("#checkout-name", "   ")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市驗證路 5 號")
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()


def test_地址過短不可啟用送出(page: Page) -> None:
    """R-18.5：地址去除空白後須 5～100 字。"""
    _prepare_checkout(page)
    page.fill("#checkout-name", "驗證買家")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北")  # 2 字，不足 5
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()


def test_地址過長不可啟用送出(page: Page) -> None:
    """R-18.5：地址去除空白後字數 > 100 時應停用送出。"""
    _prepare_checkout(page)
    page.fill("#checkout-name", "驗證買家")
    page.fill("#checkout-phone", "0912345678")
    long_address = "字" * 101
    page.fill("#checkout-address", long_address)
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
    page.locator("#checkout-address").blur()
    expect(page.locator("main")).to_contain_text("收件地址須為 5 至 100 個字")


def test_姓名超過二十字不可啟用送出(page: Page) -> None:
    """R-18.3：姓名最多 20 字。"""
    _prepare_checkout(page)
    page.fill("#checkout-name", "一二三四五六七八九十一二三四五六七八九十一")  # 21
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市驗證路 5 號")
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
