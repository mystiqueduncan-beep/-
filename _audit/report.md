# 個人履歷網站優化與品質驗證報告

日期：2026-11-03（Asia/Taipei）。狀態：已完成本次安全優化與可用本機驗證，待 PR 審查；尚未合併、尚未部署。真實 iPhone Safari、VoiceOver、外部字型及正式網站仍待驗證，不能宣稱全項完成或已符合 WCAG 2.2 AA。

## A. 修改前問題分析

| 優先級 | 檔案／位置 | 問題與影響 | 處理 |
|---|---|---|---|
| P0 | mobile.html、index.html、resume.pdf、聯絡頁 | 操作考核、機動巡店、全權負責等版本差異；無法直接整併，可能誤改事實 | 先完整建立基準；使用者明確確認保留操作考核與機動巡店、排班採「負責」後同步 |
| P1 | contact.html | Chromium 320px 文件寬 339px；照片欄與聯絡資訊的最小內容寬撐開版面 | 縮小欄位最小寬、照片自適應、長郵件換行 |
| P1 | trend.html | Chromium 320px 文件寬 346px；行內 grid 最小寬與固定欄位不適合手機；200% 文字亦溢出 | 單欄、可縮小 grid、長英文換行；保留可鍵盤捲動的比較表 |
| P1 | 三個 mobile*.html | maximum-scale=1、user-scalable=no 阻止放大 | 恢復縮放；補橫向模式固定導覽處理 |
| P1 | 六個主要頁面 | 無 skip link、一致焦點與 reduced motion；部分標題跳級或只有視覺標題；地標不足 | 語意標題、aside/nav、焦點與減少動態 |
| P1 | 六個主要頁面 | axe 發現灰字、紅字、紅字配黃底、比較表綠字對比不足 | 保留配色方向，調整文字深淺；自動檢測零違規，incomplete 仍需人工判讀 |
| P1 | contact.html、mobile-contact.html | API 不存在時拋錯；手機備援忽略 execCommand 回傳值，可能誤報成功 | 共用 async 剪貼簿操作，拒絕或不存在時顯示手動複製資訊 |
| P2 | 六頁與 mobile/ 轉址 | 缺 canonical、OG、分享圖與重複索引策略 | 完整頁獨立 canonical；手機頁 noindex,follow；舊網址保留 |
| P2 | 全站 | 無 sitemap、robots、favicon；首頁 Lighthouse 有 favicon 404 | 增補，正確使用 /-/ |
| P2 | 部分圖片 | 無尺寸或寬高比例與實際來源不符；非首屏未延遲載入 | 補尺寸、lazy、首屏高優先；全部維持原始 JPG 像素，避免品質改變 |
| P2 | 多頁 CSS／JS | 頁面內樣式與聯絡功能重複；無維護文件／可重現驗證 | 共用新增修正與複製程式；保留原有內嵌視覺 CSS，避免大規模重構 |

全儲存庫清點：9 個 HTML（6 個完整內容頁、3 個舊手機轉址）、5 個 JPG、1 個 PDF；原始版本沒有外部 JS、獨立 CSS、設定檔或自訂 workflow。HTML 的 CSS 與兩段聯絡 JS 已檢查；JPG 全部解碼驗證；PDF 已擷取文字及比對。`trend-market-channels.jpg` 現未被 HTML 引用，仍保留，沒有自行刪除素材。

架構：首頁含應徵、能力、構想、經歷、教育、研究摘要與聯絡；contact 是聯絡與履歷下載、複製；trend 是完整研究與比較表。手機版有底部導覽、內容縮寫及不同敘述，並非與完整頁完全相同。原站無可開合漢堡選單；實測對應的章節連結、底部導覽、版本切換與舊網址轉址，沒有新增不必要的選單。

## B. 實際修改

