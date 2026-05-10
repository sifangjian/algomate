import logging

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["用户"])
logger = logging.getLogger(__name__)


@router.get("")
async def get_user():
    from algomate.data.database import Database
    from algomate.models.user_settings import UserSetting

    db = Database.get_instance()
    session = db.get_session()
    try:
        nickname_setting = session.query(UserSetting).filter(UserSetting.key == "nickname").first()
        level_setting = session.query(UserSetting).filter(UserSetting.key == "level").first()
        experience_setting = session.query(UserSetting).filter(UserSetting.key == "experience").first()

        nickname = nickname_setting.value if nickname_setting else "冒险者"
        level = int(level_setting.value) if level_setting else 1
        experience = int(experience_setting.value) if experience_setting else 0

        nextLevelExp = int(100 * (1.5 ** (level - 1)))

        title_map = {
            1: "新手", 2: "见习生", 3: "探索者", 4: "冒险家", 5: "精英",
            6: "大师", 7: "宗师", 8: "传奇", 9: "神话"
        }
        title = title_map.get(level, "至尊")

        return {
            "id": 1,
            "nickname": nickname,
            "level": level,
            "experience": experience,
            "nextLevelExp": nextLevelExp,
            "title": title
        }
    finally:
        session.close()


@router.get("/stats")
async def get_user_stats():
    from algomate.core.scheduler.review_scheduler import ReviewScheduler
    from algomate.data.database import Database
    from algomate.models.cards import Card

    db = Database.get_instance()
    session = db.get_session()
    try:
        total_cards = session.query(Card).count()
        sealed_cards = session.query(Card).filter(Card.pending_retake == True).count()
        critical_cards = session.query(Card).filter(Card.durability < 30).count()

        scheduler = ReviewScheduler()
        stats = scheduler.get_review_statistics()

        return {
            "total_cards": total_cards,
            "sealed_cards": sealed_cards,
            "critical_cards": critical_cards,
            "review_stats": stats
        }
    finally:
        session.close()
