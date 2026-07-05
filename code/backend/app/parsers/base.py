"""
书籍解析器抽象基类

定义统一的解析器接口，所有格式（PDF/EPUB/TXT）的解析器必须继承此类。
遵循宪法"LLM Provider 抽象层"的设计理念 — 接口统一，实现解耦。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChapterData:
    """
    章节数据

    记录单个章节的标题、层级、内容和元数据。
    支持多级目录结构（通过 parent_id 关联）。
    """
    title: str                       # 章节标题
    level: int                       # 层级深度（1=章, 2=节, 3=小节）
    sort_order: int                  # 排序序号（同级章节的排列顺序）
    content: str                     # 章节全文
    parent_id: Optional[int] = None  # 父章节 ID（None 表示顶层章节）
    page_number: Optional[int] = None  # 起始页码（PDF 专用）
    word_count: int = 0              # 章节字数（解析后自动计算）


@dataclass
class ParseResult:
    """
    解析结果

    包含书籍元数据和完整的章节树。
    """
    title: str                        # 书名
    author: str                       # 作者
    chapters: list[ChapterData] = field(default_factory=list)  # 章节列表
    total_words: int = 0              # 总字数（所有章节累加）


class BaseParser(ABC):
    """
    解析器抽象基类

    所有格式解析器必须实现 parse 方法。
    解析完成后返回 ParseResult，由调用方负责写入数据库。
    """

    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """
        解析书籍文件

        Args:
            file_path: 书籍文件的绝对路径

        Returns:
            ParseResult: 包含书名、作者和章节树

        Raises:
            ValueError: 文件格式不支持或文件损坏
            FileNotFoundError: 文件不存在
        """
        pass