| 檔案 | 修改及原因 |
|---|---|
| index.html | 語意導覽、skip、焦點目標、分享資料、圖片載入／比例、排版、已確認的操作考核與機動巡店同步 |
| contact.html | 窄欄可縮小、語意導覽、SEO、圖片尺寸、共用剪貼簿、live status，已確認資料同步 |
| trend.html | grid、表格鍵盤捲動、標題層級、語意地標、對比、SEO；研究原文與數字均保留 |
| mobile.html | 恢復縮放、標題、語意地標、skip、圖片；保留操作考核與機動巡店原文；手機索引策略 |
| mobile-contact.html | 縮放、圖片、共用複製與 status、SEO，已確認資料同步 |
| mobile-trend.html | 縮放、標題與地標、SEO；保留原研究內容 |
| mobile/index.html、mobile/contact.html、mobile/trend.html | 保留 JS＋meta refresh＋手動連結三種轉址，補 viewport 與 noindex |
| assets/site.css | 共用窄螢幕、長字串、字級層級、留白、按鈕 44px、焦點、動態偏好、橫向、列印修正 |
| assets/contact.js | 取代兩份重複剪貼簿程式；成功才顯示成功，失敗不誤報；不加入外部服務 |
| 原 JPG 素材 | 五張原始 JPG 位元組完全不變。評估無損 WebP 後，profile 約249 KB、Levi's 約387 KB，均比原檔77／117 KB 大，故不轉換；採載入優先級與延遲載入改善請求，不犧牲圖片品質 |
| assets/favicon.svg | 使用既有姓名「黃」及既有深藍／黃的文字圖示；補網站小圖示 |
| resume.pdf | 依已核對首頁重產 A4、10 頁、含標記與大綱；使用本機 Noto CJK 字型防止中文缺字；從 4,016,958 bytes 降至約 1.9 MB。不是刪內容換體積 |
| sitemap.xml、robots.txt | 只列三個完整 canonical 頁；使用完整正式 /-/ URL；不阻止手機頁被讀取 noindex |
| README.md、_qa/、_audit/、.github/workflows/quality.yml | 維護、基準、工具、證據；PR CI 只有讀取權限，無部署權限 |

保留深藍、黃色、紅色、日系襯線與無襯線組合、雜誌區塊、全部原圖與真實資料。沒有引進網站框架、追蹤服務或額外動畫。原 Google Fonts URL、preconnect、display=swap 保留；未在無法驗證外部字型時擅自刪除字重。

## C. 資料正確性

完整逐頁原文基準與原 PDF 文字見 `baseline.md`；機器基準見 `baseline-text.json`；15 個原始檔雜湊與大小見 `original-manifest.json`。不是只用姓名／學校關鍵字抽查，而是比對 9 頁所有文字順序與內容，僅忽略排版空白、BOM、新增 skip link 及本人確認的同步字串。

