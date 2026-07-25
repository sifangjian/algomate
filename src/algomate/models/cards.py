import json
from datetime import datetime
from typing import Optional, List, Union
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from algomate.data.database import Base


def _safe_json_parse(value: str, default=None):
    try:
        return json.loads(value) if value else default
    except (json.JSONDecodeError, TypeError):
        return default


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    algorithm_type = Column(String(100), nullable=False, default="")
    difficulty = Column(Integer, default=3, nullable=False)
    durability = Column(Integer, default=80, nullable=False)
    review_level = Column(Integer, default=0, nullable=False)
    next_review_date = Column(DateTime, nullable=True)
    review_count = Column(Integer, default=0, nullable=False)
    last_reviewed = Column(DateTime, nullable=True)
    pending_retake = Column(Boolean, default=False, nullable=False)
    npc_id = Column(Integer, ForeignKey("npcs.id"), nullable=False, default=1)
    dialogue_id = Column(Integer, ForeignKey("dialogue_records.id"), nullable=True)
    topic = Column(String(100), nullable=False, default="")

    # 三层结构化内容（JSON Text）
    basic_content = Column(Text, default="{}", nullable=False)
    practical_content = Column(Text, default="{}", nullable=False)
    advanced_content = Column(Text, default="{}", nullable=False)

    my_notes = Column(Text, default="", nullable=False)
    visual_links = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    questions = relationship("Question", back_populates="card", cascade="all, delete-orphan")
    answer_records = relationship("AnswerRecord", back_populates="card", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="card", cascade="all, delete-orphan")
    npc = relationship("NPC", back_populates="cards")
    dialogue = relationship("DialogueRecord", foreign_keys=[dialogue_id])
    dialogue_records = relationship("DialogueRecord", back_populates="card", cascade="all, delete-orphan", foreign_keys="[DialogueRecord.card_id]")
    battle_records = relationship("BattleRecord", back_populates="card", cascade="all, delete-orphan")
    outgoing_links = relationship("CardLink", foreign_keys="[CardLink.source_card_id]", cascade="all, delete-orphan", back_populates="source_card")
    incoming_links = relationship("CardLink", foreign_keys="[CardLink.target_card_id]", cascade="all, delete-orphan", back_populates="target_card")

    # --- 向后兼容 @property ---
    # question_generator.py, bosses.py, review_plan_service.py 等仍用旧字段名读取

    @property
    def core_concept(self) -> str:
        data = _safe_json_parse(self.basic_content, {})
        return data.get("concept_definition", "") if isinstance(data, dict) else ""

    @core_concept.setter
    def core_concept(self, value: str):
        data = _safe_json_parse(self.basic_content, {})
        if not isinstance(data, dict):
            data = {}
        data["concept_definition"] = value
        self.basic_content = json.dumps(data, ensure_ascii=False)

    @property
    def key_points(self) -> str:
        data = _safe_json_parse(self.basic_content, {})
        return data.get("features", "") if isinstance(data, dict) else ""

    @key_points.setter
    def key_points(self, value: str):
        data = _safe_json_parse(self.basic_content, {})
        if not isinstance(data, dict):
            data = {}
        data["features"] = value
        self.basic_content = json.dumps(data, ensure_ascii=False)


class BasicContent(BaseModel):
    concept_definition: str = Field("", description="概念定义")
    features: str = Field("", description="特点")
    confusing_concepts: str = Field("", description="易混淆概念")


class Solution(BaseModel):
    name: str = Field("解法", description="解法名称")
    code: str = Field("", description="解法代码")
    principle: str = Field("", description="原理说明")
    complexity: str = Field("", description="时间/空间复杂度")


class Example(BaseModel):
    title: str = Field("例题", description="例题标题")
    problem: str = Field("", description="题目描述")
    solutions: List[Solution] = Field(default_factory=list, description="解法列表")


class PracticalContent(BaseModel):
    examples: List[Example] = Field(default_factory=list, description="例题列表")
    applicable_scenarios: str = Field("", description="适用场景")
    precautions: str = Field("", description="注意事项")


class AdvancedContent(BaseModel):
    common_mistakes: str = Field("", description="易错点")
    extensions: str = Field("", description="拓展方向")
    advanced_solutions: str = Field("", description="高级解法")


def _normalize_content(value: Union[str, dict, None], model_class) -> str:
    if value is None:
        return "{}"
    if isinstance(value, str):
        parsed = _safe_json_parse(value)
        if parsed is not None:
            return value
        return "{}"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return "{}"


class CardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="卡牌名称")
    algorithm_type: Optional[str] = Field("", description="算法类型")
    durability: int = Field(default=80, ge=0, le=100, description="耐久度")
    npc_id: Optional[int] = Field(1, description="关联NPC ID")
    dialogue_id: Optional[int] = Field(None, description="关联对话ID")
    topic: Optional[str] = Field("", description="主题")
    basic_content: Optional[Union[str, dict]] = Field("{}", description="基础内容（JSON）")
    practical_content: Optional[Union[str, dict]] = Field("{}", description="实战内容（JSON）")
    advanced_content: Optional[Union[str, dict]] = Field("{}", description="进阶内容（JSON）")
    my_notes: Optional[str] = Field("", description="个人笔记")
    visual_links: Optional[str] = Field(None, description="可视化链接")
    prerequisites: Optional[List[str]] = Field(None, description="前置算法节点列表")

    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
    algorithm_type: Optional[str] = Field(None, description="算法类型")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="难度(1-5)")
    basic_content: Optional[Union[str, dict]] = Field(None, description="基础内容（JSON）")
    practical_content: Optional[Union[str, dict]] = Field(None, description="实战内容（JSON）")
    advanced_content: Optional[Union[str, dict]] = Field(None, description="进阶内容（JSON）")
    my_notes: Optional[str] = Field(None, description="个人笔记")
    visual_links: Optional[str] = Field(None, description="可视化链接")

    class Config:
        from_attributes = True


class CardResponse(BaseModel):
    id: int
    name: str
    algorithm_type: Optional[str] = None
    difficulty: int = 3
    durability: int
    review_level: int = 0
    next_review_date: Optional[datetime] = None
    review_count: int = 0
    last_reviewed: Optional[datetime] = None
    pending_retake: bool = False
    npc_id: Optional[int] = None
    dialogue_id: Optional[int] = None
    topic: Optional[str] = None
    status: str
    basic_content: Optional[dict] = None
    practical_content: Optional[dict] = None
    advanced_content: Optional[dict] = None
    my_notes: Optional[str] = None
    visual_links: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
