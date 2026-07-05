#!/usr/bin/env python3
"""
EPUB 书籍解析脚本 — 提取目录和正文。
输出：纯文本，章节之间用 ===CHAPTER=== 分隔。
用法：python parse_epub.py <文件路径>
"""
import sys

try:
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    print("需要安装依赖: pip install ebooklib beautifulsoup4", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print("用法: python parse_epub.py <文件路径>", file=sys.stderr)
    sys.exit(1)

path = sys.argv[1]
book = epub.read_epub(path)

title = ""
for meta in book.get_metadata("DC", "title"):
    title = meta[0] if meta else ""
    break

author = ""
for meta in book.get_metadata("DC", "creator"):
    author = meta[0] if meta else ""
    break

print(f"TITLE: {title or '未知书名'}")
print(f"AUTHOR: {author or '未知作者'}")

sort_order = 0
for item in book.get_items():
    if item.get_type() == 9:  # ITEM_DOCUMENT
        sort_order += 1
        content_html = item.get_content().decode("utf-8", errors="replace")
        soup = BeautifulSoup(content_html, "html.parser")
        text = soup.get_text(separator="\n").strip()
        # 提取标题
        ch_title = ""
        for tag in ["h1", "h2", "h3"]:
            elem = soup.find(tag)
            if elem and elem.get_text(strip=True):
                ch_title = elem.get_text(strip=True)
                break
        if not ch_title:
            ch_title = f"第{sort_order}章"

        print(f"===CHAPTER {sort_order}===")
        print(f"TITLE: {ch_title}")
        print(f"CONTENT: {text[:5000]}")
