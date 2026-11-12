# 黃博詩個人應徵作品集

靜態 HTML 網站，保留日系雜誌風格。正式網址：https://mystiqueduncan-beep.github.io/-/

- `index.html`、`contact.html`、`trend.html`：桌面與窄螢幕皆可使用的完整頁面。
- `mobile.html`、`mobile-contact.html`、`mobile-trend.html`：保留原有手機版內容與操作；因內容詳略不同，暫不合併。使用 `noindex,follow` 與對應完整頁 canonical，避免競爭索引。
- `mobile/`：既有網址轉址，不刪除。
- `assets/site.css`：共用無障礙、換行、觸控、響應式及列印修正；各頁原有視覺樣式仍保留。
- `assets/contact.js`：共用剪貼簿操作及明確失敗提示。
- `resume.pdf`：從核對後首頁列印的 A4 履歷。更新資料時，必須同時更新相關 HTML 與 PDF。
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
- A4 列印版本統一由 `assets/print-layout.css` 控制；`resume.html` 是獨立雙頁簡歷，`resume.pdf` 則由 `index.html` 產生。它們都使用對應的粉彩布藝色系。
- `.github/workflows/print-pdf-sync.yml` 在會影響列印版的原始檔變動後重新產生 `resume.pdf`，先驗證六個網頁的 A4 列印與既有文字，再提交 PDF。不得直接手工修改 PDF 內的個人資料。
- 裝飾不得遮住文字、圖表、來源說明與照片，也不得破壞手機手勢、鍵盤焦點、`prefers-reduced-motion` 或 A4 分頁。
