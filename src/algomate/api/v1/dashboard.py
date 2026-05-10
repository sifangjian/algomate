import logging
from datetime import date, datetime

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])
logger = logging.getLogger(__name__)


def get_review_service():
    from algomate.review.review_plan_service import ReviewPlanService
    return ReviewPlanService()


@router.get("/today-review")
async def get_today_review(target_date: str = None):
    review_service = get_review_service()
    if target_date:
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()
    review_plan = review_service.get_today_review_plan(target_date)
    return {"reviews": review_plan, "date": target_date.isoformat()}


@router.get("/weak-points")
async def get_weak_points_endpoint(threshold: int = 70, limit: int = 10):
    review_service = get_review_service()
    weak_points = review_service.get_weak_points(threshold)
    return {"weak_points": weak_points[:limit], "total": len(weak_points)}


@router.post("/review/start/{card_id}")
async def start_review(card_id: int):
    review_service = get_review_service()
    result = review_service.start_review(card_id)
    if result is None:
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return result


@router.post("/review/complete/{card_id}")
async def complete_review(card_id: int, review_data: dict):
    review_service = get_review_service()
    action = review_data.get("action", "success")
    result = review_service.complete_review(card_id, action)
    if result is None:
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return result


@router.post("/review/skip/{card_id}")
async def skip_review(card_id: int, reason: str = ""):
    review_service = get_review_service()
    success = review_service.skip_review(card_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return {"message": "已跳过修炼", "card_id": card_id}


@router.get("/review/statistics")
async def get_review_statistics(target_date: str = None):
    review_service = get_review_service()
    if target_date:
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()
    stats = review_service.get_review_statistics(target_date)
    return stats


@router.get("/review/schedule/{card_id}")
async def get_card_review_schedule(card_id: int):
    review_service = get_review_service()
    schedule = review_service.generate_review_plan_for_card(card_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return {"schedule": schedule}


@router.get("/stats")
async def get_dashboard_stats():
    review_service = get_review_service()
    stats = review_service.get_review_statistics()
    return stats


@router.get("/new-user-status")
async def get_new_user_status():
    review_service = get_review_service()
    status = review_service.is_new_user()
    return status
