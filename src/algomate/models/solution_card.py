from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class SolutionCard(Base):
    """解法卡片 — 连接题目与技巧的中间层"""
    __tablename__ = "solution_cards"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, ForeignKey("problem_cards.id", ondelete="CASCADE"), nullable=False, comment="关联的题目 ID")
    name = Column(String(200), nullable=False, comment="解法名称，如 '哈希表法'")
    language = Column(String(50), nullable=True, default="", comment="编程语言，如 python/javascript/cpp，来自 LeetCode 导入")
    is_optimal = Column(Integer, nullable=False, default=0, comment="是否最优解: 0/1")
    time_complexity = Column(String(100), nullable=True, default="", comment="时间复杂度")
    space_complexity = Column(String(100), nullable=True, default="", comment="空间复杂度")
    breakthrough = Column(Text, nullable=True, default="", comment="突破口（针对本解法的具体切入）")
    approach = Column(Text, nullable=True, default="", comment="详细思路 Markdown")
    code = Column(Text, nullable=True, default="", comment="代码块")
    pitfalls = Column(Text, nullable=True, default="[]", comment="易错点 JSON 数组")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关联：属于哪个题目
    problem = relationship("ProblemCard", back_populates="solutions")
    # 关联：多对多 -> 技巧
    techniques = relationship("TechniqueCard", secondary="solution_techniques", back_populates="solutions")

    # 不关联 cards 表，不参与遗忘曲线复习