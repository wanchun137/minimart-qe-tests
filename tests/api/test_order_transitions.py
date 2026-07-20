"""R-6、R-7：訂單與退貨的合法、非法狀態轉換。"""

from __future__ import annotations

import pytest

from tests.api.helpers.client import MiniMartApiClient


@pytest.mark.xfail(reason="後端允許重複出貨，與 openapi CANNOT_SHIP 不符", strict=True)
def test_待出貨可出貨_已出貨不可重複出貨(authed_api: MiniMartApiClient) -> None:
    """R-6.3：僅待出貨可 ship；重複 ship 依 openapi 應回 409。"""
    order_id = authed_api.place_order_for_product("純棉素色 T 恤", recipient_name="出貨狀態 API")
    ship = authed_api.ship_order(order_id)
    assert ship.ok, f"出貨失敗：{ship.status} {ship.text()}"

    detail = authed_api.get_order(order_id).json()
    assert detail["status"] == "已出貨"
    assert detail["canShip"] is False

    again = authed_api.ship_order(order_id)
    assert again.status == 409, (
        f"重複出貨應回 409 CANNOT_SHIP，實際 {again.status} {again.text()}"
    )
    assert again.json()["error"] == "CANNOT_SHIP"


def test_已出貨可確認收貨_待出貨不可(authed_api: MiniMartApiClient) -> None:
    """R-6.4：僅已出貨可 confirm-receipt。"""
    order_id = authed_api.place_order_for_product("純棉素色 T 恤", recipient_name="收貨狀態 API")
    early = authed_api.confirm_receipt(order_id)
    assert early.status == 409
    assert early.json()["error"] == "CANNOT_CONFIRM"

    authed_api.ship_order(order_id)
    ok = authed_api.confirm_receipt(order_id)
    assert ok.ok, f"確認收貨失敗：{ok.status} {ok.text()}"
    assert authed_api.get_order(order_id).json()["status"] == "已完成"


def test_取消訂單_合法與非法狀態(authed_api: MiniMartApiClient) -> None:
    """R-6.5：待出貨可取消；已出貨後不可取消。"""
    order_id = authed_api.place_order_for_product("純棉素色 T 恤", recipient_name="取消狀態 API")
    cancel = authed_api.cancel_order(order_id)
    assert cancel.status != 404, (
        "POST /api/orders/{id}/cancel 未實作（R-6.5／openapi；見 D-23）"
    )
    assert cancel.ok, f"取消失敗：{cancel.status} {cancel.text()}"
    assert authed_api.get_order(order_id).json()["status"] == "已取消"

    order_id2 = authed_api.place_order_for_product("純棉素色 T 恤", recipient_name="取消拒絕 API")
    authed_api.ship_order(order_id2)
    denied = authed_api.cancel_order(order_id2)
    assert denied.status == 409
    assert denied.json()["error"] == "CANNOT_CANCEL"


def test_退貨申請_合法與非法狀態(authed_api: MiniMartApiClient) -> None:
    """R-7.1、R-7.3：已完成可申請；待出貨不可。"""
    order_id = authed_api.place_order_for_product("純棉素色 T 恤", recipient_name="退貨狀態 API")
    early = authed_api.apply_return(order_id, "尚未完成就想退")
    assert early.status == 409
    assert early.json()["error"] == "CANNOT_APPLY_RETURN"

    authed_api.ship_order(order_id)
    authed_api.confirm_receipt(order_id)
    empty_reason = authed_api.apply_return(order_id, "")
    assert empty_reason.status == 400
    assert empty_reason.json()["error"] == "INVALID_REASON"

    ok = authed_api.apply_return(order_id, "商品尺寸不合")
    assert ok.ok, f"退貨申請失敗：{ok.status} {ok.text()}"
    detail = authed_api.get_order(order_id).json()
    assert detail["status"] == "退貨中"
    assert detail["returnStatus"] == "待審核"


def test_退貨審核_僅待審核可執行(authed_api: MiniMartApiClient) -> None:
    """R-7.6-7.7：審核通過／駁回後不可重複審核。"""
    order_id = authed_api.place_order_for_product("純棉素色 T 恤", recipient_name="審核狀態 API")
    authed_api.ship_order(order_id)
    authed_api.confirm_receipt(order_id)
    authed_api.apply_return(order_id, "商品有瑕疵想退貨")

    review = authed_api.review_return(order_id)
    assert review.ok, f"審核失敗：{review.status} {review.text()}"

    again = authed_api.review_return(order_id)
    assert again.status == 409
    assert again.json()["error"] == "CANNOT_REVIEW"
