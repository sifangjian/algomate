import json
from datetime import datetime
from typing import Optional, List, Union, Any, Dict
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
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
    

    visual_links = Column(Text, nullable=True)

    # 当前仅 "tip"（技巧卡）挂接遗忘曲线复习；题目卡/解法卡不参与复习，不创建 Card
    card_type = Column(String(10), default="tip", nullable=False)
    content = Column(Text, default="{}", nullable=False)  # 新版结构化 JSON 内容

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    review_records = relationship("ReviewRecord", back_populates="card", cascade="all, delete-orphan")

    # --- 向后兼容 @property ---
    # question_generator.py, bosses.py, review_plan_service.py 等仍用旧字段名读取

    @property
    def core_concept(self) -> str:
        data = _safe_json_parse(self.content, {})
        return data.get("one_line_definition", "") if isinstance(data, dict) else ""

    @core_concept.setter
    def core_concept(self, value: str):
        data = _safe_json_parse(self.content, {})
        if not isinstance(data, dict):
            data = {}
        data["one_line_definition"] = value
        self.content = json.dumps(data, ensure_ascii=False)

    @property
    def key_points(self) -> str:
        data = _safe_json_parse(self.content, {})
        ideas = data.get("core_ideas", []) if isinstance(data, dict) else []
        if isinstance(ideas, list):
            return "; ".join(ideas)
        return str(ideas) if ideas else ""

    @key_points.setter
    def key_points(self, value: str):
        data = _safe_json_parse(self.content, {})
        if not isinstance(data, dict):
            data = {}
        data["core_ideas"] = [v.strip() for v in value.split(";") if v.strip()]
        self.content = json.dumps(data, ensure_ascii=False)

    @property
    def parsed_content(self) -> dict:
        """解析新版 content 字段"""
        return _safe_json_parse(self.content, {})


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


# --- 新版内容结构 Pydantic 模型 ---


class TipContent(BaseModel):
    """技巧卡内容结构"""
    one_line_definition: str = Field("", description="一句话定义，≤30字")
    trigger_condition: str = Field("", description="触发条件，使用固定句式：当看到______，且要求______时，想到______")
    core_ideas: List[str] = Field(default_factory=list, description="核心思路，3-5个要点")
    complexity: str = Field("", description="复杂度，格式：时间：O(?)  空间：O(?)")
    related_problems: List[str] = Field(default_factory=list, description="关联题目，[[双链]]格式，最多3道")
    related_tips: List[str] = Field(default_factory=list, description="关联技巧，[[双链]]格式，最多2个")
    pitfall_guide: List[str] = Field(default_factory=list, description="避坑指南，最多3点")


class ProblemContent(BaseModel):
    """题目卡内容结构"""
    one_line_problem: str = Field("", description="一句话题干，≤40字")
    core_skills: List[str] = Field(default_factory=list, description="核心考点，[[双链]]格式链接技巧卡")
    solution_approach: List[str] = Field(default_factory=list, description="解法思路，分点描述")
    core_code_snippet: str = Field("", description="核心代码片段，仅保留3-5行")
    complexity: str = Field("", description="复杂度")


class CardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="卡牌名称")
    card_type: Optional[str] = Field("tip", description="卡牌类型：tip（技巧卡）/ problem（题目卡）")
    algorithm_type: Optional[str] = Field("", description="算法类型")
    difficulty: Optional[int] = Field(3, ge=1, le=5, description="难度(1-5)")
    durability: int = Field(default=80, ge=0, le=100, description="耐久度")
    content: Optional[Union[str, dict]] = Field("{}", description="新版结构化内容（JSON）")
    visual_links: Optional[str] = Field(None, description="可视化链接")

    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
    algorithm_type: Optional[str] = Field(None, description="算法类型")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="难度(1-5)")
    content: Optional[Union[str, dict]] = Field(None, description="新版结构化内容（JSON）")
    visual_links: Optional[str] = Field(None, description="可视化链接")

    class Config:
        from_attributes = True


class CardResponse(BaseModel):
    id: int
    name: str
    card_type: Optional[str] = "tip"
    algorithm_type: Optional[str] = None
    difficulty: int = 3
    durability: int
    review_level: int = 0
    next_review_date: Optional[datetime] = None
    review_count: int = 0
    last_reviewed: Optional[datetime] = None
    pending_retake: bool = False
    
    status: str
    content: Optional[dict] = None
    visual_links: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
