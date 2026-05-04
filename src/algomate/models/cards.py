"""
卡牌模型

卡牌是算法技巧的载体，有耐久度属性
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
import json
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
        note_id: 关联心得ID（外键，可为NULL，向后兼容）
        created_at: 创建时间
        last_reviewed: 最近修炼时间
        is_sealed: 是否封印（耐久度=0时为True）
        knowledge_content: 知识内容（原心得内容）
        summary: 摘要
        algorithm_type: 算法类型
        review_level: 修炼等级（0-6）
        next_review_date: 下次修炼日期
        review_count: 修炼次数
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
    knowledge_content = Column(Text, nullable=True)
    key_points = Column(Text, default="[]", nullable=False)
    summary = Column(Text, nullable=True)
    algorithm_type = Column(String(100), nullable=True)
    review_level = Column(Integer, default=0, nullable=False)
    next_review_date = Column(DateTime, nullable=True)
    review_count = Column(Integer, default=0, nullable=False)
    
    note = relationship("Note", back_populates="cards")
    questions = relationship("Question", back_populates="card")
    answer_records = relationship("AnswerRecord", back_populates="card")
    review_records = relationship("ReviewRecord", back_populates="card")


class CardCreate(BaseModel):
    """创建卡牌的输入验证模型"""
    name: str = Field(..., min_length=1, max_length=200, description="卡牌名称")
    domain: Optional[Domain] = Field(default=Domain.NOVICE_FOREST, description="所属领域")
    algorithm_category: Optional[str] = Field(None, description="算法分类")
    difficulty: int = Field(default=3, ge=1, le=5, description="难度等级 1-5")
    durability: int = Field(default=100, ge=0, le=100, description="耐久度")
    max_durability: int = Field(default=100, ge=0, le=100, description="最大耐久度")
    note_id: Optional[int] = Field(None, description="关联心得ID")
    knowledge_content: Optional[str] = Field(None, description="知识内容")
    summary: Optional[str] = Field(None, description="摘要")
    algorithm_type: Optional[str] = Field(None, description="算法类型")
    review_level: Optional[int] = Field(None, ge=0, le=6, description="修炼等级")
    next_review_date: Optional[datetime] = Field(None, description="下次修炼日期")
    review_count: Optional[int] = Field(None, ge=0, description="修炼次数")
    
    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
    """更新卡牌的输入验证模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="卡牌名称")
    algorithm_category: Optional[str] = Field(None, description="算法分类")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="难度等级 1-5")
    durability: Optional[int] = Field(None, ge=0, le=100, description="耐久度")
    max_durability: Optional[int] = Field(None, ge=0, le=100, description="最大耐久度")
    note_id: Optional[int] = Field(None, description="关联心得ID")
    last_reviewed: Optional[datetime] = Field(None, description="最近修炼时间")
    is_sealed: Optional[bool] = Field(None, description="是否封印")
    key_points: Optional[str] = Field(None, description="关键要点列表（JSON字符串）")
    knowledge_content: Optional[str] = Field(None, description="知识内容")
    summary: Optional[str] = Field(None, description="摘要")
    algorithm_type: Optional[str] = Field(None, description="算法类型")
    review_level: Optional[int] = Field(None, ge=0, le=6, description="修炼等级")
    next_review_date: Optional[datetime] = Field(None, description="下次修炼日期")
    review_count: Optional[int] = Field(None, ge=0, description="修炼次数")
    
    class Config:
        from_attributes = True


class CardPolishRequest(BaseModel):
    content: str = Field(..., min_length=1, description="待润色内容")
    type: str = Field(..., pattern=r"^note_content$", description="润色类型：note_content")


class CardPolishResponse(BaseModel):
    polished_content: str = Field(description="润色后的内容")
    type: str = Field(description="润色类型")


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


