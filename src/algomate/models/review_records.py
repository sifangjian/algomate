"""
复习记录模型

记录用户的复习活动，用于追踪复习历史和效果
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class ReviewRecord(Base):
    """复习记录模型
    
    记录用户的复习活动，用于追踪复习历史和效果。
    
    Attributes:
        id: 记录唯一标识
        note_id: 关联笔记ID（外键）
        review_date: 复习日期
        status: 复习状态（pending/completed/skipped）
        score: 本次复习得分
    """
    __tablename__ = "review_records"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    review_date = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    score = Column(Integer, nullable=True)
    
    note = relationship("Note", back_populates="review_records")


class ReviewRecordCreate(BaseModel):
    """创建复习记录的输入验证模型"""
    note_id: int = Field(..., description="关联笔记ID")
    status: str = Field(default="pending", description="复习状态")
    score: Optional[int] = Field(None, description="本次复习得分")
    
    class Config:
        from_attributes = True


class ReviewRecordResponse(BaseModel):
    """返回给前端的复习记录数据模型"""
    id: int
    note_id: int
    review_date: datetime
    status: str
    score: Optional[int]
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/review-records", tags=["复习记录"])


@router.get("/", response_model=list[ReviewRecordResponse])
async def get_review_records():
    """获取复习记录列表"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        records = session.query(ReviewRecord).order_by(ReviewRecord.review_date.desc()).all()
        return records
    finally:
        session.close()


@router.get("/{record_id}", response_model=ReviewRecordResponse)
async def get_review_record(record_id: int):
    """获取单个复习记录"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(ReviewRecord).filter(ReviewRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"复习记录 {record_id} 不存在")
        return record
    finally:
        session.close()


@router.post("/", response_model=ReviewRecordResponse, status_code=201)
async def create_review_record(record: ReviewRecordCreate):
    """创建复习记录"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        new_record = ReviewRecord(
            note_id=record.note_id,
            status=record.status,
            score=record.score
        )
        session.add(new_record)
        session.commit()
        session.refresh(new_record)
        return new_record
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建复习记录失败: {str(e)}")
    finally:
        session.close()
