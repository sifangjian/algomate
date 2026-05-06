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
    __tablename__ = "cards"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    domain = Column(String(50), nullable=False)
    algorithm_category = Column(String(100), nullable=True)
    difficulty = Column(Integer, default=3, nullable=False)
    durability = Column(Integer, default=80, nullable=False)
    max_durability = Column(Integer, default=100, nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_reviewed = Column(DateTime, nullable=True)
    is_sealed = Column(Boolean, default=False, nullable=False)
    knowledge_content = Column(Text, nullable=True)
    key_points = Column(Text, default="[]", nullable=False)
    summary = Column(Text, nullable=True)
    algorithm_type = Column(String(100), nullable=False, default="")
    review_level = Column(Integer, default=0, nullable=False)
    next_review_date = Column(DateTime, nullable=True)
    review_count = Column(Integer, default=0, nullable=False)
    pending_retake = Column(Boolean, default=False, nullable=False)
    core_concept = Column(Text, default="", nullable=False)
    code_template = Column(Text, default="", nullable=False)
    complexity_analysis = Column(Text, default="", nullable=False)
    use_cases = Column(Text, default="", nullable=False)
    common_variants = Column(Text, default="", nullable=False)
    typical_problems = Column(Text, default="", nullable=False)
    common_pitfalls = Column(Text, default="", nullable=False)
    comparison = Column(Text, default="", nullable=False)
    my_notes = Column(Text, default="", nullable=False)
    visual_links = Column(Text, nullable=True)
    npc_id = Column(Integer, ForeignKey("npcs.id"), nullable=False, default=1)
    topic = Column(String(100), nullable=False, default="")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    note = relationship("Note", back_populates="cards")
    questions = relationship("Question", back_populates="card")
    answer_records = relationship("AnswerRecord", back_populates="card")
    review_records = relationship("ReviewRecord", back_populates="card")
    npc = relationship("NPC", back_populates="cards")


class CardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="卡牌名称")
    domain: Optional[Domain] = Field(default=Domain.NOVICE_FOREST, description="所属领域")
    algorithm_category: Optional[str] = Field(None, description="算法分类")
    difficulty: int = Field(default=3, ge=1, le=5, description="难度等级 1-5")
    durability: int = Field(default=80, ge=0, le=100, description="耐久度")
    max_durability: int = Field(default=100, ge=0, le=100, description="最大耐久度")
    note_id: Optional[int] = Field(None, description="关联心得ID")
    knowledge_content: Optional[str] = Field(None, description="知识内容")
    summary: Optional[str] = Field(None, description="摘要")
    algorithm_type: Optional[str] = Field("", description="算法类型")
    review_level: Optional[int] = Field(None, ge=0, le=6, description="修炼等级")
    next_review_date: Optional[datetime] = Field(None, description="下次修炼日期")
    review_count: Optional[int] = Field(None, ge=0, description="修炼次数")
    pending_retake: Optional[bool] = Field(False, description="是否待重修")
    core_concept: Optional[str] = Field("", description="核心概念")
    code_template: Optional[str] = Field("", description="代码模板")
    complexity_analysis: Optional[str] = Field("", description="复杂度分析")
    use_cases: Optional[str] = Field("", description="使用场景")
    common_variants: Optional[str] = Field("", description="常见变体")
    typical_problems: Optional[str] = Field("", description="典型题目")
    common_pitfalls: Optional[str] = Field("", description="常见陷阱")
    comparison: Optional[str] = Field("", description="对比分析")
    my_notes: Optional[str] = Field("", description="个人笔记")
    visual_links: Optional[str] = Field(None, description="可视化链接")
    npc_id: Optional[int] = Field(1, description="关联NPC ID")
    topic: Optional[str] = Field("", description="主题")
    
    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
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
    pending_retake: Optional[bool] = Field(None, description="是否待重修")
    core_concept: Optional[str] = Field(None, description="核心概念")
    code_template: Optional[str] = Field(None, description="代码模板")
    complexity_analysis: Optional[str] = Field(None, description="复杂度分析")
    use_cases: Optional[str] = Field(None, description="使用场景")
    common_variants: Optional[str] = Field(None, description="常见变体")
    typical_problems: Optional[str] = Field(None, description="典型题目")
    common_pitfalls: Optional[str] = Field(None, description="常见陷阱")
    comparison: Optional[str] = Field(None, description="对比分析")
    my_notes: Optional[str] = Field(None, description="个人笔记")
    visual_links: Optional[str] = Field(None, description="可视化链接")
    npc_id: Optional[int] = Field(None, description="关联NPC ID")
    topic: Optional[str] = Field(None, description="主题")
    
    class Config:
        from_attributes = True


