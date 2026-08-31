import logging
from datetime import datetime, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc

from algomate.data.database import Database
from algomate.models.activity_log import ActivityLog, ActivityLogCreate, ActivityLogResponse

router = APIRouter(prefix="/activity-logs", tags=["活动日志"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[ActivityLogResponse])
def list_activity_logs(
    date_str: Optional[str] = Query(None, description="日期，格式 YYYY-MM-DD，默认今天"),
    start_date: Optional[str] = Query(None, description="起始日期，格式 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式 YYYY-MM-DD"),
    log_type: Optional[str] = Query(None, description="日志类型筛选"),
    sort_order: Optional[str] = Query("desc", description="排序: asc 正序 / desc 倒序"),
    limit: Optional[int] = Query(200, description="返回条数上限"),
):
    db = Database.get_instance()
    session = db.get_session()
    try:
        query = session.query(ActivityLog)

        # 按日期筛选
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                start = datetime(target_date.year, target_date.month, target_date.day)
                query = query.filter(
                    ActivityLog.created_at >= start,
                    ActivityLog.created_at < start + timedelta(days=1),
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD")
        elif start_date and end_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
                ed = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(
                    ActivityLog.created_at >= datetime(sd.year, sd.month, sd.day),
                    ActivityLog.created_at < datetime(ed.year, ed.month, ed.day) + timedelta(days=1),
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD")
        elif start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(ActivityLog.created_at >= datetime(sd.year, sd.month, sd.day))
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD")
        elif end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(ActivityLog.created_at < datetime(ed.year, ed.month, ed.day) + timedelta(days=1))
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD")
        else:
            # 默认今天
            today = date.today()
            start = datetime(today.year, today.month, today.day)
            query = query.filter(
                ActivityLog.created_at >= start,
                ActivityLog.created_at < start + timedelta(days=1),
            )

        # 按类型筛选
        if log_type:
            query = query.filter(ActivityLog.type == log_type)

        # 排序
        if sort_order == "asc":
            query = query.order_by(ActivityLog.created_at.asc())
        else:
            query = query.order_by(desc(ActivityLog.created_at))

        # 限制条数
        logs = query.limit(limit).all()

        return [ActivityLogResponse(
            id=log.id,
            type=log.type,
            card_type=log.card_type,
            card_name=log.card_name,
            card_id=log.card_id,
            content=log.content,
            details=log.details,
            created_at=log.created_at,
        ) for log in logs]
    finally:
        session.close()


@router.post("", response_model=ActivityLogResponse)
def create_activity_log(data: ActivityLogCreate):
    """手动添加日志"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        log_entry = ActivityLog(
            type="manual_note",
            content=data.content,
        )
        session.add(log_entry)
        session.commit()
        session.refresh(log_entry)
        logger.info(f"Created manual activity log: id={log_entry.id}")
        return ActivityLogResponse(
            id=log_entry.id,
            type=log_entry.type,
            card_type=log_entry.card_type,
            card_name=log_entry.card_name,
            card_id=log_entry.card_id,
            content=log_entry.content,
            details=log_entry.details,
            created_at=log_entry.created_at,
        )
    finally:
        session.close()