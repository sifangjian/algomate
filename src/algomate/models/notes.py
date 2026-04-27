"""
笔记模型

存储用户通过NPC对话生成的笔记
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class Note(Base):
    """笔记模型

    存储用户的算法学习笔记，包含笔记内容、关联的NPC等信息。

    Attributes:
        id: 笔记唯一标识
        title: 笔记标题
        content: 笔记内容（Markdown格式）
        npc_id: 关联NPC ID（外键）
        summary: 摘要/概述
        algorithm_type: 算法类型
        difficulty: 难度等级
        mastery_level: 掌握程度 (0-100)
        review_count: 复习次数
        last_reviewed: 最近复习时间
        next_review_date: 下次复习日期
        tags: 标签（JSON数组）
        is_favorite: 是否收藏
        created_at: 创建时间
        updated_at: 更新时间
    """
    __tablename__ = "notes"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    npc_id = Column(Integer, ForeignKey("npcs.id"), nullable=True)
    summary = Column(Text, nullable=True)
    algorithm_type = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=True)
    mastery_level = Column(Integer, default=0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    last_reviewed = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, nullable=True)
    tags = Column(Text, default="[]", nullable=False)
    is_favorite = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    npc = relationship("NPC", back_populates="notes")
    cards = relationship("Card", back_populates="note")
    questions = relationship("Question", back_populates="note")
    review_records = relationship("ReviewRecord", back_populates="note")


class NoteCreate(BaseModel):
    """创建笔记的输入验证模型"""
    title: str = Field(..., min_length=1, max_length=200, description="笔记标题")
    content: str = Field(..., min_length=1, description="笔记内容（Markdown格式）")
    npc_id: Optional[int] = Field(None, description="关联NPC ID")
    summary: Optional[str] = Field(None, description="摘要/概述")
    algorithm_type: Optional[str] = Field(None, description="算法类型")
    difficulty: Optional[str] = Field(None, description="难度等级")
    tags: Optional[str] = Field("[]", description="标签（JSON数组）")

    class Config:
        from_attributes = True


class NoteUpdate(BaseModel):
    """更新笔记的输入验证模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="笔记标题")
    content: Optional[str] = Field(None, min_length=1, description="笔记内容（Markdown格式）")
    npc_id: Optional[int] = Field(None, description="关联NPC ID")
    summary: Optional[str] = Field(None, description="摘要/概述")
    algorithm_type: Optional[str] = Field(None, description="算法类型")
    difficulty: Optional[str] = Field(None, description="难度等级")
    mastery_level: Optional[int] = Field(None, ge=0, le=100, description="掌握程度")
    review_count: Optional[int] = Field(None, ge=0, description="复习次数")
    last_reviewed: Optional[datetime] = Field(None, description="最近复习时间")
    next_review_date: Optional[datetime] = Field(None, description="下次复习日期")
    tags: Optional[str] = Field(None, description="标签（JSON数组）")
    is_favorite: Optional[int] = Field(None, description="是否收藏")

    class Config:
        from_attributes = True


class NoteResponse(BaseModel):
    """返回给前端的笔记数据模型"""
    id: int
    title: str
    content: str
    npc_id: Optional[int]
    summary: Optional[str]
    algorithm_type: Optional[str]
    difficulty: Optional[str]
    mastery_level: int
    review_count: int
    last_reviewed: Optional[datetime]
    next_review_date: Optional[datetime]
    tags: str
    is_favorite: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/notes", tags=["笔记"])


@router.get("/", response_model=list[NoteResponse])
async def get_notes():
    """获取笔记列表"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        notes = session.query(Note).order_by(Note.updated_at.desc()).all()
        return notes
    finally:
        session.close()


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int):
    """获取单个笔记"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        note = session.query(Note).filter(Note.id == note_id).first()
        if not note:
            raise HTTPException(status_code=404, detail=f"笔记 {note_id} 不存在")
        return note
    finally:
        session.close()


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(note: NoteCreate):
    """创建笔记"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        if note.npc_id:
            from algomate.models.npcs import NPC
            npc = session.query(NPC).filter(NPC.id == note.npc_id).first()
            if not npc:
                raise HTTPException(status_code=404, detail=f"NPC {note.npc_id} 不存在")
        
        new_note = Note(
            title=note.title,
            content=note.content,
            npc_id=note.npc_id
        )
        session.add(new_note)
        session.commit()
        session.refresh(new_note)
        return new_note
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建笔记失败: {str(e)}")
    finally:
        session.close()


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, note: NoteUpdate):
    """更新笔记"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(Note).filter(Note.id == note_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail=f"笔记 {note_id} 不存在")
        
        if note.title is not None:
            existing.title = note.title
        if note.content is not None:
            existing.content = note.content
        if note.npc_id is not None:
            if note.npc_id:
                from algomate.models.npcs import NPC
                npc = session.query(NPC).filter(NPC.id == note.npc_id).first()
                if not npc:
                    raise HTTPException(status_code=404, detail=f"NPC {note.npc_id} 不存在")
            existing.npc_id = note.npc_id
        
        existing.updated_at = datetime.now()
        session.commit()
        session.refresh(existing)
        return existing
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新笔记失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: int):
    """删除笔记"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        note = session.query(Note).filter(Note.id == note_id).first()
        if not note:
            raise HTTPException(status_code=404, detail=f"笔记 {note_id} 不存在")
        
        session.delete(note)
        session.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除笔记失败: {str(e)}")
    finally:
        session.close()
