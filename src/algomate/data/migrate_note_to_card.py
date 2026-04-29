"""数据迁移脚本：Note → Card 中心化重构

将 Note 的知识内容和追踪属性迁移到 Card 新字段。
"""

import json
import logging
from datetime import datetime

from algomate.data.database import Database
from algomate.models.notes import Note
from algomate.models.cards import Card, Domain
from algomate.models.review_records import ReviewRecord
from algomate.models.questions import Question
from algomate.core.memory.forgotten_curve import ForgottenCurveEngine

logger = logging.getLogger(__name__)

DIFFICULTY_MAP = {
    "简单": 1, "中等": 3, "困难": 5,
    "easy": 1, "medium": 3, "hard": 5,
}

ALGORITHM_TYPE_TO_DOMAIN = {
    "基础数据结构": Domain.NOVICE_FOREST,
    "数组": Domain.NOVICE_FOREST,
    "链表": Domain.NOVICE_FOREST,
    "栈": Domain.NOVICE_FOREST,
    "队列": Domain.NOVICE_FOREST,
    "哈希表": Domain.NOVICE_FOREST,
    "树与图": Domain.NOVICE_FOREST,
    "二叉树": Domain.NOVICE_FOREST,
    "图": Domain.NOVICE_FOREST,
    "并查集": Domain.NOVICE_FOREST,
    "堆": Domain.NOVICE_FOREST,
    "搜索与遍历": Domain.MIST_SWAMP,
    "DFS": Domain.MIST_SWAMP,
    "BFS": Domain.MIST_SWAMP,
    "排序算法": Domain.MIST_SWAMP,
    "排序": Domain.MIST_SWAMP,
    "二分查找": Domain.MIST_SWAMP,
    "动态规划": Domain.WISDOM_TEMPLE,
    "贪心算法": Domain.GREED_TOWER,
    "贪心": Domain.GREED_TOWER,
    "回溯算法": Domain.FATE_MAZE,
    "回溯": Domain.FATE_MAZE,
    "分治算法": Domain.SPLIT_MOUNTAIN,
    "分治": Domain.SPLIT_MOUNTAIN,
    "数学与位运算": Domain.MATH_HALL,
    "位运算": Domain.MATH_HALL,
    "数学": Domain.MATH_HALL,
}

forgotten_curve = ForgottenCurveEngine()


def _map_difficulty(note_difficulty: str) -> int:
    return DIFFICULTY_MAP.get(note_difficulty, 3) if note_difficulty else 3


def _map_algorithm_type_to_domain(algorithm_type: str) -> str:
    if not algorithm_type:
        return Domain.NOVICE_FOREST.value
    domain = ALGORITHM_TYPE_TO_DOMAIN.get(algorithm_type)
    if domain:
        return domain.value
    for key, dom in ALGORITHM_TYPE_TO_DOMAIN.items():
        if key in algorithm_type or algorithm_type in key:
            return dom.value
    return Domain.TRIAL_LAND.value


def migrate_notes_to_cards():
    """执行 Note → Card 数据迁移"""
    db = Database.get_instance()
    session = db.get_session()

    migrated_count = 0
    skipped_count = 0
    created_count = 0
    error_count = 0

    try:
        cards_with_note = session.query(Card).filter(Card.note_id.isnot(None)).all()
        logger.info(f"找到 {len(cards_with_note)} 张有关联 Note 的 Card")

        for card in cards_with_note:
            try:
                note = session.query(Note).filter(Note.id == card.note_id).first()
                if not note:
                    logger.warning(f"Card(id={card.id}) 关联的 Note(id={card.note_id}) 不存在，跳过")
                    skipped_count += 1
                    continue

                if note.content:
                    card.knowledge_content = note.content
                if note.summary:
                    card.summary = note.summary
                if note.algorithm_type:
                    card.algorithm_type = note.algorithm_type
                if note.difficulty:
                    card.difficulty = _map_difficulty(note.difficulty)
                if note.tags:
                    card.key_points = note.tags
                if note.mastery_level is not None:
                    card.durability = note.mastery_level
                if note.review_count is not None:
                    card.review_count = note.review_count
                if note.next_review_date:
                    card.next_review_date = note.next_review_date
                if note.last_reviewed:
                    card.last_reviewed = note.last_reviewed

                card.review_level = forgotten_curve.calculate_review_level_from_history(
                    card.created_at, card.last_reviewed, card.review_count
                )

                migrated_count += 1
            except Exception as e:
                logger.error(f"迁移 Card(id={card.id}) 失败: {e}")
                error_count += 1

        session.commit()
        logger.info(f"已有 Card 迁移完成: 成功={migrated_count}, 跳过={skipped_count}, 失败={error_count}")

        note_ids_with_card = {card.note_id for card in session.query(Card).filter(Card.note_id.isnot(None)).all()}
        notes_without_card = session.query(Note).filter(~Note.id.in_(note_ids_with_card)).all() if note_ids_with_card else session.query(Note).all()

        logger.info(f"找到 {len(notes_without_card)} 个没有关联 Card 的 Note")

        for note in notes_without_card:
            try:
                new_card = Card(
                    name=note.title or note.algorithm_type or "未命名卡牌",
                    domain=_map_algorithm_type_to_domain(note.algorithm_type),
                    algorithm_category=note.algorithm_type,
                    difficulty=_map_difficulty(note.difficulty),
                    durability=note.mastery_level if note.mastery_level is not None else 100,
                    max_durability=100,
                    note_id=note.id,
                    knowledge_content=note.content,
                    key_points=note.tags or "[]",
                    summary=note.summary,
                    algorithm_type=note.algorithm_type,
                    review_count=note.review_count or 0,
                    next_review_date=note.next_review_date,
                    last_reviewed=note.last_reviewed,
                    is_sealed=(note.mastery_level == 0) if note.mastery_level is not None else False,
                )
                new_card.review_level = forgotten_curve.calculate_review_level_from_history(
                    new_card.created_at, new_card.last_reviewed, new_card.review_count
                )
                session.add(new_card)
                created_count += 1
            except Exception as e:
                logger.error(f"为 Note(id={note.id}) 创建 Card 失败: {e}")
                error_count += 1

        session.commit()
        logger.info(f"无 Card 的 Note 迁移完成: 新建 Card={created_count}, 失败={error_count}")

    except Exception as e:
        session.rollback()
        logger.error(f"migrate_notes_to_cards 整体失败，已回滚: {e}")
        raise
    finally:
        session.close()

    return {
        "migrated": migrated_count,
        "skipped": skipped_count,
        "created": created_count,
        "errors": error_count,
    }


