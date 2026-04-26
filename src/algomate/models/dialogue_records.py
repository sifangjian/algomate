"""
对话记录模型

记录NPC对话历史
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class DialogueRecord(Base):
    """对话记录模型
    
    记录NPC对话历史。
    
    Attributes:
        id: 记录唯一标识
        npc_id: 关联NPC ID（外键）
        dialogue_content: 对话内容（JSON数组）
        generated_cards: 生成的卡牌ID列表（JSON）
        created_at: 创建时间
    """
    __tablename__ = "dialogue_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    npc_id = Column(Integer, ForeignKey("npcs.id"), nullable=False)
    dialogue_content = Column(Text, default="[]", nullable=False)
    generated_cards = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    npc: Optional["NPC"] = relationship("NPC", back_populates="dialogue_records")


class DialogueMessage(BaseModel):
    """对话消息模型"""
    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = Field(None, description="时间戳")


class DialogueRecordCreate(BaseModel):
    """创建对话记录的输入验证模型"""
    npc_id: int = Field(..., description="关联NPC ID")
    dialogue_content: List[DialogueMessage] = Field(..., description="对话内容")
    generated_cards: List[int] = Field(default=[], description="生成的卡牌ID列表")
    
    class Config:
        from_attributes = True


class DialogueRecordResponse(BaseModel):
    """返回给前端的对话记录数据模型"""
    id: int
    npc_id: int
    dialogue_content: List[dict]
    generated_cards: List[int]
    created_at: datetime
    
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
                "created_at": record.created_at
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
            "created_at": record.created_at
        }
        return DialogueRecordResponse(**record_dict)
    finally:
        session.close()


@router.post("/", response_model=DialogueRecordResponse, status_code=201)
async def create_dialogue_record(record: DialogueRecordCreate):
    """创建对话记录（对话结束时）"""
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
            generated_cards=json.dumps(record.generated_cards)
        )
        session.add(new_record)
        session.commit()
        session.refresh(new_record)
        
        record_dict = {
            "id": new_record.id,
            "npc_id": new_record.npc_id,
            "dialogue_content": parse_dialogue_content(new_record.dialogue_content),
            "generated_cards": parse_generated_cards(new_record.generated_cards),
            "created_at": new_record.created_at
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
