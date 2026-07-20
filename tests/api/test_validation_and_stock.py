"""R-3.4、R-18：無效欄位、庫存不足與預期 HTTP 狀態碼。"""

from __future__ import annotations

import pytest

from tests.api.helpers.client import MiniMartApiClient


def test_登出後購物車清空(api: MiniMartApiClient) -> None:
    """R-1.7：登出 API 應清空購物車（v2.1 hotfix 已修復）。"""
    api.login()
    mug = api.product_by_name("手沖咖啡濾杯")
    api.add_to_cart(mug["id"], 1)
    assert api.get_cart()["count"] >= 1
    api.logout()
    cart = api.get_cart()
    assert cart["items"] == []
    assert cart["count"] == 0


def test_登入錯誤帳密回_401(api_context) -> None:
    """R-18.8：帳密錯誤回 401 與固定訊息。"""
    response = api_context.post(
        "/api/auth/login",
        data={"email": "demo@minimart.test", "password": "wrong"},
    )
    assert response.status == 401
    body = response.json()
    assert body["error"] == "INVALID_CREDENTIALS"
    assert body["message"] == "帳號或密碼錯誤"


def test_空購物車結帳回_400(authed_api: MiniMartApiClient) -> None:
    """R-12.8：購物車為空時 checkout 回 400 EMPTY_CART。"""
    response = authed_api.checkout()
    assert response.status == 400
    body = response.json()
    assert body["error"] == "EMPTY_CART"
    assert body["message"] == "購物車是空的"


@pytest.mark.xfail(reason="已知缺陷 D-07：後端未驗證 11 碼手機", strict=True)
def test_手機_11_碼驗證失敗回_400(authed_api: MiniMartApiClient) -> None:
    """R-18.4：手機須 09 開頭共 10 碼。"""
    mug = authed_api.product_by_name("手沖咖啡濾杯")
    authed_api.add_to_cart(mug["id"], 1)
    response = authed_api.checkout(phone="09123456789")
    assert response.status == 400
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert "phone" in body["errors"]


def test_收件人姓名空白回_400(authed_api: MiniMartApiClient) -> None:
    """R-18.3：姓名 1-20 字驗證。"""
    mug = authed_api.product_by_name("手沖咖啡濾杯")
    authed_api.add_to_cart(mug["id"], 1)
    response = authed_api.checkout(recipientName="")
    assert response.status == 400
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert "recipientName" in body["errors"]


def test_庫存不足結帳回_409(authed_api: MiniMartApiClient) -> None:
    """R-3.4：超過庫存整筆不成立，回 409 OUT_OF_STOCK。"""
    chair = authed_api.product_by_name("折疊露營椅")
    authed_api.add_to_cart(chair["id"], 1)
    authed_api.add_to_cart(chair["id"], 1)
    response = authed_api.checkout(recipientName="庫存不足 API 測試")
    assert response.status == 409
    body = response.json()
    assert body["error"] == "OUT_OF_STOCK"
    assert "折疊露營椅" in body["message"]


def test_不存在商品回_404(authed_api: MiniMartApiClient) -> None:
    response = authed_api.get_product(99999)
    assert response.status == 404
    body = response.json()
    assert body["error"] == "NOT_FOUND"
