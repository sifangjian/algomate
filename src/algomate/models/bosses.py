"""
Boss模型

Boss是基于用户卡牌生成的算法挑战
"""

from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class Difficulty(str, Enum):
    """难度枚举"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BossSource(str, Enum):
    """Boss来源枚举"""
    LEETCODE = "leetcode"
    AI_GENERATED = "ai_generated"


class Boss(Base):
    """Boss模型
    
    Boss是基于用户卡牌生成的算法挑战。
    
    Attributes:
        id: Boss唯一标识
        name: Boss名称
        difficulty: 难度等级
        weakness_domains: 弱点领域列表（JSON数组）
        description: 描述（游戏化包装的故事背景）
        question_id: 关联题目ID（外键）
        source: leetcode / ai_generated
        drop_rate: 掉宝率 0.0-1.0
    """
    __tablename__ = "bosses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)
    weakness_domains = Column(Text, default="[]", nullable=False)
    description = Column(Text, nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    source = Column(String(50), nullable=False)
    drop_rate = Column(Float, default=0.5, nullable=False)
    
    question: Optional["Question"] = relationship("Question", back_populates="bosses")
    answer_records: List["AnswerRecord"] = relationship("AnswerRecord", back_populates="boss")


class BossCreate(BaseModel):
    """创建Boss的输入验证模型"""
    name: str = Field(..., min_length=1, max_length=200, description="Boss名称")
    difficulty: Difficulty = Field(..., description="难度等级")
    weakness_domains: List[str] = Field(default=[], description="弱点领域列表")
    description: str = Field(..., min_length=1, description="描述")
    question_id: Optional[int] = Field(None, description="关联题目ID")
    source: BossSource = Field(..., description="来源")
    drop_rate: float = Field(default=0.5, ge=0.0, le=1.0, description="掉宝率")
    
    class Config:
        from_attributes = True


class BossUpdate(BaseModel):
    """更新Boss的输入验证模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Boss名称")
    difficulty: Optional[Difficulty] = Field(None, description="难度等级")
    weakness_domains: Optional[List[str]] = Field(None, description="弱点领域列表")
    description: Optional[str] = Field(None, min_length=1, description="描述")
    question_id: Optional[int] = Field(None, description="关联题目ID")
    source: Optional[BossSource] = Field(None, description="来源")
    drop_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="掉宝率")
    
    class Config:
        from_attributes = True


class BossResponse(BaseModel):
    """返回给前端的Boss数据模型"""
    id: int
    name: str
    difficulty: str
    weakness_domains: List[str]
    description: str
    question_id: Optional[int]
    source: str
    drop_rate: float
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/bosses", tags=["Boss"])


def parse_weakness_domains(domains_str: str) -> List[str]:
    """解析 weakness_domains JSON 字符串"""
    import json
    try:
        return json.loads(domains_str) if domains_str else []
    except:
        return []


@router.get("/", response_model=list[BossResponse])
async def get_bosses():
    """获取Boss列表"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        bosses = session.query(Boss).all()
        result = []
        for boss in bosses:
            boss_dict = {
                "id": boss.id,
                "name": boss.name,
                "difficulty": boss.difficulty,
                "weakness_domains": parse_weakness_domains(boss.weakness_domains),
                "description": boss.description,
                "question_id": boss.question_id,
                "source": boss.source,
                "drop_rate": boss.drop_rate
            }
            result.append(BossResponse(**boss_dict))
        return result
    finally:
        session.close()


@router.get("/{boss_id}", response_model=BossResponse)
async def get_boss(boss_id: int):
    """获取单个Boss详情"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        boss = session.query(Boss).filter(Boss.id == boss_id).first()
        if not boss:
            raise HTTPException(status_code=404, detail=f"Boss {boss_id} 不存在")
        
        boss_dict = {
            "id": boss.id,
            "name": boss.name,
            "difficulty": boss.difficulty,
            "weakness_domains": parse_weakness_domains(boss.weakness_domains),
            "description": boss.description,
            "question_id": boss.question_id,
            "source": boss.source,
            "drop_rate": boss.drop_rate
        }
        return BossResponse(**boss_dict)
    finally:
        session.close()


@router.post("/", response_model=BossResponse, status_code=201)
async def create_boss(boss: BossCreate):
    """创建Boss"""
    from algomate.data.database import Database
    import json
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        if boss.question_id:
            from algomate.models.questions import Question
            question = session.query(Question).filter(Question.id == boss.question_id).first()
            if not question:
                raise HTTPException(status_code=404, detail=f"题目 {boss.question_id} 不存在")
        
        new_boss = Boss(
            name=boss.name,
            difficulty=boss.difficulty.value,
            weakness_domains=json.dumps(boss.weakness_domains, ensure_ascii=False),
            description=boss.description,
            question_id=boss.question_id,
            source=boss.source.value,
            drop_rate=boss.drop_rate
        )
        session.add(new_boss)
        session.commit()
        session.refresh(new_boss)
        
        boss_dict = {
            "id": new_boss.id,
            "name": new_boss.name,
            "difficulty": new_boss.difficulty,
            "weakness_domains": parse_weakness_domains(new_boss.weakness_domains),
            "description": new_boss.description,
            "question_id": new_boss.question_id,
            "source": new_boss.source,
            "drop_rate": new_boss.drop_rate
        }
        return BossResponse(**boss_dict)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建Boss失败: {str(e)}")
    finally:
        session.close()


