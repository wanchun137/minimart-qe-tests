"""登入／登出主路徑（R-1.2、R-1.10、R-18.8）。"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import DEMO_EMAIL, login, logout


@pytest.mark.smoke
def test_正確帳密可登入並進入商品列表(page: Page) -> None:
    login(page)
    expect(page.locator(".product-grid")).to_be_visible()
    expect(page.get_by_text(DEMO_EMAIL)).to_be_visible()


def test_錯誤密碼顯示帳號或密碼錯誤(page: Page) -> None:
    page.goto("/login", wait_until="domcontentloaded")
    page.fill("#login-email", DEMO_EMAIL)
    page.fill("#login-password", "wrong-password")
    page.click('button[type="submit"]')
    expect(page.get_by_text("帳號或密碼錯誤")).to_be_visible()


def test_登出後回到登入頁(page: Page) -> None:
    login(page)
    logout(page)
    expect(page).to_have_url(re.compile(r".*/login"))
    expect(page.locator("#login-email")).to_be_visible()
