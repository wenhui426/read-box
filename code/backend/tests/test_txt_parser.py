"""
TXT 解析器单元测试

测试 TXT 解析的核心功能：编码检测、章节分割、自动分段。
"""

import os
import tempfile
import pytest
from app.parsers.txt_parser import TxtParser


class TestTxtParser:
    """TXT 解析器测试"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """每个测试前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.parser = TxtParser()

    def _create_txt(self, content: str, encoding: str = "utf-8") -> str:
        """
        创建临时 TXT 文件

        Args:
            content: 文件内容
            encoding: 文件编码

        Returns:
            文件路径
        """
        path = os.path.join(self.temp_dir, "test.txt")
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return path

    def test_parse_utf8_with_chapter_markers(self) -> None:
        """测试 UTF-8 编码且带章节标记的 TXT"""
        content = """第一章 初次见面
这是第一章的内容。
这里是更多的正文。

第二章 深入探索
这是第二章的内容。
还有更多内容在这里。

第三章 总结
最后一章的内容。
"""
        path = self._create_txt(content)
        result = self.parser.parse(path)
        assert len(result.chapters) >= 3, "应识别出至少 3 个章节"

    def test_parse_markdown_headings(self) -> None:
        """测试 Markdown 标题格式"""
        content = """## 第一节
第一节的正文内容。

## 第二节
第二节的正文内容。

## 第三节
第三节的正文内容。
"""
        path = self._create_txt(content)
        result = self.parser.parse(path)
        assert len(result.chapters) >= 3, "应识别 Markdown 标题"

    def test_parse_no_headings_auto_split(self) -> None:
        """测试无标题时自动分段"""
        # 生成大量正文（无标题），触发自动分段
        paragraphs = []
        for i in range(20):
            paragraphs.append(f"这是第{i+1}段的正文内容。每段需要足够长才能触发自动分段机制。" * 5)
        content = "\n\n".join(paragraphs)

        path = self._create_txt(content)
        result = self.parser.parse(path)
        assert len(result.chapters) >= 2, "无标题时应自动分割为多个章节"

    def test_parse_gbk_encoding(self) -> None:
        """测试 GBK 编码的 TXT 文件"""
        content = "第一章 测试\n这是中文内容。\n第二章 继续\n更多内容。\n"
        path = self._create_txt(content, encoding="gbk")
        result = self.parser.parse(path)
        assert len(result.chapters) >= 2, "GBK 文件应正常解析"

    def test_parse_preserves_content(self) -> None:
        """测试解析后内容完整"""
        content = """第一章 测试
这是正文内容。
第二行内容。"""
        path = self._create_txt(content)
        result = self.parser.parse(path)
        assert len(result.chapters) > 0
        assert "正文" in result.chapters[0].content, "章节内容应完整保留"

    def test_parse_empty_file(self) -> None:
        """测试空文件"""
        path = self._create_txt("")
        result = self.parser.parse(path)
        assert len(result.chapters) == 0, "空文件应无章节"

    def test_title_from_filename(self) -> None:
        """测试从文件名提取书名"""
        path = os.path.join(self.temp_dir, "三体.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("第一章 开始\n正文内容。\n")
        result = self.parser.parse(path)
        assert result.title == "三体", "应从文件名提取书名"

    def teardown_method(self) -> None:
        """测试后清理临时文件"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
