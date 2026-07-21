"""R-2.6、R-2.9、R-5.4、R-12.8～R-12.11、R-13.3：金額邊界、結帳與完成頁。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from playwright.sync_api import Page, expect

from tests.helpers.auth import login
from tests.helpers.cart import add_product_from_list, clear_cart
from tests.helpers.checkout import (
    fill_and_submit_checkout,
    go_to_checkout,
    summary_row_value,
)


def test_購物車頁不顯示運費(page: Page) -> None:
    """R-5.4：運費只在結帳頁出現。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.get_by_text("運費")).to_have_count(0)
    go_to_checkout(page)
    expect(page.get_by_text("運費")).to_be_visible()


def test_結帳摘要金額無小數點(page: Page) -> None:
    """R-2.9：結帳摘要金額為整數格式。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    for label in ("商品小計", "滿額折扣", "優惠券折抵", "運費", "應付金額"):
        text = summary_row_value(page, label).inner_text()
        assert "." not in text.replace("…", ""), f"{label} 不應有小數：{text}"


def test_折扣總額不得使折扣後商品金額為負(page: Page) -> None:
    """R-2.6：折抵後商品金額不為負（應付 − 運費 ≥ 0）。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    # 優先選低門檻可用券；耗盡時仍驗證無券情境
    for name in ("免運券", "新人小禮券"):
        radio = page.get_by_role("radio", name=re.compile(name))
        if radio.count():
            radio.first.click()
            break
    payable_text = summary_row_value(page, "應付金額").inner_text()
    amount = int(re.sub(r"[^\d]", "", payable_text))
    assert amount >= 0
    shipping_text = summary_row_value(page, "運費").inner_text()
    shipping = int(re.sub(r"[^\d]", "", shipping_text) or "0")
    assert amount - shipping >= 0, f"折抵後商品金額為負：應付 {amount}、運費 {shipping}"


def test_空購物車直開結帳導向購物車(page: Page) -> None:
    """R-12.11：購物車為空時開啟結帳頁應導向購物車。"""
    login(page)
    clear_cart(page)
    page.goto("/checkout", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r".*/cart"), timeout=15_000)
    expect(page.get_by_text("購物車是空的")).to_be_visible()


def test_下單成功後購物車應清空(page: Page) -> None:
    """R-12.9：訂單建立成功後清空購物車，再進購物車頁為空。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    add_product_from_list(page, "手沖咖啡濾杯")
    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.locator(".cart-row")).not_to_have_count(0)

    go_to_checkout(page)
    fill_and_submit_checkout(page, name="下單清空購物車")
    expect(page.get_by_role("heading", name="訂單已成立")).to_be_visible()

    page.goto("/cart", wait_until="domcontentloaded")
    expect(page.get_by_text("購物車是空的")).to_be_visible()
    expect(page.locator(".cart-row")).to_have_count(0)
    expect(page.get_by_test_id("cart-badge")).to_have_count(0)


def _order_list_count(page: Page) -> int:
    page.goto("/orders", wait_until="domcontentloaded")
    page.wait_for_function(
        """() => {
          const t = document.querySelector('main')?.innerText || '';
          if (t.includes('載入中')) return false;
          return t.includes('還沒有任何訂單') || /MM-\\d{8}-\\d{4}/.test(t);
        }""",
        timeout=20_000,
    )
    # 每筆訂單編號在列表通常出現一次
    return len(re.findall(r"MM-\d{8}-\d{4}", page.locator("main").inner_text()))


def test_送出訂單時按鈕顯示處理中並防重複下單(page: Page) -> None:
    """R-12.8：點擊後顯示「處理中…」或停用，且同一次操作只建立一張訂單。"""
    login(page)
    before = _order_list_count(page)

    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    page.fill("#checkout-name", "防重複測試")
    page.fill("#checkout-phone", "0912345678")
    page.fill("#checkout-address", "台北市防重複路 12 號")

    saw_processing = {"v": False}

    def slow_checkout(route):
        page.wait_for_timeout(1_200)
        route.fallback()

    page.route("**/api/checkout", slow_checkout)
    page.get_by_role("button", name="送出訂單").click()
    try:
        expect(page.get_by_role("button", name=re.compile(r"處理中"))).to_be_visible(timeout=3_000)
        saw_processing["v"] = True
    except Exception:
        try:
            expect(page.get_by_role("button", name=re.compile(r"送出|處理中"))).to_be_disabled(
                timeout=1_500
            )
            saw_processing["v"] = True
        except Exception:
            pass

    page.wait_for_url(re.compile(r".*/orders/.+/complete"), timeout=60_000)
    page.unroute("**/api/checkout")
    match = re.search(r"/orders/(MM-[^/]+)/complete", page.url)
    assert match, f"完成頁應含訂單編號：{page.url}"

    after = _order_list_count(page)
    assert after == before + 1, f"單次送出應只新增 1 筆：{before} → {after}"
    assert saw_processing["v"], "送出後應顯示「處理中…」或按鈕停用（R-12.8／D-16）"


def test_訂單完成頁預計出貨日為下單日加兩天(page: Page) -> None:
    """R-13.2／R-13.3：完成頁顯示預計出貨日 = 台北當日 + 2。"""
    login(page)
    clear_cart(page)
    add_product_from_list(page, "純棉素色 T 恤")
    go_to_checkout(page)
    fill_and_submit_checkout(page, name="出貨日測試")

    expect(page.get_by_role("heading", name="訂單已成立")).to_be_visible()
    expect(page.locator("main")).to_contain_text("預計出貨日")
    expected = (datetime.now(ZoneInfo("Asia/Taipei")).date() + timedelta(days=2)).isoformat()
    expect(page.locator("main")).to_contain_text(expected)
    # R-13.2 另含訂單編號／下單時間／應付
    expect(page.locator("main")).to_contain_text(re.compile(r"MM-\d{8}-\d{4}"))
    expect(page.locator("main")).to_contain_text("應付金額")
    expect(page.get_by_role("button", name="查看訂單")).to_be_visible()
    expect(page.get_by_role("button", name="繼續購物")).to_be_visible()
