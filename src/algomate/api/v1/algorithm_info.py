from fastapi import APIRouter

router = APIRouter(prefix="/algorithm-info", tags=["算法信息"])


@router.get("")
async def get_algorithm_info():
    from algomate.config.algorithm_types import (
        TOPIC_PREREQUISITES,
        TOPIC_IMPORTANCE,
        ALGORITHM_TYPES,
        ALGORITHM_CATEGORIES,
        LEARNING_PATH,
    )
    from algomate.data.database import Database
    from algomate.models.cards import Card
    from algomate.models.topic_prerequisites import TopicPrerequisite

    db = Database.get_instance()
    session = db.get_session()
    try:
        # 动态前置合并：从 TopicPrerequisite 表读取用户创建卡牌时生成的前置关系
        dynamic_prereqs = {}
        for row in session.query(TopicPrerequisite).all():
            dynamic_prereqs.setdefault(row.topic, set()).add(row.prerequisite)

        merged_types = list(ALGORITHM_TYPES)
        merged_path = list(LEARNING_PATH)
        merged_importance = dict(TOPIC_IMPORTANCE)

        # 合并动态前置到静态前置
        merged_prereqs = {}
        for topic, prereqs in TOPIC_PREREQUISITES.items():
            merged_prereqs[topic] = list(prereqs)
        for topic, prereqs in dynamic_prereqs.items():
            existing = set(merged_prereqs.get(topic, []))
            for p in prereqs:
                if p not in existing:
                    merged_prereqs.setdefault(topic, []).append(p)
                    existing.add(p)

        # 构建 topic_progress
        topic_progress = {}
        for topic in ALGORITHM_TYPES:
            cards = session.query(Card).filter(Card.algorithm_type == topic).all()
            if cards:
                avg_durability = sum(c.durability for c in cards) / len(cards)
                topic_progress[topic] = {
                    "card_count": len(cards),
                    "avg_durability": round(avg_durability, 1),
                    "learned": len(cards) > 0,
                }
            else:
                topic_progress[topic] = {
                    "card_count": 0,
                    "avg_durability": 0,
                    "learned": False,
                }

        return {
            "topic_prerequisites": merged_prereqs,
            "topic_importance": merged_importance,
            "algorithm_categories": ALGORITHM_CATEGORIES,
            "topic_progress": topic_progress,
            "algorithm_types": merged_types,
            "learning_path": merged_path,
        }
    finally:
        session.close()
