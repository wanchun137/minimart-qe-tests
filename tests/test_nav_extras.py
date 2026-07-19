"""R-1.5、R-1.8：通知徽章與登出後資料保留。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login, logout
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout


def _notif_nav(page: Page):
    return page.locator("nav a[href='/notifications'], a[href='/notifications']").first


def test_通知中心徽章反映未讀則數且為零時不顯示數字(page: Page) -> None:
    """R-1.5：未讀 >0 時導覽顯示數字；全部已讀後不顯示數字徽章。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    fill_and_submit_checkout(page, name="徽章測試")

    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    # 先從任一頁讀取導覽徽章（不依賴通知頁本身的未讀文案）
    nav_html = _notif_nav(page).evaluate("e => e.innerText")
    badge = page.locator("[data-testid='notification-badge'], .nav-badge, .notification-badge")
    has_digit = bool(re.search(r"\d", nav_html)) or badge.count() > 0
    assert has_digit, f"下單後導覽「通知中心」應顯示未讀徽章，實際文字={nav_html!r}"

    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )
    page.get_by_role("button", name="全部標為已讀").click()
    expect(page.locator(".notifications-unread-count")).to_contain_text("未讀 0 則")
    page.goto("/", wait_until="domcontentloaded")
    nav_after = _notif_nav(page).inner_text().strip()
    assert not re.search(r"\d", nav_after), f"未讀 0 時不應顯示數字，實際 {nav_after!r}"


def test_登出再登入後訂單與通知仍保留(page: Page) -> None:
    """R-1.8：訂單、通知在登出後仍然保留。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="登出保留測試")

    logout(page)
    login(page)

    page.goto("/orders", wait_until="domcontentloaded")
    expect(page.locator(".order-row").filter(has_text=order_id)).to_be_visible(timeout=15_000)

    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )
    expect(
        page.get_by_test_id("notification-row").filter(has_text=order_id)
    ).to_be_visible(timeout=15_000)
