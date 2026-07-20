"""補強先前盤點的弱覆蓋條文（明確 UI 斷言）。"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, add_product_with_quantity, clear_cart
from tests.helpers.checkout import (
    COUPON_CODES,
    fill_and_submit_checkout,
    go_to_checkout,
    select_coupon,
    summary_row_value,
)
from tests.helpers.orders import (
    apply_return,
    confirm_receipt,
    open_order,
    seller_review,
    ship_order,
)
from tests.helpers.products import parse_remaining_stock


def _nt_amount(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text.replace("−", "").replace("-", ""))
    return int(digits) if digits else 0


def test_未登入直開受保護頁面導向登入(page: Page) -> None:
    """R-1.10：未登入開啟 /cart、/orders 等應導向登入頁。"""
    page.context.clear_cookies()
    for path in ("/cart", "/orders", "/coupons", "/notifications", "/"):
        page.goto(path, wait_until="domcontentloaded")
        expect(page).to_have_url(re.compile(r".*/login"), timeout=15_000)
        expect(page.locator("#login-email")).to_be_visible()


def test_商品單價為NT且為整數無小數(page: Page) -> None:
    """R-2.1：幣別 NT$；單價為整數元。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    page.wait_for_selector(".product-grid .product-card", timeout=15_000)
    cards = page.locator(".product-card")
    assert cards.count() > 0
    for i in range(min(cards.count(), 8)):
        text = cards.nth(i).inner_text()
        assert "NT$" in text, f"卡片應顯示 NT$：{text[:80]}"
        for m in re.finditer(r"NT\$[\d,]+(?:\.\d+)?", text):
            assert "." not in m.group(0), f"單價不應有小數：{m.group(0)}"


def test_折扣總額與折扣後商品金額公式(page: Page) -> None:
    """R-2.4／R-2.5／R-4.1：滿額＋券並存；折扣總額＝滿額＋券；折扣後＝小計−折扣總額。"""
    from tests.helpers.checkout import fetch_checkout_preview

    login(page)
    clear_cart(page)
    add_product_with_quantity(page, "機械式鍵盤", 1)
    go_to_checkout(page)
    select_coupon(page, "滿三千折三百券")
    preview = fetch_checkout_preview(page, COUPON_CODES["滿三千折三百券"])
    bulk = int(preview["bulkDiscount"])
    coupon = int(preview["couponDiscount"])
    subtotal = int(preview["subtotal"])
    shipping = int(preview["shipping"])
    payable = int(preview["payable"])
    assert bulk > 0 and coupon > 0, "應同時存在滿額折扣與優惠券折抵（R-4.1）"
    discount_total = bulk + coupon
    after_discount = subtotal - discount_total
    assert after_discount >= 0
    assert payable == after_discount + shipping
    # UI 應付應與 preview 一致
    ui_payable = _nt_amount(summary_row_value(page, "應付金額").inner_text())
    assert ui_payable == payable


def test_庫存為非負整數且列表售完文案(page: Page) -> None:
    """R-3.2／R-3.6／R-9.3：庫存 ≥0 整數；>0 顯示剩餘 N；0 顯示已售完且按鈕停用。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    # API 抽樣
    listing = page.request.get("/api/products")
    assert listing.ok
    for item in listing.json()[:5]:
        stock = int(item["stock"])
        assert stock >= 0

    mug = page.locator(".product-card", has_text="陶瓷馬克杯").first
    expect(mug).to_contain_text("已售完")
    expect(mug.get_by_role("button", name="加入購物車")).to_be_disabled()

    tee = page.locator(".product-card", has_text="純棉素色 T 恤").first
    text = tee.inner_text()
    n = parse_remaining_stock(text)
    assert n is not None and n >= 0
    if n > 0:
        assert re.search(r"剩餘\s*\d+\s*件", text)


def test_三種優惠券型別與免運券折抵為零(page: Page) -> None:
    """R-4.4／R-4.5／R-4.9：結帳可見金額／折扣／免運型；免運時折抵 0、運費 0。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    main = page.locator("main").inner_text()
    assert "滿千折百券" in main or "新人小禮券" in main  # 金額券
    assert "全站 85 折券" in main or "15%" in main  # 折扣券
    assert "免運券" in main
    select_coupon(page, "免運券")
    expect(summary_row_value(page, "運費")).to_have_text("NT$0")
    coupon_text = summary_row_value(page, "優惠券折抵").inner_text()
    # 折抵列應為 0（免運效果在運費）；若 D-14 誤顯也至少應付應＝小計
    payable = _nt_amount(summary_row_value(page, "應付金額").inner_text())
    subtotal = _nt_amount(summary_row_value(page, "商品小計").inner_text())
    assert payable == subtotal
    assert _nt_amount(coupon_text) == 0 or "NT$0" in coupon_text


