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
        algorithm_category: 算法分类（如 Search, Sorting, DP等）
        difficulty: 难度等级 1-5
        durability: 耐久度 0-100
        max_durability: 最大耐久度，默认100
        note_id: 关联笔记ID（外键，可为NULL）
        created_at: 创建时间
        last_reviewed: 最近复习时间
        is_sealed: 是否封印（耐久度=0时为True）
    """
    __tablename__ = "cards"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    domain = Column(String(50), nullable=False)
    algorithm_category = Column(String(100), nullable=True)
    difficulty = Column(Integer, default=3, nullable=False)
    durability = Column(Integer, default=100, nullable=False)
    max_durability = Column(Integer, default=100, nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_reviewed = Column(DateTime, nullable=True)
    is_sealed = Column(Boolean, default=False, nullable=False)
    
    note = relationship("Note", back_populates="cards")
    questions = relationship("Question", back_populates="card")
    answer_records = relationship("AnswerRecord", back_populates="card")


class CardCreate(BaseModel):
    """创建卡牌的输入验证模型"""
    name: str = Field(..., min_length=1, max_length=200, description="卡牌名称")
    domain: Domain = Field(..., description="所属领域")
    algorithm_category: Optional[str] = Field(None, description="算法分类")
    difficulty: int = Field(default=3, ge=1, le=5, description="难度等级 1-5")
    durability: int = Field(default=100, ge=0, le=100, description="耐久度")
    max_durability: int = Field(default=100, ge=0, le=100, description="最大耐久度")
    note_id: Optional[int] = Field(None, description="关联笔记ID")
    
    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
    """更新卡牌的输入验证模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="卡牌名称")
    domain: Optional[Domain] = Field(None, description="所属领域")
    algorithm_category: Optional[str] = Field(None, description="算法分类")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="难度等级 1-5")
    durability: Optional[int] = Field(None, ge=0, le=100, description="耐久度")
    max_durability: Optional[int] = Field(None, ge=0, le=100, description="最大耐久度")
    note_id: Optional[int] = Field(None, description="关联笔记ID")
    last_reviewed: Optional[datetime] = Field(None, description="最近复习时间")
    is_sealed: Optional[bool] = Field(None, description="是否封印")
    
    class Config:
        from_attributes = True


REALM_INFO = {
    "新手森林": {"id": "novice_forest", "icon": "🌲"},
    "迷雾沼泽": {"id": "mist_swamp", "icon": "🌫️"},
    "智慧圣殿": {"id": "wisdom_temple", "icon": "💡"},
    "贪婪之塔": {"id": "greed_tower", "icon": "🏰"},
    "命运迷宫": {"id": "fate_maze", "icon": "🌀"},
    "分裂山脉": {"id": "split_mountain", "icon": "⛰️"},
    "数学殿堂": {"id": "math_hall", "icon": "📐"},
    "试炼之地": {"id": "trial_land", "icon": "⚔️"},
}


class NoteSummary(BaseModel):
    """卡片中显示的笔记摘要信息"""
    id: int
    title: str
    content: str
    summary: Optional[str] = None
    algorithm_type: Optional[str] = None
    difficulty: Optional[str] = None
    mastery_level: int = 0
    tags: str = "[]"
    is_favorite: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class CardResponse(BaseModel):
    """返回给前端的卡牌数据模型（兼容前端格式）"""
    id: int
    name: str
    algorithmCategory: Optional[str] = None
    realmId: str
    realmName: str
    realmIcon: str
    durability: int
    maxDurability: int
    status: str
    createdAt: datetime
    lastReviewed: Optional[datetime] = None
    reviewCount: int = 0
    noteCount: int = 0
    keyPoints: List[str] = []
    relatedAlgorithms: List[str] = []
    difficulty: int = 3
    note_id: Optional[int] = None
    note: Optional[NoteSummary] = None
    is_sealed: bool = False
    
    class Config:
        from_attributes = True


def _compute_status(durability: int, max_durability: int, is_sealed: bool) -> str:
    """根据耐久度计算状态"""
    if is_sealed or durability == 0:
        return "danger"
    percentage = (durability / max_durability * 100) if max_durability > 0 else 0
    if percentage >= 60:
        return "normal"
    elif percentage >= 30:
        return "warning"
    return "danger"


