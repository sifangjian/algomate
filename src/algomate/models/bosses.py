from typing import Optional
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from algomate.data.database import Base


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Boss(Base):
    __tablename__ = "bosses"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)
    weakness_type = Column(String(30), nullable=False)
    npc_id = Column(Integer, ForeignKey("npcs.id"), nullable=False)
    description = Column(Text, nullable=False)

    npc = relationship("NPC", backref="bosses")
    answer_records = relationship("AnswerRecord", back_populates="boss")


class BossCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    difficulty: Difficulty = Field(...)
    weakness_type: str = Field(..., min_length=1, max_length=30)
    npc_id: int = Field(...)
    description: str = Field(..., min_length=1)

    class Config:
        from_attributes = True


class BossUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    difficulty: Optional[Difficulty] = Field(None)
    weakness_type: Optional[str] = Field(None, min_length=1, max_length=30)
    npc_id: Optional[int] = Field(None)
    description: Optional[str] = Field(None, min_length=1)

    class Config:
        from_attributes = True


class BossResponse(BaseModel):
    id: int
    name: str
    difficulty: str
    weakness_type: str
    npc_id: int
    description: str

    class Config:
        from_attributes = True