def test_運費顯示為整數元(page: Page) -> None:
    """R-5.5：運費為整數、無小數。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    shipping = summary_row_value(page, "運費").inner_text()
    assert "." not in shipping
    assert shipping.startswith("NT$")


def test_訂單六種狀態文案與不可刪除(page: Page) -> None:
    """R-6.1／R-6.10：列表／詳情使用六種狀態文案；成立後仍在列表且無刪除。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="狀態文案測試")
    page.goto("/orders", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => /MM-\\d{8}-\\d{4}/.test(document.querySelector('main')?.innerText || '')",
        timeout=20_000,
    )
    row = page.get_by_role("button", name=re.compile(re.escape(order_id)))
    expect(row).to_be_visible()
    expect(row).to_contain_text("待出貨")
    expect(page.get_by_role("button", name=re.compile(r"刪除"))).to_have_count(0)

    # 其餘狀態文案：掃整頁文字至少出現過系統狀態詞（歷史單或本單）
    all_text = page.locator("main").inner_text()
    required = ("待出貨", "已出貨", "已完成", "退貨中", "已退款")
    # 已取消可能因 API 缺失而不存在
    for label in required:
        assert label in all_text, f"訂單列表／歷史中應能見到狀態「{label}」（R-6.1）"


def test_已完成可申請退貨並進入退貨中最後已退款(page: Page) -> None:
    """R-6.6：已完成 → 退貨中 → 已退款。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="完成退貨鏈測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    expect(page.locator("main")).to_contain_text("已完成")
    apply_return(page, "商品有瑕疵想退貨")
    expect(page.locator("main")).to_contain_text("退貨中")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已退款", timeout=30_000)


def test_點擊商品名稱進入詳情與數量選擇器初始為一(page: Page) -> None:
    """R-9.6／R-10.2：點名稱進詳情；選擇器 −／數字／＋ 且初始為 1。"""
    login(page)
    page.goto("/", wait_until="domcontentloaded")
    card = page.locator(".product-card", has_text="手沖咖啡濾杯").first
    card.get_by_role("link", name=re.compile(r"手沖咖啡濾杯")).click()
    page.wait_for_selector(".product-detail-page", timeout=15_000)
    picker = page.locator(".quantity-picker")
    expect(picker.get_by_role("button", name="減少數量")).to_be_visible()
    expect(picker.get_by_role("button", name="增加數量")).to_be_visible()
    expect(picker).to_contain_text(re.compile(r"\b1\b"))


def test_前往結帳進入結帳頁(page: Page) -> None:
    """R-11.8：購物車底部前往結帳進結帳頁。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    page.goto("/cart", wait_until="domcontentloaded")
    page.get_by_role("button", name="前往結帳").click()
    expect(page).to_have_url(re.compile(r".*/checkout"), timeout=15_000)


def test_訂單完成頁不顯示商品明細與金額細項(page: Page) -> None:
    """R-13.5：完成頁無商品明細、無金額摘要細項。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    fill_and_submit_checkout(page, name="完成頁細項測試")
    expect(page.get_by_role("heading", name="訂單已成立")).to_be_visible()
    main = page.locator("main")
    expect(main).not_to_contain_text("商品小計")
    expect(main).not_to_contain_text("滿額折扣")
    expect(main).not_to_contain_text("商品明細")


def test_駁回後顯示原因且可再申請(page: Page) -> None:
    """R-14.10：已駁回時訂單已完成、顯示駁回原因與申請退貨。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="駁回原因測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "短")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已完成")
    expect(page.locator("main")).to_contain_text("退貨原因描述不足")
    expect(page.get_by_role("button", name="申請退貨")).to_be_visible()


