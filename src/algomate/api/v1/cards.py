import json
import re
from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Query
from algomate.data.database import Database
from algomate.models.cards import Card, CardCreate, CardUpdate, _normalize_content
from algomate.models.card_links import CardLink, LinkCreate, LinkResponse
from algomate.core.memory.card_status import compute_card_status
from algomate.config.algorithm_types import ALGORITHM_TYPES
from collections import deque
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cards", tags=["卡牌工坊"])
logger = logging.getLogger(__name__)

# 数据迁移：将已有 problem 卡片的 related 链接更新为 tip_related
_migrated = False


def _migrate_old_links():
    global _migrated
    if _migrated:
        return
    _migrated = True
    try:
        db = Database.get_instance()
        session = db.get_session()
        try:
            # 查找 source 为 problem 卡片的 related 链接
            links_to_update = session.query(CardLink).join(
                Card, CardLink.source_card_id == Card.id
            ).filter(
                Card.card_type == 'problem',
                CardLink.link_type == 'related',
            ).all()
            for link in links_to_update:
                link.link_type = 'tip_related'
            if links_to_update:
                session.commit()
                logger.info(f"迁移了 {len(links_to_update)} 条旧链接: related → tip_related")
        finally:
            session.close()
    except Exception as e:
        logger.warning(f"链接迁移失败（非关键错误，可忽略）: {e}")


# 在模块加载时运行迁移
_migrate_old_links()


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


def _sync_content_links(session, card):
    """根据卡牌 content 中的关联字段同步 CardLink 记录。

    技巧卡：content.related_problems → 链接到题目卡 (link_type='related')
    技巧卡：content.related_tips → 链接到其他技巧卡 (link_type='tip_related')
    题目卡：content.core_skills → 链接到技巧卡 (link_type='tip_related')
    """
    content = _parse_json_field(card.content)
    if not content:
        return

    # 确定要解析的关联字段及对应的 link_type
    link_definitions = []
    if card.card_type == 'tip':
        link_definitions.append(('related', content.get('related_problems', [])))
        link_definitions.append(('tip_related', content.get('related_tips', [])))
    elif card.card_type == 'problem':
        link_definitions.append(('tip_related', content.get('core_skills', [])))

    for link_type, link_fields in link_definitions:
        # 从 [[Card Name]] 格式提取卡牌名称并查找 ID
        target_ids = set()
        for item in link_fields:
            match = re.match(r'^\[\[(.+?)\]\]', item)
            if not match:
                continue
            card_name = match.group(1)
            target_card = session.query(Card).filter(Card.name == card_name).first()
            if target_card:
                target_ids.add(target_card.id)

        # 获取当前已存在的该类型链接
        existing_links = session.query(CardLink).filter(
            CardLink.source_card_id == card.id,
            CardLink.link_type == link_type,
        ).all()
        existing_target_ids = {link.target_card_id for link in existing_links}

        # 新增不存在的链接
        for target_id in target_ids:
            if target_id not in existing_target_ids:
                session.add(CardLink(
                    source_card_id=card.id,
                    target_card_id=target_id,
                    link_type=link_type,
                ))

        # 删除已移除的链接
        for link in existing_links:
            if link.target_card_id not in target_ids:
                session.delete(link)


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


def _has_cycle(session, source_card_id, target_card_id):
    """Check if adding source->target prerequisite would create a cycle.
    A cycle exists if target is already a (transitive) prerequisite of source.
    """
    visited = set()
    queue = deque([source_card_id])
    while queue:
        current = queue.popleft()
        if current == target_card_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        prereqs = session.query(CardLink.source_card_id).filter(
            CardLink.target_card_id == current,
            CardLink.link_type == "prerequisite"
        ).all()
        for (prereq_id,) in prereqs:
            queue.append(prereq_id)
    return False


class PrerequisiteCreate(BaseModel):
    prerequisite_card_id: int = Field(..., description="前置卡牌ID")


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


@router.get("/graph")
async def get_graph():
    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).all()
        links = session.query(CardLink).all()
        nodes = [
            {
                "id": c.id,
                "name": c.name,
                "card_type": c.card_type,
                "algorithm_type": c.algorithm_type,
                "durability": c.durability,
                "review_level": c.review_level,
                "is_empty": _is_card_empty(c),
            }
            for c in cards
        ]
        edges = [
            {
                "source": l.source_card_id,
                "target": l.target_card_id,
                "link_type": l.link_type,
                "source_keyword": l.source_keyword,
                "source_card_name": l.source_card.name if l.source_card else None,
                "target_card_name": l.target_card.name if l.target_card else None,
            }
            for l in links
        ]
        return success_response(data={"nodes": nodes, "edges": edges})
    finally:
        session.close()


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

        # 同步内容中的卡牌关联关系到 CardLink 表
        _sync_content_links(session, card)

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


@router.post("")
async def create_card(card_data: CardCreate):
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


# --- 链接管理端点 ---

