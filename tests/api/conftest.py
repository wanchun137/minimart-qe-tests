"""API 層測試共用 fixture（Playwright APIRequestContext）。"""

from __future__ import annotations

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from tests.api.helpers.client import MiniMartApiClient


@pytest.fixture
def api_context(playwright: Playwright, base_url: str) -> APIRequestContext:
    """未登入的 API request context；測試結束自動釋放。"""
    context = playwright.request.new_context(
        base_url=base_url,
        ignore_https_errors=True,
    )
    yield context
    context.dispose()


@pytest.fixture
def api(api_context: APIRequestContext) -> MiniMartApiClient:
    """未登入 API 客戶端。"""
    return MiniMartApiClient(api_context)


@pytest.fixture
def authed_api(api: MiniMartApiClient) -> MiniMartApiClient:
    """已登入且購物車已清空的 API 客戶端。"""
    api.login()
    api.clear_cart()
    return api
