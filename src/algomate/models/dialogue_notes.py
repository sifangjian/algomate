from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from algomate.data.database import Base


class DialogueNote(Base):
    __tablename__ = "dialogue_notes"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    dialogue_id = Column(Integer, ForeignKey("dialogue_records.id"), nullable=False)
    content = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    dialogue = relationship("DialogueRecord", back_populates="notes")


class DialogueNoteCreate(BaseModel):
    dialogue_id: int = Field(..., description="关联对话ID")
    content: str = Field(default="", description="笔记内容")

    class Config:
        from_attributes = True


class DialogueNoteResponse(BaseModel):
    id: int
    dialogue_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
