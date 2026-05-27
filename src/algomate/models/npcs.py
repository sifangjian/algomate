"""
NPC模型

NPC是各领域的专家导师，引导用户修习
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from algomate.data.database import Base


class NPC(Base):
    __tablename__ = "npcs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False, default="")
    algorithm_type = Column(String(30), nullable=False, default="")
    specialties = Column(String(200), nullable=False, default="[]")
    avatar = Column(String(200), nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    topics = Column(Text, default="[]", nullable=False)
    domain = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    system_prompt = Column(Text, nullable=False, default="")
    greeting = Column(Text, nullable=True)

    dialogue_records = relationship("DialogueRecord", back_populates="npc")
    cards = relationship("Card", back_populates="npc")
