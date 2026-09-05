#!/usr/bin/env python3
"""Flatten visible main content into deterministic llms-full.txt Markdown."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    ("https://structaly.com/", ROOT / "index.html"),
    *[(f"https://structaly.com/trades/{s}", ROOT / "trades" / s / "index.html") for s in ("vegetable", "meat", "hardware", "supplies", "bakery", "beverage")],
    *[(f"https://structaly.com/blog/{s}", ROOT / "blog" / s / "index.html") for s in ("manual-order-taking-hidden-cost", "line-order-vs-erp", "line-order-system-how-to-choose", "where-orders-get-lost", "order-cutoff-and-late-orders", "product-alias-mapping", "line-group-order-to-picking-list", "line-order-reconciliation-csv")],
]

class MainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_main = 0
        self.skip = 0
        self.block: str | None = None
        self.buffer: list[str] = []
        self.lines: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "main": self.in_main += 1
        if not self.in_main: return
        if tag in {"nav", "script", "style", "footer", "header", "button"}: self.skip += 1
        if not self.skip and tag in {"h1", "h2", "h3", "p", "li", "figcaption", "th", "td"}:
            self.flush()
            self.block = tag

    def handle_endtag(self, tag: str) -> None:
        if self.in_main and tag in {"nav", "script", "style", "footer", "header", "button"} and self.skip:
            self.skip -= 1
        if self.block == tag:
            self.flush()
            self.block = None
        if tag == "main" and self.in_main: self.in_main -= 1

    def handle_data(self, data: str) -> None:
        if self.in_main and not self.skip and self.block:
            self.buffer.append(data)

    def flush(self) -> None:
        if not self.block or not self.buffer:
            self.buffer = []
            return
        text = re.sub(r"\s+", " ", "".join(self.buffer)).strip()
        self.buffer = []
        if not text: return
        prefix = {"h1":"# ", "h2":"## ", "h3":"### ", "li":"- ", "figcaption":"圖解說明：", "th":"| ", "td":"| "}.get(self.block, "")
        self.lines.append(prefix + text)

def extract(path: Path) -> str:
    parser = MainText()
    parser.feed(path.read_text(encoding="utf-8"))
    return "\n\n".join(parser.lines)

def main() -> None:
    chunks = ["# 訂單秘書完整內容", "> 這是 https://structaly.com 的可見正文 Markdown 展平版，供 AI 系統理解服務範圍、產業情境與實務文章。導覽、頁尾與結構化資料已移除。"]
    for url, path in PAGES:
        chunks.extend([f"\n---\n\n來源：{url}", extract(path)])
    output = "\n\n".join(chunks).strip() + "\n"
    (ROOT / "llms-full.txt").write_text(output, encoding="utf-8", newline="\n")
    print(f"llms-full.txt {len(output.encode('utf-8'))} bytes")

if __name__ == "__main__": main()
