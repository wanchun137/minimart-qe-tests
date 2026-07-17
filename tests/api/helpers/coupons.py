"""優惠券可用性檢查。"""

from __future__ import annotations

import pytest

from tests.api.helpers.client import MiniMartApiClient


def require_unused_coupon(api: MiniMartApiClient, code: str) -> dict:
    """若券非「未使用」則 skip。"""
    coupon = next((c for c in api.get_coupons() if c["code"] == code), None)
    if coupon is None:
        pytest.skip(f"帳號無 {code} 優惠券")
    if coupon["status"] != "未使用":
        pytest.skip(f"{code} 狀態為「{coupon['status']}」，略過")
    return coupon
