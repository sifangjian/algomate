"""
试炼模型

存储算法试炼及答案
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    question_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    options = Column(Text, default="[]", nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, default="", nullable=False)
    difficulty = Column(String(20), default="medium", nullable=False)
    leetcode_url = Column(String(500), default="", nullable=False)
    leetcode_title = Column(String(200), default="", nullable=False)
    leetcode_difficulty = Column(String(20), default="", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    card = relationship("Card", back_populates="questions")
