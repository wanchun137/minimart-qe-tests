# MiniMart QE UI 自動化測試

以 **Python + Playwright** 驗證 MiniMart 結帳系統的主要畫面流程。受測網址透過環境變數 `BASE_URL` 指定，不寫死在程式碼中。

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
BASE_URL=<網址> pytest --headed
BASE_URL=<網址> pytest -m smoke
```

## 目錄結構

```
tests/
  helpers/                 # 登入、購物車共用工具
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
