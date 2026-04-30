"""
修炼记录模型

记录用户的修炼活动，用于追踪修炼历史和效果
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class ReviewRecord(Base):
    """修炼记录模型
    
    记录用户的修炼活动，用于追踪修炼历史和效果。
    
    Attributes:
        id: 记录唯一标识
        card_id: 关联卡牌ID（外键）
        note_id: 关联心得ID（外键）— deprecated，请使用 card_id
        review_date: 修炼日期
        status: 修炼状态（pending/completed/skipped）
        score: 本次修炼战绩
    """
    __tablename__ = "review_records"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=True)  # deprecated: 请使用 card_id
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    review_date = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    score = Column(Integer, nullable=True)
    
    note = relationship("Note", back_populates="review_records")  # deprecated: 请使用 card
    card = relationship("Card", back_populates="review_records")


class ReviewRecordCreate(BaseModel):
    """创建修炼记录的输入验证模型"""
    note_id: Optional[int] = Field(None, description="关联心得ID — deprecated，请使用 card_id")
    card_id: Optional[int] = Field(None, description="关联卡牌ID")
    status: str = Field(default="pending", description="修炼状态")
    score: Optional[int] = Field(None, description="本次修炼战绩")
    
    class Config:
        from_attributes = True


class ReviewRecordResponse(BaseModel):
    """返回给前端的修炼记录数据模型"""
    id: int
    note_id: Optional[int] = None  # deprecated: 请使用 card_id
    card_id: Optional[int] = None
    review_date: datetime
    status: str
    score: Optional[int]
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/review-records", tags=["修炼记录"])


@router.get("/", response_model=list[ReviewRecordResponse])
async def get_review_records():
    """获取修炼记录列表"""
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
    """获取单个修炼记录"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(ReviewRecord).filter(ReviewRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"修炼记录 {record_id} 不存在")
        return record
    finally:
        session.close()


@router.post("/", response_model=ReviewRecordResponse, status_code=201)
async def create_review_record(record: ReviewRecordCreate):
    """创建修炼记录"""
    from algomate.data.database import Database
    
    if not record.card_id and not record.note_id:
        raise HTTPException(status_code=400, detail="必须提供 card_id 或 note_id")
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        if record.card_id:
            from algomate.models.cards import Card
            card = session.query(Card).filter(Card.id == record.card_id).first()
            if not card:
                raise HTTPException(status_code=404, detail=f"卡牌 {record.card_id} 不存在")
        
        if record.note_id:
            from algomate.models.notes import Note
            note = session.query(Note).filter(Note.id == record.note_id).first()
            if not note:
                raise HTTPException(status_code=404, detail=f"心得 {record.note_id} 不存在")
        
        new_record = ReviewRecord(
            note_id=record.note_id,
            card_id=record.card_id,
            status=record.status,
            score=record.score
        )
        session.add(new_record)
        session.commit()
        session.refresh(new_record)
        return new_record
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建修炼记录失败: {str(e)}")
    finally:
        session.close()
