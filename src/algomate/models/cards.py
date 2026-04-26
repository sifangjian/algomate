"""
卡牌模型

卡牌是算法技巧的载体，有耐久度属性
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

from algomate.data.database import Base


class Domain(str, Enum):
    """卡牌领域枚举"""
    NOVICE_FOREST = "新手森林"
    MIST_SWAMP = "迷雾沼泽"
    WISDOM_TEMPLE = "智慧圣殿"
    GREED_TOWER = "贪婪之塔"
    FATE_MAZE = "命运迷宫"
    SPLIT_MOUNTAIN = "分裂山脉"
    MATH_HALL = "数学殿堂"
    TRIAL_LAND = "试炼之地"


class Card(Base):
    """卡牌模型
    
    卡牌是算法技巧的载体，有耐久度属性。
    
    Attributes:
        id: 卡牌唯一标识
        name: 卡牌名称（算法技巧名）
        domain: 所属领域（对应秘境）
        durability: 耐久度 0-100
        note_id: 关联笔记ID（外键，可为NULL）
        created_at: 创建时间
        last_reviewed: 最近复习时间
        is_sealed: 是否封印（耐久度=0时为True）
    """
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    domain = Column(String(50), nullable=False)
    durability = Column(Integer, default=100, nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_reviewed = Column(DateTime, nullable=True)
    is_sealed = Column(Boolean, default=False, nullable=False)
    
    note: Optional["Note"] = relationship("Note", back_populates="cards")
    questions: List["Question"] = relationship("Question", back_populates="card")
    answer_records: List["AnswerRecord"] = relationship("AnswerRecord", back_populates="card")


class CardCreate(BaseModel):
    """创建卡牌的输入验证模型"""
    name: str = Field(..., min_length=1, max_length=200, description="卡牌名称")
    domain: Domain = Field(..., description="所属领域")
    durability: int = Field(default=100, ge=0, le=100, description="耐久度")
    note_id: Optional[int] = Field(None, description="关联笔记ID")
    
    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
    """更新卡牌的输入验证模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="卡牌名称")
    domain: Optional[Domain] = Field(None, description="所属领域")
    durability: Optional[int] = Field(None, ge=0, le=100, description="耐久度")
    note_id: Optional[int] = Field(None, description="关联笔记ID")
    last_reviewed: Optional[datetime] = Field(None, description="最近复习时间")
    is_sealed: Optional[bool] = Field(None, description="是否封印")
    
    class Config:
        from_attributes = True


class CardResponse(BaseModel):
    """返回给前端的卡牌数据模型"""
    id: int
    name: str
    domain: str
    durability: int
    note_id: Optional[int]
    created_at: datetime
    last_reviewed: Optional[datetime]
    is_sealed: bool
    
    class Config:
        from_attributes = True


class DomainStats(BaseModel):
    """领域统计数据模型"""
    domain: str
    total_count: int
    mastered_count: int
    sealed_count: int
    avg_durability: float


router = APIRouter(prefix="/api/cards", tags=["卡牌"])


@router.get("/", response_model=list[CardResponse])
async def get_cards(domain: Optional[str] = Query(None, description="按领域筛选")):
    """获取卡牌列表（支持按领域筛选）"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        query = session.query(Card)
        if domain:
            query = query.filter(Card.domain == domain)
        cards = query.order_by(Card.created_at.desc()).all()
        return cards
    finally:
        session.close()


@router.get("/critical", response_model=list[CardResponse])
async def get_critical_cards():
    """获取濒危卡牌（耐久度 < 30）"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.durability < 30).order_by(Card.durability.asc()).all()
        return cards
    finally:
        session.close()


@router.get("/domain-stats", response_model=list[DomainStats])
async def get_domain_stats():
    """获取各领域卡牌统计"""
    from algomate.data.database import Database
    from sqlalchemy import func
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        stats = []
        for domain in Domain:
            cards = session.query(Card).filter(Card.domain == domain.value).all()
            total_count = len(cards)
            mastered_count = len([c for c in cards if c.durability >= 80])
            sealed_count = len([c for c in cards if c.is_sealed])
            avg_durability = sum([c.durability for c in cards]) / total_count if total_count > 0 else 0
            
            stats.append(DomainStats(
                domain=domain.value,
                total_count=total_count,
                mastered_count=mastered_count,
                sealed_count=sealed_count,
                avg_durability=round(avg_durability, 2)
            ))
        return stats
    finally:
        session.close()


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(card_id: int):
    """获取单个卡牌"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail=f"卡牌 {card_id} 不存在")
        return card
    finally:
        session.close()


@router.post("/", response_model=CardResponse, status_code=201)
async def create_card(card: CardCreate):
    """创建卡牌"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        if card.note_id:
            from algomate.models.notes import Note
            note = session.query(Note).filter(Note.id == card.note_id).first()
            if not note:
                raise HTTPException(status_code=404, detail=f"笔记 {card.note_id} 不存在")
        
        is_sealed = card.durability == 0
        new_card = Card(
            name=card.name,
            domain=card.domain.value,
            durability=card.durability,
            note_id=card.note_id,
            is_sealed=is_sealed
        )
        session.add(new_card)
        session.commit()
        session.refresh(new_card)
        return new_card
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建卡牌失败: {str(e)}")
    finally:
        session.close()


@router.put("/{card_id}", response_model=CardResponse)
async def update_card(card_id: int, card: CardUpdate):
    """更新卡牌"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(Card).filter(Card.id == card_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail=f"卡牌 {card_id} 不存在")
        
        if card.name is not None:
            existing.name = card.name
        if card.domain is not None:
            existing.domain = card.domain.value
        if card.durability is not None:
            existing.durability = card.durability
            existing.is_sealed = card.durability == 0
        if card.note_id is not None:
            if card.note_id:
                from algomate.models.notes import Note
                note = session.query(Note).filter(Note.id == card.note_id).first()
                if not note:
                    raise HTTPException(status_code=404, detail=f"笔记 {card.note_id} 不存在")
            existing.note_id = card.note_id
        if card.last_reviewed is not None:
            existing.last_reviewed = card.last_reviewed
        if card.is_sealed is not None:
            existing.is_sealed = card.is_sealed
        
        session.commit()
        session.refresh(existing)
        return existing
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新卡牌失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{card_id}", status_code=204)
async def delete_card(card_id: int):
    """删除卡牌"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail=f"卡牌 {card_id} 不存在")
        
        session.delete(card)
        session.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除卡牌失败: {str(e)}")
    finally:
        session.close()
