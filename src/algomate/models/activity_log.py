from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from pydantic import BaseModel, Field
from algomate.data.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20), nullable=False, default="manual_note")  # auto_create, auto_view, auto_update, manual_note
    card_type = Column(String(20), nullable=True)  # problem, solution, technique
    card_name = Column(String(200), nullable=True)
    card_id = Column(Integer, nullable=True)
    content = Column(Text, nullable=False, default="")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)


class ActivityLogCreate(BaseModel):
    content: str = Field(..., min_length=1, description="日志内容")


class ActivityLogResponse(BaseModel):
    id: int
    type: str
    card_type: Optional[str] = None
    card_name: Optional[str] = None
    card_id: Optional[int] = None
    content: str
    details: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True