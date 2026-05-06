from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from algomate.data.database import Base


class DialogueMessageRecord(Base):
    __tablename__ = "dialogue_messages"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    dialogue_id = Column(Integer, ForeignKey("dialogue_records.id"), nullable=False)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    dialogue = relationship("DialogueRecord", back_populates="messages")


class DialogueMessageCreate(BaseModel):
    dialogue_id: int = Field(..., description="关联对话ID")
    role: str = Field(..., description="角色：user/assistant/system")
    content: str = Field(..., description="消息内容")

    class Config:
        from_attributes = True


class DialogueMessageResponse(BaseModel):
    id: int
    dialogue_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
