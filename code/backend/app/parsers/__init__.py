# 书籍解析引擎模块
# 支持 PDF / EPUB / TXT 三种格式
# 每个格式一个独立解析器，统一继承 BaseParser 基类

from .base import BaseParser, ParseResult, ChapterData
from .pdf_parser import PdfParser
from .epub_parser import EpubParser
from .txt_parser import TxtParser

__all__ = [
    "BaseParser",
    "ParseResult",
    "ChapterData",
    "PdfParser",
    "EpubParser",
    "TxtParser",
]
