"""R-6.7、R-6.8、R-7.11、R-7.12、R-16.4、R-16.6、R-16.8：狀態終態與退貨申請頁。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout
from tests.helpers.orders import (
    apply_return,
    confirm_receipt,
    open_order,
    seller_review,
    ship_order,
)


def _complete_order(page: Page, name: str) -> str:
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    return fill_and_submit_checkout(page, name=name)


def test_已退款為最終狀態無出貨收貨取消按鈕(page: Page) -> None:
    """R-6.7／R-7.13：已退款後不提供確認收貨／取消／出貨。"""
    login(page)
    order_id = _complete_order(page, "終態退款測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "商品有瑕疵想退貨")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已退款", timeout=30_000)
    expect(page.get_by_role("button", name="模擬出貨（Demo）")).to_have_count(0)
    expect(page.get_by_role("button", name="確認收貨")).to_have_count(0)
    expect(page.get_by_role("button", name="取消訂單")).to_have_count(0)


def test_退貨駁回後可重新申請(page: Page) -> None:
    """R-7.11：駁回後同一筆訂單可再申請退貨。"""
    login(page)
    order_id = _complete_order(page, "再申請退貨測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "太短")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已完成")
    expect(page.get_by_role("button", name="申請退貨")).to_be_visible()
    apply_return(page, "第二次申請退貨原因足夠")
    expect(page.locator("main")).to_contain_text("退貨中")


def test_待審核可撤銷退貨申請(page: Page) -> None:
    """R-7.12：待審核時可撤銷，確認後回到已完成／無退貨。"""
    login(page)
    order_id = _complete_order(page, "撤銷退貨測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "想撤銷的退貨申請")

    revoke = page.get_by_role("button", name="撤銷退貨申請")
    expect(revoke).to_be_visible(timeout=15_000)
    page.once("dialog", lambda d: d.accept())
    revoke.click()
    expect(page.locator("main")).to_contain_text("已完成", timeout=15_000)
    expect(page.get_by_role("button", name="申請退貨")).to_be_visible()
    expect(page.get_by_role("button", name="撤銷退貨申請")).to_have_count(0)


def test_退貨原因字數限制與即時計數(page: Page) -> None:
    """R-16.4：1～200 字；不符時送出停用；顯示 {n}/200。"""
    login(page)
    order_id = _complete_order(page, "退貨字數測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    page.get_by_role("button", name="申請退貨").click()
    page.wait_for_url(re.compile(r".*/return"), timeout=15_000)

    textarea = page.locator("textarea").first
    submit = page.get_by_role("button", name="送出申請")
    expect(page.locator("main")).to_contain_text("/200")

    textarea.fill("")
    expect(submit).to_be_disabled()
    textarea.fill("足夠的退貨原因")
    expect(submit).to_be_enabled()
    expect(page.locator("main")).to_contain_text(re.compile(r"\d+/200"))


def test_退貨申請頁取消不建立申請(page: Page) -> None:
    """R-16.6：點取消回到詳情且仍為已完成。"""
    login(page)
    order_id = _complete_order(page, "退貨取消連結測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    page.get_by_role("button", name="申請退貨").click()
    page.wait_for_url(re.compile(r".*/return"), timeout=15_000)
    page.get_by_role("link", name="取消").click()
    expect(page).to_have_url(re.compile(rf".*/orders/{re.escape(order_id)}$"), timeout=15_000)
    expect(page.locator("main")).to_contain_text("已完成")


def test_非已完成訂單直開退貨頁導回詳情(page: Page) -> None:
    """R-16.8：待出貨訂單開啟 /return 應導回訂單詳情。"""
    login(page)
    order_id = _complete_order(page, "退貨直開測試")
    page.goto(f"/orders/{order_id}/return", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(rf".*/orders/{re.escape(order_id)}$"), timeout=15_000)
    expect(page.get_by_role("heading", name="訂單詳情")).to_be_visible()
    expect(page.locator("main")).to_contain_text("待出貨")
