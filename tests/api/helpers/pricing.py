"""結帳 preview 金額斷言工具（R-2.6、R-4.15、R-5.1）。"""

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


def shipping_for_after_discount(after_discount: int) -> int:
    """R-5.1：依折扣後商品金額級距回傳運費（未套用免運券）。"""
    if after_discount < 500:
        return 80
    if after_discount < 1000:
        return 60
    if after_discount < 2000:
        return 30
    return 0


def assert_pricing_order(
    preview: dict[str, Any],
    *,
    free_shipping_coupon: bool = False,
) -> None:
    """R-4.15 七步計價＋R-2.6 折扣上限＋R-5.1 運費級距。"""
    subtotal = int(preview["subtotal"])
    bulk = int(preview["bulkDiscount"])
    coupon = int(preview["couponDiscount"])
    shipping = int(preview["shipping"])
    payable = int(preview["payable"])

    # R-2.6：折扣總額不得超過小計；折扣後商品金額 ≥ 0
    discount_total = min(bulk + coupon, subtotal)
    after_discount = subtotal - discount_total
    assert after_discount >= 0, (
        f"折扣後商品金額為負：小計 {subtotal}、滿額 {bulk}、券折 {coupon}"
    )

    if free_shipping_coupon:
        expected_shipping = 0
    else:
        expected_shipping = shipping_for_after_discount(after_discount)

    assert shipping == expected_shipping, (
        f"運費不符 R-5.1：折扣後 {after_discount} 預期運費 {expected_shipping}，"
        f"實際 {shipping}"
    )
    assert payable == after_discount + shipping, (
        f"計價順序不一致（R-4.15）：payable={payable}，"
        f"重算={after_discount + shipping}"
        f"（小計 {subtotal} − 折扣總額 {discount_total} + 運費 {shipping}）"
    )
