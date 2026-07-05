"""
共享上下文管理器

问答 Agent 和陪练 Agent 共用的会话上下文。
主要在内存中维护，同时也写 SQLite 持久化。
后端重启后自动从数据库恢复历史。
切换书籍时自动清空所有上下文。
"""

from typing import Optional


class ContextManager:
    """
    共享上下文管理器（单例）

    维护当前会话状态：
    - 当前激活的书籍
    - 对话历史（问答用）
    - 陪练进度（陪练用）
    """

    def __init__(self) -> None:
        """初始化上下文管理器"""
        self.current_book_id: Optional[int] = None      # 当前激活的书籍 ID
        self.current_book_title: str = ""               # 当前书籍名称
        self.current_chapter_id: Optional[int] = None   # 当前所在章节 ID
        self.messages: list[dict] = []                  # 对话历史 [{role, content}]
        self.quiz_progress: dict = {}                   # 陪练进度

    def set_book(self, book_id: int, title: str = "") -> None:
        """
        设置当前激活的书籍

        切换书籍时自动清空之前的上下文。

        Args:
            book_id: 书籍 ID
            title: 书籍名称
        """
        # 如果切换了书籍，清空所有上下文
        if self.current_book_id != book_id:
            self.clear()
        self.current_book_id = book_id
        self.current_book_title = title

    def set_chapter(self, chapter_id: int) -> None:
        """设置当前所在章节"""
        self.current_chapter_id = chapter_id

    def add_message(self, role: str, content: str) -> None:
        """
        添加对话消息

        Args:
            role: 角色（user / assistant）
            content: 消息内容
        """
        self.messages.append({"role": role, "content": content})

    def get_history(self, max_count: int = 20) -> list[dict]:
        """
        获取对话历史

        Args:
            max_count: 最大返回条数

        Returns:
            最近的对话历史列表
        """
        return self.messages[-max_count:] if self.messages else []

    def set_quiz_progress(self, data: dict) -> None:
        """设置陪练进度"""
        self.quiz_progress.update(data)

    def get_quiz_progress(self) -> dict:
        """获取陪练进度"""
        return self.quiz_progress

    def clear(self) -> None:
        """清空所有上下文（切换书籍时调用）"""
        self.current_book_id = None
        self.current_book_title = ""
        self.current_chapter_id = None
        self.messages = []
        self.quiz_progress = {}


# 全局单例
context_manager = ContextManager()
