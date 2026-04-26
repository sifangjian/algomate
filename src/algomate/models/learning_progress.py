"""
学习进度模型

记录用户每日的学习统计数据
"""

from datetime import date as date_type
from typing import Optional
from sqlalchemy import Column, Integer, Date
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class LearningProgress(Base):
    """学习进度模型
    
    记录用户每日的学习统计数据。
    
    Attributes:
        id: 记录唯一标识
        date: 日期（唯一）
        notes_count: 当日新增笔记数
        review_count: 当日复习题目数
        correct_count: 当日正确答题数
        total_count: 当日总答题数
    """
    __tablename__ = "learning_progress"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    notes_count = Column(Integer, default=0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    correct_count = Column(Integer, default=0, nullable=False)
    total_count = Column(Integer, default=0, nullable=False)


class LearningProgressCreate(BaseModel):
    """创建学习进度的输入验证模型"""
    date: date_type = Field(..., description="日期")
    notes_count: int = Field(default=0, description="当日新增笔记数")
    review_count: int = Field(default=0, description="当日复习题目数")
    correct_count: int = Field(default=0, description="当日正确答题数")
    total_count: int = Field(default=0, description="当日总答题数")
    
    class Config:
        from_attributes = True


class LearningProgressResponse(BaseModel):
    """返回给前端的学习进度数据模型"""
    id: int
    date: date_type
    notes_count: int
    review_count: int
    correct_count: int
    total_count: int
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/learning-progress", tags=["学习进度"])


@router.get("/", response_model=list[LearningProgressResponse])
async def get_learning_progress(
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None
):
    """获取学习进度列表"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        query = session.query(LearningProgress)
        
        if start_date:
            query = query.filter(LearningProgress.date >= start_date)
        if end_date:
            query = query.filter(LearningProgress.date <= end_date)
        
        progress = query.order_by(LearningProgress.date.desc()).all()
        return progress
    finally:
        session.close()


@router.get("/{progress_id}", response_model=LearningProgressResponse)
async def get_progress(progress_id: int):
    """获取单个学习进度"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        progress = session.query(LearningProgress).filter(LearningProgress.id == progress_id).first()
        if not progress:
            raise HTTPException(status_code=404, detail=f"学习进度 {progress_id} 不存在")
        return progress
    finally:
        session.close()


@router.post("/", response_model=LearningProgressResponse, status_code=201)
async def create_learning_progress(progress: LearningProgressCreate):
    """创建学习进度"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(LearningProgress).filter(LearningProgress.date == progress.date).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"日期 {progress.date} 的学习进度已存在")
        
        new_progress = LearningProgress(
            date=progress.date,
            notes_count=progress.notes_count,
            review_count=progress.review_count,
            correct_count=progress.correct_count,
            total_count=progress.total_count
        )
        session.add(new_progress)
        session.commit()
        session.refresh(new_progress)
        return new_progress
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建学习进度失败: {str(e)}")
    finally:
        session.close()
