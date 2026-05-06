"""
NPC模型

NPC是各领域的专家导师，引导用户修习
"""

from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

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
    
    notes = relationship("Note", back_populates="npc")
    dialogue_records = relationship("DialogueRecord", back_populates="npc")
    cards = relationship("Card", back_populates="npc")


class NPCCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=100)
    algorithm_type: str = Field(..., min_length=1, max_length=30)
    specialties: List[str] = Field(default=[], description="专长列表")
    avatar: str = Field(default="", max_length=200)
    description: str = Field(default="")
    topics: List[str] = Field(default=[])
    system_prompt: str = Field(default="")
    greeting: Optional[str] = Field(None)
    
    class Config:
        from_attributes = True


class NPCUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    algorithm_type: Optional[str] = Field(None, min_length=1, max_length=30)
    specialties: Optional[List[str]] = Field(None)
    avatar: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    topics: Optional[List[str]] = Field(None)
    system_prompt: Optional[str] = Field(None)
    greeting: Optional[str] = Field(None)
    
    class Config:
        from_attributes = True


class NPCResponse(BaseModel):
    id: int
    name: str
    title: str
    algorithm_type: str
    specialties: List[str]
    avatar: str
    description: str = ""
    topics: List[str] = []
    card_count: int = 0
    
    class Config:
        from_attributes = True


class NPCListItem(BaseModel):
    id: int
    name: str
    title: str
    algorithm_type: str
    specialties: List[str]
    avatar: str
    card_count: int = 0
    
    class Config:
        from_attributes = True


class NPCDetailResponse(BaseModel):
    id: int
    name: str
    title: str
    algorithm_type: str
    specialties: List[str]
    avatar: str
    description: str = ""
    topics: List[dict] = []
    card_count: int = 0
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/npcs", tags=["NPC"])


def parse_topics(topics_str: str) -> List[str]:
    import json
    try:
        return json.loads(topics_str) if topics_str else []
    except:
        return []


def parse_specialties(specialties_str: str) -> List[str]:
    import json
    try:
        return json.loads(specialties_str) if specialties_str else []
    except:
        return []


@router.get("/", response_model=list[NPCResponse])
async def get_npcs():
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        npcs = session.query(NPC).all()
        result = []
        for npc in npcs:
            npc_dict = {
                "id": npc.id,
                "name": npc.name,
                "title": npc.title or "",
                "algorithm_type": npc.algorithm_type or npc.domain or "",
                "specialties": parse_specialties(npc.specialties),
                "avatar": npc.avatar or "",
                "description": npc.description or "",
                "topics": parse_topics(npc.topics),
                "card_count": 0,
            }
            result.append(NPCResponse(**npc_dict))
        return result
    finally:
        session.close()


@router.get("/unlocked", response_model=list[NPCResponse])
async def get_unlocked_npcs():
    from algomate.data.database import Database
    from algomate.models.cards import Card
    from sqlalchemy import distinct
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        unlocked_domains = session.query(distinct(Card.domain)).filter(Card.is_sealed == False).all()
        unlocked_domains = [d[0] for d in unlocked_domains]
        
        npcs = session.query(NPC).filter(NPC.location.in_(unlocked_domains)).all()
        result = []
        for npc in npcs:
            npc_dict = {
                "id": npc.id,
                "name": npc.name,
                "title": npc.title or "",
                "algorithm_type": npc.algorithm_type or npc.domain or "",
                "specialties": parse_specialties(npc.specialties),
                "avatar": npc.avatar or "",
                "description": npc.description or "",
                "topics": parse_topics(npc.topics),
                "card_count": 0,
            }
            result.append(NPCResponse(**npc_dict))
        return result
    finally:
        session.close()


@router.get("/{npc_id}", response_model=NPCResponse)
async def get_npc(npc_id: int):
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        npc = session.query(NPC).filter(NPC.id == npc_id).first()
        if not npc:
            raise HTTPException(status_code=404, detail=f"NPC {npc_id} 不存在")
        
        npc_dict = {
            "id": npc.id,
            "name": npc.name,
            "title": npc.title or "",
            "algorithm_type": npc.algorithm_type or npc.domain or "",
            "specialties": parse_specialties(npc.specialties),
            "avatar": npc.avatar or "",
            "description": npc.description or "",
            "topics": parse_topics(npc.topics),
            "card_count": 0,
        }
        return NPCResponse(**npc_dict)
    finally:
        session.close()


@router.post("/", response_model=NPCResponse, status_code=201)
async def create_npc(npc: NPCCreate):
    from algomate.data.database import Database
    import json
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        new_npc = NPC(
            name=npc.name,
            title=npc.title,
            algorithm_type=npc.algorithm_type,
            specialties=json.dumps(npc.specialties, ensure_ascii=False),
            avatar=npc.avatar,
            description=npc.description,
            topics=json.dumps(npc.topics, ensure_ascii=False),
            system_prompt=npc.system_prompt,
            greeting=npc.greeting,
            domain=npc.algorithm_type,
        )
        session.add(new_npc)
        session.commit()
        session.refresh(new_npc)
        
        npc_dict = {
            "id": new_npc.id,
            "name": new_npc.name,
            "title": new_npc.title,
            "algorithm_type": new_npc.algorithm_type,
            "specialties": parse_specialties(new_npc.specialties),
            "avatar": new_npc.avatar,
            "description": new_npc.description,
            "topics": parse_topics(new_npc.topics),
            "card_count": 0,
        }
        return NPCResponse(**npc_dict)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建NPC失败: {str(e)}")
    finally:
        session.close()


@router.put("/{npc_id}", response_model=NPCResponse)
async def update_npc(npc_id: int, npc: NPCUpdate):
    from algomate.data.database import Database
    import json
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(NPC).filter(NPC.id == npc_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail=f"NPC {npc_id} 不存在")
        
        if npc.name is not None:
            existing.name = npc.name
        if npc.title is not None:
            existing.title = npc.title
        if npc.algorithm_type is not None:
            existing.algorithm_type = npc.algorithm_type
            existing.domain = npc.algorithm_type
        if npc.specialties is not None:
            existing.specialties = json.dumps(npc.specialties, ensure_ascii=False)
        if npc.avatar is not None:
            existing.avatar = npc.avatar
        if npc.description is not None:
            existing.description = npc.description
        if npc.topics is not None:
            existing.topics = json.dumps(npc.topics, ensure_ascii=False)
        if npc.system_prompt is not None:
            existing.system_prompt = npc.system_prompt
        if npc.greeting is not None:
            existing.greeting = npc.greeting
        
        session.commit()
        session.refresh(existing)
        
        npc_dict = {
            "id": existing.id,
            "name": existing.name,
            "title": existing.title,
            "algorithm_type": existing.algorithm_type,
            "specialties": parse_specialties(existing.specialties),
            "avatar": existing.avatar,
            "description": existing.description,
            "topics": parse_topics(existing.topics),
            "card_count": 0,
        }
        return NPCResponse(**npc_dict)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新NPC失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{npc_id}", status_code=204)
async def delete_npc(npc_id: int):
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        npc = session.query(NPC).filter(NPC.id == npc_id).first()
        if not npc:
            raise HTTPException(status_code=404, detail=f"NPC {npc_id} 不存在")
        
        session.delete(npc)
        session.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除NPC失败: {str(e)}")
    finally:
        session.close()
