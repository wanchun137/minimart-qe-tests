"""
Playwright pytest 共用設定。

受測網址一律由環境變數 BASE_URL 決定，禁止寫死。
例：
  BASE_URL=https://example.ts.net pytest
"""

from __future__ import annotations

import os
import warnings

import pytest
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "http://localhost:3000"


def get_base_url() -> str:
    """讀取 BASE_URL；未設定時警告並回退本機預設。"""
    base_url = os.environ.get("BASE_URL", "").strip()
    if not base_url:
        warnings.warn(
            "[config] 未設定 BASE_URL，將使用 http://localhost:3000"
            "（收卷時請務必指定真實環境）",
            UserWarning,
            stacklevel=2,
        )
        return DEFAULT_BASE_URL
    return base_url.rstrip("/")


@pytest.fixture(scope="session")
def base_url() -> str:
    """供 pytest-playwright 的 page.goto('/') 等相對路徑使用。"""
    return get_base_url()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """忽略自簽／企業憑證問題，並縮小失敗影片尺寸以減少片頭空檔。"""
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "record_video_size": {"width": 800, "height": 600},
    }
