"""
对话记录模型

记录NPC对话历史
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class DialogueRecord(Base):
    __tablename__ = "dialogue_records"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    npc_id = Column(Integer, ForeignKey("npcs.id"), nullable=False)
    dialogue_content = Column(Text, default="[]", nullable=False)
    generated_cards = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    topic = Column(String(100), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    last_active_at = Column(DateTime, nullable=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    npc = relationship("NPC", back_populates="dialogue_records")
    messages = relationship("DialogueMessageRecord", back_populates="dialogue", cascade="all, delete-orphan")
    notes = relationship("DialogueNote", back_populates="dialogue", cascade="all, delete-orphan")
    card = relationship("Card", back_populates="dialogue_records")
