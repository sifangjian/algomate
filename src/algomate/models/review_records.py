"""
修炼记录模型

记录用户的修炼活动，用于追踪修炼历史和效果
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class ReviewRecord(Base):
    """修炼记录模型

    记录用户的修炼活动，用于追踪修炼历史和效果。

    Attributes:
        id: 记录唯一标识
        card_id: 关联卡牌ID（外键）
        review_date: 修炼日期
        status: 修炼状态（pending/completed/skipped）
        score: 本次修炼战绩
    """
    __tablename__ = "review_records"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    review_date = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    score = Column(Integer, nullable=True)
    review_type = Column(String(20), default="content_review", nullable=False)
    completed_at = Column(DateTime, nullable=True)
    durability_before = Column(Integer, nullable=True)
    durability_after = Column(Integer, nullable=True)
    review_level_before = Column(Integer, nullable=True)
    review_level_after = Column(Integer, nullable=True)

    card = relationship("Card", back_populates="review_records")
