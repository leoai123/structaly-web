#!/bin/sh
# =============================================================================
# 換網域用：把整站寫死的網域一次改掉。
#
#   ./set-base-url.sh https://structaly.com https://新網域
#
# 第一個參數是「現在的網域」，第二個是「要換成的網域」，兩個都不要加結尾斜線。
# 會改到的檔案：index.html、privacy.html、terms.html、trades/*/index.html、
#               blog/index.html、blog/*/index.html、llms.txt、robots.txt、sitemap.xml。
#
# 為什麼只要改這些？因為所有內部連結都是相對路徑（/trades/vegetable、
# /assets/…、/privacy.html），只有這幾種東西一定得寫絕對網址：
#   · <link rel="canonical">
#   · og:url / og:image / og:image:secure_url / twitter:image
#   · JSON-LD 裡的 @id / url / item / logo / image
#   · robots.txt 的 Sitemap 行、sitemap.xml 的 <loc>
# 每個 HTML 檔的 <head> 最上面都有一塊「絕對網址區」把它們集中在一起，
# 手改也可以，這支只是幫你一次改完不漏。
#
# 改完記得：
#   1. 到 Google Search Console 重新提交 sitemap；
#   2. 舊網域設 301 轉址到新網域，不然累積的排名會斷掉。
# =============================================================================

set -eu

if [ $# -ne 2 ]; then
  echo "用法: $0 <舊網域> <新網域>" >&2
  echo "例:   $0 https://structaly.com https://www.example.com" >&2
  exit 1
fi

OLD=$1
NEW=$2
DIR=$(cd "$(dirname "$0")" && pwd)

# 除了帶 scheme 的絕對網址，註解裡還會出現「裸網域」（例如 robots.txt 第一行的
# 「# 訂單秘書 — 舊網域.com」那種）。只換帶 https:// 的會漏掉它，
# 所以這裡把主機名也單獨抓出來一起換。
OLD_HOST=${OLD#*://}
NEW_HOST=${NEW#*://}

FILES="index.html privacy.html terms.html llms.txt robots.txt sitemap.xml"
for f in $FILES; do
  [ -f "$DIR/$f" ] || { echo "找不到 ${f}，先確認目錄是完整的" >&2; exit 1; }
done

TOUCHED=0
for f in $FILES $(cd "$DIR" && ls trades/*/index.html blog/index.html blog/*/index.html 2>/dev/null); do
  if grep -q "$OLD_HOST" "$DIR/$f" 2>/dev/null; then
    # macOS 與 GNU 的 sed -i 參數不同，先寫暫存檔再覆蓋，兩邊都能跑
    sed -e "s|$OLD|$NEW|g" -e "s|$OLD_HOST|$NEW_HOST|g" "$DIR/$f" > "$DIR/$f.tmp" && mv "$DIR/$f.tmp" "$DIR/$f"
    n=$(grep -c "$NEW" "$DIR/$f" || true)
    echo "改好 ${f}（${n} 處）"
    TOUCHED=$((TOUCHED + 1))
  fi
done

echo "---"
echo "共改了 $TOUCHED 個檔案。剩下這些地方還提到舊網域（應該要是 0）："
grep -rn "$OLD_HOST" "$DIR" --include='*.html' --include='*.txt' --include='*.xml' || echo "（沒有了）"
