"""
应战记录模型

记录用户每次应战的结果，用于薄弱点分析
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class AnswerRecord(Base):
    """应战记录模型

    记录用户每次应战的结果，用于薄弱点分析。

    Attributes:
        id: 记录唯一标识
        boss_id: 关联Boss ID（外键）
        card_id: 使用的卡牌ID（外键）
        user_answer: 用户答案
        is_correct: 是否正确
        feedback: AI反馈
        answered_at: 应战时间
    """
    __tablename__ = "answer_records"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    boss_id = Column(Integer, ForeignKey("bosses.id"), nullable=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    feedback = Column(Text, default="", nullable=False)
    leetcode_url = Column(String(500), default="", nullable=False)
    answered_at = Column(DateTime, default=datetime.now, nullable=False)

    boss = relationship("Boss", back_populates="answer_records")
    card = relationship("Card", back_populates="answer_records")
