"""
应战记录模型

记录用户每次应战的结果，用于薄弱点分析
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class AnswerRecord(Base):
    """应战记录模型
    
    记录用户每次应战的结果，用于薄弱点分析。
    
    Attributes:
        id: 记录唯一标识
        boss_id: 关联Boss ID（外键）
        card_id: 使用的卡牌ID（外键）
        user_answer: 用户答案
        is_correct: 是否正确
        feedback: AI反馈
        answered_at: 应战时间
    """
    __tablename__ = "answer_records"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    boss_id = Column(Integer, ForeignKey("bosses.id"), nullable=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    feedback = Column(Text, default="", nullable=False)
    answered_at = Column(DateTime, default=datetime.now, nullable=False)
    
    boss = relationship("Boss", back_populates="answer_records")
    card = relationship("Card", back_populates="answer_records")


class AnswerRecordCreate(BaseModel):
    """创建应战记录的输入验证模型"""
    boss_id: Optional[int] = Field(None, description="关联Boss ID")
    card_id: Optional[int] = Field(None, description="使用的卡牌ID")
    user_answer: str = Field(..., min_length=1, description="用户答案")
    is_correct: bool = Field(..., description="是否正确")
    feedback: str = Field(default="", description="AI反馈")
    
    class Config:
        from_attributes = True


class AnswerRecordResponse(BaseModel):
    """返回给前端的应战记录数据模型"""
    id: int
    boss_id: Optional[int]
    card_id: Optional[int]
    user_answer: str
    is_correct: bool
    feedback: str
    answered_at: datetime
    
    class Config:
        from_attributes = True


class AnswerStats(BaseModel):
    """应战统计数据模型"""
    total_count: int
    correct_count: int
    incorrect_count: int
    accuracy_rate: float
    domain_stats: dict


router = APIRouter(prefix="/api/answers", tags=["应战记录"])


@router.get("/", response_model=list[AnswerRecordResponse])
async def get_answer_records():
    """获取应战记录列表"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        records = session.query(AnswerRecord).order_by(AnswerRecord.answered_at.desc()).all()
        return records
    finally:
        session.close()


@router.post("/", response_model=AnswerRecordResponse, status_code=201)
async def create_answer_record(record: AnswerRecordCreate):
    """提交应战记录"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        if record.boss_id:
            from algomate.models.bosses import Boss
            boss = session.query(Boss).filter(Boss.id == record.boss_id).first()
            if not boss:
                raise HTTPException(status_code=404, detail=f"Boss {record.boss_id} 不存在")
        
        if record.card_id:
            from algomate.models.cards import Card
            card = session.query(Card).filter(Card.id == record.card_id).first()
            if not card:
                raise HTTPException(status_code=404, detail=f"卡牌 {record.card_id} 不存在")
        
        new_record = AnswerRecord(
            boss_id=record.boss_id,
            card_id=record.card_id,
            user_answer=record.user_answer,
            is_correct=record.is_correct,
            feedback=record.feedback
        )
        session.add(new_record)
        session.commit()
        session.refresh(new_record)
        return new_record
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建应战记录失败: {str(e)}")
    finally:
        session.close()


@router.get("/stats", response_model=AnswerStats)
async def get_answer_stats():
    """获取应战统计（胜率等）"""
    from algomate.data.database import Database
    from algomate.models.cards import Card
    from sqlalchemy import func
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        total_count = session.query(func.count(AnswerRecord.id)).scalar() or 0
        correct_count = session.query(func.count(AnswerRecord.id)).filter(AnswerRecord.is_correct == True).scalar() or 0
        incorrect_count = total_count - correct_count
        accuracy_rate = round(correct_count / total_count * 100, 2) if total_count > 0 else 0.0
        
        domain_stats = {}
        records = session.query(AnswerRecord).all()
        for record in records:
            if record.card_id:
                card = session.query(Card).filter(Card.id == record.card_id).first()
                if card:
                    domain = card.domain
                    if domain not in domain_stats:
                        domain_stats[domain] = {"total": 0, "correct": 0}
                    domain_stats[domain]["total"] += 1
                    if record.is_correct:
                        domain_stats[domain]["correct"] += 1
        
        return AnswerStats(
            total_count=total_count,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            accuracy_rate=accuracy_rate,
            domain_stats=domain_stats
        )
    finally:
        session.close()


@router.get("/{record_id}", response_model=AnswerRecordResponse)
async def get_answer_record(record_id: int):
    """获取单个应战记录"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(AnswerRecord).filter(AnswerRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"应战记录 {record_id} 不存在")
        return record
    finally:
        session.close()


@router.delete("/{record_id}", status_code=204)
async def delete_answer_record(record_id: int):
    """删除应战记录"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(AnswerRecord).filter(AnswerRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"应战记录 {record_id} 不存在")
        
        session.delete(record)
        session.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除应战记录失败: {str(e)}")
    finally:
        session.close()
