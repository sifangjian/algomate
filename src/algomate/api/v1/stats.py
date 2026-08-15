import logging
from datetime import datetime, timedelta, date

from fastapi import APIRouter
from sqlalchemy import func

from algomate.models.cards import Card
from algomate.models.problem_card import ProblemCard
from algomate.models.solution_card import SolutionCard
from algomate.models.technique_card import TechniqueCard
from algomate.models.review_records import ReviewRecord

router = APIRouter(prefix="/stats", tags=["统计"])
logger = logging.getLogger(__name__)


@router.get("/today")
async def get_today_stats():
    """获取今日成就统计 — 主页显眼位置展示，激励用户持续使用"""
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())

        new_problems = session.query(func.count(ProblemCard.id)).filter(
            ProblemCard.created_at >= today_start,
            ProblemCard.created_at <= today_end,
        ).scalar() or 0

        new_solutions = session.query(func.count(SolutionCard.id)).filter(
            SolutionCard.created_at >= today_start,
            SolutionCard.created_at <= today_end,
        ).scalar() or 0

        new_techniques = session.query(func.count(TechniqueCard.id)).filter(
            TechniqueCard.created_at >= today_start,
            TechniqueCard.created_at <= today_end,
        ).scalar() or 0

        reviews_completed = session.query(func.count(ReviewRecord.id)).filter(
            ReviewRecord.status == "completed",
            ReviewRecord.review_date >= today_start,
            ReviewRecord.review_date <= today_end,
        ).scalar() or 0

        total_new = new_problems + new_solutions + new_techniques

        # 计算连续活跃天数（从今天往前，只要有任一活动记录就算活跃）
        streak = 0
        check_date = date.today()
        # 最多检查 365 天
        for _ in range(365):
            day_start = datetime.combine(check_date, datetime.min.time())
            day_end = datetime.combine(check_date, datetime.max.time())

            has_activity = (
                session.query(func.count(ProblemCard.id)).filter(
                    ProblemCard.created_at >= day_start, ProblemCard.created_at <= day_end
                ).scalar()
                or session.query(func.count(SolutionCard.id)).filter(
                    SolutionCard.created_at >= day_start, SolutionCard.created_at <= day_end
                ).scalar()
                or session.query(func.count(TechniqueCard.id)).filter(
                    TechniqueCard.created_at >= day_start, TechniqueCard.created_at <= day_end
                ).scalar()
                or session.query(func.count(ReviewRecord.id)).filter(
                    ReviewRecord.status == "completed",
                    ReviewRecord.review_date >= day_start,
                    ReviewRecord.review_date <= day_end,
                ).scalar()
            ) > 0

            if has_activity:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return {
            "code": 200,
            "message": "success",
            "data": {
                "new_problems": new_problems,
                "new_solutions": new_solutions,
                "new_techniques": new_techniques,
                "reviews_completed": reviews_completed,
                "total_new": total_new,
                "streak_days": streak,
            },
        }
    finally:
        session.close()


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
