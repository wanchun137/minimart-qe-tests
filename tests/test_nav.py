"""R-1.3：導覽列第五個目的地文字應為「我的優惠券」。"""

from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.helpers.auth import login


def test_第五個目的地文字為我的優惠券(page: Page) -> None:
    login(page)
    expect(page.get_by_role("link", name="我的優惠券")).to_be_visible()