@router.get("/{card_id}/links")
async def get_card_links(card_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            error_response(40404, "卡牌不存在", 404)

        outgoing = session.query(CardLink).filter(CardLink.source_card_id == card_id).all()
        incoming = session.query(CardLink).filter(CardLink.target_card_id == card_id).all()

        result = []
        for link in outgoing:
            target = session.query(Card).filter(Card.id == link.target_card_id).first()
            result.append({
                "id": link.id,
                "source_card_id": link.source_card_id,
                "target_card_id": link.target_card_id,
                "link_type": link.link_type,
                "source_keyword": link.source_keyword,
                "target_card_name": target.name if target else None,
                "direction": "outgoing",
                "created_at": link.created_at.isoformat() if link.created_at else None,
            })
        for link in incoming:
            source = session.query(Card).filter(Card.id == link.source_card_id).first()
            result.append({
                "id": link.id,
                "source_card_id": link.source_card_id,
                "target_card_id": link.target_card_id,
                "link_type": link.link_type,
                "source_keyword": link.source_keyword,
                "source_card_name": source.name if source else None,
                "direction": "incoming",
                "created_at": link.created_at.isoformat() if link.created_at else None,
            })
        return success_response(data=result)
    finally:
        session.close()


@router.post("/{card_id}/links")
async def create_card_link(card_id: int, link_data: LinkCreate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        if card_id == link_data.target_card_id:
            error_response(40001, "不能链接到自身", 400)

        source = session.query(Card).filter(Card.id == card_id).first()
        if not source:
            error_response(40404, "源卡牌不存在", 404)

        target = session.query(Card).filter(Card.id == link_data.target_card_id).first()
        if not target:
            error_response(40404, "目标卡牌不存在", 404)

        existing = session.query(CardLink).filter(
            CardLink.source_card_id == card_id,
            CardLink.target_card_id == link_data.target_card_id,
            CardLink.link_type == link_data.link_type,
        ).first()
        if existing:
            error_response(40001, "该链接已存在", 400)

        link = CardLink(
            source_card_id=card_id,
            target_card_id=link_data.target_card_id,
            link_type=link_data.link_type,
            source_keyword=link_data.source_keyword,
        )
        session.add(link)
        session.commit()
        session.refresh(link)

        return success_response(data={
            "id": link.id,
            "source_card_id": link.source_card_id,
            "target_card_id": link.target_card_id,
            "link_type": link.link_type,
            "source_keyword": link.source_keyword,
            "target_card_name": target.name,
            "created_at": link.created_at.isoformat() if link.created_at else None,
        })
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("create_card_link failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建链接失败: {str(e)}")
    finally:
        session.close()


@router.delete("/links/{link_id}")
async def delete_card_link(link_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        link = session.query(CardLink).filter(CardLink.id == link_id).first()
        if not link:
            error_response(40404, "链接不存在", 404)

        session.delete(link)
        session.commit()
        return success_response(data=None)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("delete_card_link failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除链接失败: {str(e)}")
    finally:
        session.close()


# --- 前置关联端点 ---


@router.post("/{card_id}/prerequisites")
async def add_prerequisite(card_id: int, data: PrerequisiteCreate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        if card_id == data.prerequisite_card_id:
            error_response(40001, "不能将自己设为前置卡牌", 400)

        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            error_response(40404, "卡牌不存在", 404)

        prereq_card = session.query(Card).filter(Card.id == data.prerequisite_card_id).first()
        if not prereq_card:
            error_response(40404, "前置卡牌不存在", 404)

        existing = session.query(CardLink).filter(
            CardLink.source_card_id == data.prerequisite_card_id,
            CardLink.target_card_id == card_id,
            CardLink.link_type == "prerequisite",
        ).first()
        if existing:
            error_response(40001, "该前置关联已存在", 400)

        if _has_cycle(session, data.prerequisite_card_id, card_id):
            error_response(40001, "添加此前置关联会形成循环依赖", 400)

        link = CardLink(
            source_card_id=data.prerequisite_card_id,
            target_card_id=card_id,
            link_type="prerequisite",
        )
        session.add(link)
        session.commit()
        session.refresh(link)

        return success_response(data={
            "id": link.id,
            "source_card_id": link.source_card_id,
            "target_card_id": link.target_card_id,
            "link_type": link.link_type,
            "source_keyword": link.source_keyword,
            "source_card_name": prereq_card.name,
            "created_at": link.created_at.isoformat() if link.created_at else None,
        })
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("add_prerequisite failed for card %s: %s", card_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"添加前置关联失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{card_id}/prerequisites/{prerequisite_card_id}")
async def remove_prerequisite(card_id: int, prerequisite_card_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        link = session.query(CardLink).filter(
            CardLink.source_card_id == prerequisite_card_id,
            CardLink.target_card_id == card_id,
            CardLink.link_type == "prerequisite",
        ).first()
        if not link:
            error_response(40404, "前置关联不存在", 404)

        session.delete(link)
        session.commit()
        return success_response(data=None)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("remove_prerequisite failed for card %s prereq %s: %s", card_id, prerequisite_card_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"移除前置关联失败: {str(e)}")
    finally:
        session.close()
