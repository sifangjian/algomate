import json
from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Query
from algomate.data.database import Database
from algomate.models.cards import Card, CardCreate, CardUpdate, _normalize_content
from algomate.core.memory.card_status import compute_card_status
from algomate.config.algorithm_types import ALGORITHM_TYPES

router = APIRouter(prefix="/cards", tags=["卡牌工坊"])
logger = logging.getLogger(__name__)




def success_response(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def error_response(code, message, status_code):
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _parse_json_field(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}





def _is_empty_content(value) -> bool:
    """Check if a content field is empty"""
    if value is None or value == "":
        return True
    if isinstance(value, dict):
        return len(value) == 0
    if isinstance(value, str):
        if value.strip() == "" or value.strip() == "{}":
            return True
        try:
            parsed = json.loads(value)
            return isinstance(parsed, dict) and len(parsed) == 0
        except (json.JSONDecodeError, TypeError):
            return False
    return False


def _is_card_empty(card):
    """Check if a card has no meaningful content."""
    if not _is_empty_content(card.content):
        return False
    return True


def _find_empty_cards(session):
    """Find all empty cards, excluding those that are the only card for their algorithm_type in ALGORITHM_TYPES."""
    from collections import defaultdict
    all_cards = session.query(Card).all()
    cards_by_type = defaultdict(list)
    for card in all_cards:
        cards_by_type[card.algorithm_type].append(card)

    empty_cards = []
    for card in all_cards:
        is_empty = _is_empty_content(card.content)
        if not is_empty:
            continue
        algo_type = card.algorithm_type
        total_in_type = len(cards_by_type.get(algo_type, []))
        if total_in_type == 1 and algo_type in ALGORITHM_TYPES:
            continue
        empty_cards.append(card)
    return empty_cards





def _card_to_response(card: Card) -> dict:
    return {
        "id": card.id,
        "name": card.name,
        "card_type": card.card_type,
        "algorithm_type": card.algorithm_type,
        "difficulty": card.difficulty,
        "durability": card.durability,
        "review_level": card.review_level,
        "next_review_date": card.next_review_date.isoformat() if card.next_review_date else None,
        "review_count": card.review_count,
        "last_reviewed": card.last_reviewed.isoformat() if card.last_reviewed else None,
        "pending_retake": card.pending_retake,
        "status": compute_card_status(card.durability, card.pending_retake),
        "content": _parse_json_field(card.content),
        "visual_links": card.visual_links,
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "updated_at": card.updated_at.isoformat() if card.updated_at else None,
    }


EDITABLE_FIELDS = {
    "algorithm_type", "difficulty",
    "content", "visual_links",
}





@router.get("")
async def get_cards(
    algorithm_type: Optional[str] = Query(None, description="按算法类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选：endangered/pending_retake"),
    keyword: Optional[str] = Query(None, description="按关键词搜索（匹配名称、内容）"),
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
                | (Card.content.ilike(keyword_pattern))
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


@router.get("/empty")
async def get_empty_cards():
    db = Database.get_instance()
    session = db.get_session()
    try:
        empty_cards = _find_empty_cards(session)
        result = [
            {
                "id": card.id,
                "name": card.name,
                "card_type": card.card_type,
                "algorithm_type": card.algorithm_type,
                "created_at": card.created_at.isoformat() if card.created_at else None,
            }
            for card in empty_cards
        ]
        return success_response(data={
            "empty_cards": result,
            "count": len(result),
        })
    finally:
        session.close()


@router.delete("/cleanup-empty")
async def cleanup_empty_cards():
    db = Database.get_instance()
    session = db.get_session()
    try:
        empty_cards = _find_empty_cards(session)
        deleted_cards = [
            {"id": card.id, "name": card.name, "card_type": card.card_type, "algorithm_type": card.algorithm_type}
            for card in empty_cards
        ]
        for card in empty_cards:
            session.delete(card)
        session.commit()
        return success_response(data={
            "deleted_count": len(deleted_cards),
            "deleted_cards": deleted_cards,
        })
    except Exception as e:
        session.rollback()
        logger.error("cleanup_empty_cards failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理空卡牌失败: {str(e)}")
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
            if key == "content":
                new_val = _normalize_content(value, None)
                cur_val = current_val or "{}"
            else:
                new_val = value if value is not None else ""
                cur_val = current_val if current_val is not None else ""
            if cur_val != new_val:
                has_changes = True
                break

        if not has_changes:
            error_response(40002, "内容未变更", 400)

        for key, value in update_data.items():
            if key == "content":
                setattr(card, key, _normalize_content(value, None))
            else:
                setattr(card, key, value)

        session.commit()
        session.refresh(card)
        return success_response(data=_card_to_response(card))
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("update_card failed for card %s: %s", card_id, e, exc_info=True)
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
        logger.error("delete_card failed for card %s: %s", card_id, e, exc_info=True)
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
        logger.error("retake_card failed for card %s: %s", card_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"重修卡牌失败: {str(e)}")
    finally:
        session.close()


@router.get("/by-slug/{slug}")
async def get_card_by_slug(slug: str):
    """轻量查询：根据 LeetCode slug 找系统内题卡及其复习卡。

    用于 LeetCode 页内复习浮窗(popup)检测当前题目是否已导入，
    以便回传重做标记(AC/卡住)与边界遗漏笔记。
    """
    from algomate.models.problem_card import ProblemCard
    db = Database.get_instance()
    session = db.get_session()
    try:
        slug = (slug or "").strip()
        if not slug:
            return success_response(data=None)
        pc = session.query(ProblemCard).filter(ProblemCard.leetcode_slug == slug).first()
        if not pc:
            return success_response(data=None)
        return success_response(data={
            "problem_id": pc.id,
            "title": pc.title,
            "leetcode_slug": pc.leetcode_slug,
            "leetcode_link": pc.leetcode_link,
            "card_id": pc.card_id,
            "has_variants": bool(pc.variants and pc.variants not in ("[]", "")),
        })
    except Exception as e:
        logger.error("get_card_by_slug failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询题卡失败: {str(e)}")
    finally:
        session.close()
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = Card(
            name=card_data.name,
            card_type=card_data.card_type or "tip",
            algorithm_type=card_data.algorithm_type or "",
            difficulty=card_data.difficulty or 3,
            durability=card_data.durability,
            content=_normalize_content(card_data.content, None),
            visual_links=card_data.visual_links,
        )
        session.add(card)
        session.commit()
        session.refresh(card)

        return success_response(data=_card_to_response(card))
    except Exception as e:
        session.rollback()
        logger.error("create_card failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建卡牌失败: {str(e)}")
    finally:
        session.close()