| 重要欄位 | 修改前 | 修改後／結果 |
|---|---|---|
| 姓名與外文 | 黃博詩；HUANG BO-SHIH；コウ・ハクシ | 完整保留各頁既有拼法及大小寫 |
| 應徵企業 | 台灣松本清 (Matsumoto Kiyoshi) | 不變 |
| 應徵職位 | 區域營運經理；原文附門市督導／門市營運督導 | 不變；不改為已任職 |
| 志願區域 | 桃竹苗 ＆ 大台北門市 | 不變 |
| 學校、科系 | 萬能科技大學 企業管理系 | 不變，六個主要頁及 PDF 均驗證 |
| 學歷狀態／日期 | 研讀中；2026.10 入學；預計 2030.06 畢業 | 完整保留；不因日期看似特殊而修正 |
| Tomod's | 日系藥妝；門市正職 → 門市店長；6 年含店長 3 年 | 不變；排班、庫存、損益、商品研習、總部月會及每週例會均保留 |
| 築心動物醫院 | 櫃台助理兼新人帶訓；任職 4 年，期間兼任帶訓 | 不變；原櫃台與服務職責保留 |
| Levi's | 連鎖服飾；門市銷售人員；2 年 | 不變；銷售、陳列、整燙、庫存及協作均保留 |
| 任職起訖年月 | 原文未提供 | 未新增或推算，仍僅列年資 |
| 核心能力 | 門市營運、人員帶訓、顧客服務、總部政策與例會協調 | 原文保留，未新增數據成果、證照、人數 |
| 操作考核 | mobile.html 原有「規劃新進同仁實務帶訓指引與步驟化操作考核」 | 本人確認保留；補入 index 及兩個 contact 的帶訓敘述，其餘職責不刪 |
| 居住地／巡店 | 桃園市大園區；mobile.html 附「機動巡店」 | 本人確認保留機動巡店，相關居住地列示統一；面談確認排班的條件保留 |
| 排班責任 | 網頁「負責」；舊 PDF「全權負責」 | 本人確認採「負責」，新版 PDF 同步 |
| 到職／排班 | 到職時間、排班與巡店安排，可於面談進一步確認 | 不變 |
| 電話／連結值 | 0989-591-825；tel:0989591825 | 不變；剪貼簿仍複製 0989591825 |
| Email | mystiqueduncan@gmail.com | 不變，mailto 與複製均一致 |
| 研究與數據 | 47.7%、21.4%、13.7%、7.3%、7.0%；45.2%、42.5%、28.7%、24.4%；3.4／4.9 倍等原文 | 所有逐頁原文、日期、來源與限制均保留，不重新推論 |
| 構想與未來規劃 | 三階段到任規劃、研究建議、主管／總部權責條件 | 原文保留，不改為既有成果 |
| 更新日期 | 2026 年 11 月 | 不變 |

`integrity.json`：9/9 頁通過。新版 PDF 以 `pdftotext` 取出文字，對照最終首頁 header/main 的 204 個實質中文文字節點，缺漏 0；隱藏的是列印時無意義的操作按鈕，不是履歷內容。已確認的三項差異亦記錄於 `pdf-integrity.json`。PDF 文字前後 diff 附於證據，版序與換頁改變不代表資料被刪除。

## D. 測試結果

| 測試 | 執行方式 | 結果 | 限制 |
|---|---|---|---|
| 履歷完整文字／事實比對 | python3 _qa/check.py | 通過，9 頁，僅排除已確認同步與操作字串 | PDF 另驗證；不替本人判定未確認資料真偽 |
| HTML 結構 | html-validate 11.18.0 recommended | 9 頁通過，0 error | 保留既有行內樣式、電話格式，僅停用對應兩個風格規則 |
| 內部連結／資源 | 路徑與跨頁 fragment 檢查 | 116 個連結／資源引用通過；favicon 另於瀏覽器載入 | 外部 Google Fonts 無法連線驗證 |
| JS | node --check；42 組瀏覽器 pageerror | 通過，0 pageerror | 真實 Safari 仍待驗證 |
| 響應式 | Chromium：6 頁 × 320/375/390/430/768/1024/1440px | 42/42 通過，無整頁水平溢出 | 使用本機備援字型，非真實 iOS |
| 圖片 | 5 JPG 解碼；逐一捲動至所有圖片 | 全數載入，0 broken image；首屏 eager/high，非首屏 lazy | 已保留原圖；主圖顯示裁切沿用既有設計 |
| 實際截圖 | 六頁於 390、1440，各有修改前後截圖 | 完成；交付含最終載入完整圖片版 | 長頁截圖不代替所有真機閱讀驗收 |
| 基本無障礙 | axe-core 4.14.0：WCAG 2/2.1/2.2 A/AA＋best practice，6 頁 × 2 尺寸 | 12/12 零 violations | 存在 color-contrast incomplete；須人工判讀，不能宣稱 WCAG 認證 |
| 鍵盤與減少動態 | Tab→skip、Enter→main；reduced motion emulation | 12 組通過，焦點目標正確、scroll behavior auto | VoiceOver、完整焦點順序與表格讀法仍待人工 |
| 剪貼簿 | 成功寫入後讀回；模擬 API 不存在 | 兩個 contact 在 390/1440 均通過；失敗不顯示成功 | iPhone 權限提示與系統貼上需真機 |
| 橫向／放大 | 844×390；390px 下 html 字級 200% | 六頁皆無整頁溢出 | 文字放大不是所有瀏覽器 zoom 的等價替代 |
| 舊路徑 | /-/mobile/index/contact/trend.html 實際導向 | 3/3 導向正確手機頁 | 仍保留 meta refresh 與手動備援 |
| SEO | title、description、canonical、OG、robots、sitemap 靜態檢查 | 通過；正式 URL 含 /-/；手機不競爭索引 | 不宣稱已被搜尋引擎收錄；未使用未經核實結構化資料 |
| PDF | A4／標記、中文擷取、204 節點、學歷與聯絡核對；首頁視覺檢查 | 通過；10 頁 | 完整螢幕閱讀器閱讀順序仍待人工 |
| GitHub Pages | 實際建置記錄與 /-/ 本機路徑測試 | 原 main 建置成功，根目錄來源已由 log 確認；本次未部署 | Pages 設定 API 不在工具允許端點，未讀設定 UI |
| 公開網站 HTTP | curl 經既有代理 | 已執行但環境阻擋：CONNECT 403 | 這是代理拒絕，不能視為網站故障；尚未完成公開網站檢查 |
| 真實 iPhone Safari／WebKit | 檢查可用環境 | 尚未執行 | WebKit 執行檔不存在；未宣稱 iPhone 已通過 |

