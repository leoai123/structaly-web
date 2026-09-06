#!/usr/bin/env python3
"""
產生品牌的 PNG 圖示（favicon / apple-touch-icon / PWA icon）。

單一來源是 assets/brand/mark-tile.svg——改品牌標只要改那一支，跑這支腳本即可。

## 為什麼用 qlmanage 而不是自己畫

2026-09-06 之前的品牌標是「描邊」造形，可以用 PIL 沿路徑蓋圓畫出來。
改成 carbon（兩張錯位複寫單）之後是**實心 path 加 fill-rule="evenodd" 負空間**，
自己寫光柵器要處理貝茲曲線與奇偶填充規則，不划算也容易出錯。
macOS 內建的 qlmanage 可以直接把 SVG 轉成 PNG，用它先出高解析度再用 PIL 縮放。

這台機器沒有 rsvg-convert 也沒有 cairosvg，所以不用它們。

## 用法

    python3 tools/make-brand-icons.py          # 產出全部尺寸
    python3 tools/make-brand-icons.py --check  # 只驗證現有檔案，不覆寫

## 輸出（assets/brand/）

    favicon-16.png  favicon-32.png      滿版圓角方（直接縮放 mark-tile）
    apple-touch-icon.png (180)          ink 底 + 內縮的標記，**不透明**（iOS 不吃透明）
    icon-192.png  icon-512.png          同上，PWA 用
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BRAND = os.path.join(ROOT, "assets", "brand")
SRC = os.path.join(BRAND, "mark-tile.svg")

INK = (13, 21, 18)          # --ink #0d1512
RENDER_PX = 1024            # 先出這個解析度，再往下縮

TARGETS = [
    # (檔名, 尺寸, 是否放在 ink 底上並內縮)
    ("favicon-16.png", 16, False),
    ("favicon-32.png", 32, False),
    ("apple-touch-icon.png", 180, True),
    ("icon-192.png", 192, True),
    ("icon-512.png", 512, True),
]


def rasterize(svg_path, px):
    """用 qlmanage 把 SVG 轉成 RGBA PNG。回傳 PIL Image。"""
    if not shutil.which("qlmanage"):
        sys.exit("找不到 qlmanage（macOS 內建）。請改用其他 SVG 光柵化工具。")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["qlmanage", "-t", "-s", str(px), "-o", tmp, svg_path],
            capture_output=True, check=False,
        )
        out = [f for f in os.listdir(tmp) if f.endswith(".png")]
        if not out:
            sys.exit(f"qlmanage 無法轉換 {svg_path}")
        im = Image.open(os.path.join(tmp, out[0])).convert("RGBA")
        im.load()
        return im


def build(base, size, inset):
    if not inset:
        return base.resize((size, size), Image.LANCZOS)
    # ink 不透明底 + 內縮的標記。內縮比例跟前一版一致，換標記時視覺重量才不會跳。
    canvas = Image.new("RGB", (size, size), INK)
    pad = round(size * 0.115)
    inner = size - 2 * pad
    tile = base.resize((inner, inner), Image.LANCZOS)
    canvas.paste(tile, (pad, pad), tile)
    return canvas


def check():
    bad = 0
    for name, size, inset in TARGETS:
        p = os.path.join(BRAND, name)
        if not os.path.isfile(p):
            print(f"  ✗ {name} 不存在"); bad += 1; continue
        im = Image.open(p)
        size_ok = im.size == (size, size)
        g = im.convert("L").getextrema()
        drawn = (g[1] - g[0]) > 30          # 不是一片空白
        opaque = True
        if inset:
            opaque = im.convert("RGBA").split()[-1].getextrema()[0] == 255
        good = size_ok and drawn and opaque
        bad += 0 if good else 1
        print(f"  {'✓' if good else '✗'} {name} {im.size[0]}x{im.size[1]} "
              f"對比={g[1]-g[0]} {'不透明' if opaque else '有透明！'}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只驗證，不覆寫")
    args = ap.parse_args()
    if args.check:
        sys.exit(1 if check() else 0)

    base = rasterize(SRC, RENDER_PX)
    print(f"  來源 {os.path.relpath(SRC, ROOT)} → {base.size[0]}px")
    for name, size, inset in TARGETS:
        build(base, size, inset).save(os.path.join(BRAND, name))
        print(f"  寫入 {name} ({size}x{size})")
    print("\n驗證：")
    sys.exit(1 if check() else 0)


if __name__ == "__main__":
    main()
