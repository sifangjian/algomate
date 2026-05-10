import logging
from datetime import date, datetime

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/tasks", tags=["任务"])
logger = logging.getLogger(__name__)


@router.get("/completed-count")
async def get_completed_count():
    from algomate.data.database import Database
    from algomate.models.review_records import ReviewRecord

    db = Database.get_instance()
    session = db.get_session()
    try:
        target_date = date.today()
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        count = session.query(ReviewRecord).filter(
            ReviewRecord.status == "completed",
            ReviewRecord.review_date >= start,
            ReviewRecord.review_date <= end,
        ).count()
        return {"completed_today": count}
    finally:
        session.close()


@router.get("")
async def get_tasks(date: str = None):
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        if date == "today" or date is None:
            tasks = scheduler.generate_daily_tasks()
        else:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                tasks = scheduler.generate_daily_tasks(target_date)
            except ValueError:
                tasks = scheduler.generate_daily_tasks()
        return {"tasks": [task.to_dict() for task in tasks]}
    except Exception as e:
        logger.error("get_review_tasks failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
async def get_upcoming_tasks(days: int = 7):
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        reviews = scheduler.get_upcoming_reviews(days)
        return {"upcoming": reviews, "days": days}
    except Exception as e:
        logger.error("get_upcoming_reviews failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_daily_tasks():
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        count = await scheduler.execute_daily_review()
        return {"executed": count, "message": f"执行了 {count} 个修炼任务"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
