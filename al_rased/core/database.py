import aiosqlite
import logging
from pathlib import Path

# Use absolute path relative to this module to avoid creating multiple DB files
_MODULE_DIR = Path(__file__).parent.parent  # al_rased/
DB_PATH = _MODULE_DIR / "data" / "bot.db"

# Ensure data directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Table for storing group configs
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_type TEXT PRIMARY KEY, -- 'review' or 'training'
                chat_id INTEGER
            )
        """)
        
        # Table for storing topic mappings: category -> positive/negative topic IDs
        await db.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                category TEXT NOT NULL,
                topic_type TEXT NOT NULL, -- 'positive' or 'negative'
                message_thread_id INTEGER,
                review_group_id INTEGER,
                PRIMARY KEY (category, topic_type, review_group_id)
            )
        """)
        
        # Table for category settings (enabled/disabled per category)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS category_settings (
                category TEXT PRIMARY KEY,
                is_enabled INTEGER DEFAULT 1
            )
        """)
        
        # Table for banned names per category
        await db.execute("""
            CREATE TABLE IF NOT EXISTS banned_names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, name)
            )
        """)
        
        # Table for per-group category settings
        await db.execute("""
            CREATE TABLE IF NOT EXISTS group_category_settings (
                group_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                is_enabled INTEGER DEFAULT 1,
                PRIMARY KEY (group_id, category)
            )
        """)
        
        # Table for custom category names
        await db.execute("""
            CREATE TABLE IF NOT EXISTS category_names (
                category TEXT PRIMARY KEY,
                custom_name TEXT NOT NULL
            )
        """)
        
        # Table for bot settings (key-value store)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Table for managed groups
        await db.execute("""
            CREATE TABLE IF NOT EXISTS managed_groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT,
                member_count INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by INTEGER
            )
        """)
        
        # Table for notification settings per group/category
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notification_settings (
                group_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                delete_after_seconds INTEGER DEFAULT 0,
                PRIMARY KEY (group_id, category)
            )
        """)
        
        
        # Insert default mode (dry_run) if not exists
        await db.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('mode', 'dry_run')")
        
        await db.commit()
    
    # Initialize prohibited keywords table
    await init_prohibited_keywords_table()
    logging.info("Database initialized.")

async def set_group(group_type: str, chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO groups (group_type, chat_id) VALUES (?, ?)",
            (group_type, chat_id)
        )
        await db.commit()

async def get_group(group_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT chat_id FROM groups WHERE group_type = ?", (group_type,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def save_topic(category: str, topic_type: str, message_thread_id: int, review_group_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO topics (category, topic_type, message_thread_id, review_group_id) VALUES (?, ?, ?, ?)",
            (category, topic_type, message_thread_id, review_group_id)
        )
        await db.commit()

async def get_topic(category: str, topic_type: str, review_group_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT message_thread_id FROM topics WHERE category = ? AND topic_type = ? AND review_group_id = ?",
            (category, topic_type, review_group_id)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

# ==================== Category Settings ====================

async def get_category_status(category: str) -> bool:
    """Get category enabled status. Returns True if enabled (default)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT is_enabled FROM category_settings WHERE category = ?",
            (category,)
        )
        row = await cursor.fetchone()
        return row[0] == 1 if row else True  # Default enabled

async def set_category_status(category: str, enabled: bool):
    """Set category enabled/disabled status."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO category_settings (category, is_enabled) VALUES (?, ?)",
            (category, 1 if enabled else 0)
        )
        await db.commit()

async def get_all_category_statuses() -> dict:
    """Get all category statuses."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT category, is_enabled FROM category_settings")
        rows = await cursor.fetchall()
        return {row[0]: row[1] == 1 for row in rows}

# ==================== Banned Names ====================

async def get_banned_names(category: str) -> list:
    """Get all banned names for a category."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT name FROM banned_names WHERE category = ? ORDER BY added_at DESC",
            (category,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def add_banned_name(category: str, name: str) -> bool:
    """Add a banned name to a category. Returns True if added, False if exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO banned_names (category, name) VALUES (?, ?)",
                (category, name)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False  # Already exists

async def remove_banned_name(category: str, name: str) -> bool:
    """Remove a banned name from a category. Returns True if removed."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM banned_names WHERE category = ? AND name = ?",
            (category, name)
        )
        await db.commit()
        return cursor.rowcount > 0

