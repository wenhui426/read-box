"""
标注/高亮 API 路由

提供文本高亮和批注的增删查改接口。
高亮数据会影响到 AI 提炼时的权重分配。
"""

from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from app.database import get_db

router = APIRouter(prefix="/api/highlights", tags=["highlights"])


@router.get("/{book_id}")
async def get_highlights(book_id: int) -> dict:
    """获取指定书籍的所有高亮"""
    db = await get_db()
    rows = await db.execute_fetchall(
        """
        SELECT id, chapter_id, text, color, note, created_at
        FROM highlights
        WHERE book_id = ?
        ORDER BY created_at DESC
        """,
        (book_id,),
    )
    await db.close()
    return {
        "highlights": [
            {
                "id": r[0],
                "chapter_id": r[1],
                "text": r[2],
                "color": r[3],
                "note": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    }


@router.get("/{book_id}/chapters/{chapter_id}")
async def get_chapter_highlights(book_id: int, chapter_id: int) -> dict:
    """获取指定章节的高亮"""
    db = await get_db()
    rows = await db.execute_fetchall(
        """
        SELECT id, text, color, note, created_at
        FROM highlights
        WHERE book_id = ? AND chapter_id = ?
        ORDER BY created_at ASC
        """,
        (book_id, chapter_id),
    )
    await db.close()
    return {
        "highlights": [
            {
                "id": r[0],
                "text": r[1],
                "color": r[2],
                "note": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]
    }


@router.post("/{book_id}/chapters/{chapter_id}")
async def create_highlight(book_id: int, chapter_id: int, request: Request) -> dict:
    """创建高亮"""
    body = await request.json()
    text = body.get("text", "").strip()
    color = body.get("color", "yellow")
    note = body.get("note", "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="高亮内容不能为空")

    db = await get_db()
    cursor = await db.execute(
        """
        INSERT INTO highlights (book_id, chapter_id, text, color, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (book_id, chapter_id, text, color, note),
    )
    highlight_id = cursor.lastrowid
    await db.commit()
    await db.close()

    return {"id": highlight_id, "status": "created"}


@router.put("/{highlight_id}")
async def update_highlight(highlight_id: int, request: Request) -> dict:
    """更新高亮（修改颜色或批注）"""
    body = await request.json()
    color = body.get("color")
    note = body.get("note")

    db = await get_db()
    if color:
        await db.execute(
            "UPDATE highlights SET color = ? WHERE id = ?", (color, highlight_id)
        )
    if note is not None:
        await db.execute(
            "UPDATE highlights SET note = ? WHERE id = ?", (note, highlight_id)
        )
    await db.commit()
    await db.close()
    return {"status": "updated"}


@router.delete("/{highlight_id}")
async def delete_highlight(highlight_id: int) -> dict:
    """删除高亮"""
    db = await get_db()
    await db.execute("DELETE FROM highlights WHERE id = ?", (highlight_id,))
    await db.commit()
    await db.close()
    return {"status": "deleted"}
