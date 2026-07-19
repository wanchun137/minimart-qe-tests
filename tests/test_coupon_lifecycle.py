"""R-4.12～R-4.14：下單後券狀態、返還與到期邊界。"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import (
    fill_and_submit_checkout,
    go_to_checkout,
    select_coupon,
    summary_row_value,
)
from tests.helpers.orders import (
    apply_return,
    cancel_order,
    confirm_receipt,
    open_order,
    seller_review,
    ship_order,
)


def _select_usable_low_threshold_coupon(page: Page) -> str:
    """選一張低金額訂單可用的券，回傳券名稱。"""
    for name in ("新人小禮券", "免運券"):
        option = page.locator("label.coupon-option", has_text=name)
        if option.count():
            select_coupon(page, name)
            return name
    pytest.skip("無低門檻可用優惠券")


def test_下單後使用的優惠券變為已使用並記錄完整訂單編號(page: Page) -> None:
    """R-4.12／R-17.7：用券下單後，「已使用」頁籤顯示完整 MM- 訂單編號。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    coupon_name = _select_usable_low_threshold_coupon(page)
    if coupon_name == "免運券":
        expect(summary_row_value(page, "運費")).to_have_text("NT$0", timeout=10_000)
    elif coupon_name == "新人小禮券":
        expect(summary_row_value(page, "應付金額")).to_have_text("NT$460", timeout=10_000)
    order_id = fill_and_submit_checkout(page, name="用券狀態測試")
    serial = order_id.removeprefix("MM-")

    page.goto("/coupons", wait_until="domcontentloaded")
    page.get_by_role("button", name=re.compile(r"^已使用")).click()
    page.wait_for_timeout(600)
    used_text = page.locator("main").inner_text()

    if coupon_name not in used_text and serial not in used_text:
        page.get_by_role("button", name=re.compile(r"^可使用")).click()
        avail = page.locator("main").inner_text()
        if coupon_name in avail:
            raise AssertionError(
                f"用券下單後「{coupon_name}」仍在可使用、未進入已使用（R-4.12／D-19）"
            )
        raise AssertionError(f"已使用頁籤找不到「{coupon_name}」或訂單 {order_id}")

    # R-6.9／R-17.7：應為完整訂單編號（含 MM-）；缺前綴則為 D-18
    assert order_id in used_text, (
        f"已使用券訂單編號缺少 MM- 前綴（D-18／R-17.7）：預期 {order_id}，"
        f"頁面可見片段含 {serial!r}"
    )


def test_已使用頁籤訂單編號應含MM前綴(page: Page) -> None:
    """R-17.7／R-6.9：已使用券上的訂單編號須為完整 MM- 格式（D-18）。"""
    login(page)
    page.goto("/coupons", wait_until="domcontentloaded")
    page.get_by_role("button", name=re.compile(r"^已使用")).click()
    page.wait_for_timeout(500)
    text = page.locator("main").inner_text()
    refs = re.findall(r"訂單編號\s+(\S+)", text)
    if not refs:
        pytest.skip("尚無已使用券可驗證編號格式")
    bad = [r for r in refs if not r.startswith("MM-")]
    assert not bad, f"已使用券訂單編號缺少 MM- 前綴（D-18）：{bad}"



def test_退款後優惠券應返還為未使用(page: Page) -> None:
    """R-4.13：退款完成後，該筆訂單使用的券狀態變回未使用。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    coupon_name = _select_usable_low_threshold_coupon(page)
    order_id = fill_and_submit_checkout(page, name="還券退款測試")

    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "商品有瑕疵想退貨")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已退款", timeout=30_000)

    page.goto("/coupons", wait_until="domcontentloaded")
    page.get_by_role("button", name=re.compile(r"^可使用")).click()
    expect(page.get_by_test_id("coupon-card").filter(has_text=coupon_name)).to_be_visible(
        timeout=15_000
    )


def test_取消訂單後優惠券應返還(page: Page) -> None:
    """R-4.13：取消訂單後券返還未使用。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    coupon_name = _select_usable_low_threshold_coupon(page)
    order_id = fill_and_submit_checkout(page, name="還券取消測試")

    open_order(page, order_id)
    if page.get_by_role("button", name="取消訂單").count() == 0:
        probe = page.request.post(f"/api/orders/{order_id}/cancel")
        if probe.status == 404:
            pytest.skip("此環境未實作取消訂單，無法驗證還券")
    cancel_order(page, order_id)

    page.goto("/coupons", wait_until="domcontentloaded")
    page.get_by_role("button", name=re.compile(r"^可使用")).click()
    expect(page.get_by_test_id("coupon-card").filter(has_text=coupon_name)).to_be_visible()


def test_已過期券不可在結帳選用(page: Page) -> None:
    """R-4.14／R-4.11：已過期券顯示「已過期」且不可點選。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    expect(page.locator("main")).to_contain_text("舊版折五十券")
    expect(page.locator("main")).to_contain_text("已過期")
    expect(page.get_by_role("radio", name=re.compile(r"舊版折五十券"))).to_have_count(0)
