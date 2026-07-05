"""
首页数据 API 路由

提供首页所需的聚合数据：
- 最近阅读书籍
- 阅读统计摘要
- 待办任务提醒
"""

from fastapi import APIRouter
from app.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard() -> dict:
    """获取首页聚合数据"""
    db = await get_db()

    # 1. 最近阅读书籍（按导入时间倒序取 5 本）
    recent_books = await db.execute_fetchall(
        """
        SELECT id, title, author, file_type, total_chapters, total_words,
               created_at
        FROM books
        ORDER BY created_at DESC
        LIMIT 5
        """
    )
    books_list = [
        {
            "id": r[0],
            "title": r[1],
            "author": r[2],
            "file_type": r[3],
            "total_chapters": r[4],
            "total_words": r[5],
            "created_at": r[6],
        }
        for r in recent_books
    ]

    # 2. 书籍总数
    count_row = await db.execute_fetchall("SELECT COUNT(*) FROM books")
    total_books = count_row[0][0] if count_row else 0

    # 3. 提炼任务统计（待办提醒）
    pending_digests = await db.execute_fetchall(
        "SELECT COUNT(*) FROM digests WHERE status IN ('processing', 'pending')"
    )
    pending_digest_count = pending_digests[0][0] if pending_digests else 0

    await db.close()

    return {
        "recent_books": books_list,
        "total_books": total_books,
        "pending_digest_count": pending_digest_count,
    }