async def get_banned_names_count(category: str) -> int:
    """Get count of banned names for a category."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM banned_names WHERE category = ?",
            (category,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

async def get_all_banned_names_mapping() -> dict:
    """Get all banned names grouped by category."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT category, name FROM banned_names")
        rows = await cursor.fetchall()
        mapping = {}
        for category, name in rows:
            if category not in mapping:
                mapping[category] = []
            mapping[category].append(name)
        return mapping

# ==================== Group Category Settings ====================

async def get_group_category_status(group_id: int, category: str) -> bool:
    """Get category enabled status for a specific group. Returns True if enabled (default)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT is_enabled FROM group_category_settings WHERE group_id = ? AND category = ?",
            (group_id, category)
        )
        row = await cursor.fetchone()
        # If no setting, check global status
        if row is None:
            return await get_category_status(category)
        return row[0] == 1

async def set_group_category_status(group_id: int, category: str, enabled: bool):
    """Set category enabled/disabled status for a specific group."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO group_category_settings (group_id, category, is_enabled) VALUES (?, ?, ?)",
            (group_id, category, 1 if enabled else 0)
        )
        await db.commit()

async def get_group_all_category_statuses(group_id: int) -> dict:
    """Get all category statuses for a specific group."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT category, is_enabled FROM group_category_settings WHERE group_id = ?",
            (group_id,)
        )
        rows = await cursor.fetchall()
        return {row[0]: row[1] == 1 for row in rows}

async def get_published_categories() -> list:
    """Get list of globally published (enabled) categories."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT category FROM category_settings WHERE is_enabled = 1"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

# ==================== Category Custom Names ====================

async def get_category_custom_name(category: str) -> str:
    """Get custom name for a category. Returns None if not set."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT custom_name FROM category_names WHERE category = ?",
            (category,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_category_custom_name(category: str, custom_name: str):
    """Set custom name for a category."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO category_names (category, custom_name) VALUES (?, ?)",
            (category, custom_name)
        )
        await db.commit()

async def get_all_category_custom_names() -> dict:
    """Get all custom category names."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT category, custom_name FROM category_names")
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

# ==================== Bot Settings ====================

async def get_bot_setting(key: str, default: str = None) -> str:
    """Get a bot setting value."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else default

async def set_bot_setting(key: str, value: str):
    """Set a bot setting value."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()

async def get_activation_threshold() -> int:
    """Get minimum members threshold for activation. Default is 3."""
    value = await get_bot_setting("activation_threshold", "3")
    return int(value)

async def set_activation_threshold(threshold: int):
    """Set minimum members threshold for activation."""
    await set_bot_setting("activation_threshold", str(threshold))

# ==================== Managed Groups ====================

async def add_managed_group(group_id: int, title: str, member_count: int, added_by: int = None):
    """Add or update a managed group."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO managed_groups 
            (group_id, title, member_count, added_by, added_at) 
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(group_id) DO UPDATE SET
                title = excluded.title,
                member_count = excluded.member_count
        """, (group_id, title, member_count, added_by))
        await db.commit()

async def get_managed_group(group_id: int) -> dict:
    """Get a managed group by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT group_id, title, member_count, is_vip, is_active, added_at, added_by FROM managed_groups WHERE group_id = ?",
            (group_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {
                "group_id": row[0],
                "title": row[1],
                "member_count": row[2],
                "is_vip": row[3] == 1,
                "is_active": row[4] == 1,
                "added_at": row[5],
                "added_by": row[6]
            }
        return None

async def set_group_vip(group_id: int, is_vip: bool):
    """Set group VIP status."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE managed_groups SET is_vip = ? WHERE group_id = ?",
            (1 if is_vip else 0, group_id)
        )
        await db.commit()

async def set_group_active(group_id: int, is_active: bool):
    """Set group active status."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE managed_groups SET is_active = ? WHERE group_id = ?",
            (1 if is_active else 0, group_id)
        )
        await db.commit()

