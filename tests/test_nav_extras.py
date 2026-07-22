"""R-1.5、R-1.8：通知徽章與登出後資料保留。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login, logout
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, go_to_checkout


def _notif_nav(page: Page):
    return page.locator("nav a[href='/notifications'], a[href='/notifications']").first


def _unread_count_from_notifications_page(page: Page) -> int:
    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )
    label = page.locator(".notifications-unread-count").inner_text()
    match = re.search(r"(\d+)", label)
    assert match, f"無法解析未讀則數：{label!r}"
    return int(match.group(1))


def _nav_badge_text(page: Page) -> str:
    badge = page.locator(
        "[data-testid='notification-badge'], .nav-badge, .notification-badge"
    )
    if badge.count() > 0 and badge.first.is_visible():
        return badge.first.inner_text().strip()
    nav_text = _notif_nav(page).inner_text().strip()
    match = re.search(r"(\d+|99\+)", nav_text)
    return match.group(1) if match else ""


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


def test_通知徽章未讀數與通知頁一致(page: Page) -> None:
    """R-1.5：導覽徽章數字須等於通知頁「未讀 N 則」的 N。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    fill_and_submit_checkout(page, name="徽章精確值測試")

    unread_n = _unread_count_from_notifications_page(page)
    assert unread_n > 0, "下單後應至少有 1 則未讀通知"

    page.goto("/", wait_until="domcontentloaded")
    badge_text = _nav_badge_text(page)
    if "99+" in badge_text:
        assert unread_n > 99, f"徽章為 99+ 時未讀應 >99，實際 {unread_n}"
    else:
        match = re.search(r"(\d+)", badge_text)
        assert match, f"導覽徽章應顯示未讀數字，實際 {badge_text!r}"
        assert int(match.group(1)) == unread_n, (
            f"徽章 {match.group(1)} 與通知頁未讀 {unread_n} 不一致"
        )


def test_未讀超過99則導覽徽章顯示99加(page: Page) -> None:
    """R-1.5：未讀 >99 時導覽徽章顯示「99+」。"""
    login(page)
    fake_notifications = [
        {
            "id": i,
            "type": "ORDER_CONFIRMED",
            "orderId": f"MM-20260701-{i:04d}",
            "title": f"測試通知 {i}",
            "body": "測試內文",
            "createdAt": "2026-07-01 10:00",
            "read": False,
        }
        for i in range(1, 101)
    ]

    def fulfill_notifications(route) -> None:
        route.fulfill(status=200, json=fake_notifications)

    page.route("**/api/notifications", fulfill_notifications)
    page.goto("/", wait_until="domcontentloaded")
    badge_text = _nav_badge_text(page)
    assert "99+" in badge_text, f"未讀 >99 時徽章應顯示 99+，實際 {badge_text!r}"


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
