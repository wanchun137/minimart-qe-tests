# API 合約覆蓋紀錄

依 `candidate-package-v2.0/openapi.yaml` 建立 Python Playwright API 層測試（`tests/api/`）。

執行環境：`BASE_URL=https://cand2.tail296b14.ts.net`（2026-07-17）

## 覆蓋對照

| OpenAPI operationId | 測試檔案 | 覆蓋狀態 |
|---------------------|----------|----------|
| postAuthLogin | `test_validation_and_stock.py` | 已覆蓋（401） |
| postAuthLogout | `test_validation_and_stock.py` | 已覆蓋（v2.1：登出清空購物車 PASS） |
| getProducts / getProductsId | `test_validation_and_stock.py` | 已覆蓋（404） |
| getCart / postCartItems | 各 preview／狀態測試前置 | 已覆蓋 |
| postCheckoutPreview | `test_checkout_preview.py`、`test_coupon_boundaries.py` | 已覆蓋 |
| postCheckout | `test_validation_and_stock.py`、`test_order_transitions.py` | 已覆蓋（400／409） |
| getOrders / getOrdersId | `test_ui_api_cross.py`、`test_orders_list.py` | 已覆蓋（getOrders 排序見 D-22 FAIL） |
| postOrdersIdShip | `test_order_transitions.py` | 已覆蓋（xfail：重複出貨） |
| postOrdersIdCancel | `test_order_transitions.py` | 已覆蓋（cand2 404 → D-23 FAIL） |
| postOrdersIdConfirm-receipt | `test_order_transitions.py` | 已覆蓋 |
| postOrdersIdReturns | `test_order_transitions.py` | 已覆蓋 |
| postOrdersIdReturnsReview | `test_order_transitions.py` | 已覆蓋 |

## 最近一次執行摘要

```
17 passed, 3 skipped, 4 xfailed（2026-07-17）
```

| 案例 | 結果 | 說明 |
|------|------|------|
| PRD 範例 1～4 計價 | PASS | R-4.15 七步順序恆等式 |
| PCT15 門檻恰等於 800 | XFAIL | 缺陷 D-08 |
| 手機 11 碼 | XFAIL | 缺陷 D-07（API 未擋） |
| 重複出貨 | XFAIL | 與 openapi `CANNOT_SHIP` 不符 |
| 登出清空購物車 | XFAIL | API 未清空（UI 層另有覆蓋） |
| UI ↔ API 金額交叉 | PASS | R-12.5、R-14.4 |

## 執行指令

```bash
BASE_URL=<網址> pytest tests/api/
BASE_URL=<網址> pytest tests/api/test_checkout_preview.py
```

純 API 案例僅使用 `playwright.request` fixture，不啟動瀏覽器；交叉驗證案例需 Chromium。
