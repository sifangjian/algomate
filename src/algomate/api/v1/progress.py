from datetime import date, datetime

from fastapi import APIRouter

from algomate.data.database import Database
from algomate.models.cards import Card
from algomate.models.review_records import ReviewRecord

router = APIRouter(prefix="/progress", tags=["进度"])


@router.get("/stats")
async def get_stats():
    db = Database.get_instance()
    session = db.get_session()
    try:
        total_cards = session.query(Card).count()

        target_date = date.today()
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        completed_today = session.query(ReviewRecord).filter(
            ReviewRecord.status == "completed",
            ReviewRecord.review_date >= start,
            ReviewRecord.review_date <= end,
        ).count()

        total_reviews = session.query(ReviewRecord).filter(
            ReviewRecord.status == "completed",
        ).count()

        correct_reviews = session.query(ReviewRecord).filter(
            ReviewRecord.status == "completed",
            ReviewRecord.durability_after > ReviewRecord.durability_before,
        ).count()

        accuracy_rate = round(correct_reviews / total_reviews * 100, 1) if total_reviews > 0 else 0.0

        first_card = session.query(Card).order_by(Card.created_at.asc()).first()
        learning_days = 0
        if first_card and first_card.created_at:
            learning_days = (date.today() - first_card.created_at.date()).days + 1

        return {
            "total_cards": total_cards,
            "total_practice": total_reviews,
            "accuracy_rate": accuracy_rate,
            "learning_days": learning_days,
            "completed_today": completed_today,
        }
    finally:
        session.close()


@router.get("/mastery")
async def get_mastery():
    from sqlalchemy import func

    db = Database.get_instance()
    session = db.get_session()
    try:
        rows = session.query(
            Card.algorithm_type,
            func.count(Card.id),
            func.avg(Card.durability),
        ).group_by(Card.algorithm_type).all()

        mastery = {}
        for row in rows:
            algo_type = row[0] or "其他"
            mastery[algo_type] = {
                "card_count": row[1],
                "avg_durability": round(row[2], 1) if row[2] else 0,
            }

        return {"mastery": mastery}
    finally:
        session.close()
