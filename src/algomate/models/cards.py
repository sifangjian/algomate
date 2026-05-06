from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from algomate.data.database import Base


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    algorithm_type = Column(String(100), nullable=False, default="")
    durability = Column(Integer, default=80, nullable=False)
    review_level = Column(Integer, default=0, nullable=False)
    next_review_date = Column(DateTime, nullable=True)
    review_count = Column(Integer, default=0, nullable=False)
    last_reviewed = Column(DateTime, nullable=True)
    pending_retake = Column(Boolean, default=False, nullable=False)
    npc_id = Column(Integer, ForeignKey("npcs.id"), nullable=False, default=1)
    topic = Column(String(100), nullable=False, default="")
    core_concept = Column(Text, default="", nullable=False)
    key_points = Column(Text, default="[]", nullable=False)
    code_template = Column(Text, default="", nullable=False)
    complexity_analysis = Column(Text, default="", nullable=False)
    use_cases = Column(Text, default="", nullable=False)
    common_variants = Column(Text, default="", nullable=False)
    typical_problems = Column(Text, default="", nullable=False)
    common_pitfalls = Column(Text, default="", nullable=False)
    comparison = Column(Text, default="", nullable=False)
    my_notes = Column(Text, default="", nullable=False)
    visual_links = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    questions = relationship("Question", back_populates="card")
    answer_records = relationship("AnswerRecord", back_populates="card")
    review_records = relationship("ReviewRecord", back_populates="card")
    npc = relationship("NPC", back_populates="cards")
    dialogue_records = relationship("DialogueRecord", back_populates="card")


class CardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="卡牌名称")
    algorithm_type: Optional[str] = Field("", description="算法类型")
    durability: int = Field(default=80, ge=0, le=100, description="耐久度")
    npc_id: Optional[int] = Field(1, description="关联NPC ID")
    topic: Optional[str] = Field("", description="主题")
    core_concept: Optional[str] = Field("", description="核心概念")
    key_points: Optional[str] = Field("[]", description="关键要点")
    code_template: Optional[str] = Field("", description="代码模板")
    complexity_analysis: Optional[str] = Field("", description="复杂度分析")
    use_cases: Optional[str] = Field("", description="使用场景")
    common_variants: Optional[str] = Field("", description="常见变体")
    typical_problems: Optional[str] = Field("", description="典型题目")
    common_pitfalls: Optional[str] = Field("", description="常见陷阱")
    comparison: Optional[str] = Field("", description="对比分析")
    my_notes: Optional[str] = Field("", description="个人笔记")
    visual_links: Optional[str] = Field(None, description="可视化链接")

    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
    core_concept: Optional[str] = Field(None, description="核心概念")
    key_points: Optional[str] = Field(None, description="关键要点")
    code_template: Optional[str] = Field(None, description="代码模板")
    complexity_analysis: Optional[str] = Field(None, description="复杂度分析")
    use_cases: Optional[str] = Field(None, description="使用场景")
    common_variants: Optional[str] = Field(None, description="常见变体")
    typical_problems: Optional[str] = Field(None, description="典型题目")
    common_pitfalls: Optional[str] = Field(None, description="常见陷阱")
    comparison: Optional[str] = Field(None, description="对比分析")
    my_notes: Optional[str] = Field(None, description="个人笔记")
    visual_links: Optional[str] = Field(None, description="可视化链接")

    class Config:
        from_attributes = True


class CardResponse(BaseModel):
    id: int
    name: str
    algorithm_type: Optional[str] = None
    durability: int
    review_level: int = 0
    next_review_date: Optional[datetime] = None
    review_count: int = 0
    last_reviewed: Optional[datetime] = None
    pending_retake: bool = False
    npc_id: Optional[int] = None
    topic: Optional[str] = None
    status: str
    core_concept: Optional[str] = None
    key_points: Optional[str] = None
    code_template: Optional[str] = None
    complexity_analysis: Optional[str] = None
    use_cases: Optional[str] = None
    common_variants: Optional[str] = None
    typical_problems: Optional[str] = None
    common_pitfalls: Optional[str] = None
    comparison: Optional[str] = None
    my_notes: Optional[str] = None
    visual_links: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
