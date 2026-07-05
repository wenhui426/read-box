"""
EPUB 书籍解析器

使用 ebooklib 解析 EPUB 文件。
优先读取 NCX 目录文件获取官方章节结构，无 NCX 时按 HTML 标签构建。

解析策略：
- 通过 ebooklib 读取书籍元数据（书名、作者）
- 优先解析 NCX 目录（toc.ncx）获取章节树
- 无 NCX 时遍历 HTML 文档，按 h1/h2/h3 标签识别标题
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from app.parsers.base import BaseParser, ParseResult, ChapterData


class EpubParser(BaseParser):
    """EPUB 格式解析器"""

    def __init__(self) -> None:
        """初始化 EPUB 解析器"""
        self.title: str = ""
        self.author: str = ""

    def parse(self, file_path: str) -> ParseResult:
        """
        解析 EPUB 文件

        Args:
            file_path: EPUB 文件的绝对路径

        Returns:
            ParseResult: 包含书名、作者和章节树
        """
        # 打开 EPUB 文件
        book: epub.EpubBook = epub.read_epub(file_path)

        # 提取元数据
        self.title = self._get_metadata(book, "title")
        self.author = self._get_metadata(book, "creator")

        chapters: list[ChapterData] = []
        sort_order: int = 0

        # 遍历所有 HTML 文档，提取章节结构和正文
        # 不依赖 NCX 目录（ebooklib 的 NCX API 在不同版本中表现不一致）
        for item in book.get_items():
            # 跳过导航文件（Nav），只解析真正的章节文档
            if item.get_type() == ebooklib.ITEM_DOCUMENT and not isinstance(item, epub.EpubNav):
                sort_order += 1
                content_html = item.get_content().decode("utf-8", errors="replace")
                text = self._html_to_text(content_html)

                # 从 HTML 中提取标题，无标题时使用默认名称
                title = self._extract_title(content_html) or f"第{sort_order}章"
                chapter = ChapterData(
                    title=title,
                    level=1,
                    sort_order=sort_order,
                    content=text,
                    word_count=len(text),
                )
                chapters.append(chapter)

        total_words = sum(ch.word_count for ch in chapters)

        return ParseResult(
            title=self.title or "未知书名",
            author=self.author or "未知作者",
            chapters=chapters,
            total_words=total_words,
        )

    def _get_metadata(self, book: epub.EpubBook, key: str) -> str:
        """
        从 EPUB 元数据中提取指定字段

        Args:
            book: EPUB 书籍对象
            key: 元数据键名（title / creator）

        Returns:
            元数据值，未找到返回空字符串
        """
        try:
            dc_key = f"DC{{{key}}}"
            values = book.get_metadata("http://purl.org/dc/elements/1.1/", key)
            if values:
                return str(values[0][0])
        except Exception:
            pass
        return ""

    def _html_to_text(self, html_content: str) -> str:
        """
        将 HTML 内容转换为纯文本

        Args:
            html_content: HTML 字符串

        Returns:
            提取后的纯文本
        """
        soup = BeautifulSoup(html_content, "html.parser")
        # 移除脚本和样式
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n").strip()

    def _extract_title(self, html_content: str) -> str:
        """
        从 HTML 中提取标题

        Args:
            html_content: HTML 字符串

        Returns:
            标题文本，未找到返回空字符串
        """
        soup = BeautifulSoup(html_content, "html.parser")
        # 依次查找 h1-h3 标签作为标题
        for tag in ["h1", "h2", "h3"]:
            elem = soup.find(tag)
            if elem and elem.get_text(strip=True):
                return elem.get_text(strip=True)
        return ""