class PolishFieldType(str, Enum):
    note_content = "note_content"
    summary = "summary"
    key_points = "key_points"


class CardPolishRequest(BaseModel):
    content: str = Field(..., min_length=1, description="待润色内容")
    type: PolishFieldType = Field(..., description="润色类型：note_content/summary/key_points")


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
    pendingRetake: bool = False
    coreConcept: Optional[str] = None
    codeTemplate: Optional[str] = None
    complexityAnalysis: Optional[str] = None
    useCases: Optional[str] = None
    commonVariants: Optional[str] = None
    typicalProblems: Optional[str] = None
    commonPitfalls: Optional[str] = None
    comparison: Optional[str] = None
    myNotes: Optional[str] = None
    visualLinks: Optional[str] = None
    npcId: Optional[int] = None
    topic: Optional[str] = None
    updatedAt: Optional[datetime] = None
    
    class Config:
        from_attributes = True


def _compute_status(durability: int, max_durability: int, is_sealed: bool) -> str:
    if is_sealed or durability == 0:
        return "pending_retake"
    if durability < 30:
        return "endangered"
    return "normal"


def _card_to_response(card: Card, review_count: int = 0, note_count: int = 0,
                      related_algorithms: List[str] = None,
                      note: Optional[dict] = None) -> CardResponse:
    
    return CardResponse(
        id=card.id,
        name=card.name,
        algorithmCategory=card.algorithm_category,
        durability=card.durability,
        maxDurability=card.max_durability,
        status=_compute_status(card.durability, card.max_durability, card.pending_retake or card.is_sealed),
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
        pendingRetake=card.pending_retake,
        coreConcept=card.core_concept,
        codeTemplate=card.code_template,
        complexityAnalysis=card.complexity_analysis,
        useCases=card.use_cases,
        commonVariants=card.common_variants,
        typicalProblems=card.typical_problems,
        commonPitfalls=card.common_pitfalls,
        comparison=card.comparison,
        myNotes=card.my_notes,
        visualLinks=card.visual_links,
        npcId=card.npc_id,
        topic=card.topic,
        updatedAt=card.updated_at,
    )


class DomainStats(BaseModel):
    """领域统计数据模型"""
    domain: str
    total_count: int
    mastered_count: int
    sealed_count: int
    avg_durability: float


router = APIRouter(prefix="/api/cards", tags=["卡牌"])


