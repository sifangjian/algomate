import logging

from fastapi import APIRouter
from sqlalchemy import func

from algomate.models.cards import Card

router = APIRouter(prefix="/stats", tags=["统计"])
logger = logging.getLogger(__name__)


@router.get("/overview")
async def get_stats_overview():
    from algomate.data.database import Database
    from algomate.data.repositories.progress_repo import ProgressRepository
    from algomate.core.game.realm_unlock import Realm

    db = Database.get_instance()
    session = db.get_session()
    try:
        total_cards = session.query(Card).count()
    finally:
        session.close()

    progress_repo = ProgressRepository(db)
    consecutive_days = progress_repo.get_consecutive_days()

    return {
        "total_cards": total_cards,
        "total_realms": len(Realm),
        "consecutive_days": consecutive_days,
    }


@router.get("")
async def get_hall_stats():
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        total_cards = session.query(Card).count()
        endangered_cards = session.query(Card).filter(
            Card.durability < 30,
            Card.durability > 0,
        ).count()
        pending_retake_cards = session.query(Card).filter(
            Card.pending_retake == True,
        ).count()

        cards_by_type_rows = session.query(
            Card.algorithm_type, func.count(Card.id)
        ).group_by(Card.algorithm_type).all()
        cards_by_type = {row[0]: row[1] for row in cards_by_type_rows if row[0]}

        return {
            "code": 200,
            "message": "success",
            "data": {
                "total_cards": total_cards,
                "endangered_cards": endangered_cards,
                "pending_retake_cards": pending_retake_cards,
                "cards_by_type": cards_by_type,
                "is_new_user": total_cards == 0,
            },
        }
    finally:
        session.close()
