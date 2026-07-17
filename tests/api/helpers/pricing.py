"""結帳 preview 金額斷言工具。"""

from __future__ import annotations

from typing import Any


def assert_preview_amounts(preview: dict[str, Any], **expected: int) -> None:
    """對照 CheckoutPreview 五欄位（snake_case 參數名）。"""
    mapping = {
        "subtotal": "subtotal",
        "bulk_discount": "bulkDiscount",
        "coupon_discount": "couponDiscount",
        "shipping": "shipping",
        "payable": "payable",
    }
    for key, value in expected.items():
        field = mapping[key]
        actual = preview[field]
        assert actual == value, f"{key} 預期 {value}，實際 {actual}"


def assert_pricing_order(preview: dict[str, Any]) -> None:
    """R-4.15：驗證應付 = 小計 − 滿額 − 券折 + 運費。"""
    computed = (
        preview["subtotal"]
        - preview["bulkDiscount"]
        - preview["couponDiscount"]
        + preview["shipping"]
    )
    assert preview["payable"] == computed, (
        f"計價順序不一致：payable={preview['payable']}，重算={computed}"
    )
