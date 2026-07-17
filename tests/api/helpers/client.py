"""MiniMart API 客戶端（依 openapi.yaml 合約）。"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse

from tests.helpers.auth import DEMO_EMAIL, DEMO_PASSWORD

VALID_CHECKOUT = {
    "recipientName": "API 測試買家",
    "phone": "0912345678",
    "address": "台北市中山區測試路 1 號",
}


class MiniMartApiClient:
    """以 Playwright APIRequestContext 操作 MiniMart REST API。"""

    def __init__(self, request: APIRequestContext) -> None:
        self._request = request

    def _json(self, response: APIResponse) -> Any:
        return response.json()

    def login(
        self,
        email: str = DEMO_EMAIL,
        password: str = DEMO_PASSWORD,
    ) -> dict[str, Any]:
        response = self._request.post(
            "/api/auth/login",
            data={"email": email, "password": password},
        )
        assert response.ok, f"登入失敗：{response.status} {response.text()}"
        return self._json(response)

    def logout(self) -> dict[str, Any]:
        response = self._request.post("/api/auth/logout")
        assert response.ok, f"登出失敗：{response.status} {response.text()}"
        return self._json(response)

    def get_products(self) -> list[dict[str, Any]]:
        response = self._request.get("/api/products")
        assert response.ok, f"商品列表失敗：{response.status} {response.text()}"
        return self._json(response)

    def get_product(self, product_id: int) -> APIResponse:
        return self._request.get(f"/api/products/{product_id}")

    def get_cart(self) -> dict[str, Any]:
        response = self._request.get("/api/cart")
        assert response.ok, f"取得購物車失敗：{response.status} {response.text()}"
        return self._json(response)

    def clear_cart(self) -> dict[str, Any]:
        cart = self.get_cart()
        for item in cart.get("items", []):
            self._request.delete(f"/api/cart/items/{item['productId']}")
        return self.get_cart()

    def add_to_cart(self, product_id: int, quantity: int = 1) -> dict[str, Any]:
        response = self._request.post(
            "/api/cart/items",
            data={"productId": product_id, "quantity": quantity},
        )
        assert response.ok, f"加入購物車失敗：{response.status} {response.text()}"
        return self._json(response)

    def patch_cart_item(self, product_id: int, quantity: int) -> APIResponse:
        return self._request.patch(
            f"/api/cart/items/{product_id}",
            data={"quantity": quantity},
        )

    def get_coupons(self) -> list[dict[str, Any]]:
        response = self._request.get("/api/coupons")
        assert response.ok, f"優惠券列表失敗：{response.status} {response.text()}"
        return self._json(response)

    def checkout_preview(self, coupon_code: str | None = None) -> dict[str, Any]:
        response = self._request.post(
            "/api/checkout/preview",
            data={"couponCode": coupon_code},
        )
        assert response.ok, f"preview 失敗：{response.status} {response.text()}"
        return self._json(response)

    def checkout(self, *, coupon_code: str | None = None, **fields: str) -> APIResponse:
        payload = {**VALID_CHECKOUT, **fields}
        if coupon_code is not None:
            payload["couponCode"] = coupon_code
        elif "couponCode" in fields:
            payload["couponCode"] = fields["couponCode"]
        return self._request.post("/api/checkout", data=payload)

    def get_orders(self) -> list[dict[str, Any]]:
        response = self._request.get("/api/orders")
        assert response.ok, f"訂單列表失敗：{response.status} {response.text()}"
        return self._json(response)

    def get_order(self, order_id: str) -> APIResponse:
        return self._request.get(f"/api/orders/{order_id}")

    def ship_order(self, order_id: str) -> APIResponse:
        return self._request.post(f"/api/orders/{order_id}/ship")

    def cancel_order(self, order_id: str) -> APIResponse:
        return self._request.post(f"/api/orders/{order_id}/cancel")

    def confirm_receipt(self, order_id: str) -> APIResponse:
        return self._request.post(f"/api/orders/{order_id}/confirm-receipt")

    def apply_return(self, order_id: str, reason: str) -> APIResponse:
        return self._request.post(f"/api/orders/{order_id}/returns", data={"reason": reason})

    def review_return(self, order_id: str) -> APIResponse:
        return self._request.post(f"/api/orders/{order_id}/returns/review")

    def withdraw_return(self, order_id: str) -> APIResponse:
        return self._request.post(f"/api/orders/{order_id}/returns/withdraw")

    def product_by_name(self, name: str) -> dict[str, Any]:
        for product in self.get_products():
            if product["name"] == name:
                return product
        raise AssertionError(f"找不到商品：{name}")

    def place_order_for_product(
        self,
        product_name: str,
        *,
        quantity: int = 1,
        recipient_name: str = "API 下單測試",
        coupon_code: str | None = None,
    ) -> str:
        """清空購物車、加入商品並下單，回傳訂單編號。"""
        self.clear_cart()
        product = self.product_by_name(product_name)
        self.add_to_cart(product["id"], quantity)
        kwargs: dict[str, str] = {"recipientName": recipient_name}
        if coupon_code is not None:
            kwargs["couponCode"] = coupon_code
        response = self.checkout(**kwargs)
        assert response.status == 201, f"下單失敗：{response.status} {response.text()}"
        return self._json(response)["orderId"]
