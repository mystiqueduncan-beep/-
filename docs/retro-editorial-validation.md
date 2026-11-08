# 日系復古雜誌重排與驗證

> 此為第一版的歷史紀錄。使用者後續指定新的網站參考與低飽和粉色方向，最新設計請見 [粉色活動網站改版報告](pastel-campaign-validation.md)。

基準：main `5646383cf2ea0bb24201ee18fc51e43540f0d8df`。功能分支：`feat/retro-shoujo-editorial`。不合併、不正式部署，草稿供畫面確認。本次未收到三張參考附件，依使用者列出的 A／B／C 圖文構成規則設計。

## 頁面與修改檔案

| 頁面 | 實際版面變更 | 修改前 | 修改後 |
| --- | --- | --- | --- |
| index.html | 重建 cover-story、人物照與獨立操作側欄；姓名為封面視覺核心。動機採雙欄、能力採錯位分欄、構想採側標、經歷採 career-spread 圖文欄。 | [桌機](retro-preview/index-before.webp) | [桌機](retro-preview/index.webp) |
| mobile.html | 手機人物照／姓名左右並列；學歷獨立分隔、經歷圖片錯位、內容改單欄；新增可續播的同款章節跑馬燈，底部原有導覽保留。 | [手機](retro-preview/mobile-before.webp) | [手機](retro-preview/mobile.webp) |
| contact.html | 高幅拱形人物照、檔案邊欄與右側專訪／聯絡筆記；三個聯絡方式保持一次性彈出。 | [桌機](retro-preview/contact-before.webp) | [桌機](retro-preview/contact.webp) |
| mobile-contact.html | 獨立手機專訪閱讀節奏、分隔線聯絡方式與觸控操作。 | [手機](retro-preview/mobile-contact-before.webp) | [手機](retro-preview/mobile-contact.webp) |
| trend.html | 大型章節扉頁、錯位研究分欄、圖表邊註統計、細條 0–100% 比例尺；取消粗框、黃色 KPI 卡與硬陰影。 | [桌機](retro-preview/trend-before.webp) | [桌機](retro-preview/trend.webp) |
| mobile-trend.html | 統計邊註改雙欄導讀後接圖表、分析採單欄；新增同款章節跑馬燈。 | [手機](retro-preview/mobile-trend-before.webp) | [手機](retro-preview/mobile-trend.webp) |

共用系統：`assets/retro-editorial.css`，替代六頁引用的黑白 editorial.css；原檔保留供其他歷史工作參考。奶油白／裸粉／燕麥／玫瑰棕，中文明體與黑體、英文襯線、細線章節與不同欄寬。沿用既有字型子集，移除未使用且阻塞載入的 Playfair 請求。沒有引入新外部圖片。

測試修改：`_qa/check.py`、`_qa/section_reveal_audit.py`、`_qa/browser_audit.py`、新增 `_qa/editorial_interactions.py`；`.github/workflows/quality.yml` 納入新增互動與圖表回歸，release baseline 改用該 PR 真正的 base SHA。

## 內容與功能

九頁原始文字核對通過。另以最新 main 六頁完整正文 SHA-256 逐頁比較，包含 audited 圖表與 SVG 說明，全部完全相同；新增的手機導覽僅排除已獨立驗證的重複標籤，見 `_qa/editorial_content.py` 及 `content-parity.log`。工作照片 URL／來源署名、原始 JPG、履歷 PDF、學歷、任職期間與描述、研究段落及 SVG 幾何未更改。圖表 45.2%、42.5%、28.7%、24.4% 維持原始比例；獨立檢查完整名稱、百分比、CSS 絕對寬度、複選題及非市場占有率語義，沒有正規化。

原有互動 JavaScript 未修改。保留右往左進場方向、原有 observer 觸發、一次性顯示、鍵盤焦點、錨點、返回歷史、print、停用 JS／observer／reduced-motion 回退。三個聯絡方式只彈出一次並持續顯示；站內同分頁切換，原有跨文件轉場保留。

跑馬燈在桌機 hover 暫停、離開續播；觸控放開後恢復，錨點點擊立即續播，頁面捲動不中止；不新增暫停按鈕。鍵盤導覽與 reduced-motion 暫停屬既有無障礙行為。

## 實際執行

