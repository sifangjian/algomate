from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class BattleRecord(Base):
    __tablename__ = "battle_records"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    boss_id = Column(Integer, ForeignKey("bosses.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    question_type = Column(String(20), nullable=False)
    is_weakness_card = Column(Boolean, nullable=False, default=False)
    is_victory = Column(Boolean, nullable=False)
    answer = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    durability_change = Column(Integer, nullable=False, default=0)
    question_content = Column(Text, nullable=True)
    question_options = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    leetcode_url = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='in_progress')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    boss = relationship("Boss", backref="battle_records")
    card = relationship("Card", backref="battle_records")
