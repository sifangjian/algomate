from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class ProblemCard(Base):
    """题目卡片 — 记录 LeetCode 题目的索引与突破口（本题要解决的核心问题）

    前置：用户已在 LeetCode AC 才导入，因此不记录"是否通过"类状态。
    是否最优解属于解法维度（见 SolutionCard.is_optimal），不在题卡。
    """
    __tablename__ = "problem_cards"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="题目全称，如 '645. 错误的集合'")
    leetcode_slug = Column(String(200), nullable=True, default=None, index=True, comment="LeetCode 题目唯一标识(slug)，用于一键导入去重")
    difficulty = Column(String(20), nullable=False, default="medium", comment="难度: easy/medium/hard")
    leetcode_link = Column(String(500), nullable=True, default="", comment="原题链接")
    tags = Column(Text, nullable=True, default="[]", comment="标签 JSON 数组（LeetCode 算法分类属性，用于归类检索）")
    breakthrough = Column(Text, nullable=True, default="", comment="突破口：本题要解决的核心问题（由用户手动写）")
    is_optimal = Column(Integer, nullable=False, default=0, comment="是否已有最优解: 0/1（属于解法维度，题卡仅作汇总标记）")
    variants = Column(Text, nullable=True, default="[]", comment="同考点变体题 slug 列表 JSON 数组（用于变体题复习法，如 ['two-sum','3sum']）")
    video_demo_link = Column(String(500), nullable=True, default="", comment="视频演示链接")
    related_problem_ids = Column(Text, nullable=True, default="[]", comment="关联题目ID列表 JSON数组")
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True, default=None, comment="关联的复习卡(Card) ID，题卡作为修炼主单元时挂接遗忘曲线复习状态")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关联：一个题目有多个解法
    solutions = relationship("SolutionCard", back_populates="problem", cascade="all, delete-orphan")

    # 不关联 cards 表，不参与遗忘曲线复习