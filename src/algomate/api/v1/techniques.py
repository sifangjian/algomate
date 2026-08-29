import json
import logging
from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc

from algomate.data.database import Database
from algomate.models.activity_log import ActivityLog
from algomate.models.technique_card import TechniqueCard
from algomate.models.cards import Card

router = APIRouter(prefix="/techniques", tags=["技巧卡片"])
logger = logging.getLogger(__name__)


class TechniqueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="技巧名称（用户提炼）")
    use_cases: str = Field("", description="适用场景 / 触发条件")
    code_template: str = Field("", description="标准代码模板")
    memory_anchors: str = Field("", description="记忆锚点/关键词")
    difficulty: int = Field(3, ge=1, le=5, description="难度 1-5（用于复习调度）")
    notes: str = Field("", description="注意事项")
    video_demo_link: str = Field("", description="视频演示链接")


class TechniqueUpdate(BaseModel):
    name: Optional[str] = None
    use_cases: Optional[str] = None
    code_template: Optional[str] = None
    memory_anchors: Optional[str] = None
    difficulty: Optional[int] = None
    notes: Optional[str] = None
    video_demo_link: Optional[str] = None


class TechniqueResponse(BaseModel):
    id: int
    card_id: int
    name: str
    use_cases: str
    code_template: str
    memory_anchors: str
    difficulty: int = 3
    notes: str = ""
    video_demo_link: str = ""
    created_at: datetime
    updated_at: Optional[datetime] = None
    solution_count: int = 0
    review_status: str = "normal"  # normal / due / critical
    next_review_date: Optional[datetime] = None
    durability: int = 80

    class Config:
        from_attributes = True


class TechniqueDetailResponse(TechniqueResponse):
    solutions: List[dict] = []

    class Config:
        from_attributes = True


class SelfReviewRequest(BaseModel):
    self_rating: str = Field(..., description="自评等级: forgot/struggled/passed/mastered")


def _compute_review_status(card: Optional[Card]) -> str:
    if not card:
        return "normal"
    if card.durability < 30:
        return "critical"
    if card.next_review_date and card.next_review_date.date() <= date.today():
        return "due"
    return "normal"


def _technique_to_response(t: TechniqueCard, card: Optional[Card] = None) -> TechniqueResponse:
    return TechniqueResponse(
        id=t.id,
        card_id=t.card_id,
        name=t.name,
        use_cases=t.use_cases or "",
        code_template=t.code_template or "",
        memory_anchors=t.memory_anchors or "",
        difficulty=card.difficulty if card else 3,
        notes=t.notes or "",
        video_demo_link=t.video_demo_link or "",
        created_at=t.created_at,
        updated_at=t.updated_at,
        solution_count=len(t.solutions) if t.solutions else 0,
        review_status=_compute_review_status(card),
        next_review_date=card.next_review_date if card else None,
        durability=card.durability if card else 80,
    )


