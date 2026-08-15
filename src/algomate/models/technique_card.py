from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class TechniqueCard(Base):
    """技巧卡片 — 原子化知识沉淀，关联遗忘曲线复习"""
    __tablename__ = "technique_cards"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, comment="关联的遗忘曲线复习卡片 ID")
    name = Column(String(200), nullable=False, comment="技巧名称")
    category = Column(String(50), nullable=False, default="algorithm", comment="分类: data_structure/algorithm/template")
    use_cases = Column(Text, nullable=True, default="", comment="适用场景")
    code_template = Column(Text, nullable=True, default="", comment="标准代码模板")
    memory_anchors = Column(Text, nullable=True, default="", comment="记忆锚点/关键词")
    proficiency = Column(Integer, nullable=False, default=1, comment="熟练度 1-5")
    review_interval = Column(Integer, nullable=False, default=1, comment="复习间隔天数")
    notes = Column(Text, nullable=True, default="", comment="注意事项")
    video_demo_link = Column(String(500), nullable=True, default="", comment="视频演示链接")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关联：遗忘曲线复习卡片
    review_card = relationship("Card", backref="technique_card", uselist=False, cascade="all")
    # 关联：多对多 -> 解法
    solutions = relationship("SolutionCard", secondary="solution_techniques", back_populates="techniques")