- 48 頁面／視口案例：六頁 × 320、375、390、428、768、1024、1440、1920。無水平溢出、本機破圖與 JS 錯誤。
- axe-core 4.10.3：六頁 × 390／1440，WCAG A／AA 掃描 0 violations；不代表人工無障礙全面認證。
- 一次性 reveal 六頁稽核通過，包含聯絡 3 pops、焦點、hash、列印、無 JS、無 observer、observer throws、執行中切換 reduced-motion。
- 新增實際瀏覽器互動測試：四頁跑馬燈、觸碰恢復、hover、捲動、錨點、鍵盤焦點、reduced-motion、同分頁切換與返回均通過。
- 原有 Node 三組檔案全部通過；HTML validate、字型涵蓋檢查、`git diff --check` 通過。
- 外部來源 8 條實際 HEAD：7 條 HTTP 200，Kantar HTTP 503，未擅改來源。

重現：

```sh
python3 _qa/check.py
python3 _qa/editorial_content.py
python3 _qa/mobile_font_subset.py --check
node --test _qa/*.test.cjs
CHROME_PATH=/usr/bin/chromium python3 _qa/section_reveal_audit.py
CHROME_PATH=/usr/bin/chromium python3 _qa/editorial_interactions.py
CHROME_PATH=/usr/bin/chromium python3 _qa/browser_audit.py --out /tmp/retro-audit --axe /path/to/axe.min.js
```

## Lighthouse

Lighthouse 12.8.2／系統 Chromium／本機 Python HTTP server，預設桌機與手機設定。分數依序為效能／無障礙／最佳實務／SEO。可讀證據見 [lighthouse.json](retro-evidence/lighthouse.json)。

| 版本 | 桌機 | 手機 |
| --- | --- | --- |
| 原版 main | 98 / 96 / 100 / 100 | 97 / 95 / 100 / 69 |
| 最終版（手機含跑馬燈） | 100 / 100 / 100 / 100 | 98 / 100 / 100 / 69 |

早期並行測試曾測得效能 79／77；追查 forced reflow 並移除逐段 pretty 文字重排後改善。最終手機跑馬燈加入後再次單獨重測為 98／100／100／69；並行 reveal 稽核時另有 74 分結果，保留於本機原始紀錄，不用於同環境基準比較。上述為本機個別測量，不冒稱三次中位數。手機原有 noindex,follow 導致 SEO 低於 80，依要求保留政策。

## 原始 CI 根因

已取得指定 run `42446447042` 的實際 job logs：

- source-integrity：trend／mobile-trend 的舊圖表標籤仍在 baseline，但 Page parser 排除 audited-visual 整塊，新增 SVG title／desc 又進入正文核對。保留既有完整性契約，精確列明這兩項表示方式差異，另增加圖表資料獨立檢查，沒有重建或覆寫原始基準。
- browser-accessibility：section_reveal_audit 在 CSS 過渡中要求 opacity 嚴格為 0，實際為 0.000569405、x=29.9641；是稽核取樣競態。原 main 的等待只看第一個 pending 元素，本次在取樣目標等待其動畫完成，若 observer 已讓它進場則跳過 pending 斷言；held-observer 仍獨立驗證每個單元 opacity=0、x>0，沒有放寬正式進場方向契約。
- PR #26 尚未合併，其資料與技術改善已有相近內容進入 main，本次從最新 main 工作，不 cherry-pick 舊分支；PR #16 只記錄圖片授權且有歷史衝突，未更動該 PR。

桌機與手機圖表實際畫面：[桌機圖表](retro-preview/trend-chart.webp)、[手機圖表](retro-preview/mobile-trend-chart.webp)。

## 限制與待確認

未收到參考圖附件，因此無法逐張視覺比對。PR #16 已記錄的工作照片公開再利用權仍待確認；本次保留精確既有素材與註記，沒有替換。離線版面稽核主動封鎖外部字型／工作圖片，相關截圖可能顯示原有載入失敗提示，不能宣稱外部圖永遠可用。

觸控為 Chromium 模擬，未以實體手機測雙指縮放；viewport 未限制縮放。沒有執行完整人工螢幕閱讀器測試。Kantar 暫時 503。手機 SEO 69 為保留原索引政策的例外。最終以使用者畫面確認為準，不合併、不正式部署。
