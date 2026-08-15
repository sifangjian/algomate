from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from algomate.data.database import Base


class ProblemStatus(str, enum.Enum):
    untried = "untried"
    accepted = "accepted"
    optimal = "optimal"


class ProblemCard(Base):
    """题目卡片 — 记录 LeetCode 题目的索引和状态"""
    __tablename__ = "problem_cards"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="题目全称，如 '645. 错误的集合'")
    difficulty = Column(String(20), nullable=False, default="medium", comment="难度: easy/medium/hard")
    leetcode_link = Column(String(500), nullable=True, default="", comment="原题链接")
    tags = Column(Text, nullable=True, default="[]", comment="标签 JSON 数组")
    my_status = Column(String(20), nullable=False, default="untried", comment="我的状态: untried/accepted/optimal")
    notes = Column(Text, nullable=True, default="", comment="注意事项")
    video_demo_link = Column(String(500), nullable=True, default="", comment="视频演示链接")
    related_problem_ids = Column(Text, nullable=True, default="[]", comment="关联题目ID列表 JSON数组")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关联：一个题目有多个解法
    solutions = relationship("SolutionCard", back_populates="problem", cascade="all, delete-orphan")

    # 不关联 cards 表，不参与遗忘曲线复习