class CardResponse(BaseModel):
    """返回给前端的卡牌数据模型（兼容前端格式）"""
    id: int
    name: str
    algorithmCategory: Optional[str] = None
    durability: int
    maxDurability: int
    status: str
    createdAt: datetime
    lastReviewed: Optional[datetime] = None
    reviewCount: int = 0
    noteCount: int = 0
    relatedAlgorithms: List[str] = []
    difficulty: int = 3
    note_id: Optional[int] = None
    note: Optional[dict] = None
    is_sealed: bool = False
    keyPoints: Optional[list] = None
    knowledgeContent: Optional[str] = None
    summary: Optional[str] = None
    algorithmType: Optional[str] = None
    reviewLevel: int = 0
    nextReviewDate: Optional[datetime] = None
    
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
                      related_algorithms: List[str] = None,
                      note: Optional[dict] = None) -> CardResponse:
    """将 Card 模型转换为 CardResponse 格式"""
    
    return CardResponse(
        id=card.id,
        name=card.name,
        algorithmCategory=card.algorithm_category,
        durability=card.durability,
        maxDurability=card.max_durability,
        status=_compute_status(card.durability, card.max_durability, card.is_sealed),
        createdAt=card.created_at,
        lastReviewed=card.last_reviewed,
        reviewCount=review_count or card.review_count or 0,
        noteCount=note_count,
        relatedAlgorithms=related_algorithms or [],
        difficulty=card.difficulty,
        note_id=card.note_id,
        note=note,
        is_sealed=card.is_sealed,
        keyPoints=json.loads(card.key_points) if card.key_points else [],
        knowledgeContent=card.knowledge_content,
        summary=card.summary,
        algorithmType=card.algorithm_type,
        reviewLevel=card.review_level or 0,
        nextReviewDate=card.next_review_date,
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
async def get_cards(
    domain: Optional[str] = Query(None, description="按领域筛选"),
    algorithm_type: Optional[str] = Query(None, description="按算法类型筛选"),
    algorithm_category: Optional[str] = Query(None, description="按算法分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词（匹配名称和算法分类）"),
    sort: Optional[str] = Query(None, description="排序字段：name/durability/last_reviewed"),
    order: Optional[str] = Query("asc", description="排序方向：asc/desc"),
    available: Optional[bool] = Query(None, description="仅返回未封印卡牌"),
):
    """获取卡牌列表（支持按领域、算法类型、算法分类筛选，搜索和排序）"""
    from algomate.data.database import Database
    from algomate.models.answer_records import AnswerRecord

    db = Database.get_instance()
    session = db.get_session()
    try:
        query = session.query(Card)
        if domain:
            query = query.filter(Card.domain == domain)
        if algorithm_type:
            query = query.filter(Card.algorithm_type == algorithm_type)
        if algorithm_category:
            query = query.filter(Card.algorithm_category == algorithm_category)
        if available:
            query = query.filter(Card.is_sealed == False)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Card.name.ilike(search_pattern)) |
                (Card.algorithm_category.ilike(search_pattern))
            )

        sort_column = Card.created_at
        if sort == "name":
            sort_column = Card.name
        elif sort == "durability":
            sort_column = Card.durability
        elif sort == "last_reviewed":
            sort_column = Card.last_reviewed

        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            if sort == "last_reviewed":
                query = query.order_by(sort_column.desc().nulls_last())
            else:
                query = query.order_by(sort_column.asc())

        cards = query.all()
        
        result = []
        for card in cards:
            review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == card.id).count()
            note_count = 1 if card.note_id else 0
            result.append(_card_to_response(card, review_count, note_count))
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
            note_count = 1 if card.note_id else 0
            result.append(_card_to_response(card, review_count, note_count))
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
        
        return _card_to_response(card, review_count, note_count)
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
                raise HTTPException(status_code=404, detail=f"心得 {card.note_id} 不存在")
        
        is_sealed = card.durability == 0
        new_card = Card(
            name=card.name,
            domain=card.domain.value if card.domain else Domain.NOVICE_FOREST.value,
            algorithm_category=card.algorithm_category,
            difficulty=card.difficulty,
            durability=card.durability,
            max_durability=card.max_durability,
            note_id=card.note_id,
            is_sealed=is_sealed,
            knowledge_content=card.knowledge_content,
            summary=card.summary,
            algorithm_type=card.algorithm_type,
            review_level=card.review_level or 0,
            next_review_date=card.next_review_date,
            review_count=card.review_count or 0,
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
                    raise HTTPException(status_code=404, detail=f"心得 {card.note_id} 不存在")
            existing.note_id = card.note_id
        if card.last_reviewed is not None:
            existing.last_reviewed = card.last_reviewed
        if card.is_sealed is not None:
            existing.is_sealed = card.is_sealed
        if card.key_points is not None:
            existing.key_points = card.key_points
        if card.knowledge_content is not None:
            existing.knowledge_content = card.knowledge_content
        if card.summary is not None:
            existing.summary = card.summary
        if card.algorithm_type is not None:
            existing.algorithm_type = card.algorithm_type
        if card.review_level is not None:
            existing.review_level = card.review_level
        if card.next_review_date is not None:
            existing.next_review_date = card.next_review_date
        if card.review_count is not None:
            existing.review_count = card.review_count
        
        session.commit()
        session.refresh(existing)
        
        review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == existing.id).count()
        note_count = 1 if existing.note_id else 0
        
        return _card_to_response(existing, review_count, note_count)
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


@router.post("/{card_id}/unseal", response_model=CardResponse)
async def unseal_card(card_id: int):
    from algomate.data.database import Database
    from algomate.models.answer_records import AnswerRecord
    from datetime import timedelta
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail=f"卡牌 {card_id} 不存在")
        
        if not card.is_sealed:
            raise HTTPException(status_code=400, detail="该卡牌未封印，无需解封")
        
        card.is_sealed = False
        card.durability = 30
        
        review_intervals = [1, 3, 7, 14, 30, 60, 90]
        interval_days = review_intervals[min(card.review_level or 0, len(review_intervals) - 1)]
        card.next_review_date = datetime.now() + timedelta(days=interval_days)
        
        session.commit()
        session.refresh(card)
        
        review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == card.id).count()
        note_count = 1 if card.note_id else 0
        
        return _card_to_response(card, review_count, note_count)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"解封卡牌失败: {str(e)}")
    finally:
        session.close()


@router.post("/polish", response_model=CardPolishResponse)
async def polish_card_content(request: CardPolishRequest):
    """AI润色卡牌内容"""
    from algomate.config.settings import AppConfig
    from algomate.core.agent.chat_client import ChatClient

    config = AppConfig.load()
    if not config.LLM_API_KEY:
        raise HTTPException(status_code=500, detail="AI服务未配置，请先设置API Key")

    try:
        client = ChatClient(api_key=config.LLM_API_KEY)

        system_prompt = """你是一个专业的算法知识编辑，擅长优化算法心得的表述。
请将用户提供的心得内容进行润色，改善语言流畅性和逻辑性。
保持原文的核心含义不变，优化表述方式，使其更清晰易懂。
直接返回润色后的内容，不要添加额外说明。"""
        user_prompt = f"请润色以下算法心得内容：\n{request.content}"

        result = client.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.5
        )

        return CardPolishResponse(
            polished_content=result.strip(),
            type=request.type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI润色失败: {str(e)}")
