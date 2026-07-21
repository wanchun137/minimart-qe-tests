"""R-18.8：錯誤訊息文字對照表（缺口補強）。"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import go_to_checkout
from tests.helpers.checkout import fill_and_submit_checkout
import re

from tests.helpers.orders import confirm_receipt, open_order, ship_order


def _prepare_checkout(page: Page) -> None:
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)


def test_R18_8_結帳欄位錯誤訊息對照表五情境(page: Page) -> None:
    """R-18.8：涵蓋收件人姓名空、超過 20、手機格式錯誤、地址空、地址超界。"""
    _prepare_checkout(page)

    # 1) 收件人姓名空
    page.fill("#checkout-name", "")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市驗證路 5 號")
    page.locator("#checkout-name").blur()
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
    expect(page.locator("main")).to_contain_text("請輸入收件人姓名")

    # 2) 收件人姓名超過 20
    _prepare_checkout(page)
    page.fill("#checkout-name", "一" * 21)
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市驗證路 5 號")
    page.locator("#checkout-name").blur()
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
    expect(page.locator("main")).to_contain_text("收件人姓名不可超過 20 個字")

    # 3) 手機號碼格式錯誤（非 09 開頭但剛好 10 碼）
    _prepare_checkout(page)
    page.fill("#checkout-name", "驗證買家")
    page.fill("#checkout-phone", "0812345678")
    page.fill("#checkout-address", "台北市驗證路 5 號")
    page.locator("#checkout-phone").blur()
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
    expect(page.locator("main")).to_contain_text(
        "請輸入正確的手機號碼（09 開頭，共 10 位數字）"
    )

    # 4) 收件地址為空
    _prepare_checkout(page)
    page.fill("#checkout-name", "驗證買家")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "")
    page.locator("#checkout-address").blur()
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
    expect(page.locator("main")).to_contain_text("請輸入收件地址")

    # 5) 收件地址超出（> 100 字）
    _prepare_checkout(page)
    page.fill("#checkout-name", "驗證買家")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "字" * 101)
    page.locator("#checkout-address").blur()
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
    expect(page.locator("main")).to_contain_text("收件地址須為 5 至 100 個字")


def test_R18_8_退貨原因錯誤訊息對照表兩情境(page: Page) -> None:
    """R-18.8：涵蓋退貨原因空、超過 200 字。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(
        page,
        name="退貨原因錯誤訊息測試買家",
        phone="0912345678",
        address="台北市退貨原因測試路 10 號",
    )

    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)

    # 進入退貨申請頁（先不送出，只做欄位驗證）
    page.get_by_role("button", name="申請退貨").click()
    page.wait_for_url(re.compile(r".*/return"), timeout=15_000)

    page.locator("textarea").first.fill("")
    page.locator("textarea").first.blur()
    expect(page.get_by_role("button", name="送出申請")).to_be_disabled()
    expect(page.locator("main")).to_contain_text("請填寫退貨原因")

    # >200
    page.locator("textarea").first.fill("字" * 201)
    page.locator("textarea").first.blur()
    expect(page.get_by_role("button", name="送出申請")).to_be_disabled()
    expect(page.locator("main")).to_contain_text("退貨原因不可超過 200 個字")

