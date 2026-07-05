"""
EPUB 解析器单元测试

测试 EPUB 解析的核心功能：目录提取、正文解析、异常处理。
"""

import os
import tempfile
import pytest
from app.parsers.epub_parser import EpubParser


def create_test_epub(file_path: str) -> None:
    """
    创建测试用 EPUB 文件

    使用 ebooklib 的 EpubBook API 生成包含两个章节的 EPUB。
    包含 Nav 文件以确保 spine 的 toc 属性有正确引用。

    Args:
        file_path: 输出 EPUB 路径
    """
    from ebooklib import epub

    book = epub.EpubBook()

    # 设置元数据
    book.set_identifier("test-book-001")
    book.set_title("测试EPUB")
    book.set_language("zh-CN")
    book.add_author("测试作者")

    # 第一章
    chapter1 = epub.EpubHtml(
        title="第一章",
        file_name="chap_01.xhtml",
        lang="zh-CN",
    )
    chapter1.content = (
        "<html><body>"
        "<h1>第一章 入门指南</h1>"
        "<p>这是第一章的正文内容。</p>"
        "<p>用于测试 EPUB 解析器是否能正确提取文本。</p>"
        "</body></html>"
    )

    # 第二章
    chapter2 = epub.EpubHtml(
        title="第二章",
        file_name="chap_02.xhtml",
        lang="zh-CN",
    )
    chapter2.content = (
        "<html><body>"
        "<h2>第二章 进阶内容</h2>"
        "<p>这是第二章的内容。</p>"
        "</body></html>"
    )

    # 添加章节到书籍
    book.add_item(chapter1)
    book.add_item(chapter2)

    # 自动创建导航文件（Nav）
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 定义目录
    book.toc = [
        epub.Link("chap_01.xhtml", "第一章", "chap01"),
        epub.Link("chap_02.xhtml", "第二章", "chap02"),
    ]

    # 设置 spine（必须包含 nav）
    book.spine = ["nav", chapter1, chapter2]

    # 添加默认样式
    style = epub.EpubItem(
        uid="style",
        file_name="style/default.css",
        media_type="text/css",
        content=b"body { font-family: serif; }",
    )
    book.add_item(style)

    # 保存
    epub.write_epub(file_path, book)


class TestEpubParser:
    """EPUB 解析器测试"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """每个测试前创建临时 EPUB 文件"""
        self.temp_dir = tempfile.mkdtemp()
        self.epub_path = os.path.join(self.temp_dir, "test.epub")
        create_test_epub(self.epub_path)
        self.parser = EpubParser()

    def test_parse_extracts_title(self) -> None:
        """测试能否正确提取书名"""
        result = self.parser.parse(self.epub_path)
        assert result.title == "测试EPUB"

    def test_parse_extracts_author(self) -> None:
        """测试能否正确提取作者"""
        result = self.parser.parse(self.epub_path)
        assert result.author == "测试作者"

    def test_parse_detects_chapters(self) -> None:
        """测试能否正确识别章节数量"""
        result = self.parser.parse(self.epub_path)
        assert len(result.chapters) == 2, "应识别出 2 个章节"

    def test_parse_chapter_has_content(self) -> None:
        """测试章节内容是否包含正文"""
        result = self.parser.parse(self.epub_path)
        for chapter in result.chapters:
            assert len(chapter.content) > 0

    def test_parse_chapter_has_title(self) -> None:
        """测试章节是否有标题"""
        result = self.parser.parse(self.epub_path)
        titles = [ch.title for ch in result.chapters]
        assert any("第一章" in t for t in titles), "应包含第一章"

    def test_parse_raises_on_nonexistent_file(self) -> None:
        """测试文件不存在时应抛出异常"""
        with pytest.raises(Exception):
            self.parser.parse("/nonexistent/test.epub")

    def teardown_method(self) -> None:
        """测试后清理临时文件"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
