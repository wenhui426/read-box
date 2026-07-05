#!/usr/bin/env python3
"""
PDF 书籍解析脚本 — 提取文本和章节结构。
输出：纯文本，章节之间用 ===CHAPTER=== 分隔。
用法：python parse_pdf.py <文件路径>
"""
import sys, re

try:
    import fitz
except ImportError:
    print("需要安装 PyMuPDF: pip install PyMuPDF", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print("用法: python parse_pdf.py <文件路径>", file=sys.stderr)
    sys.exit(1)

path = sys.argv[1]
doc = fitz.open(path)

# 元数据
meta = doc.metadata
title = meta.get("title", "") or ""
author = meta.get("author", "") or ""

# 提取全文本
chapters = []
current_text = []
current_title = "前言"

title_patterns = [
    re.compile(r'^第[一二三四五六七八九十百千万\d]+[篇章节部]'),
    re.compile(r'^[一二三四五六七八九十百千]+[、\.]\s*'),
    re.compile(r'^\d{1,3}[、\.]\s*'),
]

def is_title(line):
    if len(line) > 40:
        return False
    for p in title_patterns:
        if p.match(line):
            return True
    return False

for page in doc:
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if b["type"] != 0:
            continue
        for line in b["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                font_size = span["size"]
                # 字号 >= 16 或内容模式匹配 → 标题
                if font_size >= 16 or is_title(text):
                    if current_text:
                        chapters.append((current_title, "\n".join(current_text)))
                    current_title = text
                    current_text = []
                else:
                    current_text.append(text)

if current_text:
    chapters.append((current_title, "\n".join(current_text)))

doc.close()

# 输出
print(f"TITLE: {title or '未知书名'}")
print(f"AUTHOR: {author or '未知作者'}")
for i, (t, c) in enumerate(chapters, 1):
    print(f"===CHAPTER {i}===")
    print(f"TITLE: {t}")
    print(f"CONTENT: {c[:5000]}")
