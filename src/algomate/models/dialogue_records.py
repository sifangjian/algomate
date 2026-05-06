"""
对话记录模型

记录NPC对话历史
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

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


class DialogueMessage(BaseModel):
    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = Field(None, description="时间戳")


class DialogueRecordCreate(BaseModel):
    npc_id: int = Field(..., description="关联NPC ID")
    dialogue_content: List[DialogueMessage] = Field(..., description="对话内容")
    generated_cards: List[int] = Field(default=[], description="生成的卡牌ID列表")
    topic: Optional[str] = Field(None, description="对话主题")
    status: Optional[str] = Field(default="active", description="对话状态")
    card_id: Optional[int] = Field(None, description="关联卡牌ID")

    class Config:
        from_attributes = True


class DialogueRecordResponse(BaseModel):
    id: int
    npc_id: int
    dialogue_content: List[dict]
    generated_cards: List[int]
    created_at: datetime
    topic: Optional[str] = None
    status: Optional[str] = "active"
    last_active_at: Optional[datetime] = None
    card_id: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/dialogues", tags=["对话记录"])


def parse_dialogue_content(content_str: str) -> List[dict]:
    """解析 dialogue_content JSON 字符串"""
    import json
    try:
        return json.loads(content_str) if content_str else []
    except:
        return []


def parse_generated_cards(cards_str: str) -> List[int]:
    """解析 generated_cards JSON 字符串"""
    import json
    try:
        return json.loads(cards_str) if cards_str else []
    except:
        return []


@router.get("/", response_model=list[DialogueRecordResponse])
async def get_dialogue_records():
    """获取对话记录列表"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        records = session.query(DialogueRecord).order_by(DialogueRecord.created_at.desc()).all()
        result = []
        for record in records:
            record_dict = {
                "id": record.id,
                "npc_id": record.npc_id,
                "dialogue_content": parse_dialogue_content(record.dialogue_content),
                "generated_cards": parse_generated_cards(record.generated_cards),
                "created_at": record.created_at,
                "topic": record.topic,
                "status": record.status,
                "last_active_at": record.last_active_at,
                "card_id": record.card_id,
                "updated_at": record.updated_at,
            }
            result.append(DialogueRecordResponse(**record_dict))
        return result
    finally:
        session.close()


@router.get("/{record_id}", response_model=DialogueRecordResponse)
async def get_dialogue_record(record_id: int):
    """获取单个对话详情"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"对话记录 {record_id} 不存在")
        
        record_dict = {
            "id": record.id,
            "npc_id": record.npc_id,
            "dialogue_content": parse_dialogue_content(record.dialogue_content),
            "generated_cards": parse_generated_cards(record.generated_cards),
            "created_at": record.created_at,
            "topic": record.topic,
            "status": record.status,
            "last_active_at": record.last_active_at,
            "card_id": record.card_id,
            "updated_at": record.updated_at,
        }
        return DialogueRecordResponse(**record_dict)
    finally:
        session.close()


@router.post("/", response_model=DialogueRecordResponse, status_code=201)
async def create_dialogue_record(record: DialogueRecordCreate):
    from algomate.data.database import Database
    import json

    db = Database.get_instance()
    session = db.get_session()
    try:
        from algomate.models.npcs import NPC
        npc = session.query(NPC).filter(NPC.id == record.npc_id).first()
        if not npc:
            raise HTTPException(status_code=404, detail=f"NPC {record.npc_id} 不存在")

        for card_id in record.generated_cards:
            from algomate.models.cards import Card
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                raise HTTPException(status_code=404, detail=f"卡牌 {card_id} 不存在")

        dialogue_content_list = [msg.model_dump() for msg in record.dialogue_content]

        new_record = DialogueRecord(
            npc_id=record.npc_id,
            dialogue_content=json.dumps(dialogue_content_list, ensure_ascii=False, default=str),
            generated_cards=json.dumps(record.generated_cards),
            topic=record.topic,
            status=record.status or "active",
            card_id=record.card_id,
        )
        session.add(new_record)
        session.commit()
        session.refresh(new_record)

        record_dict = {
            "id": new_record.id,
            "npc_id": new_record.npc_id,
            "dialogue_content": parse_dialogue_content(new_record.dialogue_content),
            "generated_cards": parse_generated_cards(new_record.generated_cards),
            "created_at": new_record.created_at,
            "topic": new_record.topic,
            "status": new_record.status,
            "last_active_at": new_record.last_active_at,
            "card_id": new_record.card_id,
            "updated_at": new_record.updated_at,
        }
        return DialogueRecordResponse(**record_dict)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建对话记录失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{record_id}", status_code=204)
async def delete_dialogue_record(record_id: int):
    """删除对话记录"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"对话记录 {record_id} 不存在")
        
        session.delete(record)
        session.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除对话记录失败: {str(e)}")
    finally:
        session.close()
