#!/usr/bin/env python3
"""Build the static 1200x630 Open Graph cards from og-manifest.json."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("og-manifest.json")
OUT = ROOT / "assets" / "og"
FONT_CANDIDATES = [
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
]


def font_path() -> Path:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise SystemExit("找不到可用的中文字型，停止產圖（未使用替代字型）。")


def width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=font)


def wrap_title(draw: ImageDraw.ImageDraw, title: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    break_after = set("，。？！：；、— ")
    for char in title:
        trial = current + char
        if current and width(draw, trial, font) > max_width:
            split = -1
            for idx in range(len(current) - 1, max(-1, len(current) - 8), -1):
                if current[idx] in break_after:
                    split = idx + 1
                    break
            if split > 0:
                lines.append(current[:split].strip())
                current = current[split:].strip() + char
            else:
                lines.append(current.strip())
                current = char
        else:
            current = trial
    if current.strip():
        lines.append(current.strip())
    return lines


def spaced_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont, fill: str, spacing: int = 5) -> None:
    x, y = xy
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += int(width(draw, char, font)) + spacing


def build(entry: dict[str, str], font_file: Path) -> Path:
    image = Image.new("RGB", (1200, 630), "#0d1512")
    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(0, 1201, 40):
        draw.line((x, 0, x, 630), fill=(232, 239, 233, 14), width=1)
    for y in range(0, 631, 40):
        draw.line((0, y, 1200, y), fill=(232, 239, 233, 14), width=1)

    brand_font = ImageFont.truetype(str(font_file), 28)
    eyebrow_font = ImageFont.truetype(str(font_file), 24)
    domain_font = ImageFont.truetype(str(font_file), 23)
    draw.rounded_rectangle((80, 73, 102, 95), radius=3, fill="#3fa878")
    draw.text((116, 67), "訂單秘書", font=brand_font, fill="#e8efe9")
    spaced_text(draw, (80, 146), entry["category"], eyebrow_font, "#3fa878", 4)

    size = 72
    while size >= 46:
        title_font = ImageFont.truetype(str(font_file), size)
        lines = wrap_title(draw, entry["title"], title_font, 1040)
        line_height = int(size * 1.35)
        if len(lines) <= 3 and len(lines) * line_height <= 286:
            break
        size -= 2
    if len(lines) > 3:
        raise SystemExit(f"標題無法在三行內排下：{entry['title']}")
    y = 195
    for line in lines:
        draw.text((80, y), line, font=title_font, fill="#e8efe9", stroke_width=0)
        y += line_height

    draw.rectangle((80, 550, 350, 555), fill="#3fa878")
    domain = "structaly.com"
    domain_width = width(draw, domain, domain_font)
    draw.text((1120 - domain_width, 530), domain, font=domain_font, fill="#93a69b")

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / entry["output"]
    image.save(target, format="PNG", optimize=True)
    return target


def main() -> None:
    selected_font = font_path()
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if len(entries) != 16:
        raise SystemExit(f"og-manifest.json 應有 16 筆，目前是 {len(entries)} 筆。")
    for entry in entries:
        target = build(entry, selected_font)
        with Image.open(target) as check:
            if check.size != (1200, 630):
                raise SystemExit(f"尺寸錯誤：{target}")
            # 標題區若只有底色與網格，非背景像素比例會異常低。
            crop = check.crop((70, 185, 1130, 500)).convert("RGB")
            bright = sum(1 for r, g, b in crop.getdata() if r > 120 and g > 120 and b > 120)
            if bright < 1500:
                raise SystemExit(f"標題區像素不足，疑似未成功繪字：{target}")
        print(f"{target.relative_to(ROOT)} 1200x630")
    print(f"font={selected_font}")


if __name__ == "__main__":
    main()
