#!/usr/bin/env python3
"""
CSS 健全性檢查：確認每一份樣式來源的 :root 真的會被瀏覽器套用。

為什麼需要這支：2026-09-06 發現 assets/trade.css 檔頭註解裡寫了
「/trades/ 星號 斜線 index.html」，那個「星號斜線」提早關閉了註解，
後面的中文說明變成無效 CSS，瀏覽器進入錯誤復原、把緊接著的整個 :root
區塊一起吞掉。結果是全站 23 個頁面的色票安靜失效、頁面整片白掉，
但檔案本身「看起來」完全正常，grep 也找得到 :root。

用法： python3 tools/check-css.py     （非 0 離開碼表示有問題）
"""
import glob
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def strip_comments(css):
    """照瀏覽器的規則移除註解：第一個 */ 就關閉，不管作者想不想。"""
    out, i = [], 0
    while True:
        a = css.find("/*", i)
        if a < 0:
            out.append(css[i:]); break
        out.append(css[i:a])
        b = css.find("*/", a + 2)
        if b < 0:
            break            # 未關閉的註解，後面全被吃掉
        i = b + 2
    return "".join(out)


def sources():
    for p in sorted(glob.glob(os.path.join(ROOT, "assets", "*.css"))):
        yield os.path.relpath(p, ROOT), open(p, encoding="utf-8").read()
    for p in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        css = "\n".join(re.findall(r"(?s)<style>(.*?)</style>", open(p, encoding="utf-8").read()))
        if css.strip():
            yield os.path.relpath(p, ROOT) + " (inline)", css


def main():
    bad = 0
    for name, css in sources():
        stripped = strip_comments(css)
        first = re.search(r"([^\s{][^{]*)\{", stripped)
        first_sel = first.group(1).strip() if first else "(無規則)"
        declares_root = ":root" in css
        root_survives = ":root" in stripped

        # 第一條規則的選擇器裡不該出現中文——出現就代表註解漏出來變成 CSS
        leaked = bool(re.search(r"[一-鿿]", first_sel))

        state = "✓"
        if declares_root and not root_survives:
            state = "✗"; bad += 1
        elif leaked:
            state = "✗"; bad += 1

        print(f"  {state} {name:30} 第一條規則 = {first_sel[:46]!r}")
        if state == "✗":
            print(f"      ↑ 註解提早關閉，後面的內容被當成 CSS。檢查註解裡有沒有『星號接斜線』。")

    print()
    print("全部通過" if not bad else f"{bad} 份樣式來源有問題")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