### Lighthouse 前後數據

Lighthouse 13.6.0、Chromium 154.0.8037.57，本機 HTTP `/-/` 路徑、預設模擬手機節流，每頁每階段 1 次。明確阻擋 fonts.googleapis.com 與 fonts.gstatic.com，兩階段條件相同。以下是實測實驗室數據，**不是公開網站或真實訪客 Core Web Vitals**。每階段只有單次測試，不宣稱速度顯著提升。聯絡頁 LCP 約增加 0.15 秒，保留原圖品質優先，不宣稱每項效能皆改善。

| 頁面 | Performance 前→後 | Accessibility 前→後 | SEO 前→後 | LCP 秒 前→後 |
|---|---:|---:|---:|---:|
| index.html | 99 → 99 | 91 → 100 | 100 → 100 | 1.682 → 1.682 |
| contact.html | 99 → 99 | 93 → 100 | 100 → 100 | 1.651 → 1.802 |
| trend.html | 98 → 98 | 89 → 100 | 100 → 100 | 1.831 → 1.831 |
| mobile.html | 99 → 99 | 78 → 100 | 100 → 69 | 1.683 → 1.680 |
| mobile-contact.html | 97 → 99 | 81 → 100 | 100 → 69 | 1.652 → 1.804 |
| mobile-trend.html | 99 → 99 | 71 → 100 | 100 → 66 | 1.681 → 1.681 |

所有頁面兩階段 TBT=0ms、CLS=0。FCP、Speed Index 與全部原始數值附於 lighthouse summary／原始 JSON。完整頁修改後 Best Practices=100。手機頁 SEO 66–69 是刻意 noindex 與 canonical 指向對應完整頁帶來的結果，不為追分移除索引策略。Lighthouse 分數不是完整品質證明。

### 重現方式

```sh
python3 _qa/check.py
node --check assets/contact.js
npx --yes --package=html-validate@11.18.0 html-validate --config _qa/htmlvalidate.json '*.html' 'mobile/*.html'
# 選用：測試機需有 Playwright、Chromium；axe-core 不放入網站執行依賴
python3 _qa/browser_audit.py --out /tmp/resume-qa --axe /path/to/axe.min.js
# 更新 PDF 需先核對所有資料，並在機器安裝 Noto Sans/Serif CJK TC
python3 _qa/print_pdf.py
```

## E. 未解決與待確認