def migrate_review_records():
    """迁移 ReviewRecord 的 note_id → card_id"""
    db = Database.get_instance()
    session = db.get_session()

    migrated_count = 0
    skipped_count = 0
    error_count = 0

    try:
        records = session.query(ReviewRecord).filter(
            ReviewRecord.note_id.isnot(None),
            ReviewRecord.card_id.is_(None),
        ).all()
        logger.info(f"找到 {len(records)} 条只有 note_id 没有 card_id 的 ReviewRecord")

        for record in records:
            try:
                card = session.query(Card).filter(Card.note_id == record.note_id).first()
                if card:
                    record.card_id = card.id
                    migrated_count += 1
                else:
                    logger.warning(f"ReviewRecord(id={record.id}) 的 Note(id={record.note_id}) 没有关联的 Card，跳过")
                    skipped_count += 1
            except Exception as e:
                logger.error(f"迁移 ReviewRecord(id={record.id}) 失败: {e}")
                error_count += 1

        session.commit()
        logger.info(f"ReviewRecord 迁移完成: 成功={migrated_count}, 跳过={skipped_count}, 失败={error_count}")

    except Exception as e:
        session.rollback()
        logger.error(f"migrate_review_records 整体失败，已回滚: {e}")
        raise
    finally:
        session.close()

    return {
        "migrated": migrated_count,
        "skipped": skipped_count,
        "errors": error_count,
    }


def migrate_questions():
    """迁移 Question 的 note_id → card_id"""
    db = Database.get_instance()
    session = db.get_session()

    migrated_count = 0
    skipped_count = 0
    error_count = 0

    try:
        if not hasattr(Question, "note_id"):
            logger.info("Question 模型没有 note_id 字段，跳过 Question 迁移")
            return {"migrated": 0, "skipped": 0, "errors": 0}

        questions = session.query(Question).filter(
            Question.note_id.isnot(None),
        ).all()
        logger.info(f"找到 {len(questions)} 条有 note_id 的 Question")

        for question in questions:
            try:
                if question.card_id:
                    skipped_count += 1
                    continue

                card = session.query(Card).filter(Card.note_id == question.note_id).first()
                if card:
                    question.card_id = card.id
                    migrated_count += 1
                else:
                    logger.warning(f"Question(id={question.id}) 的 Note(id={question.note_id}) 没有关联的 Card，跳过")
                    skipped_count += 1
            except Exception as e:
                logger.error(f"迁移 Question(id={question.id}) 失败: {e}")
                error_count += 1

        session.commit()
        logger.info(f"Question 迁移完成: 成功={migrated_count}, 跳过={skipped_count}, 失败={error_count}")

    except Exception as e:
        session.rollback()
        logger.error(f"migrate_questions 整体失败，已回滚: {e}")
        raise
    finally:
        session.close()

    return {
        "migrated": migrated_count,
        "skipped": skipped_count,
        "errors": error_count,
    }


def run_migration():
    """执行完整迁移流程"""
    logger.info("=" * 60)
    logger.info("开始数据迁移：Note → Card 中心化重构")
    logger.info("=" * 60)

    results = {}

    try:
        logger.info("\n--- 步骤 1: 迁移 Note 内容到 Card ---")
        results["notes_to_cards"] = migrate_notes_to_cards()
    except Exception as e:
        logger.error(f"步骤 1 失败: {e}")

    try:
        logger.info("\n--- 步骤 2: 迁移 ReviewRecord ---")
        results["review_records"] = migrate_review_records()
    except Exception as e:
        logger.error(f"步骤 2 失败: {e}")

    try:
        logger.info("\n--- 步骤 3: 迁移 Question ---")
        results["questions"] = migrate_questions()
    except Exception as e:
        logger.error(f"步骤 3 失败: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("数据迁移完成，结果摘要：")
    logger.info("-" * 40)
    for step, data in results.items():
        logger.info(f"  {step}: {data}")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_migration()
