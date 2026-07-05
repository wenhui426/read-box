"""
书籍管理 API 路由

提供书籍导入、查询、删除等功能。
导入时自动复制文件到应用目录，启动异步解析流程。
"""

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from app.database import get_db, init_db
from app.parsers import PdfParser, EpubParser, TxtParser, ParseResult
from app.parsers.base import BaseParser

# 书籍文件存储目录（相对于 backend/）
BOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "books"

# 支持的文件格式
SUPPORTED_FORMATS: dict[str, type[BaseParser]] = {
    ".pdf": PdfParser,
    ".epub": EpubParser,
    ".txt": TxtParser,
}

# 创建路由，挂载到 /api 路径
router = APIRouter(prefix="/api/books", tags=["books"])


def _get_parser(file_path: str) -> type[BaseParser]:
    """
    根据文件扩展名获取对应的解析器

    Args:
        file_path: 文件路径

    Returns:
        对应的 Parser 类

    Raises:
        HTTPException: 不支持的文件格式
    """
    ext = Path(file_path).suffix.lower()
    parser_class = SUPPORTED_FORMATS.get(ext)
    if parser_class is None:
        raise HTTPException(
            status_code=400,
            detail=f"暂不支持 {ext} 格式，支持: PDF/EPUB/TXT",
        )
    return parser_class


@router.post("/import")
async def import_book(file: UploadFile = File(...)) -> JSONResponse:
    """
    导入书籍

    接收前端上传的文件，复制到应用存储目录，启动解析流程。
    """
    # 验证文件格式
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"暂不支持 {ext} 格式，当前支持: PDF、EPUB、TXT",
        )

    # 确保存储目录存在
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)

    # 读取上传的文件内容
    content = await file.read()

    # 创建书籍数据库记录
    db = await get_db()
    cursor = await db.execute(
        """
        INSERT INTO books (title, author, file_type, file_path, status)
        VALUES (?, ?, ?, ?, 'importing')
        """,
        (filename, "", ext.replace(".", ""), filename),
    )
    book_id = cursor.lastrowid
    await db.commit()

    # 创建书籍子目录并保存文件
    book_dir = BOOKS_DIR / str(book_id)
    book_dir.mkdir(parents=True, exist_ok=True)
    storage_path = book_dir / filename
    with open(storage_path, "wb") as f:
        f.write(content)

    # 更新存储路径
    await db.execute(
        "UPDATE books SET storage_path = ?, status = 'parsing' WHERE id = ?",
        (str(storage_path), book_id),
    )
    await db.commit()

    # 执行解析
    try:
        parser_class = _get_parser(filename)
        parser = parser_class()
        result: ParseResult = parser.parse(str(storage_path))

        # 更新书籍元数据
        await db.execute(
            """
            UPDATE books
            SET title = ?, author = ?, status = 'completed',
                total_chapters = ?, total_words = ?
            WHERE id = ?
            """,
            (
                result.title,
                result.author,
                len(result.chapters),
                result.total_words,
                book_id,
            ),
        )

        # 批量插入章节
        for idx, chapter in enumerate(result.chapters):
            await db.execute(
                """
                INSERT INTO chapters
                    (book_id, parent_id, title, level, sort_order,
                     page_number, content, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    chapter.parent_id,
                    chapter.title,
                    chapter.level,
                    chapter.sort_order,
                    chapter.page_number,
                    chapter.content,
                    chapter.word_count,
                ),
            )

        await db.commit()
    except Exception as e:
        # 解析失败，更新状态
        await db.execute(
            "UPDATE books SET status = 'failed' WHERE id = ?",
            (book_id,),
        )
        await db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()

    return JSONResponse(
        content={
            "book_id": book_id,
            "title": result.title if 'result' in dir() else filename,
            "status": "completed",
        }
    )


@router.get("")
async def list_books() -> JSONResponse:
    """
    获取已导入的书籍列表

    返回所有书籍的简要信息，按导入时间倒序排列。
    """
    db = await get_db()
    rows = await db.execute_fetchall(
        """
        SELECT id, title, author, file_type, status,
               total_chapters, total_words, created_at
        FROM books
        ORDER BY created_at DESC
        """
    )
    await db.close()

    books_list = []
    for row in rows:
        books_list.append(
            {
                "id": row[0],
                "title": row[1],
                "author": row[2],
                "file_type": row[3],
                "status": row[4],
                "total_chapters": row[5],
                "total_words": row[6],
                "created_at": row[7],
            }
        )

    return JSONResponse(content=books_list)


@router.get("/{book_id}")
async def get_book(book_id: int) -> JSONResponse:
    """
    获取单本书籍详情

    Args:
        book_id: 书籍 ID
    """
    db = await get_db()
    rows = await db.execute_fetchall(
        """
        SELECT id, title, author, file_type, file_path, storage_path,
               status, total_chapters, total_words, created_at
        FROM books WHERE id = ?
        """,
        (book_id,),
    )
    await db.close()

    if not rows:
        raise HTTPException(status_code=404, detail="书籍不存在")

    row = rows[0]
    return JSONResponse(
        content={
            "id": row[0],
            "title": row[1],
            "author": row[2],
            "file_type": row[3],
            "file_path": row[4],
            "storage_path": row[5],
            "status": row[6],
            "total_chapters": row[7],
            "total_words": row[8],
            "created_at": row[9],
        }
    )


@router.get("/{book_id}/chapters")
async def get_chapters(book_id: int) -> JSONResponse:
    """
    获取指定书籍的章节树

    返回按层级组织的章节列表，前端据此渲染左侧目录树。

    Args:
        book_id: 书籍 ID
    """
    db = await get_db()
    rows = await db.execute_fetchall(
        """
        SELECT id, parent_id, title, level, sort_order,
               page_number, word_count
        FROM chapters
        WHERE book_id = ?
        ORDER BY sort_order ASC
        """,
        (book_id,),
    )
    await db.close()

    chapters_list = []
    for row in rows:
        chapters_list.append(
            {
                "id": row[0],
                "parent_id": row[1],
                "title": row[2],
                "level": row[3],
                "sort_order": row[4],
                "page_number": row[5],
                "word_count": row[6],
            }
        )

    return JSONResponse(content=chapters_list)


@router.get("/{book_id}/chapters/{chapter_id}")
async def get_chapter_content(book_id: int, chapter_id: int) -> JSONResponse:
    """
    获取指定章节的完整文本内容

    Args:
        book_id: 书籍 ID
        chapter_id: 章节 ID
    """
    db = await get_db()
    rows = await db.execute_fetchall(
        """
        SELECT id, title, content, word_count
        FROM chapters
        WHERE id = ? AND book_id = ?
        """,
        (chapter_id, book_id),
    )
    await db.close()

    if not rows:
        raise HTTPException(status_code=404, detail="章节不存在")

    row = rows[0]
    return JSONResponse(
        content={
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "word_count": row[3],
        }
    )


@router.delete("/{book_id}")
async def delete_book(book_id: int) -> JSONResponse:
    """
    删除书籍及其所有章节数据

    Args:
        book_id: 书籍 ID
    """
    db = await get_db()

    # 查询书籍信息（获取存储路径）
    rows = await db.execute_fetchall(
        "SELECT storage_path FROM books WHERE id = ?",
        (book_id,),
    )
    if not rows:
        await db.close()
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 删除数据库记录（chapters 通过外键级联删除）
    await db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    await db.commit()
    await db.close()

    # 删除存储的文件目录
    book_dir = BOOKS_DIR / str(book_id)
    if book_dir.exists():
        shutil.rmtree(book_dir)

    return JSONResponse(content={"status": "deleted"})
