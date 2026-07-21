"""R-14.4～R-14.8：訂單詳情五區塊與內容須對應該筆訂單。"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_with_quantity, clear_cart
from tests.helpers.checkout import fill_and_submit_checkout, format_nt, go_to_checkout
from tests.helpers.orders import cancel_order, open_order


def test_訂單詳情五區塊與商品收件資訊正確(page: Page) -> None:
    """R-14.4～R-14.8：詳情含訂單資訊／商品明細／金額摘要／收件資訊／狀態操作。"""
    product = "手沖咖啡濾杯"
    qty = 2
    recipient = "詳情核對買家"
    phone = "0912345678"
    address = "台北市詳情測試路 14 號"

    login(page)
    clear_cart(page)
    add_product_with_quantity(page, product, qty)
    go_to_checkout(page)
    preview = page.request.post("/api/checkout/preview", data={"couponCode": None})
    assert preview.ok, preview.text()
    payable = preview.json()["payable"]
    order_id = fill_and_submit_checkout(
        page, name=recipient, phone=phone, address=address
    )

    open_order(page, order_id)
    main = page.locator("main")

    # R-14.4 五區塊
    for heading in ("訂單資訊", "商品明細", "金額摘要", "收件資訊", "狀態與操作"):
        expect(main).to_contain_text(heading)

    # R-14.5 訂單資訊
    expect(main).to_contain_text(order_id)
    expect(main).to_contain_text("待出貨")

    # R-14.6 商品明細
    expect(main).to_contain_text(product)
    expect(main).to_contain_text(f"x{qty}")
    expect(main).to_contain_text("NT$480")

    # R-14.7 金額摘要含應付
    expect(main).to_contain_text("商品小計")
    expect(main).to_contain_text("應付金額")
    expect(main).to_contain_text(format_nt(payable))

    # R-14.8 收件資訊
    expect(main).to_contain_text(recipient)
    expect(main).to_contain_text(phone)
    expect(main).to_contain_text(address)

    # R-14.9 待出貨操作
    expect(page.get_by_role("button", name="模擬出貨（Demo）")).to_be_visible()


def test_已取消狀態顯示取消時間且無任何按鈕(page: Page) -> None:
    """R-14.9：已取消顯示取消時間；無任何按鈕。"""
    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "純棉素色 T 恤", 1)
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(
        page,
        name="已取消時間測試買家",
        phone="0912345678",
        address="台北市已取消測試路 88 號",
    )

    open_order(page, order_id)
    cancel_order(page, order_id)

    main_text = page.locator("main").inner_text()
    assert "已取消" in main_text
    assert re.search(r"取消時間\s*\d{4}-\d{2}-\d{2} \d{2}:\d{2}", main_text), (
        f"主畫面需出現 R-14.9 的「取消時間 YYYY-MM-DD HH:mm」，實際：{main_text[:2000]}"
    )

    # R-14.9：已取消無任何按鈕
    for btn in (
        "模擬出貨（Demo）",
        "取消訂單",
        "確認收貨",
        "申請退貨",
        "賣家審核（Demo）",
        "撤銷退貨申請",
    ):
        expect(page.get_by_role("button", name=btn)).to_have_count(0)
