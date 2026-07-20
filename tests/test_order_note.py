"""PRD v2.1 增補：訂單備註（R-12.12、R-14.11、R-18.10）。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout
from tests.helpers.orders import open_order


def _prepare_checkout(page: Page) -> None:
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)


def _fill_recipient(page: Page) -> None:
    page.fill("#checkout-name", "備註測試買家")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市備註測試路 21 號")


def test_結帳頁訂單備註區塊位置標籤與字數(page: Page) -> None:
    """R-12.12：備註在收件資訊下方、優惠券上方；標籤與 0/100。"""
    _prepare_checkout(page)

    note_section = page.locator("section.checkout-section").filter(
        has=page.get_by_role("heading", name="訂單備註")
    )
    expect(note_section).to_be_visible()
    expect(page.get_by_label("訂單備註（選填）")).to_be_visible()
    expect(page.locator(".checkout-note-count")).to_have_text("0/100")

    main_text = page.locator(".checkout-main").inner_text()
    idx_recipient = main_text.find("收件資訊")
    idx_note = main_text.find("訂單備註")
    idx_coupon = main_text.find("優惠券")
    assert idx_recipient != -1 and idx_note != -1 and idx_coupon != -1
    assert idx_recipient < idx_note < idx_coupon

    page.fill("#checkout-note", "你好")
    expect(page.locator(".checkout-note-count")).to_have_text("2/100")


def test_備註留空可送出且詳情顯示無備註(page: Page) -> None:
    """R-12.12／R-14.11／R-18.10：選填留空可送出；詳情顯示（無備註）。"""
    _prepare_checkout(page)
    _fill_recipient(page)
    expect(page.get_by_role("button", name="送出訂單")).to_be_enabled()
    expect(page.locator(".field-error", has_text="訂單備註")).to_have_count(0)

    order_id = fill_and_submit_checkout(
        page,
        name="備註測試買家",
        address="台北市備註測試路 21 號",
    )
    # R-13：完成頁不顯示備註
    complete = page.locator("main").inner_text()
    assert "訂單備註" not in complete
    assert "（無備註）" not in complete

    open_order(page, order_id)
    note_block = page.locator(".order-detail-note")
    expect(note_block).to_have_text("（無備註）")


def test_填寫備註可在詳情查看且保留換行(page: Page) -> None:
    """R-14.11：有備註時逐字顯示並保留換行；列表／通知不含備註。"""
    note = "請晚上送\n門鈴壞了請電聯"
    _prepare_checkout(page)
    order_id = fill_and_submit_checkout(
        page,
        name="備註內容買家",
        address="台北市備註測試路 22 號",
        note=note,
    )

    # 完成頁不顯示備註內容區塊
    expect(page.locator(".order-detail-note")).to_have_count(0)
    assert note.split("\n")[0] not in page.locator("main").inner_text()

    page.goto("/orders", wait_until="domcontentloaded")
    row = page.locator(".order-row").filter(has_text=order_id).first
    expect(row).to_be_visible(timeout=15_000)
    row_text = row.inner_text()
    assert "請晚上送" not in row_text
    assert "訂單備註" not in row_text

    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )
    notif = page.get_by_test_id("notification-row").filter(has_text=order_id).first
    expect(notif).to_be_visible(timeout=15_000)
    notif_text = notif.inner_text()
    assert "請晚上送" not in notif_text
    assert "門鈴壞了" not in notif_text

    open_order(page, order_id)
    note_el = page.locator(".order-detail-note")
    expect(note_el).to_be_visible()
    expect(note_el).to_have_text(note)
    white_space = note_el.evaluate("el => getComputedStyle(el).whiteSpace")
    assert white_space in ("pre-line", "pre-wrap", "pre"), white_space


def test_僅空白備註視為未填並去除前後空白後儲存(page: Page) -> None:
    """R-18.10：全空白視為未填；有內容時以 trim 後結果儲存。"""
    _prepare_checkout(page)
    _fill_recipient(page)
    page.fill("#checkout-note", "   \n  ")
    expect(page.get_by_role("button", name="送出訂單")).to_be_enabled()
    page.get_by_role("button", name="送出訂單").click()
    page.wait_for_url(re.compile(r".*/orders/.+/complete"), timeout=30_000)
    blank_order = re.search(r"/orders/(MM-[^/]+)/complete", page.url).group(1)

    open_order(page, blank_order)
    expect(page.locator(".order-detail-note")).to_have_text("（無備註）")

    # 第二筆：前後空白應被去除後儲存
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(
        page,
        name="備註Trim買家",
        address="台北市備註測試路 23 號",
        note="  請放門口  ",
    )
    open_order(page, order_id)
    expect(page.locator(".order-detail-note")).to_have_text("請放門口")


def test_備註超過一百字顯示錯誤並停用送出(page: Page) -> None:
    """R-18.10：trim 後超過 100 字紅字錯誤且送出停用；剛好 100 字可送。"""
    _prepare_checkout(page)
    _fill_recipient(page)
    submit = page.get_by_role("button", name="送出訂單")

    over = "一" * 101
    page.fill("#checkout-note", over)
    expect(page.locator(".checkout-note-count")).to_have_text("101/100")
    expect(page.locator(".field-error")).to_have_text("訂單備註不可超過 100 個字")
    expect(submit).to_be_disabled()

    exact = "二" * 100
    page.fill("#checkout-note", exact)
    expect(page.locator(".checkout-note-count")).to_have_text("100/100")
    expect(page.locator(".field-error", has_text="訂單備註")).to_have_count(0)
    expect(submit).to_be_enabled()

    page.get_by_role("button", name="送出訂單").click()
    page.wait_for_url(re.compile(r".*/orders/.+/complete"), timeout=30_000)
    order_id = re.search(r"/orders/(MM-[^/]+)/complete", page.url).group(1)
    open_order(page, order_id)
    expect(page.locator(".order-detail-note")).to_have_text(exact)


def test_備註前後空白超過一百時以_trim_後長度驗證(page: Page) -> None:
    """R-18.10：字數以去除前後空白後計算。"""
    _prepare_checkout(page)
    _fill_recipient(page)
    # 原始 102 字、trim 後 100 字 → 應允許送出
    padded_ok = "  " + ("三" * 100) + "  "
    page.fill("#checkout-note", padded_ok)
    expect(page.get_by_role("button", name="送出訂單")).to_be_enabled()
    expect(page.locator(".field-error", has_text="訂單備註")).to_have_count(0)

    # trim 後 101 字 → 應失敗
    padded_bad = "  " + ("四" * 101) + "  "
    page.fill("#checkout-note", padded_bad)
    expect(page.locator(".field-error")).to_have_text("訂單備註不可超過 100 個字")
    expect(page.get_by_role("button", name="送出訂單")).to_be_disabled()
