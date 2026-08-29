import logging
from datetime import date, datetime

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/reviews", tags=["修炼V1"])
logger = logging.getLogger(__name__)


@router.get("/today")
async def get_today_review_tasks(target_date: str = None):
    from algomate.core.scheduler.review_scheduler import ReviewScheduler
    from algomate.data.database import Database
    from algomate.models.cards import Card

    db = Database.get_instance()
    session = db.get_session()
    try:
        total_cards = session.query(Card).count()
        has_cards = total_cards > 0

        scheduler = ReviewScheduler()
        tasks = scheduler.generate_daily_tasks()

        endangered_count = sum(1 for t in tasks if t.priority == "critical")
        due_count = sum(1 for t in tasks if t.priority in ("high", "medium"))
        total_count = len(tasks)

        task_list = []
        for task in tasks:
            task_dict = task.to_dict()
            task_list.append(task_dict)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "tasks": task_list,
                "endangered_count": endangered_count,
                "due_count": due_count,
                "total_count": total_count,
                "has_cards": has_cards,
            }
        }
    except Exception as e:
        logger.error("get_today_review_tasks failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{card_id}/complete")
async def complete_review_v1(card_id: int, review_data: dict):
    from algomate.review.review_plan_service import ReviewPlanService
    from algomate.models.cards import Card
    from algomate.data.database import Database

    # 新用法: 传 action (forgot/struggled/passed/mastered/redone_ac/redone_stuck)
    # 兼容旧用法: 传 review_type (content_review/quick_quiz/leetcode_challenge)
    action = review_data.get("action")
    review_type = review_data.get("review_type", "content_review")
    note = review_data.get("note")

    if not action:
        # 旧调用兼容: 用 review_type 推断一个默认 action
        action = "passed" if review_type != "quick_quiz" else "struggled"

    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="卡牌不存在")
        if card.pending_retake:
            raise HTTPException(status_code=409, detail="卡牌已封印，无法修炼")
    finally:
        session.close()

    review_service = ReviewPlanService()
    result = review_service.complete_review(card_id, action=action, review_type=review_type, note=note)
    if result is None:
        raise HTTPException(status_code=404, detail="卡牌不存在")

    return {
        "code": 200,
        "message": "success",
        "data": result
    }