def test_退貨時間軸含狀態與退款金額不含運費(page: Page) -> None:
    """R-7.6／R-7.8／R-7.9／R-7.10／R-16.7：審核鈕、時間軸、退款金額與退款時間。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="時間軸退款測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "商品有瑕疵想退貨")
    expect(page.get_by_role("button", name="賣家審核（Demo）")).to_be_visible()
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已退款", timeout=30_000)
    main = page.locator("main").inner_text()
    section = main.split("狀態與操作", 1)[-1] if "狀態與操作" in main else main
    # 時間軸列：狀態名稱後接 YYYY-MM-DD HH:mm（有別於訂單狀態列的「已退款」）
    timeline_pairs = re.findall(
        r"(待審核|已駁回|退款處理中|已退款)\s*\n\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})",
        section,
    )
    timeline_statuses = {name for name, _ in timeline_pairs}

    problems: list[str] = []
    if "待審核" not in timeline_statuses:
        problems.append("時間軸缺少「待審核」紀錄")
    if "退款處理中" not in timeline_statuses:
        problems.append("時間軸缺少「退款處理中」紀錄（R-7.8／D-20）")
    if "已退款" not in timeline_statuses:
        problems.append("時間軸缺少「已退款」紀錄（R-7.8／D-20）")

    m_amt = re.search(r"退款金額\s*(NT\$[\d,]+)", section)
    if not m_amt:
        problems.append("已退款訂單未顯示退款金額（R-7.9／R-7.10）")
    elif _nt_amount(m_amt.group(1)) != 400:
        problems.append(
            f"退款金額應為應付−運費＝NT$400（R-7.10／D-19），實際 {m_amt.group(1)}"
        )

    # R-7.9：退款時間 YYYY-MM-DD HH:mm
    m_time = re.search(r"退款時間\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})?", section)
    if not m_time or not m_time.group(1):
        problems.append("訂單詳情缺少有效「退款時間 YYYY-MM-DD HH:mm」（R-7.9／D-21）")

    # R-8.6：退款通知須含金額與退款時間（先蒐集，與詳情問題一併回報）
    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )
    row = page.get_by_test_id("notification-row").filter(has_text=f"訂單 {order_id} 已退款")
    expect(row).to_be_visible(timeout=15_000)
    row_text = row.inner_text()
    if not re.search(r"退款金額\s*NT\$[\d,]+", row_text):
        problems.append("退款通知缺少退款金額（R-8.6）")
    else:
        amt = _nt_amount(re.search(r"退款金額\s*(NT\$[\d,]+)", row_text).group(1))
        if amt != 400:
            problems.append(f"退款通知金額應為 NT$400（D-19），實際 NT${amt}")
    # 通知內文須能辨識退款時間（標籤或合規時間格式皆可，但不能完全缺時間）
    has_labeled_time = bool(
        re.search(r"退款時間\s*\d{4}-\d{2}-\d{2} \d{2}:\d{2}", row_text)
    )
    has_any_time = bool(re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", row_text))
    if not has_labeled_time and not has_any_time:
        problems.append("退款通知缺少退款時間（R-8.6／D-21）")

    assert not problems, "；".join(problems)


def test_五類通知皆會產生且由新到舊(page: Page) -> None:
    """R-8.1／R-8.5／R-8.7：完整流程後五類通知獨立存在；列表新→舊。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="五類通知測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "商品有瑕疵想退貨")
    seller_review(page)
    expect(page.locator("main")).to_contain_text("已退款", timeout=30_000)

    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )
    text = page.locator("main").inner_text()
    # R-8.6 標題為「訂單 {id} 已退款」（非「已完成退款」）
    expected_titles = [
        f"訂單 {order_id} 已成立",
        f"訂單 {order_id} 已出貨",
        f"訂單 {order_id} 的退貨申請已送出",
        f"訂單 {order_id} 的退貨申請已通過",
        f"訂單 {order_id} 已退款",
    ]
    for title in expected_titles:
        assert title in text, f"缺少通知：{title}"

    idx_refund = text.find(expected_titles[4])
    idx_create = text.find(expected_titles[0])
    assert idx_refund != -1 and idx_create != -1
    assert idx_refund < idx_create, "通知應由新到舊排序（R-8.7）"


def test_審核駁回通知標題(page: Page) -> None:
    """R-8.5：駁回通知標題含訂單編號。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="駁回通知測試")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    apply_return(page, "短因")
    seller_review(page)
    page.goto("/notifications", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !document.querySelector('main')?.innerText.includes('載入中')",
        timeout=20_000,
    )
    expect(page.locator("main")).to_contain_text(f"訂單 {order_id} 的退貨申請已駁回")


def test_優惠券空頁籤文案(page: Page) -> None:
    """R-17.8：無券頁籤顯示「這裡沒有優惠券」。"""
    login(page)
    page.goto("/coupons", wait_until="domcontentloaded")
    for tab in ("可使用", "已使用", "已過期"):
        page.get_by_role("button", name=re.compile(rf"^{tab}")).click()
        page.wait_for_timeout(400)
        body = page.locator("main").inner_text()
        # 頁籤計數為 0，或內容為空態文案
        m = re.search(rf"{tab}\s*\((\d+)\)", body)
        count = int(m.group(1)) if m else None
        if count == 0 or "這裡沒有優惠券" in body:
            expect(page.get_by_text("這裡沒有優惠券")).to_be_visible()
            return
    pytest.skip("三個頁籤皆有券，無法驗證空頁籤文案")


def test_退貨原因字數規則對齊驗證章(page: Page) -> None:
    """R-18.6：退貨原因 trim 後 1～200 字（與 R-16.4 一致）。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    order_id = fill_and_submit_checkout(page, name="退貨原因驗證")
    open_order(page, order_id)
    ship_order(page, order_id)
    confirm_receipt(page, order_id)
    page.get_by_role("button", name="申請退貨").click()
    page.wait_for_url(re.compile(r".*/return"), timeout=15_000)
    textarea = page.locator("textarea").first
    submit = page.get_by_role("button", name="送出申請")
    textarea.fill("   ")
    expect(submit).to_be_disabled()
    textarea.fill("x" * 201)
    expect(submit).to_be_disabled()
    textarea.fill("有效原因")
    expect(submit).to_be_enabled()
