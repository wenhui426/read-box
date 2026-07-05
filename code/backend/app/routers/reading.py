"""
阅读统计 API 路由

记录每章的阅读时长，计算阅读速度和进度。
"""

import time
from datetime import datetime

from fastapi import APIRouter
from starlette.requests import Request
from app.database import get_db

router = APIRouter(prefix="/api/reading", tags=["reading"])

# 内存中追踪活跃阅读会话 {book_id_chapter_id: start_timestamp}
_active_sessions: dict[str, float] = {}


@router.post("/start/{book_id}/{chapter_id}")
async def start_reading(book_id: int, chapter_id: int) -> dict:
    """开始阅读章节（记录开始时间）"""
    key = f"{book_id}_{chapter_id}"
    _active_sessions[key] = time.time()
    return {"status": "started"}


@router.post("/stop/{book_id}/{chapter_id}")
async def stop_reading(book_id: int, chapter_id: int) -> dict:
    """结束阅读章节（计算时长并存入数据库）"""
    key = f"{book_id}_{chapter_id}"
    start_time = _active_sessions.pop(key, None)
    if start_time is None:
        return {"status": "no_active_session"}

    duration_seconds = int(time.time() - start_time)
    if duration_seconds < 5:
        return {"status": "too_short", "seconds": duration_seconds}

    db = await get_db()

    # 获取章节字数
    rows = await db.execute_fetchall(
        "SELECT word_count FROM chapters WHERE id = ? AND book_id = ?",
        (chapter_id, book_id),
    )
    word_count = rows[0][0] if rows else 0

    # 查找今日是否已有该章节记录
    today = datetime.now().strftime("%Y-%m-%d")
    existing = await db.execute_fetchall(
        """
        SELECT id, total_seconds FROM reading_records
        WHERE book_id = ? AND chapter_id = ? AND date = ?
        """,
        (book_id, chapter_id, today),
    )

    if existing:
        # 累加阅读时长
        new_seconds = existing[0][1] + duration_seconds
        await db.execute(
            "UPDATE reading_records SET total_seconds = ? WHERE id = ?",
            (new_seconds, existing[0][0]),
        )
    else:
        # 新建记录
        await db.execute(
            """
            INSERT INTO reading_records (book_id, chapter_id, date, total_seconds, word_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (book_id, chapter_id, today, duration_seconds, word_count),
        )

    await db.commit()
    await db.close()

    wpm = int(word_count / (duration_seconds / 60)) if duration_seconds > 0 else 0
    return {
        "status": "recorded",
        "seconds": duration_seconds,
        "words": word_count,
        "wpm": wpm,
    }


@router.get("/stats/{book_id}")
async def get_reading_stats(book_id: int) -> dict:
    """获取指定书籍的阅读统计"""
    db = await get_db()

    # 总阅读时长
    time_rows = await db.execute_fetchall(
        "SELECT SUM(total_seconds) FROM reading_records WHERE book_id = ?",
        (book_id,),
    )
    total_seconds = time_rows[0][0] or 0 if time_rows else 0

    # 已读章节数
    chapter_rows = await db.execute_fetchall(
        "SELECT COUNT(DISTINCT chapter_id) FROM reading_records WHERE book_id = ?",
        (book_id,),
    )
    read_chapters = chapter_rows[0][0] or 0 if chapter_rows else 0

    # 总章节数
    total_rows = await db.execute_fetchall(
        "SELECT COUNT(*) FROM chapters WHERE book_id = ?",
        (book_id,),
    )
    total_chapters = total_rows[0][0] or 0 if total_rows else 0

    # 总字数
    word_rows = await db.execute_fetchall(
        "SELECT SUM(word_count) FROM chapters WHERE book_id = ?",
        (book_id,),
    )
    total_words = word_rows[0][0] or 0 if word_rows else 0

    # 今日阅读时长
    today = datetime.now().strftime("%Y-%m-%d")
    today_rows = await db.execute_fetchall(
        "SELECT SUM(total_seconds) FROM reading_records WHERE book_id = ? AND date = ?",
        (book_id, today),
    )
    today_seconds = today_rows[0][0] or 0 if today_rows else 0

    # 阅读速度（平均 WPM）
    wpm_rows = await db.execute_fetchall(
        """
        SELECT SUM(word_count), SUM(total_seconds) FROM reading_records WHERE book_id = ?
        """,
        (book_id,),
    )
    avg_wpm = 0
    if wpm_rows and wpm_rows[0][1] and wpm_rows[0][1] > 0:
        avg_wpm = int((wpm_rows[0][0] or 0) / (wpm_rows[0][1] / 60))

    await db.close()

    progress_pct = round(read_chapters / total_chapters * 100, 1) if total_chapters > 0 else 0
    remaining_chapters = total_chapters - read_chapters
    remaining_minutes = int(remaining_chapters * (total_seconds / max(read_chapters, 1) / 60))

    return {
        "total_seconds": total_seconds,
        "today_seconds": today_seconds,
        "read_chapters": read_chapters,
        "total_chapters": total_chapters,
        "progress_pct": progress_pct,
        "total_words": total_words,
        "avg_wpm": avg_wpm,
        "remaining_minutes": max(remaining_minutes, 0),
    }


@router.get("/today")
async def get_today_stats() -> dict:
    """获取今日阅读总统计（首页用）"""
    db = await get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    rows = await db.execute_fetchall(
        """
        SELECT SUM(total_seconds), COUNT(DISTINCT book_id), COUNT(DISTINCT chapter_id)
        FROM reading_records WHERE date = ?
        """,
        (today,),
    )

    today_seconds = rows[0][0] or 0 if rows else 0
    today_books = rows[0][1] or 0 if rows else 0
    today_chapters = rows[0][2] or 0 if rows else 0

    await db.close()

    return {
        "today_seconds": today_seconds,
        "today_books": today_books,
        "today_chapters": today_chapters,
    }
