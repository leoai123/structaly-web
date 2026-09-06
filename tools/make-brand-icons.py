#!/usr/bin/env python3
"""
產生品牌的 PNG 圖示（favicon / apple-touch-icon / PWA icon）。

為什麼要有這支腳本：品牌標的原稿是 assets/brand/mark.svg，但 favicon 與 app icon
必須是 PNG。這台機器不一定有 rsvg/cairosvg，所以這裡直接用 PIL 把同一組幾何
畫出來——**幾何定義只有一份，就在下面的 MARK**，改標記時只改那裡再重跑一次。

用法：
    python3 tools/make-brand-icons.py          # 產出全部尺寸
    python3 tools/make-brand-icons.py --check  # 只驗證現有檔案，不覆寫

輸出（assets/brand/）：
    favicon-16.png  favicon-32.png     滿版 pine 圓角方
    apple-touch-icon.png (180)          ink 底 + 內縮 pine 方塊，**不透明**（iOS 不吃透明）
    icon-192.png  icon-512.png          同上，PWA 用
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "assets", "brand")

INK = (13, 21, 18)        # --ink    #0d1512
PINE = (30, 77, 59)       # --pine   #1e4d3b
PAPER = (237, 240, 234)   # --paper  #edf0ea

SS = 8  # 超取樣倍率；PIL 沒有抗鋸齒，先畫大再縮小


# ── 標記幾何（32×32 viewBox，與 assets/brand/mark.svg 同一份定義）──────────
# 方向 B「先問清楚」：一個問號。對應的 SVG path 是
#   M9.5 11a6.5 6.5 0 0 1 13 0c0 4.5-6.5 4.5-6.5 9   (問號主體)
#   M16 25.5h.01                                      (下方的點)
def mark_polylines():
    """回傳 [(點串, 是否為點)]；座標在 32×32 空間，之後再依尺寸縮放。"""
    # 上半圓：圓心 (16,11)、半徑 6.5，從 180° 掃到 360°（SVG 的 y 向下，所以是繞過頂端）
    arc = [
        (16 + 6.5 * math.cos(math.radians(a)), 11 + 6.5 * math.sin(math.radians(a)))
        for a in range(180, 361, 3)
    ]
    # 三次貝茲：(22.5,11) → 控制點 (22.5,15.5) 與 (16,15.5) → (16,20)
    p0, p1, p2, p3 = (22.5, 11.0), (22.5, 15.5), (16.0, 15.5), (16.0, 20.0)
    cur = []
    for i in range(41):
        t = i / 40
        u = 1 - t
        cur.append(
            (
                u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
            )
        )
    return [(arc + cur[1:], False), ([(16.0, 25.5)], True)]


STROKE_W = 3.0  # 與 SVG 的 stroke-width 一致


def rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _stamp(draw, pts, r, color, step=0.45):
    """沿路徑密集蓋圓來畫描邊。

    比 ImageDraw.line(joint="curve") 可靠——那個做法在轉折處會留下鋸齒狀缺口
    （2026-09-06 實測，512px 的問號弧線上看得很清楚）。蓋圓等價於
    stroke-linecap:round + stroke-linejoin:round，而且不會有接縫。
    """
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / step))
        for j in range(n + 1):
            t = j / n
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def draw_mark(draw, ox, oy, tile_px, color):
    """把 32×32 空間的標記畫進一個邊長 tile_px、左上角在 (ox,oy) 的方塊裡。"""
    k = tile_px / 32.0
    r = max(0.5, STROKE_W * k / 2.0)
    for pts, is_dot in mark_polylines():
        scaled = [(ox + x * k, oy + y * k) for x, y in pts]
        if is_dot:
            cx, cy = scaled[0]
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
            continue
        _stamp(draw, scaled, r, color)


def render(size, inset):
    """inset=False → 滿版 pine 方塊；inset=True → ink 底 + 內縮的 pine 方塊。"""
    n = size * SS
    if inset:
        im = Image.new("RGB", (n, n), INK)          # 不透明，iOS 要求
        d = ImageDraw.Draw(im)
        pad = n * 0.115
        tile = n - 2 * pad
        rounded_rect(d, [pad, pad, n - pad, n - pad], tile * 0.22, PINE)
        draw_mark(d, pad, pad, tile, PAPER)
    else:
        im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        rounded_rect(d, [0, 0, n - 1, n - 1], n * 0.1875, PINE)  # rx 6/32
        draw_mark(d, 0, 0, n, PAPER)
    return im.resize((size, size), Image.LANCZOS)


TARGETS = [
    ("favicon-16.png", 16, False),
    ("favicon-32.png", 32, False),
    ("apple-touch-icon.png", 180, True),
    ("icon-192.png", 192, True),
    ("icon-512.png", 512, True),
]


def check():
    bad = 0
    for name, size, inset in TARGETS:
        p = os.path.join(OUT, name)
        if not os.path.isfile(p):
            print(f"  ✗ {name} 不存在"); bad += 1; continue
        im = Image.open(p)
        oks = im.size == (size, size)
        g = im.convert("L").getextrema()
        has_ink = (g[1] - g[0]) > 30
        opaque = True
        if inset:
            a = im.convert("RGBA").split()[-1]
            opaque = a.getextrema()[0] == 255
        state = oks and has_ink and opaque
        print(f"  {'✓' if state else '✗'} {name} {im.size[0]}x{im.size[1]} "
              f"對比={g[1]-g[0]} {'不透明' if opaque else '有透明！'}")
        bad += 0 if state else 1
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只驗證，不覆寫")
    a = ap.parse_args()
    if a.check:
        sys.exit(1 if check() else 0)
    os.makedirs(OUT, exist_ok=True)
    for name, size, inset in TARGETS:
        render(size, inset).save(os.path.join(OUT, name))
        print(f"  寫入 {name} ({size}x{size})")
    print("\n驗證：")
    sys.exit(1 if check() else 0)


if __name__ == "__main__":
    main()
