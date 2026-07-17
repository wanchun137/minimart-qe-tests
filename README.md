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

## 目錄結構（規劃）

```
tests/
  helpers/          # 登入、購物車共用工具
  test_auth.py      # 登入／登出
  test_cart.py      # 加入購物車與件數
  test_checkout.py  # 結帳主路徑
  ...
conftest.py         # BASE_URL、失敗截圖／trace
.env.example
```

登入帳號：`demo@minimart.test` / `demo1234`（系統內建測試帳號）。

## 失敗時的報告與證據

（後續 commit 會補上截圖、trace、HTML 報告設定與說明。）
