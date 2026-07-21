"""R-4.10、R-4.11、R-12.4、R-12.5：結帳換券、取消套用、不可用券與折抵列顯示。"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import go_to_checkout, summary_row_value


def _click_any_usable_coupon(page: Page) -> None:
    labels = page.locator("label.coupon-option")
    for i in range(labels.count()):
        lab = labels.nth(i)
        text = lab.inner_text()
        if "不使用" in text:
            continue
        radio = lab.locator("input[type='radio']")
        if radio.count() and radio.is_disabled():
            continue
        lab.click()
        return
    pytest.skip("無可用優惠券，無法驗證取消套用路徑")


def test_結帳切換優惠券直接改用後者無確認框(page: Page) -> None:
    """R-4.10：已選一張再選另一張，直接改用新券、無確認對話框。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)

    dialogs: list[str] = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    expect(summary_row_value(page, "應付金額")).to_have_text("NT$480")

    page.get_by_role("radio", name=re.compile(r"新人小禮券")).click()
    expect(summary_row_value(page, "應付金額")).to_have_text("NT$460")

    page.get_by_role("radio", name=re.compile(r"免運券")).click()
    expect(summary_row_value(page, "運費")).to_have_text("NT$0")
    expect(summary_row_value(page, "應付金額")).to_have_text("NT$400")
    assert dialogs == [], f"切換優惠券不應出現對話框：{dialogs}"


def test_點選不使用優惠券取消套用(page: Page) -> None:
    """R-12.4：選券後點「不使用優惠券」，取消套用並還原金額摘要。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)

    baseline_payable = summary_row_value(page, "應付金額").inner_text()
    baseline_coupon = summary_row_value(page, "優惠券折抵").inner_text()
    expect(page.get_by_role("radio", name="不使用優惠券")).to_be_checked()

    _click_any_usable_coupon(page)
    expect(page.get_by_role("radio", name="不使用優惠券")).not_to_be_checked()
    expect(summary_row_value(page, "應付金額")).not_to_have_text(baseline_payable)

    page.get_by_role("radio", name="不使用優惠券").click()
    expect(page.get_by_role("radio", name="不使用優惠券")).to_be_checked()
    expect(summary_row_value(page, "應付金額")).to_have_text(baseline_payable)
    expect(summary_row_value(page, "優惠券折抵")).to_have_text(baseline_coupon)


def test_選用金額券時優惠券折抵列應顯示折抵(page: Page) -> None:
    """R-12.5／R-4.8：選用新人小禮券後，「優惠券折抵」列應顯示折抵金額（非 NT$0）。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    page.get_by_role("radio", name=re.compile(r"新人小禮券")).click()
    expect(summary_row_value(page, "應付金額")).to_have_text("NT$460")
    expect(summary_row_value(page, "優惠券折抵")).to_contain_text("20")


def test_未達門檻券顯示原因且不可點選(page: Page) -> None:
    """R-4.11：未達門檻券標示「未達使用門檻」，且無可用 radio。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")  # 小計 400 < 1000
    go_to_checkout(page)

    coupon_block = page.locator("main")
    expect(coupon_block).to_contain_text("滿千折百券")
    expect(coupon_block).to_contain_text("未達使用門檻 NT$1,000")
    expect(page.get_by_role("radio", name=re.compile(r"滿千折百券"))).to_have_count(0)
