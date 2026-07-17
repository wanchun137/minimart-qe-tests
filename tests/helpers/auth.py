"""共用登入／登出工具（帳密來自題目說明書內建測試帳號，非環境密鑰）。"""

from __future__ import annotations

import re

from playwright.sync_api import Page

DEMO_EMAIL = "demo@minimart.test"
DEMO_PASSWORD = "demo1234"


def login(page: Page, email: str = DEMO_EMAIL, password: str = DEMO_PASSWORD) -> None:
    """以內建測試帳號登入，登入後停在商品列表頁。"""
    page.goto("/login", wait_until="domcontentloaded")
    page.fill("#login-email", email)
    page.fill("#login-password", password)
    page.click('button[type="submit"]')
    page.wait_for_url(lambda url: "/login" not in url, timeout=60_000)
    page.wait_for_selector(".product-grid", timeout=60_000)


def logout(page: Page) -> None:
    """點擊導覽列「登出」，回到登入頁。"""
    btn = page.get_by_role("button", name="登出")
    if btn.count():
        btn.click()
    else:
        page.get_by_role("link", name="登出").click()
    page.wait_for_url(re.compile(r".*/login"), timeout=60_000)
