"""R-8.2／R-8.3～R-8.8／R-15：下單確認與其他通知類型、已讀行為。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, add_product_with_quantity, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, format_nt, go_to_checkout
from tests.helpers.orders import (
    apply_return,
    confirm_receipt,
    open_order,
    seller_review,
    ship_order,
)


def _wait_notifications(page: Page) -> None:
    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )


def _notification_row(page: Page, title_substr: str):
    return page.get_by_test_id("notification-row").filter(has_text=title_substr).first


def test_下單確認通知標題與商品明細對應該筆訂單(page: Page) -> None:
    """R-8.2：標題含訂單編號；內文商品明細為「{名稱} × {數量}」且對應該筆訂單。"""
    product_name = "手沖咖啡濾杯"
    quantity = 3
    recipient = "通知對帳買家"

    login(page)
    clear_cart(page)
    add_product_with_quantity(page, product_name, quantity)
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(
        page,
        name=recipient,
        address="台北市通知測試路 8 號",
    )

    _wait_notifications(page)
    row = _notification_row(page, f"訂單 {order_id} 已成立")
    expect(row).to_be_visible(timeout=20_000)

    expect(row.locator(".notification-title")).to_have_text(f"訂單 {order_id} 已成立")

    body = row.locator("[data-testid^='notification-body']")
    expect(body).to_be_visible()
    body_text = body.inner_text()

    line = f"{product_name} × {quantity}"
    expect(body).to_contain_text(line)
    product_lines = [ln.strip() for ln in body_text.splitlines() if " × " in ln]
    assert len(product_lines) == 1, f"預期 1 行商品明細，實際 {product_lines!r}"
    assert product_lines[0] == line
    expect(body).to_contain_text(f"收件人 {recipient}")


def test_多品項訂單_通知商品明細行數與內容一致(page: Page) -> None:
    """R-15.7：商品明細行數等於訂單商品項數；R-8.2：每一行對應該筆訂單。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "手沖咖啡濾杯")
    add_product_from_list(page, "手沖咖啡濾杯")
    add_product_from_list(page, "不鏽鋼保溫瓶")
    go_to_checkout(page)

    preview = page.request.post("/api/checkout/preview", data={"couponCode": None})
    assert preview.ok, preview.text()
    payable = preview.json()["payable"]

    order_id = fill_and_submit_checkout(
        page,
        name="多品項通知買家",
        address="台北市通知測試路 15 號",
    )

    _wait_notifications(page)
    row = _notification_row(page, f"訂單 {order_id} 已成立")
    expect(row).to_be_visible(timeout=20_000)
    body = row.locator("[data-testid^='notification-body']")
    body_text = body.inner_text()

    expect(body).to_contain_text("手沖咖啡濾杯 × 2")
    expect(body).to_contain_text("不鏽鋼保溫瓶 × 1")
    product_lines = [ln.strip() for ln in body_text.splitlines() if " × " in ln]
    assert len(product_lines) == 2, f"預期 2 行商品明細，實際 {product_lines!r}"

    expect(body).to_contain_text(f"應付金額 {format_nt(payable)}")
    expect(body).to_contain_text("收件人 多品項通知買家")


def test_出貨後產生出貨通知(page: Page) -> None:
    """R-8.3：狀態轉已出貨時新增「訂單 {id} 已出貨」。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="出貨通知測試")
    open_order(page, order_id)
    ship_order(page, order_id)

    _wait_notifications(page)
    row = _notification_row(page, f"訂單 {order_id} 已出貨")
    expect(row).to_be_visible(timeout=20_000)
    expect(row.locator(".notification-title")).to_have_text(f"訂單 {order_id} 已出貨")

    detail = page.request.get(f"/api/orders/{order_id}")
    assert detail.ok, detail.text()
    shipped_at = detail.json().get("shippedAt")
    assert shipped_at, "出貨後 API 應有 shippedAt"

    body = row.locator("[data-testid^='notification-body']")
    expect(body).to_be_visible()
    body_text = body.inner_text()
    assert shipped_at in body_text or re.search(
        rf"出貨時間\s*{re.escape(shipped_at)}", body_text
    ), f"出貨通知內文應含出貨時間 {shipped_at!r}（R-8.3），實際：{body_text!r}"


def test_退貨申請與退款完成產生對應通知(page: Page) -> None:
    """R-8.4／R-8.6：退貨受理與退款完成通知標題對應該筆訂單。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="退貨通知測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "商品有瑕疵想退貨")

    _wait_notifications(page)
    accept_row = _notification_row(page, f"訂單 {order_id} 的退貨申請已送出")
    expect(accept_row).to_be_visible(timeout=20_000)
    expect(accept_row).to_contain_text("商品有瑕疵想退貨")

    open_order(page, order_id)
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已退款", timeout=30_000)

    _wait_notifications(page)
    refund_row = _notification_row(page, f"訂單 {order_id} 已退款")
    expect(refund_row).to_be_visible(timeout=20_000)
    expect(refund_row).to_contain_text(re.compile(r"退款金額\s*NT\$"))


def test_點擊通知後轉為已讀且未讀數減少(page: Page) -> None:
    """R-8.8／R-15.3／R-15.4：點擊後藍點消失；未讀則數減少。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="已讀通知測試")

    _wait_notifications(page)
    unread_label = page.locator(".notifications-unread-count")
    expect(unread_label).to_be_visible()
    before_text = unread_label.inner_text()
    before_n = int(re.search(r"(\d+)", before_text).group(1))

    row = _notification_row(page, f"訂單 {order_id} 已成立")
    expect(row).to_be_visible(timeout=20_000)
    expect(row.get_by_test_id("unread-dot")).to_be_visible()
    row.click()
    expect(row.get_by_test_id("unread-dot")).to_have_count(0, timeout=10_000)

    after_text = unread_label.inner_text()
    after_n = int(re.search(r"(\d+)", after_text).group(1))
    assert after_n == before_n - 1, f"未讀應減 1：{before_n} → {after_n}"


def test_全部標為已讀後未讀歸零(page: Page) -> None:
    """R-15.5：全部標為已讀後未讀則數為 0。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    fill_and_submit_checkout(page, name="全部已讀測試")

    _wait_notifications(page)
    page.get_by_role("button", name="全部標為已讀").click()
    expect(page.locator(".notifications-unread-count")).to_contain_text("未讀 0 則", timeout=10_000)
    # 導覽列不應再顯示未讀數字徽章（允許尾端空白）
    nav_text = page.get_by_role("link", name=re.compile(r"通知中心")).inner_text().strip()
    assert not re.search(r"\d", nav_text), f"導覽通知徽章應消失，實際：{nav_text!r}"
