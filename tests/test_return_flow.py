"""R-7、R-16：退貨申請、審核通過／駁回與退款流程。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout
from tests.helpers.orders import apply_return, confirm_receipt, open_order, seller_review, ship_order


def _complete_order(page: Page, *, name: str) -> str:
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    return fill_and_submit_checkout(page, name=name)


def test_退貨原因不足五字審核駁回(page: Page) -> None:
    """R-7.7：原因 < 5 字駁回，訂單回到已完成。"""
    login(page)
    order_id = _complete_order(page, name="退貨駁回測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "太短")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已完成")
    expect(page.locator("main")).to_contain_text("退貨原因描述不足，請補充後重新申請")
    expect(page.get_by_role("button", name="申請退貨")).to_be_visible()


def test_退貨原因足夠審核通過並退款(page: Page) -> None:
    """R-7.7～R-7.9：原因 ≥ 5 字通過，訂單狀態為已退款。"""
    login(page)
    order_id = _complete_order(page, name="退貨通過測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "商品有瑕疵想退")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已退款", timeout=30_000)
    expect(page.get_by_role("button", name="確認收貨")).to_have_count(0)
    expect(page.get_by_role("button", name="取消訂單")).to_have_count(0)


def test_退貨申請頁顯示預計退款金額不含運費(page: Page) -> None:
    """R-16.3：預計退款 = 應付 − 運費（T 恤 400 + 運費 80）。"""
    login(page)
    order_id = _complete_order(page, name="退款金額測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    page.get_by_role("button", name="申請退貨").click()
    page.wait_for_url(re.compile(r".*/return"))
    expect(page.locator("main")).to_contain_text("預計退款金額")
    expect(page.locator("main")).to_contain_text("NT$400")
    expect(page.locator("main")).to_contain_text("不含運費")
