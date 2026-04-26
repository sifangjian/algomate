"""
题目模型

存储算法题目及答案
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from algomate.data.database import Base


class QuestionType(str, Enum):
    """题目类型枚举"""
    CHOICE = "选择题"
    SHORT_ANSWER = "简答题"
    CODE = "代码题"


class QuestionDifficulty(str, Enum):
    """题目难度枚举"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(Base):
    """题目模型
    
    存储算法题目及答案。
    
    Attributes:
        id: 题目唯一标识
        note_id: 关联笔记ID（外键，可为NULL）
        card_id: 关联卡牌ID（外键，可为NULL）
        question_type: 题目类型（选择题/简答题/代码题）
        content: 题目内容（Markdown）
        options: 选项列表（JSON，选择题用）
        answer: 参考答案
        explanation: 详细解析
        difficulty: 难度等级
        created_at: 创建时间
    """
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    question_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    options = Column(Text, default="[]", nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, default="", nullable=False)
    difficulty = Column(String(20), default="medium", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    note: Optional["Note"] = relationship("Note", back_populates="questions")
    card: Optional["Card"] = relationship("Card", back_populates="questions")
    bosses: List["Boss"] = relationship("Boss", back_populates="question")


class QuestionCreate(BaseModel):
    """创建题目的输入验证模型"""
    note_id: Optional[int] = Field(None, description="关联笔记ID")
    card_id: Optional[int] = Field(None, description="关联卡牌ID")
    question_type: QuestionType = Field(..., description="题目类型")
    content: str = Field(..., min_length=1, description="题目内容")
    options: List[str] = Field(default=[], description="选项列表（选择题用）")
    answer: str = Field(..., min_length=1, description="参考答案")
    explanation: str = Field(default="", description="详细解析")
    difficulty: QuestionDifficulty = Field(default=QuestionDifficulty.MEDIUM, description="难度等级")
    
    class Config:
        from_attributes = True


class QuestionUpdate(BaseModel):
    """更新题目的输入验证模型"""
    note_id: Optional[int] = Field(None, description="关联笔记ID")
    card_id: Optional[int] = Field(None, description="关联卡牌ID")
    question_type: Optional[QuestionType] = Field(None, description="题目类型")
    content: Optional[str] = Field(None, min_length=1, description="题目内容")
    options: Optional[List[str]] = Field(None, description="选项列表（选择题用）")
    answer: Optional[str] = Field(None, min_length=1, description="参考答案")
    explanation: Optional[str] = Field(None, description="详细解析")
    difficulty: Optional[QuestionDifficulty] = Field(None, description="难度等级")
    
    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    """返回给前端的题目数据模型"""
    id: int
    note_id: Optional[int]
    card_id: Optional[int]
    question_type: str
    content: str
    options: List[str]
    answer: str
    explanation: str
    difficulty: str
    created_at: datetime
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/questions", tags=["题目"])


def parse_options(options_str: str) -> List[str]:
    """解析 options JSON 字符串"""
    import json
    try:
        return json.loads(options_str) if options_str else []
    except:
        return []


@router.get("/", response_model=list[QuestionResponse])
async def get_questions():
    """获取题目列表"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        questions = session.query(Question).order_by(Question.created_at.desc()).all()
        result = []
        for q in questions:
            q_dict = {
                "id": q.id,
                "note_id": q.note_id,
                "card_id": q.card_id,
                "question_type": q.question_type,
                "content": q.content,
                "options": parse_options(q.options),
                "answer": q.answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "created_at": q.created_at
            }
            result.append(QuestionResponse(**q_dict))
        return result
    finally:
        session.close()


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int):
    """获取单个题目"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        question = session.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"题目 {question_id} 不存在")
        
        q_dict = {
            "id": question.id,
            "note_id": question.note_id,
            "card_id": question.card_id,
            "question_type": question.question_type,
            "content": question.content,
            "options": parse_options(question.options),
            "answer": question.answer,
            "explanation": question.explanation,
            "difficulty": question.difficulty,
            "created_at": question.created_at
        }
        return QuestionResponse(**q_dict)
    finally:
        session.close()


@router.post("/", response_model=QuestionResponse, status_code=201)
async def create_question(question: QuestionCreate):
    """创建题目"""
    from algomate.data.database import Database
    import json
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        if question.note_id:
            from algomate.models.notes import Note
            note = session.query(Note).filter(Note.id == question.note_id).first()
            if not note:
                raise HTTPException(status_code=404, detail=f"笔记 {question.note_id} 不存在")
        
        if question.card_id:
            from algomate.models.cards import Card
            card = session.query(Card).filter(Card.id == question.card_id).first()
            if not card:
                raise HTTPException(status_code=404, detail=f"卡牌 {question.card_id} 不存在")
        
        new_question = Question(
            note_id=question.note_id,
            card_id=question.card_id,
            question_type=question.question_type.value,
            content=question.content,
            options=json.dumps(question.options, ensure_ascii=False),
            answer=question.answer,
            explanation=question.explanation,
            difficulty=question.difficulty.value
        )
        session.add(new_question)
        session.commit()
        session.refresh(new_question)
        
        q_dict = {
            "id": new_question.id,
            "note_id": new_question.note_id,
            "card_id": new_question.card_id,
            "question_type": new_question.question_type,
            "content": new_question.content,
            "options": parse_options(new_question.options),
            "answer": new_question.answer,
            "explanation": new_question.explanation,
            "difficulty": new_question.difficulty,
            "created_at": new_question.created_at
        }
        return QuestionResponse(**q_dict)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建题目失败: {str(e)}")
    finally:
        session.close()


@router.post("/generate", response_model=list[QuestionResponse], status_code=201)
async def generate_questions(request: dict):
    """AI生成题目
    
    Args:
        request: 包含 topic（主题）和 count（数量，默认3）的字典
    """
    from algomate.data.database import Database
    from algomate.core.agent.chat_client import ChatClient
    from algomate.config.settings import AppConfig
    import json
    import re
    
    topic = request.get("topic", "")
    count = request.get("count", 3)
    
    if not topic:
        raise HTTPException(status_code=400, detail="主题不能为空")
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        prompt = f"""针对"{topic}"这个算法主题，生成{count}道高质量的练习题。

要求：
- 包含选择题、简答题和代码题的组合
- 选择题必须有4个选项（A、B、C、D），只有一个正确答案
- 简答题考查对概念和原理的理解
- 代码题需要编写代码实现
- 每道题都要有详细的解析

请返回JSON格式，包含一个questions数组：
{{
    "questions": [
        {{
            "question_type": "选择题",
            "content": "题目内容（包含选项A、B、C、D）",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "answer": "正确答案",
            "explanation": "解析",
            "difficulty": "easy/medium/hard"
        }},
        {{
            "question_type": "简答题",
            "content": "题目内容",
            "options": [],
            "answer": "参考答案要点",
            "explanation": "解析",
            "difficulty": "easy/medium/hard"
        }},
        {{
            "question_type": "代码题",
            "content": "题目描述",
            "options": [],
            "answer": "参考代码",
            "explanation": "解题思路",
            "difficulty": "easy/medium/hard"
        }}
    ]
}}"""
        
        config = AppConfig.load()
        client = ChatClient(api_key=config.LLM_API_KEY)
        result = client.chat([{"role": "user", "content": prompt}])
        
        json_match = re.search(r'\{[\s\S]*\}', result)
        if not json_match:
            raise HTTPException(status_code=500, detail="AI生成题目失败：无法解析结果")
        
        questions_data = json.loads(json_match.group())
        questions_list = questions_data.get("questions", [])
        
        created_questions = []
        for q_data in questions_list:
            new_question = Question(
                question_type=q_data.get("question_type", "简答题"),
                content=q_data.get("content", ""),
                options=json.dumps(q_data.get("options", []), ensure_ascii=False),
                answer=q_data.get("answer", ""),
                explanation=q_data.get("explanation", ""),
                difficulty=q_data.get("difficulty", "medium")
            )
            session.add(new_question)
            created_questions.append(new_question)
        
        session.commit()
        
        result_list = []
        for q in created_questions:
            session.refresh(q)
            q_dict = {
                "id": q.id,
                "note_id": q.note_id,
                "card_id": q.card_id,
                "question_type": q.question_type,
                "content": q.content,
                "options": parse_options(q.options),
                "answer": q.answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "created_at": q.created_at
            }
            result_list.append(QuestionResponse(**q_dict))
        
        return result_list
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"生成题目失败: {str(e)}")
    finally:
        session.close()


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(question_id: int, question: QuestionUpdate):
    """更新题目"""
    from algomate.data.database import Database
    import json
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(Question).filter(Question.id == question_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail=f"题目 {question_id} 不存在")
        
        if question.note_id is not None:
            if question.note_id:
                from algomate.models.notes import Note
                note = session.query(Note).filter(Note.id == question.note_id).first()
                if not note:
                    raise HTTPException(status_code=404, detail=f"笔记 {question.note_id} 不存在")
            existing.note_id = question.note_id
        if question.card_id is not None:
            if question.card_id:
                from algomate.models.cards import Card
                card = session.query(Card).filter(Card.id == question.card_id).first()
                if not card:
                    raise HTTPException(status_code=404, detail=f"卡牌 {question.card_id} 不存在")
            existing.card_id = question.card_id
        if question.question_type is not None:
            existing.question_type = question.question_type.value
        if question.content is not None:
            existing.content = question.content
        if question.options is not None:
            existing.options = json.dumps(question.options, ensure_ascii=False)
        if question.answer is not None:
            existing.answer = question.answer
        if question.explanation is not None:
            existing.explanation = question.explanation
        if question.difficulty is not None:
            existing.difficulty = question.difficulty.value
        
        session.commit()
        session.refresh(existing)
        
        q_dict = {
            "id": existing.id,
            "note_id": existing.note_id,
            "card_id": existing.card_id,
            "question_type": existing.question_type,
            "content": existing.content,
            "options": parse_options(existing.options),
            "answer": existing.answer,
            "explanation": existing.explanation,
            "difficulty": existing.difficulty,
            "created_at": existing.created_at
        }
        return QuestionResponse(**q_dict)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新题目失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{question_id}", status_code=204)
async def delete_question(question_id: int):
    """删除题目"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        question = session.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"题目 {question_id} 不存在")
        
        session.delete(question)
        session.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除题目失败: {str(e)}")
    finally:
        session.close()