async def remove_managed_group(group_id: int):
    """Remove a managed group."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM managed_groups WHERE group_id = ?", (group_id,))
        await db.commit()

async def get_all_managed_groups() -> list:
    """Get all managed groups."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT group_id, title, member_count, is_vip, is_active FROM managed_groups ORDER BY added_at DESC"
        )
        rows = await cursor.fetchall()
        return [{
            "group_id": row[0],
            "title": row[1],
            "member_count": row[2],
            "is_vip": row[3] == 1,
            "is_active": row[4] == 1
        } for row in rows]

async def is_group_vip(group_id: int) -> bool:
    """Check if group is VIP."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT is_vip FROM managed_groups WHERE group_id = ?",
            (group_id,)
        )
        row = await cursor.fetchone()
        return row[0] == 1 if row else False

# ==================== Notification Settings ====================

async def get_notification_delete_time(group_id: int, category: str) -> int:
    """Get delete after seconds for a group/category. 0 means don't delete."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT delete_after_seconds FROM notification_settings WHERE group_id = ? AND category = ?",
            (group_id, category)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

async def set_notification_delete_time(group_id: int, category: str, seconds: int):
    """Set delete after seconds for a group/category."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO notification_settings (group_id, category, delete_after_seconds) VALUES (?, ?, ?)",
            (group_id, category, seconds)
        )
        await db.commit()

# ==================== Bot Mode Settings ====================

async def get_bot_mode() -> str:
    """Get bot mode: 'active' or 'dry_run'."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM bot_settings WHERE key = 'mode'")
        row = await cursor.fetchone()
        return row[0] if row else "dry_run"

async def set_bot_mode(mode: str):
    """Set bot mode: 'active' or 'dry_run'."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('mode', ?)",
            (mode,)
        )
        await db.commit()

async def get_system_flag(key: str, default: str = None) -> str:
    """Get a system flag value (prefixed in bot_settings)."""
    return await get_bot_setting(f"flag:{key}", default)

async def set_system_flag(key: str, value: str):
    """Set a system flag value (prefixed in bot_settings)."""
    await set_bot_setting(f"flag:{key}", value)

async def get_all_system_flags_mapping() -> dict:
    """Get all system flags."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT key, value FROM bot_settings WHERE key LIKE 'flag:%'")
        rows = await cursor.fetchall()
        # Remove 'flag:' prefix
        return {row[0][5:]: row[1] for row in rows}


# ==================== Prohibited Keywords ====================

async def init_prohibited_keywords_table():
    """Initialize prohibited keywords table if not exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS prohibited_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                keyword TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, keyword)
            )
        """)
        await db.commit()

async def get_prohibited_keywords(category: str) -> list:
    """Get all prohibited keywords for a category."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT keyword FROM prohibited_keywords WHERE category = ? ORDER BY keyword",
            (category,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def add_prohibited_keyword(category: str, keyword: str) -> bool:
    """Add a prohibited keyword. Returns True if added, False if already exists."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO prohibited_keywords (category, keyword) VALUES (?, ?)",
                (category, keyword)
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False

async def remove_prohibited_keyword(category: str, keyword: str) -> bool:
    """Remove a prohibited keyword. Returns True if removed."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM prohibited_keywords WHERE category = ? AND keyword = ?",
            (category, keyword)
        )
        await db.commit()
        return cursor.rowcount > 0

async def get_prohibited_keywords_count(category: str) -> int:
    """Get count of prohibited keywords for a category."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM prohibited_keywords WHERE category = ?",
            (category,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

async def get_all_prohibited_keywords_mapping() -> dict:
    """Get all prohibited keywords grouped by category."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT category, keyword FROM prohibited_keywords ORDER BY category, keyword"
        )
        rows = await cursor.fetchall()
        result = {}
        for cat, kw in rows:
            if cat not in result:
                result[cat] = []
            result[cat].append(kw)
        return result
