"""
PDF 书籍解析器

使用 PyMuPDF（fitz）解析 PDF 文件。
通过字体大小和样式分析来识别章节标题，构建章节树。

解析策略：
- 逐页提取文本块及其位置信息
- 根据字体大小判断标题层级（字号≥20 为章级标题，≥16 为节级标题）
- 标题后的文本归入该章节，直到遇到下一级标题
"""

import re
import fitz  # PyMuPDF
from app.parsers.base import BaseParser, ParseResult, ChapterData


# 标题识别阈值（字号）
# 根据常见中文排版习惯设定
CHAPTER_FONT_SIZE = 20    # 章级标题最小字号
SECTION_FONT_SIZE = 16    # 节级标题最小字号
BODY_FONT_SIZE = 12       # 正文典型字号

# 内容模式标题识别（用于字号统一时的兜底）
# 匹配 "第X章" "第X节" "第X篇" 等
CHAPTER_PATTERN = re.compile(r'^第[一二三四五六七八九十百千万\d]+[篇章节部]')
# 匹配 "XX." 或 "XX、" 开头的数字标题（如 "1." "2、"）
NUM_HEADING = re.compile(r'^\d{1,3}[\.、]\s*')
# 匹配中文数字标题如 "一、" "二、"
CN_NUM_HEADING = re.compile(r'^[一二三四五六七八九十百千万]+[、\.]\s*')


class PdfParser(BaseParser):
    """PDF 格式解析器"""

    def __init__(self) -> None:
        """初始化 PDF 解析器"""
        self.title: str = ""
        self.author: str = ""

    def parse(self, file_path: str) -> ParseResult:
        """
        解析 PDF 文件

        Args:
            file_path: PDF 文件的绝对路径

        Returns:
            ParseResult: 包含书名、作者和章节树

        Raises:
            ValueError: PDF 为扫描版或无文本层
            FileNotFoundError: 文件不存在
        """
        # 打开 PDF 文件
        doc: fitz.Document = fitz.open(file_path)

        # 提取元数据
        metadata = doc.metadata
        raw_title = metadata.get("title", "") or ""
        raw_author = metadata.get("author", "") or ""

        # 处理 Hex 编码的乱码标题（部分国产 PDF 元数据以 Hex 格式存储）
        self.title = raw_title
        if raw_title and raw_title.startswith("<") and raw_title.endswith(">"):
            try:
                import re
                hex_str = raw_title.strip("<>")
                title_bytes = bytes.fromhex(hex_str)
                decoded = title_bytes.decode("gbk", errors="replace")
                # 清理 "Microsoft Word - " 前缀和 ".doc" 后缀
                decoded = re.sub(r'^Microsoft\s+Word\s*-\s*', '', decoded)
                decoded = re.sub(r'\.docx?$', '', decoded)
                if decoded.strip():
                    self.title = decoded.strip()
            except Exception:
                pass

        self.author = raw_author

        chapters: list[ChapterData] = []
        current_chapter: ChapterData | None = None
        current_section: ChapterData | None = None
        total_words: int = 0

        for page_num in range(len(doc)):
            page: fitz.Page = doc[page_num]
            blocks: list[dict] = page.get_text("dict")["blocks"]

            for block in blocks:
                if block["type"] != 0:
                    # 跳过图片等非文本块
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        text: str = span["text"].strip()
                        if not text:
                            continue

                        font_size: float = span["size"]
                        is_bold: bool = "Bold" in span["font"]

                        # 判断是否为标题
                        if font_size >= CHAPTER_FONT_SIZE or (
                            font_size >= SECTION_FONT_SIZE and is_bold
                        ):
                            if font_size >= CHAPTER_FONT_SIZE:
                                # 章级标题
                                chapter = ChapterData(
                                    title=text,
                                    level=1,
                                    sort_order=len(chapters) + 1,
                                    page_number=page_num + 1,
                                    content="",
                                )
                                chapters.append(chapter)
                                current_chapter = chapter
                                current_section = None
                            else:
                                # 节级标题
                                section = ChapterData(
                                    title=text,
                                    level=2,
                                    sort_order=0,
                                    page_number=page_num + 1,
                                    content="",
                                )
                                if current_chapter:
                                    section.parent_id = len(chapters)
                                    current_chapter.content += f"\n\n"
                                chapters.append(section)
                                current_section = section
                        else:
                            # 正文内容，归入当前章节
                            target = current_chapter or (
                                chapters[-1] if chapters else None
                            )
                            if target:
                                # 添加文本到当前章节
                                sep = "\n" if target.content else ""
                                target.content += f"{sep}{text}"
                                target.word_count += len(text)
                                total_words += len(text)

        # 如果字号检测没找到章节，尝试基于内容模式匹配（统一字号 PDF 的兜底策略）
        use_pattern = not chapters or len(chapters) <= 2
        if use_pattern:
            chapters = self._detect_chapters_by_pattern(doc)
            total_words = sum(ch.word_count for ch in chapters)

        doc.close()

        # 如果仍然没有解析出任何章节，可能是扫描版 PDF
        if not chapters:
            raise ValueError("无法从此 PDF 提取文本，可能是扫描版或不含文本层")

        # 计算总字数
        for ch in chapters:
            total_words += ch.word_count

        return ParseResult(
            title=self.title or "未知书名",
            author=self.author or "未知作者",
            chapters=chapters,
            total_words=total_words,
        )

    def _detect_chapters_by_pattern(self, doc: fitz.Document) -> list[ChapterData]:
        """
        基于内容模式识别章节（兜底策略，用于字号统一的 PDF）

        通过正则匹配标题行（如"第X章""XX.""一、"等）分割章节。
        """
        import re
        chapters: list[ChapterData] = []
        current_title = "前言"
        current_content: list[str] = []
        sort_order = 0
        page_num = 0

        # 全局标题模式
        title_patterns = [
            re.compile(r'^第[一二三四五六七八九十百千万\d]+[篇章节部]'),  # 第一篇/第一章
            re.compile(r'^[一二三四五六七八九十百千万]+[、\.]\s*'),      # 一、/二.
            re.compile(r'^\d{1,3}[、\.]\s*'),                           # 1./2、
        ]

        def is_title(text: str) -> bool:
            if len(text) > 30:
                return False
            for p in title_patterns:
                if p.match(text):
                    return True
            return False

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            lines = page_text.split("\n")

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    current_content.append("")
                    continue

                if is_title(stripped):
                    # 保存上一章
                    if current_content:
                        content = "\n".join(current_content).strip()
                        if content:
                            sort_order += 1
                            chapters.append(ChapterData(
                                title=current_title,
                                level=1,
                                sort_order=sort_order,
                                content=content,
                                word_count=len(content),
                            ))
                    current_title = stripped
                    current_content = []
                else:
                    current_content.append(stripped)

        # 最后一章
        if current_content:
            content = "\n".join(current_content).strip()
            if content:
                sort_order += 1
                chapters.append(ChapterData(
                    title=current_title,
                    level=1,
                    sort_order=sort_order,
                    content=content,
                    word_count=len(content),
                ))

        return chapters
