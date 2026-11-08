# 低飽和粉色活動網站風格改版

本次依使用者新增的 [Hello Kitty 的感性散步](https://hellokittyemotion.sanrio.com.tw/) 網站參考及「整體低飽和粉色」要求，更新既有 PR #28。承接已確認的第一版 `d8de4bc`，main 仍為 `5646383`。不合併、不正式部署。

## 參考分析與實際改動

已用 Chromium 開啟參考網站、捲動觸發進場，檢查 1440px 及 390px 的實際畫面。參考特徵為大幅主視覺、圓潤字形、傾斜拍立得拼貼、對話框標籤、分段色塊、波浪棚邊與底部固定操作區。

轉譯為霧粉／奶油白／玫瑰棕及少量灰綠，移除參考的亮黃、紅綠高彩度。人物使用既有本人照，花草、愛心、紙膠帶與星形為本次原創 SVG／CSS 裝飾，沒有把 Sanrio 的角色、商標、文案或照片放入履歷。

| 頁面 | 本次構圖 | 前版 | 新版 |
| --- | --- | --- | --- |
| index.html | 將姓名／職務、介紹與學歷、三項歷練分成新 cover-heading／cover-introduction／highlight shelf；右側為膠帶拍立得與植物塗鴉主視覺，原操作欄移為底部橫向區。 | [桌機](pastel-preview/index-before.webp) | [桌機](pastel-preview/index.webp) |
| mobile.html | 上下堆疊的完整人物海報、獨立人物說明與檔案筆記；維持章節跑馬燈及底部導覽。 | [手機](pastel-preview/mobile-before.webp) | [手機](pastel-preview/mobile.webp) |
| contact.html | 拍立得人物照片與左側資料便箋，右側為圓角信紙與三個聯絡區塊。 | [桌機](pastel-preview/contact-before.webp) | [桌機](pastel-preview/contact.webp) |
| mobile-contact.html | 姓名、照片、檔案與聯絡方式重新組成單欄信紙。 | [手機](pastel-preview/mobile-contact-before.webp) | [手機](pastel-preview/mobile-contact.webp) |
| trend.html | 圓潤大標分為主題／研究對象／策略副標三層，粉色扉頁與波浪邊界，分析段落維持開放分欄。 | [桌機](pastel-preview/trend-before.webp) | [桌機](pastel-preview/trend.webp) |
| mobile-trend.html | 研究導讀氣泡、上下閱讀、獨立數據邊註，延續同款粉色標籤與比例圖。 | [手機](pastel-preview/mobile-trend-before.webp) | [手機](pastel-preview/mobile-trend.webp) |

工作經歷改成稍微錯位的照片拼貼與職責欄，保留指定的三個圖片 URL 與來源。未能載入外部照片時保留既有失敗提示。圖表仍以 0–100% 絕對尺度展示原數字，沒有把複選題變成市場占有率或重新正規化。

## 檔案摘要

- 六個 HTML：首頁新增語義分組、手機主視覺類別、研究大標分層，以及新頁面樣式引用。原始可見文字及順序沒有變更。
- `assets/retro-editorial.css`：重寫共用色彩、主視覺、文字、圓角標籤、照片拼貼、段落與手機版構圖。
- `assets/pastel-details.css`：聯絡頁信紙／拍立得及研究頁扉頁／圖表／資料來源排版。
- `assets/pastel-garden.svg`、`assets/pastel-flower.svg`：原創、無文字的裝飾插圖。
- `docs/pastel-preview/`、`docs/pastel-evidence/`：本次畫面與驗證證據；前版資料仍存於 retro 目錄。

既有互動 JavaScript、導覽目的地、PDF、照片 URL、研究資料與 noindex 政策未更動；沒有新增第三方套件或資源來源。

## 驗證

六頁完整正文（包含圖表、SVG 說明與署名）與最新 main 的 SHA-256 比對通過；既有九頁 check.py 內容、連結、圖片、canonical 與索引契約通過。HTML validate、字型涵蓋、原有 Node 三組回歸及 git diff --check 通過。

本次瀏覽器測試、無障礙、進場、互動與 Lighthouse 結果見下方最終實測紀錄及同目錄證據。瀏覽器版面稽核封鎖外部資源，相關圖片載入能力由 CI 的線上 release-audit 另行確認。

## 限制

觸控為 Chromium 模擬，沒有實體手機雙指縮放或完整人工螢幕閱讀器稽核。保留手機 noindex,follow，因此 SEO 分數可低於 80。PR #16 的既有工作照片公開再利用權問題仍待確認，沒有擅換素材。本次已收到可瀏覽的參考網址，未引用其受保護素材。

## 最終本機實測紀錄

- 六頁 × 320、375、390、428、768、1024、1440、1920：48 案例全數通過；沒有水平溢出、JavaScript 錯誤或本機破圖。
- 六頁 × 390／1440：12 次 axe-core 4.10.3 掃描，0 violations。第一次檢查找到聯絡頁手機版切換連結的淡色文字對比問題，修正後已對最終樣式完整重驗 48 案例與 12 次 axe。
- 六頁進場與三個聯絡區塊一次性彈出：通過；包含不重播、focus、hash、print、停用 JS、observer 失效與 reduced-motion。
- 四頁跑馬燈：hover 暫停、觸控放開後恢復、捲動與錨點續播、鍵盤焦點、同分頁轉場及返回全部通過。
- 最終頁面改用明確 body 類別，減少 relational selector 比對；重構後已完整重驗。
- Lighthouse 12.8.2／系統 Chromium，本機逐一執行、單次取樣，沒有把並行測試當成效能基準：

| 裝置 | 效能 | 無障礙 | 最佳實務 | SEO |
| --- | ---: | ---: | ---: | ---: |
| 桌機 | 100 | 100 | 100 | 100 |
| 手機 | 97 | 100 | 100 | 69 |

手機效能與原 main 在前次相同環境量得的 97 一致。手機 SEO 69 為既有 noindex,follow 的政策例外，未更改。分數與完整摘要見 [lighthouse.json](pastel-evidence/lighthouse.json)。CI 的三次量測及線上圖片檢查另見 PR checks／release-audit artifact，不將未完成的 CI 宣稱通過。

原始資料核對：[內容](pastel-evidence/content-parity.log)、[完整性](pastel-evidence/integrity.json)；瀏覽器證據：[視口與 axe](pastel-evidence/browser.json)、[進場](pastel-evidence/reveal.log)、[互動](pastel-evidence/interactions.log)、[Node](pastel-evidence/node.log)。

完整頁面畫面：[桌機首頁](pastel-preview/index-full.webp)、[手機首頁](pastel-preview/mobile-full.webp)、[桌機聯絡](pastel-preview/contact-full.webp)、[手機聯絡](pastel-preview/mobile-contact-full.webp)、[桌機研究](pastel-preview/trend-full.webp)、[手機研究](pastel-preview/mobile-trend-full.webp)。
