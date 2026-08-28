from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class TechniqueCard(Base):
    """技巧卡片 — 原子化知识沉淀，关联遗忘曲线复习

    复习状态完全由关联的 Card（durability / review_level / next_review_date）承载，
    本表不重复存储熟练度/间隔（避免与遗忘曲线双轨冲突）。
    """
    __tablename__ = "technique_cards"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, comment="关联的遗忘曲线复习卡片 ID")
    name = Column(String(200), nullable=False, comment="技巧名称（用户提炼，如 '哈希表存差值'）")
    use_cases = Column(Text, nullable=True, default="", comment="适用场景 / 触发条件（也可结构化存于 cards.content）")
    code_template = Column(Text, nullable=True, default="", comment="标准代码模板")
    memory_anchors = Column(Text, nullable=True, default="", comment="记忆锚点/关键词")
    notes = Column(Text, nullable=True, default="", comment="注意事项 / 用户补充")
    video_demo_link = Column(String(500), nullable=True, default="", comment="视频演示链接")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关联：遗忘曲线复习卡片
    review_card = relationship("Card", backref="technique_card", uselist=False, cascade="all")
    # 关联：多对多 -> 解法
    solutions = relationship("SolutionCard", secondary="solution_techniques", back_populates="techniques")