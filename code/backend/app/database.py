"""
数据库初始化与连接管理

使用 aiosqlite 异步访问 SQLite 数据库。
首次启动时自动创建所有表结构。

表清单：
- books：书籍元数据
- chapters：章节结构
- digests：AI 提炼任务
- chapter_digests：章节提炼结果
- key_concepts：关键概念
- golden_quotes：金句摘录
- app_config：应用配置
"""

import aiosqlite

# SQLite 数据库文件路径（相对于 backend/ 目录）
DATABASE_PATH = "readbox.db"


async def init_db() -> None:
    """
    初始化数据库

    创建应用所需的全部表结构，首次运行时插入默认配置。
    所有表使用 IF NOT EXISTS，确保重复运行不会报错。
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 设置行工厂，支持按列名访问（如 row["title"]）
        db.row_factory = aiosqlite.Row

        # 批量执行建表语句
        await db.executescript("""
            -- ========================================
            -- 书籍表：记录导入的书籍元数据
            -- 由解析引擎写入，提炼/问答/陪练 Agent 读取
            -- ========================================
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 书籍唯一标识
                title TEXT NOT NULL,                    -- 书名
                author TEXT DEFAULT '',                 -- 作者
                file_type TEXT NOT NULL,                -- 文件类型（pdf/epub/txt）
                file_path TEXT NOT NULL,                -- 文件原始路径
                storage_path TEXT DEFAULT '',           -- 文件在应用目录中的存储路径
                status TEXT DEFAULT 'importing',        -- 导入状态（importing/parsing/completed/failed）
                total_chapters INTEGER DEFAULT 0,       -- 总章节数
                total_words INTEGER DEFAULT 0,          -- 总字数
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 导入时间
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 最后更新时间
            );

            -- ========================================
            -- 章节表：存储解析后的章节结构和文本
            -- 支持多级目录（通过 parent_id 关联）
            -- ========================================
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 章节唯一标识
                book_id INTEGER NOT NULL,               -- 所属书籍 ID
                parent_id INTEGER DEFAULT NULL,         -- 父章节 ID（支持多级目录，NULL 表示顶层）
                title TEXT NOT NULL,                    -- 章节标题
                level INTEGER DEFAULT 1,                -- 层级深度（1=章, 2=节, 3=小节）
                sort_order INTEGER DEFAULT 0,           -- 排序序号（同级章节的排列顺序）
                page_number INTEGER DEFAULT NULL,       -- 起始页码（PDF 专用，EPUB/TXT 为 NULL）
                content TEXT NOT NULL,                  -- 章节全文
                word_count INTEGER DEFAULT 0,           -- 章节字数
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
            );

            -- 章节表索引：按书籍 ID 快速查询章节树
            CREATE INDEX IF NOT EXISTS idx_chapters_book_id ON chapters(book_id);

            -- ========================================
            -- 提炼任务表：AI 提炼 Agent 的任务记录
            -- 记录全书提炼的进度和状态
            -- ========================================
            CREATE TABLE IF NOT EXISTS digests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 任务唯一标识
                book_id INTEGER NOT NULL,               -- 所属书籍 ID
                status TEXT DEFAULT 'pending',          -- 提炼状态（pending/processing/completed/failed）
                total_chapters INTEGER DEFAULT 0,       -- 总章节数（提炼开始前确定）
                processed_chapters INTEGER DEFAULT 0,   -- 已处理章节数（前端轮询用）
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 最后更新时间
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
            );

            -- ========================================
            -- 章节提炼结果表：每章的提炼产物
            -- 存储 AI 生成的章节摘要
            -- ========================================
            CREATE TABLE IF NOT EXISTS chapter_digests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 结果唯一标识
                digest_id INTEGER NOT NULL,             -- 所属提炼任务 ID
                chapter_id INTEGER NOT NULL,            -- 所属章节 ID
                summary TEXT NOT NULL,                  -- 章节摘要（200-500 字）
                status TEXT DEFAULT 'pending',          -- 处理状态（pending/completed/failed）
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 处理时间
                FOREIGN KEY (digest_id) REFERENCES digests(id) ON DELETE CASCADE,
                FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
            );

            -- ========================================
            -- 关键概念表：每章提取的核心概念
            -- 问答和陪练 Agent 可读取此表获取知识点
            -- ========================================
            -- 测验题目表：陪练 Agent 生成的题目
            -- 可持久化已完成的测验记录
            -- ========================================
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                chapter_id INTEGER,
                question_type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                options TEXT DEFAULT '',
                correct_answer TEXT NOT NULL,
                explanation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
            );

            -- ========================================
            CREATE TABLE IF NOT EXISTS key_concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 概念唯一标识
                chapter_digest_id INTEGER NOT NULL,     -- 所属章节提炼结果 ID
                term TEXT NOT NULL,                     -- 术语名称
                explanation TEXT NOT NULL,              -- 一句话解释
                sort_order INTEGER DEFAULT 0,           -- 排序序号
                FOREIGN KEY (chapter_digest_id) REFERENCES chapter_digests(id) ON DELETE CASCADE
            );

            -- ========================================
            -- 金句表：每章摘录的精彩句子
            -- 附带摘录理由，说明为什么选这句
            -- ========================================
            CREATE TABLE IF NOT EXISTS golden_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 金句唯一标识
                chapter_digest_id INTEGER NOT NULL,     -- 所属章节提炼结果 ID
                quote TEXT NOT NULL,                    -- 金句原文
                reason TEXT NOT NULL,                   -- 摘录理由
                sort_order INTEGER DEFAULT 0,           -- 排序序号
                FOREIGN KEY (chapter_digest_id) REFERENCES chapter_digests(id) ON DELETE CASCADE
            );

            -- ========================================
            -- 对话历史表：问答 Agent 的消息记录
            -- 持久化到磁盘，后端重启后不丢失
            -- ========================================
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_chat_history_book ON chat_history(book_id);

            -- 高亮表：用户标注的文本高亮和批注
            -- 提炼和问答时高亮内容获得更高权重
            -- ========================================
            CREATE TABLE IF NOT EXISTS highlights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                chapter_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                color TEXT DEFAULT 'yellow',
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_highlights_book ON highlights(book_id, chapter_id);

            -- 阅读记录表：每章阅读时长统计
            -- ========================================
            CREATE TABLE IF NOT EXISTS reading_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                chapter_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                total_seconds INTEGER DEFAULT 0,
                word_count INTEGER DEFAULT 0,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_reading_book ON reading_records(book_id, date);

            -- 应用配置表：键值对存储
            -- 用于数据库版本号、用户偏好等
            -- ========================================
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,   -- 配置键名
                value TEXT NOT NULL     -- 配置值
            );

            -- 插入数据库版本号（首次运行时执行，后续忽略）
            INSERT OR IGNORE INTO app_config (key, value) VALUES ('db_version', '1');
        """)
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """
    获取数据库连接

    返回一个配置好行工厂的异步数据库连接实例。

    使用方式：
        db = await get_db()
        rows = await db.execute_fetchall("SELECT * FROM books")
        await db.close()
    """
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db