@router.post("", response_model=TechniqueResponse)
def create_technique(data: TechniqueCreate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        # 同步创建 Card 复习记录
        review_card = Card(
            name=data.name,
            difficulty=data.difficulty,
            durability=80,
            review_level=0,
            card_type="tip",
            content="{}",
        )
        session.add(review_card)
        session.flush()

        technique = TechniqueCard(
            card_id=review_card.id,
            name=data.name,
            use_cases=data.use_cases,
            code_template=data.code_template,
            memory_anchors=data.memory_anchors,
            notes=data.notes,
            video_demo_link=data.video_demo_link,
        )
        session.add(technique)
        session.commit()
        session.refresh(technique)

        log_entry = ActivityLog(
            type="auto_create",
            card_type="technique",
            card_name=technique.name,
            card_id=technique.id,
            content=f"创建技巧卡片: {technique.name}",
        )
        session.add(log_entry)
        session.commit()

        logger.info(f"Created technique card: {technique.name} (id={technique.id})")
        return _technique_to_response(technique, review_card)
    finally:
        session.close()


@router.get("", response_model=List[TechniqueResponse])
def list_techniques(
    due_only: Optional[bool] = Query(False, description="只显示待复习的"),
):
    db = Database.get_instance()
    session = db.get_session()
    try:
        query = session.query(TechniqueCard)

        techniques = query.order_by(desc(TechniqueCard.created_at)).all()

        result = []
        for t in techniques:
            card = session.query(Card).filter(Card.id == t.card_id).first()
            if due_only and _compute_review_status(card) == "normal":
                continue
            result.append(_technique_to_response(t, card))

        # 待复习技巧优先
        result.sort(key=lambda r: (
            0 if r.review_status != "normal" else 1,
            -r.solution_count,
        ))

        return result
    finally:
        session.close()


@router.get("/{technique_id}", response_model=TechniqueDetailResponse)
def get_technique(technique_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        technique = session.query(TechniqueCard).filter(TechniqueCard.id == technique_id).first()
        if not technique:
            raise HTTPException(status_code=404, detail="技巧卡片不存在")

        card = session.query(Card).filter(Card.id == technique.card_id).first()

        solutions = []
        if technique.solutions:
            for s in technique.solutions:
                solutions.append({
                    "id": s.id,
                    "name": s.name,
                    "time_complexity": s.time_complexity or "",
                    "space_complexity": s.space_complexity or "",
                    "problem_title": s.problem.title if s.problem else "",
                    "problem_id": s.problem_id,
                    "leetcode_link": s.problem.leetcode_link if s.problem and s.problem.leetcode_link else "",
                })

        return TechniqueDetailResponse(
            id=technique.id,
            card_id=technique.card_id,
            name=technique.name,
            use_cases=technique.use_cases or "",
            code_template=technique.code_template or "",
            memory_anchors=technique.memory_anchors or "",
            difficulty=card.difficulty if card else 3,
            notes=technique.notes or "",
            video_demo_link=technique.video_demo_link or "",
            created_at=technique.created_at,
            updated_at=technique.updated_at,
            solution_count=len(technique.solutions) if technique.solutions else 0,
            review_status=_compute_review_status(card),
            solutions=solutions,
        )
    finally:
        session.close()


@router.put("/{technique_id}", response_model=TechniqueResponse)
def update_technique(technique_id: int, data: TechniqueUpdate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        technique = session.query(TechniqueCard).filter(TechniqueCard.id == technique_id).first()
        if not technique:
            raise HTTPException(status_code=404, detail="技巧卡片不存在")

        update_data = data.model_dump(exclude_unset=True)

        changed_fields = {}
        for key, value in update_data.items():
            old_val = getattr(technique, key)
            if old_val != value:
                changed_fields[key] = {"old": old_val, "new": value}

        for key, value in update_data.items():
            setattr(technique, key, value)

        technique.updated_at = datetime.now()
        session.commit()
        session.refresh(technique)

        card = session.query(Card).filter(Card.id == technique.card_id).first()
        if card:
            card.name = technique.name
            if 'difficulty' in update_data:
                card.difficulty = update_data['difficulty']
            session.commit()

        if changed_fields:
            log_entry = ActivityLog(
                type="auto_update",
                card_type="technique",
                card_name=technique.name,
                card_id=technique.id,
                content=f"修改技巧卡片: {technique.name}",
                details={"changed_fields": changed_fields},
            )
            session.add(log_entry)
            session.commit()

        logger.info(f"Updated technique card: {technique.name} (id={technique.id})")
        return _technique_to_response(technique, card)
    finally:
        session.close()


@router.delete("/{technique_id}")
def delete_technique(technique_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        technique = session.query(TechniqueCard).filter(TechniqueCard.id == technique_id).first()
        if not technique:
            raise HTTPException(status_code=404, detail="技巧卡片不存在")

        card_id = technique.card_id
        session.delete(technique)
        # 同时删除关联的 Card 复习记录
        card = session.query(Card).filter(Card.id == card_id).first()
        if card:
            session.delete(card)
        session.commit()
        logger.info(f"Deleted technique card: {technique.name} (id={technique.id})")
        return {"message": "删除成功"}
    finally:
        session.close()


# --- 自评复习 ---

@router.post("/{technique_id}/review")
def self_review(technique_id: int, data: SelfReviewRequest):
    """自评复习：用户练习后自评，系统根据自评+遗忘曲线计算下次复习安排"""
    if data.self_rating not in ("forgot", "struggled", "passed", "mastered"):
        raise HTTPException(status_code=400, detail="自评等级无效，可选: forgot/struggled/passed/mastered")

    db = Database.get_instance()
    session = db.get_session()
    try:
        technique = session.query(TechniqueCard).filter(TechniqueCard.id == technique_id).first()
        if not technique:
            raise HTTPException(status_code=404, detail="技巧卡片不存在")

        card = session.query(Card).filter(Card.id == technique.card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="复习卡片不存在")

        # 根据自评等级调整耐久度和复习等级（单一遗忘曲线机制，由 Card 承载）
        from algomate.core.memory.forgetting_curve import ForgettingCurveEngine
        engine = ForgettingCurveEngine()

        rating = data.self_rating
        if rating == "forgot":
            card.durability = max(0, card.durability - 30)
            card.review_level = max(0, card.review_level - 1)
        elif rating == "struggled":
            card.durability = max(0, card.durability - 10)
            # review_level 不变
        elif rating == "passed":
            card.durability = min(100, card.durability + 10)
            card.review_level = min(engine.max_level, card.review_level + 1)
        elif rating == "mastered":
            card.durability = min(100, card.durability + 25)
            card.review_level = min(engine.max_level, card.review_level + 2)

        # 间隔由遗忘曲线引擎按当前复习等级计算（不再使用技巧卡冗余字段）
        new_interval = engine.get_review_interval(card.review_level)

        # 更新 Card 记录
        card.last_reviewed = datetime.now()
        from datetime import timedelta
        card.next_review_date = datetime.now() + timedelta(days=new_interval)
        card.pending_retake = False
        card.review_count = (card.review_count or 0) + 1

        session.commit()
        logger.info(f"Self-review for technique {technique_id}: rating={rating}, new_interval={new_interval}d")

        return {
            "message": "自评完成",
            "self_rating": rating,
            "new_durability": card.durability,
            "new_review_level": card.review_level,
            "new_interval_days": new_interval,
            "next_review_date": card.next_review_date.isoformat(),
            "review_status": _compute_review_status(card),
        }
    finally:
        session.close()


# --- 反向链接：技巧关联的解法 ---
@router.get("/{technique_id}/backlinks")
def get_technique_backlinks(technique_id: int):
    """查询引用了该技巧的解法列表"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        technique = session.query(TechniqueCard).filter(TechniqueCard.id == technique_id).first()
        if not technique:
            raise HTTPException(status_code=404, detail="技巧卡片不存在")

        solutions = []
        if technique.solutions:
            for s in technique.solutions:
                solutions.append({
                    "id": s.id,
                    "name": s.name,
                    "problem_id": s.problem_id,
                    "problem_title": s.problem.title if s.problem else "",
                })

        return {"solutions": solutions}
    finally:
        session.close()