def _card_to_response(card: Card, review_count: int = 0, note_count: int = 0,
                      key_points: List[str] = None, related_algorithms: List[str] = None,
                      note: "NoteSummary" = None) -> CardResponse:
    """将 Card 模型转换为 CardResponse 格式"""
    realm_info = REALM_INFO.get(card.domain, {"id": card.domain, "icon": "🗝️"})
    realm_id = realm_info["id"]
    realm_icon = realm_info["icon"]
    realm_name = card.domain
    
    return CardResponse(
        id=card.id,
        name=card.name,
        algorithmCategory=card.algorithm_category,
        realmId=realm_id,
        realmName=realm_name,
        realmIcon=realm_icon,
        durability=card.durability,
        maxDurability=card.max_durability,
        status=_compute_status(card.durability, card.max_durability, card.is_sealed),
        createdAt=card.created_at,
        lastReviewed=card.last_reviewed,
        reviewCount=review_count,
        noteCount=note_count,
        keyPoints=key_points or [],
        relatedAlgorithms=related_algorithms or [],
        difficulty=card.difficulty,
        note_id=card.note_id,
        note=note,
        is_sealed=card.is_sealed,
    )


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
    from algomate.models.answer_records import AnswerRecord
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        query = session.query(Card)
        if domain:
            query = query.filter(Card.domain == domain)
        cards = query.order_by(Card.created_at.desc()).all()
        
        result = []
        for card in cards:
            review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == card.id).count()
            note_count = 1 if card.note_id else 0
            key_points = []
            related_algorithms = []
            note_summary = None
            if card.note_id:
                from algomate.models.notes import Note
                note = session.query(Note).filter(Note.id == card.note_id).first()
                if note:
                    note_summary = NoteSummary(
                        id=note.id,
                        title=note.title,
                        content=note.content,
                        summary=note.summary,
                        algorithm_type=note.algorithm_type,
                        difficulty=note.difficulty,
                        mastery_level=note.mastery_level,
                        tags=note.tags,
                        is_favorite=note.is_favorite,
                        created_at=note.created_at
                    )
                    if note.tags:
                        import json
                        try:
                            tags = json.loads(note.tags)
                            key_points = tags[:5]
                        except:
                            pass
            result.append(_card_to_response(card, review_count, note_count, key_points, related_algorithms, note_summary))
        return result
    finally:
        session.close()


@router.get("/critical", response_model=list[CardResponse])
async def get_critical_cards():
    """获取濒危卡牌（耐久度 < 30）"""
    from algomate.data.database import Database
    from algomate.models.answer_records import AnswerRecord
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.durability < 30).order_by(Card.durability.asc()).all()
        result = []
        for card in cards:
            review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == card.id).count()
            note_summary = None
            if card.note_id:
                from algomate.models.notes import Note
                note = session.query(Note).filter(Note.id == card.note_id).first()
                if note:
                    note_summary = NoteSummary(
                        id=note.id,
                        title=note.title,
                        content=note.content,
                        summary=note.summary,
                        algorithm_type=note.algorithm_type,
                        difficulty=note.difficulty,
                        mastery_level=note.mastery_level,
                        tags=note.tags,
                        is_favorite=note.is_favorite,
                        created_at=note.created_at
                    )
            result.append(_card_to_response(card, review_count, 0 if not card.note_id else 1, [], [], note_summary))
        return result
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
    from algomate.models.answer_records import AnswerRecord
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail=f"卡牌 {card_id} 不存在")
        
        review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == card.id).count()
        note_count = 1 if card.note_id else 0
        key_points = []
        related_algorithms = []
        
        if card.note_id:
            from algomate.models.notes import Note
            note = session.query(Note).filter(Note.id == card.note_id).first()
            if note:
                note_summary = NoteSummary(
                    id=note.id,
                    title=note.title,
                    content=note.content,
                    summary=note.summary,
                    algorithm_type=note.algorithm_type,
                    difficulty=note.difficulty,
                    mastery_level=note.mastery_level,
                    tags=note.tags,
                    is_favorite=note.is_favorite,
                    created_at=note.created_at
                )
                if note.tags:
                    import json
                    try:
                        tags = json.loads(note.tags)
                        key_points = tags[:5]
                    except:
                        pass
            else:
                note_summary = None
        else:
            note_summary = None
        
        return _card_to_response(card, review_count, note_count, key_points, related_algorithms, note_summary)
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
            algorithm_category=card.algorithm_category,
            difficulty=card.difficulty,
            durability=card.durability,
            max_durability=card.max_durability,
            note_id=card.note_id,
            is_sealed=is_sealed
        )
        session.add(new_card)
        session.commit()
        session.refresh(new_card)
        return _card_to_response(new_card)
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
    from algomate.models.answer_records import AnswerRecord
    
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
        if card.algorithm_category is not None:
            existing.algorithm_category = card.algorithm_category
        if card.difficulty is not None:
            existing.difficulty = card.difficulty
        if card.durability is not None:
            existing.durability = card.durability
            existing.is_sealed = card.durability == 0
        if card.max_durability is not None:
            existing.max_durability = card.max_durability
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
        
        review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == existing.id).count()
        note_count = 1 if existing.note_id else 0
        key_points = []
        if existing.note_id:
            from algomate.models.notes import Note
            note = session.query(Note).filter(Note.id == existing.note_id).first()
            if note and note.tags:
                import json
                try:
                    key_points = json.loads(note.tags)[:5]
                except:
                    pass
        
        return _card_to_response(existing, review_count, note_count, key_points)
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
