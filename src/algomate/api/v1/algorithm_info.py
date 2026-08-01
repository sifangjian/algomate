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

    db = Database.get_instance()
    session = db.get_session()
    try:
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
            "topic_prerequisites": {k: list(v) for k, v in TOPIC_PREREQUISITES.items()},
            "topic_importance": TOPIC_IMPORTANCE,
            "algorithm_categories": ALGORITHM_CATEGORIES,
            "topic_progress": topic_progress,
            "algorithm_types": list(ALGORITHM_TYPES),
            "learning_path": list(LEARNING_PATH),
        }
    finally:
        session.close()
