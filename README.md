# structaly-web — 訂單秘書官網

[structaly.com](https://structaly.com) 的整站原始檔。給食材行、材料行、耗材行等
中小供應商的 LINE 收單服務「訂單秘書」的對外官網。

**純靜態，沒有建置流程與框架。** 執行期唯一的外部資源是 Google Fonts 提供的
IBM Plex Mono 與 Noto Sans TC；其餘 CSS、JavaScript 與圖片都在 repo 內。
repo 裡的目錄結構就是網站的網址結構，改完檔案直接部署即可。

---

## 網站結構

| 網址 | 檔案 |
|---|---|
| `/` | `index.html` |
| `/trades/vegetable`、`/meat`、`/hardware`、`/supplies`、`/bakery`、`/beverage` | `trades/<slug>/index.html` |
| `/privacy` | `privacy.html` |
| `/terms` | `terms.html` |
| `/blog` | `blog/index.html` |
| `/blog/<slug>` | `blog/<slug>/index.html` |
| `/404` 與不存在的路徑 | `404.html` |
| `/llms.txt`、`/llms-full.txt` | 給 AI 讀取的網站索引與正文展平版 |
| `/blog/feed.xml` | 部落格 RSS 2.0 feed |
| `/robots.txt`、`/sitemap.xml` | 同名檔案 |
| 圖片／影片／CSS／JS | `assets/` |
| 離線產生工具 | `tools/`（OG 圖與 llms-full.txt；由 `.assetsignore` 排除，不公開） |

六個 `/trades/<slug>` 是產業別的到達頁，共用 `assets/trade.css` 與
`assets/trade.js`（首頁 `index.html` 的樣式是自己 inline 的，改主視覺時兩邊要一起改）。

### 為什麼 `/privacy` 沒有 `.html`

檔案叫 `privacy.html`，但線上網址是 `/privacy`。Cloudflare Workers Static Assets
會把所有 `.html` 結尾的請求 307 導向去掉副檔名的網址，這是平台行為、關不掉
（除非改用 `html_handling: "none"`，但那樣 `/trades/meat` 這種資料夾索引頁會直接 404）。
canonical 一定要寫「真的回 200 的那一個網址」，所以站內連結、canonical、sitemap
全部都不帶 `.html`。**不要把它們改回 `.html`**，會造成 canonical 指向一個 307。

---

## 本地預覽

沒有 npm install 這種東西，兩種都可以：

```bash
# 1) 最快：內建 HTTP server（注意：/trades/meat 這種網址在這裡要打 /trades/meat/）
python3 -m http.server 8000

# 2) 跟線上行為一致（含 drop-trailing-slash 的轉址規則），推薦改網址結構時用這個
npx wrangler dev
```

`wrangler dev` 會照 `wrangler.jsonc` 的設定跑，是唯一能重現線上轉址行為的方式。

---

## 部署

Cloudflare **Workers Static Assets**（不是 Pages）。已用 OAuth 登入的話直接：

```bash
npx wrangler deploy
```

- Worker 名稱 `structaly-web`，設定全在 `wrangler.jsonc`。
- `.assetsignore` 列的檔案不會被上傳，也就不會被公開存取
  （`wrangler.jsonc`、`set-base-url.sh`、`README.md` 等維護用檔案）。
  **新增任何不該被公開的檔案時記得補進去**——`assets.directory` 是 repo 根目錄，
  沒列到的東西一律會上線。
- 每次部署都是一個新版本，可以在 Cloudflare dashboard 直接 rollback。

### `html_handling` 這個設定不要亂改

`wrangler.jsonc` 裡的 `"html_handling": "drop-trailing-slash"` 是刻意選的。
Cloudflare 的預設值是 `auto-trailing-slash`，那會把 `/trades/meat` 導去
`/trades/meat/`（帶結尾斜線），六個產業頁的 canonical 就會全部指向 307。
現在的設定讓不帶斜線的網址直接回 200，跟站內連結、canonical、sitemap 一致。

實測過的行為（`structaly-web.taipei666.workers.dev`）：

| 請求 | 結果 |
|---|---|
| `/trades/meat` | 200 |
| `/trades/meat/`、`/trades/meat/index.html` | 307 → `/trades/meat` |
| `/privacy` | 200 |
| `/privacy.html` | 307 → `/privacy` |
| `/index.html` | 307 → `/` |
| 不存在的路徑 | 404 |

---

## 換網域

整站的內部連結都是相對路徑，搬家時不用動。真正把網域寫死的只有這幾種：
`<link rel="canonical">`、`og:url` / `og:image` / `twitter:image`、
JSON-LD 裡的 `@id` / `url` / `item` / `logo` / `image`、`robots.txt` 的 `Sitemap:` 行、
`sitemap.xml` 的 `<loc>`。每個 HTML 的 `<head>` 最上面有一塊「絕對網址區」把它們集中在一起。

`set-base-url.sh` 會一次改完全部：

```bash
./set-base-url.sh https://structaly.com https://新網域
# 參數是「現在的網域」和「要換成的網域」，都不要加結尾斜線。
# 跑完會自己 grep 一次，列出還提到舊網域的地方（應該要是 0）。
```

改完之後一定要做的三件事：

1. `npx wrangler deploy` 重新部署；
2. 到 Google Search Console 重新提交 `sitemap.xml`；
3. **舊網域設全站 301 對應到新網域**（路徑一對一，不要全部導首頁），
   不然累積的搜尋排名會斷掉。

自己驗一次（不要只信腳本的輸出）：

```bash
grep -rn "舊網域" . --exclude-dir=.git
```

---

## 綁定 structaly.com（尚未完成，需要人工到 GoDaddy 操作）

現況：`structaly.com` 的 nameserver 在 GoDaddy（`ns33/ns34.domaincontrol.com`），
A 記錄指向 Render（`216.24.57.1`），`www` 是 CNAME 到 `structaly-pify.onrender.com`。
Cloudflare 帳號底下目前**一個 zone 都沒有**。

Workers 的自訂網域**必須**由 Cloudflare 當該網域的權威 DNS，不能只在 GoDaddy 加一筆
記錄指過來。所以要做的是**換 nameserver**，不是改單筆記錄。

### 步驟

1. Cloudflare dashboard → Add a domain → `structaly.com` → Free 方案。
   Cloudflare 會掃描現有記錄並匯入，**匯入後一定要逐筆核對**，特別是收信用的：

   | 類型 | 名稱 | 值 |
   |---|---|---|
   | MX | `@` | `smtp.secureserver.net`（優先度 0） |
   | MX | `@` | `mailstore1.secureserver.net`（優先度 10） |
   | TXT | `@` | `v=spf1 include:spf.em.secureserver.net ?all` |
   | TXT | `@` | `google-site-verification=hbMezpaxYsIH7pP0zQ-r0GTJk8PIvlEugQiTONwma2c` |

   **這四筆漏掉就會收不到信、Google 驗證也會掉。**

2. Cloudflare 會給兩台 nameserver，到 GoDaddy 把 NS 換成那兩台。
   生效通常幾分鐘到數小時。

3. zone 變 active 後，把 `wrangler.jsonc` 裡 `routes` 那段註解拿掉，
   `npx wrangler deploy`。Cloudflare 會自動建立 DNS 記錄與憑證。

4. 加一條 Redirect Rule：`www.structaly.com/*` → `https://structaly.com/$1`（301）。

5. 舊的 `order.tripdaynday.com` 再上 301（見「搬家紀錄」）。

---

## 搬家紀錄

- 本站原本在 Vercel 的 `order.tripdaynday.com`（Vercel 專案 `order-landing`）。
- 2026-09 搬到 Cloudflare Workers + `structaly.com`。
- 舊的 Vercel 專案保留著，只放一份 `vercel.json` 做全站 301 對應到新網域，
  用來保住已經累積的 SEO。那個專案不要刪，也不要讓它過期。
