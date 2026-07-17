"""R-1.4 / R-9.4：商品列表加入後，導覽列徽章應即時反映件數。"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, cart_badge, clear_cart


@pytest.fixture(autouse=True)
def _logged_in_empty_cart(page: Page):
    login(page)
    clear_cart(page)


def test_商品列表加入後徽章即時更新為_1(page: Page) -> None:
    add_product_from_list(page, "純棉素色 T 恤")
    # 不離開商品列表，直接斷言徽章（對應 AI 報告 D-03）
    expect(cart_badge(page)).to_have_text("1", timeout=5_000)
