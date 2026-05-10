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
            task_dict["review_types"] = ["content_review", "quick_quiz", "boss_challenge"]
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
    from algomate.core.guide.service import GuideService

    review_type = review_data.get("review_type", "content_review")
    valid_types = ["content_review", "quick_quiz", "boss_challenge"]
    if review_type not in valid_types:
        raise HTTPException(status_code=400, detail="修炼形式参数不合法")

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
    result = review_service.complete_review(card_id, review_type)
    if result is None:
        raise HTTPException(status_code=404, detail="卡牌不存在")

    remaining_endangered = result.get("remaining_endangered", 0)

    session = db.get_session()
    try:
        due_tasks_count = session.query(Card).filter(
            Card.next_review_date <= date.today(),
            Card.pending_retake == False,
        ).count()
        has_due_tasks = due_tasks_count > 0
    finally:
        session.close()

    guide_service = GuideService()
    guide = guide_service.generate_guides(
        scene="after_review",
        remaining_endangered=remaining_endangered,
        has_due_tasks=has_due_tasks,
    )
    result["guide"] = guide.model_dump()

    return {
        "code": 200,
        "message": "success",
        "data": result
    }


@router.post("/{card_id}/quiz")
async def generate_review_quiz_v1(card_id: int, quiz_data: dict = None):
    from algomate.core.agent.question_generator import QuestionGenerator
    from algomate.models.cards import Card
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="卡牌不存在")
    finally:
        session.close()

    count = 2
    if quiz_data:
        count = quiz_data.get("count", 2)

    try:
        generator = QuestionGenerator()
        questions = generator.generate_review_quiz(card_id, count)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "card_id": card_id,
                "questions": questions,
            }
        }
    except Exception as e:
        error_msg = str(e).lower()
        logger.error("generate_review_quiz_v1 failed: %s", e, exc_info=True)
        if "timeout" in error_msg:
            raise HTTPException(status_code=504, detail="AI服务响应超时")
        if "rate limit" in error_msg or "429" in error_msg:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        raise HTTPException(status_code=500, detail="AI服务异常")
