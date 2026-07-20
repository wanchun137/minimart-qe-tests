"""R-14.1：訂單列表 API 排序與 openapi 合約。"""

from __future__ import annotations

from tests.api.helpers.client import MiniMartApiClient
from tests.helpers.orders import assert_orders_sorted_new_to_old


def test_訂單列表_API_依下單時間新到舊(authed_api: MiniMartApiClient) -> None:
    """R-14.1／openapi getOrders：全部訂單依下單時間由新到舊。"""
    orders = authed_api.get_orders()
    assert orders, "此帳號應至少有一筆訂單以驗證 API 排序"
    assert_orders_sorted_new_to_old([order["createdAt"] for order in orders])
