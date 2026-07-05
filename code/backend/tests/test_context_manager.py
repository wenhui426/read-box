"""
共享上下文管理器单元测试

测试 ContextManager 的核心功能：
设置书籍、添加消息、清空上下文、切换书籍自动清空。
"""
from app.context.manager import ContextManager


class TestContextManager:
    """上下文管理器测试"""

    def setup_method(self) -> None:
        """每个测试前创建新的上下文管理器实例"""
        self.ctx = ContextManager()

    def test_initial_state(self) -> None:
        """测试初始状态应为空"""
        assert self.ctx.current_book_id is None
        assert self.ctx.messages == []
        assert self.ctx.quiz_progress == {}

    def test_set_book(self) -> None:
        """测试设置当前书籍"""
        self.ctx.set_book(1, "测试书籍")
        assert self.ctx.current_book_id == 1
        assert self.ctx.current_book_title == "测试书籍"

    def test_add_message(self) -> None:
        """测试添加对话消息"""
        self.ctx.set_book(1)
        self.ctx.add_message("user", "你好")
        self.ctx.add_message("assistant", "你好！有什么可以帮助你的？")
        assert len(self.ctx.messages) == 2
        assert self.ctx.messages[0]["role"] == "user"

    def test_get_history(self) -> None:
        """测试获取对话历史"""
        self.ctx.set_book(1)
        for i in range(25):
            self.ctx.add_message("user", f"消息{i}")
        history = self.ctx.get_history()
        assert len(history) <= 20, "历史记录应限制在 20 条"

    def test_clear(self) -> None:
        """测试清空上下文"""
        self.ctx.set_book(1, "测试")
        self.ctx.add_message("user", "你好")
        self.ctx.clear()
        assert self.ctx.current_book_id is None
        assert self.ctx.messages == []

    def test_switch_book_clears_context(self) -> None:
        """测试切换书籍应自动清空上下文"""
        self.ctx.set_book(1, "第一本书")
        self.ctx.add_message("user", "关于第一本书的问题")
        self.ctx.set_book(2, "第二本书")
        assert self.ctx.current_book_id == 2
        assert self.ctx.messages == [], "切换书籍后历史应清空"

    def test_quiz_progress(self) -> None:
        """测试陪练进度管理"""
        self.ctx.set_quiz_progress({"current_question": 1, "score": 80})
        assert self.ctx.get_quiz_progress()["current_question"] == 1
        assert self.ctx.get_quiz_progress()["score"] == 80
