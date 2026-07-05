"""
TXT 书籍解析器

使用 chardet 自动检测编码，通过正则匹配识别章节标题。
支持"第X章""第X节""## "等多种常见章节标题格式。

解析策略：
- 先用 chardet 检测文件编码
- 按检测结果解码全文
- 逐行扫描匹配章节标题正则
- 无标题匹配时按空行分段组合
"""

import re
import chardet
from app.parsers.base import BaseParser, ParseResult, ChapterData


# 章节标题匹配模式
# 支持以下格式：
# - 第X章 / 第X节 / 第X部 / 第X篇
# - ## / ### / #### （Markdown 标题）
# - X. / X、 （数字序号标题）
# - 【XXX】（括号标题）
CHAPTER_PATTERNS = [
    r"^第[零一二三四五六七八九十百千\d]+[章节部篇].*",  # 第X章/节/部/篇
    r"^#{2,4}\s.+",                                    # ## Markdown 标题
    r"^\d{1,2}[、\.]\s.*",                             # 数字序号
    r"^【.+】",                                         # 【括号】标题
    r"^[一二三四五六七八九十]{1,2}[、\.]\s.*",          # 中文数字序号
]

# TXT 读取块大小（用于编码检测）
DETECT_READ_SIZE = 8192

# 单章最大段落数（无标题时的自动分段策略）
MAX_PARAGRAPHS_PER_CHAPTER = 8


class TxtParser(BaseParser):
    """TXT 格式解析器"""

    def __init__(self) -> None:
        """初始化 TXT 解析器"""
        self.title: str = ""
        self.author: str = ""

    def parse(self, file_path: str) -> ParseResult:
        """
        解析 TXT 文件

        Args:
            file_path: TXT 文件的绝对路径

        Returns:
            ParseResult: 包含书名、作者和章节树
        """
        # 检测文件编码
        encoding = self._detect_encoding(file_path)

        # 读取全文
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            text = f.read()

        # 从文件名提取书名
        import os
        filename = os.path.basename(file_path)
        self.title = os.path.splitext(filename)[0]

        # 按行分割
        lines = text.split("\n")

        chapters: list[ChapterData] = []
        current_lines: list[str] = []
        current_title = "前言"
        current_order = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                current_lines.append("")
                continue

            # 检查是否为章节标题
            if self._is_chapter_title(stripped):
                # 保存上一章节
                if current_lines:
                    content = "\n".join(current_lines).strip()
                    if content:
                        current_order += 1
                        chapter = ChapterData(
                            title=current_title,
                            level=1,
                            sort_order=current_order,
                            content=content,
                            word_count=len(content),
                        )
                        chapters.append(chapter)

                # 新章节开始
                current_title = stripped
                current_lines = []

            # 收集正文内容（包括标题行后的首段）
            current_lines.append(stripped)

        # 处理最后一章
        if current_lines:
            content = "\n".join(current_lines).strip()
            if content:
                current_order += 1
                chapter = ChapterData(
                    title=current_title,
                    level=1,
                    sort_order=current_order,
                    content=content,
                    word_count=len(content),
                )
                chapters.append(chapter)

        # 如果没有按标题分割出章节，按段落自动分段
        if len(chapters) <= 1:
            chapters = self._auto_split(text)

        total_words = sum(ch.word_count for ch in chapters)

        return ParseResult(
            title=self.title or "未知书名",
            author=self.author or "",
            chapters=chapters,
            total_words=total_words,
        )

    def _detect_encoding(self, file_path: str) -> str:
        """
        检测文件编码

        优先使用 chardet 自动检测，检测失败时默认 UTF-8。

        Args:
            file_path: 文件路径

        Returns:
            检测到的编码名称
        """
        with open(file_path, "rb") as f:
            raw_data = f.read(DETECT_READ_SIZE)
        result = chardet.detect(raw_data)
        encoding = result.get("encoding", "utf-8")
        # 统一常见编码别名
        encoding = encoding.lower().replace("gb2312", "gbk").replace("gb18030", "gbk")
        return encoding if encoding else "utf-8"

    def _is_chapter_title(self, line: str) -> bool:
        """
        判断一行文本是否为章节标题

        Args:
            line: 单行文本

        Returns:
            True 表示是标题
        """
        # 标题行通常较短
        if len(line) > 50:
            return False

        for pattern in CHAPTER_PATTERNS:
            if re.match(pattern, line):
                return True
        return False

    def _auto_split(self, text: str) -> list[ChapterData]:
        """
        自动按段落分割文本（无标题时的兜底策略）

        Args:
            text: 全文内容

        Returns:
            按段落组合的章节列表
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chapters: list[ChapterData] = []
        order = 0

        for i in range(0, len(paragraphs), MAX_PARAGRAPHS_PER_CHAPTER):
            order += 1
            chunk = paragraphs[i : i + MAX_PARAGRAPHS_PER_CHAPTER]
            content = "\n\n".join(chunk)
            chapter = ChapterData(
                title=f"第{order}部分",
                level=1,
                sort_order=order,
                content=content,
                word_count=len(content),
            )
            chapters.append(chapter)

        return chapters