@router.post("/generate", response_model=BossResponse, status_code=201)
async def generate_boss(card_ids: List[int]):
    """根据卡牌生成Boss（AI）
    
    Args:
        card_ids: 卡牌ID列表，用于生成针对性的Boss
    """
    from algomate.data.database import Database
    from algomate.models.cards import Card
    from algomate.core.agent.chat_client import ChatClient
    from algomate.config.settings import AppConfig
    import json
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.id.in_(card_ids)).all()
        if not cards:
            raise HTTPException(status_code=400, detail="未找到有效的卡牌")
        
        card_info = "\n".join([f"- {card.name} (领域: {card.domain}, 耐久度: {card.durability})" for card in cards])
        
        prompt = f"""根据以下卡牌信息，生成一个Boss挑战：

卡牌信息：
{card_info}

请生成一个Boss，要求：
1. Boss名称要有创意，符合游戏化风格
2. 难度根据卡牌耐久度平均值得出（低=hard, 中=medium, 高=easy）
3. 弱点领域是卡牌所属领域的列表
4. 描述要有故事性，游戏化包装
5. 掉宝率根据难度设定（easy=0.8, medium=0.5, hard=0.3）

返回JSON格式：
{{
    "name": "Boss名称",
    "difficulty": "easy/medium/hard",
    "weakness_domains": ["领域1", "领域2"],
    "description": "Boss描述",
    "drop_rate": 0.5
}}"""
        
        config = AppConfig.load()
        client = ChatClient(api_key=config.LLM_API_KEY)
        result = client.chat([{"role": "user", "content": prompt}])
        
        import re
        json_match = re.search(r'\{[\s\S]*\}', result)
        if not json_match:
            raise HTTPException(status_code=500, detail="AI生成Boss失败：无法解析结果")
        
        boss_data = json.loads(json_match.group())
        
        new_boss = Boss(
            name=boss_data.get("name", "未知Boss"),
            difficulty=boss_data.get("difficulty", "medium"),
            weakness_domains=json.dumps(boss_data.get("weakness_domains", []), ensure_ascii=False),
            description=boss_data.get("description", ""),
            source="ai_generated",
            drop_rate=boss_data.get("drop_rate", 0.5)
        )
        session.add(new_boss)
        session.commit()
        session.refresh(new_boss)
        
        boss_dict = {
            "id": new_boss.id,
            "name": new_boss.name,
            "difficulty": new_boss.difficulty,
            "weakness_domains": parse_weakness_domains(new_boss.weakness_domains),
            "description": new_boss.description,
            "question_id": new_boss.question_id,
            "source": new_boss.source,
            "drop_rate": new_boss.drop_rate
        }
        return BossResponse(**boss_dict)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"生成Boss失败: {str(e)}")
    finally:
        session.close()


@router.put("/{boss_id}", response_model=BossResponse)
async def update_boss(boss_id: int, boss: BossUpdate):
    """更新Boss"""
    from algomate.data.database import Database
    import json
    
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
        if boss.weakness_domains is not None:
            existing.weakness_domains = json.dumps(boss.weakness_domains, ensure_ascii=False)
        if boss.description is not None:
            existing.description = boss.description
        if boss.question_id is not None:
            if boss.question_id:
                from algomate.models.questions import Question
                question = session.query(Question).filter(Question.id == boss.question_id).first()
                if not question:
                    raise HTTPException(status_code=404, detail=f"题目 {boss.question_id} 不存在")
            existing.question_id = boss.question_id
        if boss.source is not None:
            existing.source = boss.source.value
        if boss.drop_rate is not None:
            existing.drop_rate = boss.drop_rate
        
        session.commit()
        session.refresh(existing)
        
        boss_dict = {
            "id": existing.id,
            "name": existing.name,
            "difficulty": existing.difficulty,
            "weakness_domains": parse_weakness_domains(existing.weakness_domains),
            "description": existing.description,
            "question_id": existing.question_id,
            "source": existing.source,
            "drop_rate": existing.drop_rate
        }
        return BossResponse(**boss_dict)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新Boss失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{boss_id}", status_code=204)
async def delete_boss(boss_id: int):
    """删除Boss"""
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
