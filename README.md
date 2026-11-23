# 黃博詩個人應徵作品集

靜態 HTML 網站，保留日系雜誌風格。正式網址：https://mystiqueduncan-beep.github.io/-/

- `index.html`、`contact.html`、`trend.html`：桌面與窄螢幕皆可使用的完整頁面。
- `mobile.html`、`mobile-contact.html`、`mobile-trend.html`：保留原有手機版內容與操作；因內容詳略不同，暫不合併。使用 `noindex,follow` 與對應完整頁 canonical，避免競爭索引。
- `mobile/`：既有網址轉址，不刪除。
- `assets/site.css`：共用無障礙、換行、觸控、響應式及列印修正；各頁原有視覺樣式仍保留。
- `assets/contact.js`：共用剪貼簿操作及明確失敗提示。
- `resume.html`：原有 A4 雙頁個人簡歷。頁面工具列現在明確分為「列印簡歷」（僅叫出系統列印）與「下載 PDF」（直接下載 `resume.pdf`），不混用兩種操作。
- `_audit/`：原始資料基準、雜湊、前後測試證據及報告；底線目錄由既有 Jekyll Pages 建置排除。
- `_qa/`：檢查工具，不屬網站執行依賴。無大型框架或網站建置依賴。

## 檢查

```sh
python3 _qa/check.py
node --check assets/contact.js
npx --yes --package=html-validate@11.18.0 html-validate --config _qa/htmlvalidate.json '*.html' 'mobile/*.html'
```

HTML 檢查採 recommended，僅停用 `no-inline-style`（保留既有行內設計，降低重構風險）、`tel-non-breaking`（保留原電話格式）。不關閉結構、標籤、重複 ID 或必要屬性檢查。

完整瀏覽器與 Lighthouse 重現說明見 `_audit/report.md`。自動測試不取代真實 iPhone Safari、VoiceOver 與人工閱讀檢查。

## 資料維護原則

基準為 `679a20b890044b79d06fe4977925f5fa0f8933fe`。學歷固定保留「萬能科技大學 企業管理系，2026.10 入學，預計 2030.06 畢業」。未經本人確認不得改動任何履歷事實、年資、技能、工作成果或目標職位。

本次使用者確認：保留操作考核與機動巡店，排班採「負責」。`_qa/check.py` 只排除這些已確認的同步文字與新增 skip link 後，比對所有頁面完整文字；後續更新履歷需先記錄本人授權，再更新基準與檢查。

## 部署與回復

現有 Pages 由 `main` 根目錄經 GitHub 管理的 Jekyll 流程發布。品質 workflow 只檢查，沒有部署權限。工作分支及 PR 不會直接發布正式網站。

合併必須等待使用者確認。備份分支 `backup/resume-before-quality-20261103` 指向原始正式 commit。回復時建立新分支，以 `git revert` 回復本 PR 的合併 commit（merge commit 使用 `git revert -m 1 <merge-sha>`；squash commit 使用 `git revert <squash-sha>`），經 PR 審查再合併；不得強制推送或重設正式歷史。

GitHub Pages 專案路徑為 `/-/`。資源採相對路徑；canonical、OG、sitemap 使用完整正式網址。專案的 `robots.txt` 不等同網域根目錄 `/robots.txt`，不能控制整個 `github.io` 網域的爬取政策；頁面索引控制以 meta robots 為準。

完整交付報告：[_audit/report.md](_audit/report.md)；截圖與 Lighthouse 原始證據：[_audit/qa-evidence.zip](_audit/qa-evidence.zip)。


## 刺繡海島配色與紙本同步

- 視覺設計以奶油白、草莓粉、淺鼠尾草綠及布章縫線質感為主，使用原創的 `assets/island-stitched-flora.svg` 花卉與海島紋樣，不複製任何外部角色或參考圖。
- 六個頁面的裝飾統一維護於既有的 `assets/pastel-details.css`，避免改動已核准並受雜湊保護的研究頁 HTML。
- 個人聯絡頁第一張刺繡風卡片連到 `resume.html`；該頁原有兩頁 A4 列印功能保留，另提供同一份版面的真正 PDF 檔供下載。
- `resume.pdf` 由 `_qa/export_resume_pdf.py` 以同一份 `resume.html` 生成；`.github/workflows/resume-pdf.yml` 在版面或匯出程式修改時核對兩頁 A4，再自動更新 PDF。請勿把原本已移除的首頁長篇 PDF 或下載舊按鈕恢復。
- 裝飾不得遮住文字、圖表、來源說明與照片，也不得破壞手機手勢、鍵盤焦點、`prefers-reduced-motion` 或 A4 分頁。
- 柔粉色卡片上的小標籤採用高對比深玫瑰色文字；研究專題入口的漸層發光效果和桌面／手機切換鈕的原有功能色不受全站換色規則覆蓋。

## 2026-11-21 精準修正與尚待處理項目

- 版本切換新增「自動」選項，清除手動模式記憶並還原裝置判斷；切換後保留原頁面錨點。自動模式已在正確頁面時，清除一次性 query 參數。
- 手機首頁「個人作品集」封面標籤保留通過原始內容鎖定的 HTML，由既有漸進增強 JS 將其標為呈現性元素，讓姓名作為輔助科技讀取時的第一個主要標題；停用 JS 時維持原有標題結構。
- 為上述行為新增 Node 回歸測試，並納入品質 workflow。正式合併前應等待 CI 與視覺檢查。
- **未解風險：**工作經歷的 TOMOD'S、築心與 Levi's 照片仍從第三方連結載入，既有圖片來源標示**不等於**取得公開再利用授權。未經本人確認，不變更指定照片；公開擴散前仍應向權利人確認許可或更換為可使用的素材。
- **刻意未動：**本人已指定的低解析度咖啡廳照片、履歷事實、研究數字、A4 PDF、兩套頁面的資料與配色。大型 CSS 去重及手機／桌機模板整併會牽動既有審核基準與列印效果，應獨立處理並完整比對視覺回歸，不在本輪盲目刪除。

## 個人 AI 數位分身（GitHub Pages 無 API 版本）

- `assets/ai-assistant.js` 和 `assets/ai-assistant.css` 由七個網站內容頁共同載入；A4 簡歷頁 `resume.html` 不載入，列印結果不受影響。
- 右下角浮動入口、歡迎訊息、四個快捷問題及自由輸入，搭配「正在回覆」動畫、無障礙鍵盤操作及減少動態偏好支援。
- 答覆僅依網站已公開的學歷、三段工作經歷、四項核心能力及藥妝研究提案建立的前端關鍵字知識庫；會區分提案與已實際完成的工作。新資料需手動同步更新知識庫。
- **這不是外部生成式 AI。** 不申請 API Key，不呼叫外部 API、不儲存問題、不將對話傳送到伺服器。對未涵蓋問題會明確說明限制並提供頁面連結。
- `_qa/ai-assistant_browser.py` 檢查桌機與手機版開合、快捷問答、品牌經驗、未知問題、導航連結、鍵盤 Escape、位置遮擋及 320px 窄螢幕。
