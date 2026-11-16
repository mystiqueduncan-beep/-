# 跑馬燈橫幅驗收

基準：最新 `main` 的 `6b3d4bfc51e3f0cc2976a08667b6255a1d1fb45c`。變更與最終 CI：[PR #105](https://github.com/mystiqueduncan-beep/-/pull/105)。

## 變更

- 背景從整行 sticky 移到實際 `.keycap-marquee`；外層保持透明、無整行 blur 或邊框。
- 框寬依原始 `.keycap-marquee__group` 的內容寬度加框內留白計算；首頁上限 980px、研究頁上限 1120px。未使用含前後留白的 belt 寬度。
- 手機保留原 wrapper、約 12px 外距、53px sticky 偏移及既有按鈕尺寸。
- 四頁背景統一 `rgba(255,249,247,.70)`、12px blur、24px 圓角及淡粉框。按鈕不透明，軌道透明，星星愛心與原有間距保留。
- start/interlude 仍以實際 viewport 計算，比例未縮減；新增 viewport ResizeObserver。偏好狀態僅在 change 事件讀取，並在重新啟用動態時初始化位置，避免切換減少動態效果後出現空白。
- 沒有修改 HTML、履歷、研究內容、圖表數據、聯絡功能、卡片展開或圖片素材。

## 實際框寬

本機 Playwright 1.62.0、Chrome for Testing 151.0.7922.34；以帶 `?view=desktop/mobile` 的四個實際頁面測試。字型環境不同時內容自適應寬度可略變，上限保持一致。

| 視窗 | 首頁桌面 | 研究桌面 | 手機首頁 | 手機研究 |
| --- | ---: | ---: | ---: | ---: |
| 390px | 346px | 346px | 366px | 366px |
| 430px | 386px | 386px | 406px | 406px |
| 768px | 724px | 724px | 744px | 744px |
| 1024px | 848px | 980px | 744px | 1000px |
| 1440px | 848px | 1120px | 744px | 1416px |
| 1920px | 848px | 1120px | 744px | 1456px |

大螢幕強制手機版保留原本 wrapper/container 上限；12px 外距相對該頁的內容區域。完整量測與各案互動結果見 [measurements.json](measurements.json)。

## 修改前後截圖

所有截圖以同一瀏覽器、相同尺寸、相同 sticky 捲動位置擷取，暫停跑馬燈以利比對。完整六尺寸截圖由 CI `compact-marquee-banner-review` artifact 保存。

| 頁面 | 修改前 | 修改後 |
| --- | --- | --- |
| 桌面首頁 1440px | [前](before/index-1440.png) | [後](after/index-1440.png) |
| 桌面研究 1440px | [前](before/trend-1440.png) | [後](after/trend-1440.png) |
| 手機首頁 390px | [前](before/mobile-390.png) | [後](after/mobile-390.png) |
| 手機研究 390px | [前](before/mobile-trend-390.png) | [後](after/mobile-trend-390.png) |

## 驗證與限制

- 新增真實瀏覽器驗收：四頁 × 390/430/768/1024/1440/1920，共 24/24 通過。包含外框與背景範圍、內容尺寸、裝飾、滑動循環、滑鼠 hover/拖曳、CDP 觸控、鍵盤與點擊跳轉、章節高亮、sticky、resize，以及原生 reduced-motion 往返切換。
- 來源完整性檢查 17 組命令通過；最終 Node 回歸 38/38 通過；JS 語法與 diff 格式檢查通過。
- 既有響應式套件 60/60 通過；12 次 axe-core 4.10.3，0 violations。見 [browser-summary.json](browser-summary.json)。axe 仍列有既有 aria-label/role 與複雜背景對比的 incomplete，未宣稱這些人工檢查項目全部排除；跑馬燈按鈕保留不透明底色、既有高對比文字與焦點框。
- 既有 sticky 首頁、研究頁、高亮/聯絡回歸、section reveal、research CTA、editorial interactions、roadmap interactions 均通過。
- 本機 Lighthouse 12.8.2 前後各執行桌面/手機各三次，共 12 次，無 runtimeError；無障礙均為 100。桌面修改後 performance 99/99/99、手機 86/67/60，並行負載及網路會影響數值，不據此宣稱效能提升。完整分數及限制見 [local-lighthouse-summary.json](local-lighthouse-summary.json)。
- 本機 `release_audit.py` **未通過**：Chromium 不信任環境代理 CA，三張既有外站圖片出現 `ERR_CERT_AUTHORITY_INVALID`。修改前相同，HTTPS client 驗證三張圖均 200；沒有停用 TLS 或更換圖片。GitHub CI 的 `release-audit` 可在正常信任環境執行同一套完整檢查，合併依最後一次 CI 通過結果判定。
- 本機系統 Chromium 的三語標題測試在修改前後均有既存 3px 字框差，超過其 2px 斷言。另嘗試 CI 指定 Playwright 1.51 / Chromium134，但本機載入 mobile 時 Page crashed，未宣稱通過；沒有修改相關 CSS 或放寬斷言。該項由 GitHub CI 相同固定版本驗證。

[Git diff](changes.patch) 包含正式碼與相應測試；PR 的 Files changed 提供完整版本比較。部署前必須等待 PR 所有必要 CI 通過。
