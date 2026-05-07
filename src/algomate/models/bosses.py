from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

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


router = APIRouter(prefix="/api/bosses", tags=["Boss"])


@router.get("/", response_model=list[BossResponse])
async def get_bosses():
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        bosses = session.query(Boss).all()
        return [BossResponse(
            id=b.id,
            name=b.name,
            difficulty=b.difficulty,
            weakness_type=b.weakness_type,
            npc_id=b.npc_id,
            description=b.description,
        ) for b in bosses]
    finally:
        session.close()


@router.get("/{boss_id}", response_model=BossResponse)
async def get_boss(boss_id: int):
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        boss = session.query(Boss).filter(Boss.id == boss_id).first()
        if not boss:
            raise HTTPException(status_code=404, detail=f"Boss {boss_id} 不存在")
        return BossResponse(
            id=boss.id,
            name=boss.name,
            difficulty=boss.difficulty,
            weakness_type=boss.weakness_type,
            npc_id=boss.npc_id,
            description=boss.description,
        )
    finally:
        session.close()


@router.post("/", response_model=BossResponse, status_code=201)
async def create_boss(boss: BossCreate):
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        new_boss = Boss(
            name=boss.name,
            difficulty=boss.difficulty.value,
            weakness_type=boss.weakness_type,
            npc_id=boss.npc_id,
            description=boss.description,
        )
        session.add(new_boss)
        session.commit()
        session.refresh(new_boss)
        return BossResponse(
            id=new_boss.id,
            name=new_boss.name,
            difficulty=new_boss.difficulty,
            weakness_type=new_boss.weakness_type,
            npc_id=new_boss.npc_id,
            description=new_boss.description,
        )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建Boss失败: {str(e)}")
    finally:
        session.close()


@router.put("/{boss_id}", response_model=BossResponse)
async def update_boss(boss_id: int, boss: BossUpdate):
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(Boss).filter(Boss.id == boss_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Boss {boss_id} 不存在")

        if boss.name is not None:
            existing.name = boss.name
        if boss.difficulty is not None:
            existing.difficulty = boss.difficulty.value
        if boss.weakness_type is not None:
            existing.weakness_type = boss.weakness_type
        if boss.npc_id is not None:
            existing.npc_id = boss.npc_id
        if boss.description is not None:
            existing.description = boss.description

        session.commit()
        session.refresh(existing)
        return BossResponse(
            id=existing.id,
            name=existing.name,
            difficulty=existing.difficulty,
            weakness_type=existing.weakness_type,
            npc_id=existing.npc_id,
            description=existing.description,
        )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新Boss失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{boss_id}", status_code=204)
async def delete_boss(boss_id: int):
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        boss = session.query(Boss).filter(Boss.id == boss_id).first()
        if not boss:
            raise HTTPException(status_code=404, detail=f"Boss {boss_id} 不存在")

        session.delete(boss)
        session.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除Boss失败: {str(e)}")
    finally:
        session.close()
