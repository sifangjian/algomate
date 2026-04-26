"""
NPC模型

NPC是各领域的专家导师，引导用户学习
"""

from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class NPC(Base):
    """NPC模型
    
    NPC是各领域的专家导师，引导用户学习。
    
    Attributes:
        id: NPC唯一标识
        name: NPC名称
        domain: 专长领域
        location: 所在秘境
        avatar: 头像URL
        system_prompt: 角色设定提示词
        greeting: 问候语
        topics: 可教话题列表（JSON数组）
    """
    __tablename__ = "npcs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    avatar = Column(String(500), nullable=True)
    system_prompt = Column(Text, nullable=False)
    greeting = Column(Text, nullable=True)
    topics = Column(Text, default="[]", nullable=False)
    
    notes = relationship("Note", back_populates="npc")
    dialogue_records = relationship("DialogueRecord", back_populates="npc")


class NPCCreate(BaseModel):
    """创建NPC的输入验证模型"""
    name: str = Field(..., min_length=1, max_length=100, description="NPC名称")
    domain: str = Field(..., min_length=1, max_length=100, description="专长领域")
    location: str = Field(..., min_length=1, max_length=100, description="所在秘境")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")
    system_prompt: str = Field(..., min_length=1, description="角色设定提示词")
    greeting: Optional[str] = Field(None, description="问候语")
    topics: List[str] = Field(default=[], description="可教话题列表")
    
    class Config:
        from_attributes = True


class NPCUpdate(BaseModel):
    """更新NPC的输入验证模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="NPC名称")
    domain: Optional[str] = Field(None, min_length=1, max_length=100, description="专长领域")
    location: Optional[str] = Field(None, min_length=1, max_length=100, description="所在秘境")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")
    system_prompt: Optional[str] = Field(None, min_length=1, description="角色设定提示词")
    greeting: Optional[str] = Field(None, description="问候语")
    topics: Optional[List[str]] = Field(None, description="可教话题列表")
    
    class Config:
        from_attributes = True


class NPCResponse(BaseModel):
    """返回给前端的NPC数据模型"""
    id: int
    name: str
    domain: str
    location: str
    avatar: Optional[str]
    system_prompt: str
    greeting: Optional[str]
    topics: List[str]
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/npcs", tags=["NPC"])


def parse_topics(topics_str: str) -> List[str]:
    """解析 topics JSON 字符串"""
    import json
    try:
        return json.loads(topics_str) if topics_str else []
    except:
        return []


@router.get("/", response_model=list[NPCResponse])
async def get_npcs():
    """获取NPC列表"""
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
                "domain": npc.domain,
                "location": npc.location,
                "avatar": npc.avatar,
                "system_prompt": npc.system_prompt,
                "greeting": npc.greeting,
                "topics": parse_topics(npc.topics)
            }
            result.append(NPCResponse(**npc_dict))
        return result
    finally:
        session.close()


@router.get("/unlocked", response_model=list[NPCResponse])
async def get_unlocked_npcs():
    """获取已解锁的NPC列表
    
    根据用户拥有的卡牌领域判断哪些NPC已解锁
    """
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
                "domain": npc.domain,
                "location": npc.location,
                "avatar": npc.avatar,
                "system_prompt": npc.system_prompt,
                "greeting": npc.greeting,
                "topics": parse_topics(npc.topics)
            }
            result.append(NPCResponse(**npc_dict))
        return result
    finally:
        session.close()


@router.get("/{npc_id}", response_model=NPCResponse)
async def get_npc(npc_id: int):
    """获取单个NPC详情"""
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
            "domain": npc.domain,
            "location": npc.location,
            "avatar": npc.avatar,
            "system_prompt": npc.system_prompt,
            "greeting": npc.greeting,
            "topics": parse_topics(npc.topics)
        }
        return NPCResponse(**npc_dict)
    finally:
        session.close()


@router.post("/", response_model=NPCResponse, status_code=201)
async def create_npc(npc: NPCCreate):
    """创建NPC"""
    from algomate.data.database import Database
    import json
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        new_npc = NPC(
            name=npc.name,
            domain=npc.domain,
            location=npc.location,
            avatar=npc.avatar,
            system_prompt=npc.system_prompt,
            greeting=npc.greeting,
            topics=json.dumps(npc.topics, ensure_ascii=False)
        )
        session.add(new_npc)
        session.commit()
        session.refresh(new_npc)
        
        npc_dict = {
            "id": new_npc.id,
            "name": new_npc.name,
            "domain": new_npc.domain,
            "location": new_npc.location,
            "avatar": new_npc.avatar,
            "system_prompt": new_npc.system_prompt,
            "greeting": new_npc.greeting,
            "topics": parse_topics(new_npc.topics)
        }
        return NPCResponse(**npc_dict)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建NPC失败: {str(e)}")
    finally:
        session.close()


@router.put("/{npc_id}", response_model=NPCResponse)
async def update_npc(npc_id: int, npc: NPCUpdate):
    """更新NPC"""
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
        if npc.domain is not None:
            existing.domain = npc.domain
        if npc.location is not None:
            existing.location = npc.location
        if npc.avatar is not None:
            existing.avatar = npc.avatar
        if npc.system_prompt is not None:
            existing.system_prompt = npc.system_prompt
        if npc.greeting is not None:
            existing.greeting = npc.greeting
        if npc.topics is not None:
            existing.topics = json.dumps(npc.topics, ensure_ascii=False)
        
        session.commit()
        session.refresh(existing)
        
        npc_dict = {
            "id": existing.id,
            "name": existing.name,
            "domain": existing.domain,
            "location": existing.location,
            "avatar": existing.avatar,
            "system_prompt": existing.system_prompt,
            "greeting": existing.greeting,
            "topics": parse_topics(existing.topics)
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
    """删除NPC"""
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
