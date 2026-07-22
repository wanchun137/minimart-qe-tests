"""R-2、R-4、R-5：運費、滿額折扣與應付金額精確斷言。"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from tests.helpers.auth import login
from tests.helpers.cart import add_product_with_quantity, clear_cart
from tests.helpers.checkout import (
    COUPON_CODES,
    assert_preview_amounts,
    expect_summary_matches_preview,
    format_nt,
    go_to_checkout,
    select_coupon,
    summary_row_value,
)


def test_咖啡濾杯兩件_PRD_範例_1_金額(page: Page) -> None:
    """R-5.6 範例 1：小計 960、運費 60、應付 1,020。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "手沖咖啡濾杯", 2)
    go_to_checkout(page)
    preview = expect_summary_matches_preview(page)
    assert_preview_amounts(
        preview,
        subtotal=960,
        bulk_discount=0,
        coupon_discount=0,
        shipping=60,
        payable=1020,
    )


def test_機械式鍵盤_PRD_範例_2_滿額折扣與免運(page: Page) -> None:
    """R-4.2、R-5.6 範例 2：小計 3,180、滿額 −159、運費 0、應付 3,021。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "機械式鍵盤", 1)
    go_to_checkout(page)
    preview = expect_summary_matches_preview(page)
    assert_preview_amounts(
        preview,
        subtotal=3180,
        bulk_discount=159,
        coupon_discount=0,
        shipping=0,
        payable=3021,
    )


def test_機械式鍵盤加滿三千折三百券_PRD_範例_3(page: Page) -> None:
    """R-4.8、R-5.6 範例 3：滿額 −159、券折 300、應付 2,721。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "機械式鍵盤", 1)
    go_to_checkout(page)
    select_coupon(page, "滿三千折三百券")
    preview = expect_summary_matches_preview(page, coupon_code=COUPON_CODES["滿三千折三百券"])
    assert_preview_amounts(
        preview,
        subtotal=3180,
        bulk_discount=159,
        coupon_discount=300,
        shipping=0,
        payable=2721,
    )


def test_滿額折扣列顯示減號格式(page: Page) -> None:
    """R-2.8：折扣金額行須以 −NT$ 格式顯示（含 Unicode 減號）。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "機械式鍵盤", 1)
    go_to_checkout(page)
    preview = expect_summary_matches_preview(page)
    assert preview["bulkDiscount"] > 0

    bulk_text = summary_row_value(page, "滿額折扣").inner_text()
    assert bulk_text.startswith("−NT$") or bulk_text.startswith("-NT$"), (
        f"滿額折扣應以減號開頭（R-2.8），實際 {bulk_text!r}"
    )
    expect(summary_row_value(page, "滿額折扣")).to_have_text(format_nt(preview["bulkDiscount"], as_discount=True))


def test_藍牙耳機_PRD_範例_4_百分比四捨五入(page: Page) -> None:
    """R-2.3、R-5.6 範例 4：2,150 × 5% = 108，應付 2,042。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "無線藍牙耳機", 1)
    go_to_checkout(page)
    preview = expect_summary_matches_preview(page)
    assert_preview_amounts(
        preview,
        subtotal=2150,
        bulk_discount=108,
        coupon_discount=0,
        shipping=0,
        payable=2042,
    )


def test_免運券不論級距運費為零(page: Page) -> None:
    """R-5.2：低金額訂單使用免運券，運費 NT$0。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "手沖咖啡濾杯", 1)
    go_to_checkout(page)
    free_label = page.locator("label.coupon-option", has_text="免運券").first
    if free_label.count() == 0:
        pytest.skip("免運券選項不存在")
    label_text = free_label.inner_text()
    if "已過期" in label_text or "已使用" in label_text:
        pytest.skip("免運券已過期或已使用")
    select_coupon(page, "免運券")
    preview = expect_summary_matches_preview(page, coupon_code=COUPON_CODES["免運券"])
    assert preview["shipping"] == 0
    assert preview["payable"] == 480