@router.get("/", response_model=dict)
async def get_cards(
    domain: Optional[str] = Query(None, description="按领域筛选"),
    algorithm_type: Optional[str] = Query(None, description="按算法类型筛选"),
    algorithm_category: Optional[str] = Query(None, description="按算法分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词（匹配名称和算法分类）"),
    status: Optional[str] = Query(None, description="按状态筛选：normal/endangered/pending_retake"),
    keyword: Optional[str] = Query(None, description="按关键词搜索（匹配名称和内容）"),
    sort: Optional[str] = Query(None, description="排序字段：name/durability/last_reviewed"),
    order: Optional[str] = Query("asc", description="排序方向：asc/desc"),
    available: Optional[bool] = Query(None, description="仅返回未封印卡牌"),
):
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
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                (Card.name.ilike(keyword_pattern)) |
                (Card.knowledge_content.ilike(keyword_pattern))
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
        endangered_count = 0
        pending_retake_count = 0
        for card in cards:
            card_status = _compute_status(card.durability, card.max_durability, card.pending_retake or card.is_sealed)
            if status and card_status != status:
                continue
            if card_status == "endangered":
                endangered_count += 1
            elif card_status == "pending_retake":
                pending_retake_count += 1
            review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == card.id).count()
            note_count = 1 if card.note_id else 0
            result.append(_card_to_response(card, review_count, note_count))
        return {
            "cards": result,
            "endangered_count": endangered_count,
            "pending_retake_count": pending_retake_count,
        }
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
            pending_retake=card.pending_retake or False,
            core_concept=card.core_concept or "",
            code_template=card.code_template or "",
            complexity_analysis=card.complexity_analysis or "",
            use_cases=card.use_cases or "",
            common_variants=card.common_variants or "",
            typical_problems=card.typical_problems or "",
            common_pitfalls=card.common_pitfalls or "",
            comparison=card.comparison or "",
            my_notes=card.my_notes or "",
            visual_links=card.visual_links,
            npc_id=card.npc_id or 1,
            topic=card.topic or "",
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
    from algomate.data.database import Database
    from algomate.models.answer_records import AnswerRecord
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(Card).filter(Card.id == card_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail={"code": 40404, "message": f"卡牌 {card_id} 不存在"})
        
        update_data = card.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail={"code": 40002, "message": "内容未变更"})
        
        has_changes = False
        for key, value in update_data.items():
            current_val = getattr(existing, key, None)
            if current_val != value:
                has_changes = True
                break
        
        if not has_changes:
            raise HTTPException(status_code=400, detail={"code": 40002, "message": "内容未变更"})
        
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
        if card.pending_retake is not None:
            existing.pending_retake = card.pending_retake
        if card.core_concept is not None:
            existing.core_concept = card.core_concept
        if card.code_template is not None:
            existing.code_template = card.code_template
        if card.complexity_analysis is not None:
            existing.complexity_analysis = card.complexity_analysis
        if card.use_cases is not None:
            existing.use_cases = card.use_cases
        if card.common_variants is not None:
            existing.common_variants = card.common_variants
        if card.typical_problems is not None:
            existing.typical_problems = card.typical_problems
        if card.common_pitfalls is not None:
            existing.common_pitfalls = card.common_pitfalls
        if card.comparison is not None:
            existing.comparison = card.comparison
        if card.my_notes is not None:
            existing.my_notes = card.my_notes
        if card.visual_links is not None:
            existing.visual_links = card.visual_links
        if card.npc_id is not None:
            existing.npc_id = card.npc_id
        if card.topic is not None:
            existing.topic = card.topic
        
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
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail={"code": 40404, "message": f"卡牌 {card_id} 不存在"})
        
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


@router.post("/{card_id}/retake", response_model=CardResponse)
async def retake_card(card_id: int):
    from algomate.data.database import Database
    from algomate.models.answer_records import AnswerRecord
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail={"code": 40404, "message": f"卡牌 {card_id} 不存在"})
        
        if not card.pending_retake:
            raise HTTPException(status_code=400, detail={"code": 40003, "message": "该卡牌不在待重修状态"})
        
        card.pending_retake = False
        card.durability = 30
        
        session.commit()
        session.refresh(card)
        
        review_count = session.query(AnswerRecord).filter(AnswerRecord.card_id == card.id).count()
        note_count = 1 if card.note_id else 0
        
        return _card_to_response(card, review_count, note_count)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"重修卡牌失败: {str(e)}")
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

        prompts = {
            "note_content": {
                "system": """你是一个专业的算法知识编辑，擅长优化算法心得的表述。
请将用户提供的心得内容进行润色，改善语言流畅性和逻辑性。
保持原文的核心含义不变，优化表述方式，使其更清晰易懂。
直接返回润色后的内容，不要添加额外说明。""",
                "user_template": "请润色以下算法心得内容：\n{}"
            },
            "summary": {
                "system": """你是一个专业的算法知识编辑，擅长撰写精炼的摘要。
请将用户提供的摘要内容进行润色，使其更加精炼、准确、易于理解。
摘要应当简洁明了地概括核心要点，语言流畅，逻辑清晰。
直接返回润色后的摘要内容，不要添加额外说明。""",
                "user_template": "请润色以下算法知识摘要：\n{}"
            },
            "key_points": {
                "system": """你是一个专业的算法知识编辑，擅长提炼和优化关键要点。
请将用户提供的关键要点进行润色，使每个要点更加清晰、准确、简洁。
要点应当使用简短的短语或句子表达，便于快速理解和记忆。
每个要点一行，直接返回润色后的要点列表，不要添加额外说明或编号。""",
                "user_template": "请润色以下算法关键要点：\n{}"
            }
        }

        prompt_config = prompts.get(request.type.value, prompts["note_content"])
        system_prompt = prompt_config["system"]
        user_prompt = prompt_config["user_template"].format(request.content)

        result = client.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.5
        )

        return CardPolishResponse(
            polished_content=result.strip(),
            type=request.type.value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI润色失败: {str(e)}")
