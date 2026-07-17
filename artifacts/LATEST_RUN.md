# 最近一次完整執行摘要

- 日期：2026-07-17
- 框架：Python + Playwright + pytest
- BASE_URL：由執行時環境變數指定（本機對 cand2 環境）
- 結果：**6 passed / 7 failed**
- HTML 報告：見同目錄 `playwright-report/report.html`

## 通過（主路徑）

- 登入成功／失敗／登出
- 加入購物車後件數正確、累加
- 結帳下單主路徑

## 失敗（預期用來抓缺陷／寫 bug report）

| 測試 | 對應 | 觀察 |
|------|------|------|
| nav 優惠券文字 | D-01 / R-1.3 | 實際為「我的優惠卷」 |
| cart-badge 即時更新 | D-03 / R-1.4 | 商品列表加入後徽章未出現／未更新 |
| logout 清空購物車 | D-04 / R-1.7 | 再登入後購物車仍有商品 |
| orders-count 3 件 | D-05 / R-14.2 | 列表件數不符「3 件」 |
| coupon-discount 477 | D-06 / R-4.7 | 折抵金額不符預期 |
| phone 11 碼 | D-07 / R-18.4 | 仍可成功下單 |
| coupon-threshold | D-08 / R-4.6 | 恰等於門檻時仍不可用 |

失敗產物（截圖／trace／video）位於執行當下的 `test-results/`（預設不進版控，可於本機重跑產生）。