1. 真實 iPhone Safari、橫向真機、VoiceOver、完整焦點順序、200% 瀏覽器 zoom、系統縮放與剪貼簿權限：需要人工確認；本次僅 Chromium 模擬。
2. axe 的 color-contrast incomplete（背景／覆蓋與複合元素）需人工判讀；截圖可供初審，零 violations 不代表沒有無障礙問題。
3. Google Fonts 與公開網站域名不在目前網路允許範圍；外部字型載入、實際訪客 CWV、公開社群預覽及正式網站需在可連線環境複驗。
4. `mobile/index.html`、`mobile/contact.html` 的轉址說明仍寫「區域經營經理」，主要履歷是「區域營運經理」。依禁止擅改職位規則保留，列為疑似錯字待本人確認；不阻擋既有轉址。
5. 手機研究是摘要，與完整頁內容不完全一致（例如會員／App、案例與策略詳略），未取得外部資料核實前不自行統一；全部原文已存基準。任職起訖年月未提供，不補猜測資料。
6. 原內嵌視覺 CSS 仍有跨頁重複；只把本次共用修正與複製行為集中，不在內容不同與外部字型未實測的情況做大幅抽離或刪 mobile.html。
7. 專案目錄的 robots.txt 不是站台根目錄 robots；不能用它控制 GitHub 子網域政策。meta noindex 與 canonical 才是本次實際頁面策略；sitemap 可於網站管理工具提交。
8. 正式合併、Pages 新版建置及公開網站檢查尚未執行，必須等使用者確認後才進行。

## F. GitHub 與部署資訊

- 儲存庫：https://github.com/mystiqueduncan-beep/-
- 預設分支：main；分析及備份基準：679a20b890044b79d06fe4977925f5fa0f8933fe。
- 正式 Pages：最近成功 run 41454414594，`dynamic/pages/pages-build-deployment`；logs 明列 checkout ref main、source `.`、Jekyll，build/deploy 均 success。
- 既有 PR #1（draft）：resume-site-audit-20261103-v2，3da71dfe4d83a18bec7b160b65ae29f989d81369，只改首頁17行新增／4行刪除。已讀全文差異，本次包含其安全改善並擴及所有頁；沒有推送該分支或關閉／合併該 PR。
- 遠端備份：backup/resume-before-quality-20261103，指向原 main。
- 本次獨立分支：resume-quality-20261103；程式碼 commit：db9dbfff8a1b99931862e625e3c54180294aca98。
- 審查 PR：https://github.com/mystiqueduncan-beep/-/pull/2 ，open、未合併。
- GitHub CI 已通過：https://github.com/mystiqueduncan-beep/-/actions/runs/41573058176 ，履歷／連結／JS／HTML 步驟均 success。
- 截圖與 Lighthouse 原始證據：本目錄 qa-evidence.zip；內含 24 組載入完整圖片的修改前後截圖（無損 WebP；過長圖分段並附座標 manifest，與原截圖像素相同）、12 份 Lighthouse 原始 JSON、所有結果與工具。
- 新增品質 CI 是 pull_request / workflow_dispatch，contents:read；沒有 Pages 寫入或部署步驟。
- 本次正式部署狀態：未合併、未部署。請勿同時合併首頁舊 PR #1，以免產生重複或衝突；選定本次整體 PR 後再處理舊 PR。

## G. 回復方案

正式分支未變更，目前不需要回復。若之後核准合併而出現問題：

1. 從當時最新 main 建立 revert 分支，先檢查是否有後續其他人的修改。
2. merge commit 採 `git revert -m 1 <本PR的merge-sha>`；squash commit 採 `git revert <squash-sha>`。只反轉本次變更，不用 reset/force push。
3. 對照備份分支與原始 manifest、執行 `_qa/check.py`（如回復同時移除此工具則使用備份版本檢查）、建立回復 PR。
4. 使用者確認後合併；確認 Pages 建置成功，再於可連線環境檢查公開網址、PDF、手機與內部連結。

本次沒有刪除歷史、強制推送、變更正式部署設定或擅自發布。
