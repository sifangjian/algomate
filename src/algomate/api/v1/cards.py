from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func

from algomate.data.database import Database
from algomate.models.cards import Card, CardUpdate, CardResponse

router = APIRouter(prefix="/cards", tags=["卡牌工坊"])


def compute_card_status(durability: int, pending_retake: bool) -> str:
    if pending_retake or durability == 0:
        return "pending_retake"
    if durability < 30:
        return "endangered"
    return "normal"


def success_response(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def error_response(code, message, status_code):
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _card_to_response(card: Card) -> dict:
    return {
        "id": card.id,
        "name": card.name,
        "algorithm_type": card.algorithm_type,
        "durability": card.durability,
        "review_level": card.review_level,
        "next_review_date": card.next_review_date.isoformat() if card.next_review_date else None,
        "review_count": card.review_count,
        "last_reviewed": card.last_reviewed.isoformat() if card.last_reviewed else None,
        "pending_retake": card.pending_retake,
        "npc_id": card.npc_id,
        "topic": card.topic,
        "status": compute_card_status(card.durability, card.pending_retake),
        "core_concept": card.core_concept,
        "key_points": card.key_points,
        "code_template": card.code_template,
        "complexity_analysis": card.complexity_analysis,
        "use_cases": card.use_cases,
        "common_variants": card.common_variants,
        "typical_problems": card.typical_problems,
        "common_pitfalls": card.common_pitfalls,
        "comparison": card.comparison,
        "my_notes": card.my_notes,
        "visual_links": card.visual_links,
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "updated_at": card.updated_at.isoformat() if card.updated_at else None,
    }


EDITABLE_FIELDS = {
    "core_concept", "key_points", "code_template", "complexity_analysis",
    "use_cases", "common_variants", "typical_problems", "common_pitfalls",
    "comparison", "my_notes", "visual_links",
}


@router.get("")
async def get_cards(
    algorithm_type: Optional[str] = Query(None, description="按算法类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选：endangered/pending_retake"),
    keyword: Optional[str] = Query(None, description="按关键词搜索（匹配名称、核心概念、关键要点）"),
):
    db = Database.get_instance()
    session = db.get_session()
    try:
        endangered_count = session.query(Card).filter(
            Card.durability < 30, Card.durability > 0
        ).count()
        pending_retake_count = session.query(Card).filter(
            Card.pending_retake == True
        ).count()

        query = session.query(Card)

        if algorithm_type:
            query = query.filter(Card.algorithm_type == algorithm_type)

        if status == "endangered":
            query = query.filter(Card.durability < 30, Card.durability > 0)
        elif status == "pending_retake":
            query = query.filter(Card.pending_retake == True)

        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                (Card.name.ilike(keyword_pattern))
                | (Card.core_concept.ilike(keyword_pattern))
                | (Card.key_points.ilike(keyword_pattern))
            )

        cards = query.order_by(Card.created_at.desc()).all()
        result = [_card_to_response(card) for card in cards]

        return success_response(data={
            "cards": result,
            "endangered_count": endangered_count,
            "pending_retake_count": pending_retake_count,
        })
    finally:
        session.close()


@router.get("/{card_id}")
async def get_card(card_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            error_response(40404, "卡牌不存在", 404)
        return success_response(data=_card_to_response(card))
    finally:
        session.close()


@router.put("/{card_id}")
async def update_card(card_id: int, card_update: CardUpdate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            error_response(40404, "卡牌不存在", 404)

        update_data = card_update.model_dump(exclude_unset=True)
        if not update_data:
            error_response(40002, "内容未变更", 400)

        for key in update_data:
            if key not in EDITABLE_FIELDS:
                error_response(40001, f"字段 {key} 不可编辑", 400)

        has_changes = False
        for key, value in update_data.items():
            current_val = getattr(card, key, None)
            new_val = value if value is not None else ""
            cur_val = current_val if current_val is not None else ""
            if cur_val != new_val:
                has_changes = True
                break

        if not has_changes:
            error_response(40002, "内容未变更", 400)

        for key, value in update_data.items():
            setattr(card, key, value)

        session.commit()
        session.refresh(card)
        return success_response(data={"updated": True})
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新卡牌失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{card_id}")
async def delete_card(card_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            error_response(40404, "卡牌不存在", 404)

        session.delete(card)
        session.commit()
        return success_response(data=None)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除卡牌失败: {str(e)}")
    finally:
        session.close()


@router.post("/{card_id}/retake")
async def retake_card(card_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            error_response(40404, "卡牌不存在", 404)

        if not card.pending_retake:
            error_response(40001, "该卡牌不在待重修状态", 400)

        durability_before = card.durability

        card.durability = 80
        card.pending_retake = False
        card.review_level = 0
        card.review_count = 0
        card.next_review_date = datetime.now() + timedelta(days=1)
        card.last_reviewed = None

        session.commit()
        session.refresh(card)

        return success_response(data={
            "card_id": card.id,
            "durability_before": durability_before,
            "durability_after": card.durability,
            "pending_retake": card.pending_retake,
            "status": compute_card_status(card.durability, card.pending_retake),
        })
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"重修卡牌失败: {str(e)}")
    finally:
        session.close()
