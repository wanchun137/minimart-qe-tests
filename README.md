# MiniMart QE 自動化測試

以 **Python + Playwright** 驗證 MiniMart 結帳系統的 UI 與 API 流程。受測網址透過環境變數 `BASE_URL` 指定，不寫死在程式碼中。

## 環境需求

- Python 3.10 以上
- 可連線的 MiniMart 測試環境

## 安裝

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## 設定 BASE_URL

```bash
# 一次性執行
BASE_URL=https://your-minimart-env.example.com pytest

# 或複製範例後匯出
cp .env.example .env
# 編輯 .env 後：
export $(grep -v '^#' .env | xargs)
pytest
```

> 重要：評審收卷後會用不同 `BASE_URL` 跑同一套測試，請勿把網址寫死在測試碼。

## 執行

```bash
BASE_URL=<你的 MiniMart 環境網址> pytest
BASE_URL=<網址> pytest tests/api/          # 僅 API 層
BASE_URL=<網址> pytest --headed
BASE_URL=<網址> pytest -m smoke
```

## 目錄結構

```
tests/
  helpers/
    auth.py                # 登入／登出
    cart.py                # 購物車（含 API 清空）
    checkout.py            # 結帳摘要、preview 比對
    orders.py              # 訂單狀態操作
  test_auth.py             # 登入／登出
  test_cart.py             # 加入購物車與件數
  test_cart_badge.py       # 徽章即時更新（D-03）
  test_checkout.py         # 結帳主路徑
  test_nav.py              # 導覽列文字（D-01）
  test_logout_cart.py      # 登出清空購物車（D-04）
  test_orders_count.py     # 訂單列表件數（D-05）
  test_coupon_threshold.py # 券門檻邊界（D-08）
  test_coupon_discount.py  # 折抵金額（D-06）
  test_phone_validation.py # 手機長度（D-07）
  test_stock_boundaries.py # 庫存／數量上限（R-3、R-10、R-11）
  test_pricing_summary.py  # 運費／滿額／應付（R-2、R-4、R-5）
  test_order_status.py     # 取消／出貨／收貨（R-6）
  test_return_flow.py      # 退貨審核／退款（R-7、R-16）
  api/
    conftest.py            # API session／request fixture
    helpers/
      client.py            # MiniMart API 客戶端
      pricing.py           # preview 金額斷言
      coupons.py           # 券可用性檢查
    test_checkout_preview.py   # R-4.15 計價順序
    test_coupon_boundaries.py  # 券門檻邊界
    test_validation_and_stock.py # 400／409 驗證
    test_order_transitions.py    # 訂單／退貨狀態
    test_ui_api_cross.py         # UI 與 API 交叉驗證
docs/
  API合約覆蓋紀錄.md
conftest.py
.env.example
pytest.ini
artifacts/                 # 最近一次 HTML 報告快照
```

登入帳號：`demo@minimart.test` / `demo1234`（系統內建測試帳號）。

## 失敗時的報告與證據

設定已啟用（見 `pytest.ini`）：

| 產物 | 時機 | 位置 |
|------|------|------|
| HTML 報告 | 每次執行 | `playwright-report/report.html` |
| 失敗截圖 | 測試失敗 | `test-results/**/test-failed-*.png` |
| Trace | 測試失敗 | `test-results/**/trace.zip` |
| 短影片 | 測試失敗 | `test-results/**/*.webm` |

```bash
# 用瀏覽器開啟最近一次 HTML 報告
open playwright-report/report.html   # macOS
# 或：xdg-open playwright-report/report.html

# 用 Playwright 檢視某個失敗 trace
playwright show-trace test-results/<失敗資料夾>/trace.zip
```

撰寫 bug report 時建議附上：失敗截圖、trace（或 HTML 報告連結）、對應的 `R-x.y` 規格條文。

## 備註

- 購物車清空改用 `DELETE /api/cart/items/{productId}`，避免 UI 移除殘留造成金額斷言失敗。
- 金額精確斷言以 `/api/checkout/preview` 為基準，再比對結帳頁 UI 的關鍵欄位（小計／運費／應付）。
- 若受測環境未提供「取消訂單」或「免運券已用盡」，相關案例會 `pytest.skip` 而非誤判通過。
- API 層依 `openapi.yaml` 合約撰寫；已知缺陷以 `pytest.mark.xfail` 標記，詳見 `docs/API合約覆蓋紀錄.md`。
- 失敗影片尺寸設為 800×600，並縮短 UI 等待（`domcontentloaded`、移除固定 `wait_for_timeout`）。
