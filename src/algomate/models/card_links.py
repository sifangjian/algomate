from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional

from algomate.data.database import Base


class CardLink(Base):
    __tablename__ = "card_links"
    __table_args__ = (
        UniqueConstraint("source_card_id", "target_card_id", "link_type", name="uq_card_link"),
        {'extend_existing': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    target_card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    link_type = Column(String(50), default="related", nullable=False)
    source_keyword = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    source_card = relationship("Card", foreign_keys=[source_card_id], back_populates="outgoing_links")
    target_card = relationship("Card", foreign_keys=[target_card_id], back_populates="incoming_links")


class LinkCreate(BaseModel):
    target_card_id: int = Field(..., description="目标卡牌ID")
    link_type: str = Field("related", description="链接类型: related/prerequisite/comparison/keyword")
    source_keyword: Optional[str] = Field(None, description="触发链接的关键词")


class LinkResponse(BaseModel):
    id: int
    source_card_id: int
    target_card_id: int
    link_type: str
    source_keyword: Optional[str] = None
    target_card_name: Optional[str] = None
    source_card_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
