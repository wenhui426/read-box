"""
PDF 解析器单元测试

测试 PDF 解析的核心功能：章节识别、文本提取、异常处理。
"""

import os
import tempfile
import pymupdf  # PyMuPDF 的 FileNotFoundError 异常
import pytest
from app.parsers.pdf_parser import PdfParser


def create_test_pdf(file_path: str, pages: int = 3) -> None:
    """
    创建测试用 PDF 文件

    使用 PyMuPDF 生成简单的测试 PDF，包含标题和正文。

    Args:
        file_path: 输出 PDF 路径
        pages: 页数
    """
    import fitz

    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        if i == 0:
            # 第一章标题（大字号）
            page.insert_text(
                (72, 100), "第一章 测试章节",
                fontsize=24, fontname="helv",
            )
            # 正文
            page.insert_text(
                (72, 150),
                "这是第一章的正文内容，用于验证解析器是否能正确提取文本。",
                fontsize=12, fontname="helv",
            )
            # 第一节标题（字号稍小但加粗）
            page.insert_text(
                (72, 220), "第一节 测试小节",
                fontsize=16, fontname="helv",
            )
            page.insert_text(
                (72, 260), "这是第一节的内容。",
                fontsize=12, fontname="helv",
            )
        elif i == 1:
            page.insert_text(
                (72, 100), "第二章 进阶测试",
                fontsize=24, fontname="helv",
            )
            page.insert_text(
                (72, 150), "第二章的内容。",
                fontsize=12, fontname="helv",
            )
    # 设置元数据
    doc.set_metadata({
        "title": "测试PDF",
        "author": "测试作者",
    })
    doc.save(file_path)
    doc.close()


class TestPdfParser:
    """PDF 解析器测试"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """每个测试前创建临时 PDF 文件"""
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_path = os.path.join(self.temp_dir, "test.pdf")
        create_test_pdf(self.pdf_path)
        self.parser = PdfParser()

    def test_parse_extracts_title(self) -> None:
        """测试能否正确提取书名"""
        result = self.parser.parse(self.pdf_path)
        assert result.title == "测试PDF"

    def test_parse_extracts_author(self) -> None:
        """测试能否正确提取作者"""
        result = self.parser.parse(self.pdf_path)
        assert result.author == "测试作者"

    def test_parse_detects_chapters(self) -> None:
        """测试能否正确识别章节"""
        result = self.parser.parse(self.pdf_path)
        assert len(result.chapters) >= 2, "应至少识别出 2 个章节"

    def test_parse_chapter_has_content(self) -> None:
        """测试章节是否包含正文内容"""
        result = self.parser.parse(self.pdf_path)
        for chapter in result.chapters:
            assert len(chapter.content) > 0, f"章节 '{chapter.title}' 应有正文内容"

    def test_parse_raises_on_scanned_pdf(self) -> None:
        """
        测试扫描版 PDF（无文本层）应抛出异常

        创建一个仅包含空白页的 PDF，解析器无法提取文本时应抛出 ValueError。
        """
        import fitz
        doc = fitz.open()
        # 添加一页空白页（无任何文本）
        doc.new_page()
        blank_path = os.path.join(self.temp_dir, "blank.pdf")
        doc.save(blank_path)
        doc.close()

        with pytest.raises(ValueError, match="无法从此"):
            self.parser.parse(blank_path)

    def test_parse_raises_on_nonexistent_file(self) -> None:
        """测试文件不存在时应抛出异常"""
        with pytest.raises((FileNotFoundError, pymupdf.FileNotFoundError)):
            self.parser.parse(os.path.join(self.temp_dir, "no_such_file.pdf"))

    def teardown_method(self) -> None:
        """测试后清理临时文件"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
