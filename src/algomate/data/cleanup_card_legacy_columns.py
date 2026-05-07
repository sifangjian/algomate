"""数据迁移脚本：清理 Card 表中的废弃列

Card 模型在 F05 卡牌工坊重构中移除了以下废弃字段：
- domain（已被 algorithm_type 替代）
- is_sealed（已被 pending_retake 替代）
- note_id（Note→Card 迁移完成后不再需要）
- knowledge_content（已被 core_concept 替代）
- summary（已被 my_notes 替代）
- algorithm_category（已被 algorithm_type 替代）
- difficulty（不再作为 Card 字段）
- max_durability（不再作为 Card 字段）

此脚本会检查这些列是否仍存在于数据库中，如存在则安全删除。
仅适用于 SQLite 数据库。

Usage:
    uv run python -m algomate.data.cleanup_card_legacy_columns
"""

import logging
import sqlite3
from pathlib import Path

from algomate.config.settings import AppConfig
from algomate.data.database import Database

logger = logging.getLogger(__name__)

LEGACY_COLUMNS = [
    "domain",
    "is_sealed",
    "note_id",
    "knowledge_content",
    "summary",
    "algorithm_category",
    "difficulty",
    "max_durability",
]


def get_existing_columns(cursor, table_name="cards"):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def cleanup_legacy_columns(db_path=None):
    if db_path is None:
        config = AppConfig.load()
        db_path = str(config.DB_PATH)

    logger.info(f"Checking database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    existing = get_existing_columns(cursor)
    columns_to_drop = [col for col in LEGACY_COLUMNS if col in existing]

    if not columns_to_drop:
        logger.info("No legacy columns found. Database is clean.")
        conn.close()
        return

    logger.info(f"Found legacy columns to remove: {columns_to_drop}")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cards'")
    if not cursor.fetchone():
        logger.warning("Table 'cards' does not exist. Nothing to clean up.")
        conn.close()
        return

    keep_columns = existing - set(columns_to_drop)
    keep_columns_sql = ", ".join(sorted(keep_columns))

    cursor.execute(f"CREATE TABLE cards_new AS SELECT {keep_columns_sql} FROM cards")
    cursor.execute("DROP TABLE cards")
    cursor.execute("ALTER TABLE cards_new RENAME TO cards")

    conn.commit()
    conn.close()

    logger.info(f"Successfully removed {len(columns_to_drop)} legacy columns: {columns_to_drop}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    cleanup_legacy_columns()
