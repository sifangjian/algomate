import json
from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Query
from algomate.data.database import Database
from algomate.models.cards import Card, CardCreate, CardUpdate, _normalize_content
from algomate.models.card_links import CardLink, LinkCreate, LinkResponse
from algomate.core.game.durability import compute_card_status

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
        "dialogue_id": card.dialogue_id,
        "topic": card.topic,
        "status": compute_card_status(card.durability, card.pending_retake),
        "basic_content": _parse_json_field(card.basic_content),
        "practical_content": _parse_json_field(card.practical_content),
        "advanced_content": _parse_json_field(card.advanced_content),
        "my_notes": card.my_notes,
        "visual_links": card.visual_links,
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "updated_at": card.updated_at.isoformat() if card.updated_at else None,
    }


EDITABLE_FIELDS = {
    "basic_content", "practical_content", "advanced_content",
    "my_notes", "visual_links",
}


@router.get("/graph")
async def get_graph():
    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).all()
        links = session.query(CardLink).all()
        nodes = [
            {"id": c.id, "name": c.name, "algorithm_type": c.algorithm_type}
            for c in cards
        ]
        edges = [
            {
                "source": l.source_card_id,
                "target": l.target_card_id,
                "link_type": l.link_type,
                "source_keyword": l.source_keyword,
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
                | (Card.basic_content.ilike(keyword_pattern))
                | (Card.practical_content.ilike(keyword_pattern))
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
            if key in ("basic_content", "practical_content", "advanced_content"):
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
            if key in ("basic_content", "practical_content", "advanced_content"):
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


@router.post("")
async def create_card(card_data: CardCreate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        card = Card(
            name=card_data.name,
            algorithm_type=card_data.algorithm_type or "",
            durability=card_data.durability,
            npc_id=card_data.npc_id,
            dialogue_id=card_data.dialogue_id,
            topic=card_data.topic or "",
            basic_content=_normalize_content(card_data.basic_content, None),
            practical_content=_normalize_content(card_data.practical_content, None),
            advanced_content=_normalize_content(card_data.advanced_content, None),
            my_notes=card_data.my_notes or "",
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


@router.post("/polish")
async def polish_card(request: dict):
    from algomate.core.agent.chat_client import ChatClient
    from algomate.config.settings import AppConfig

    content = request.get("content", "")
    field_type = request.get("type", "")

    if not content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")

    try:
        config = AppConfig.load()
        client = ChatClient(api_key=config.LLM_API_KEY)

        FIELD_LABELS = {
            "concept_definition": "概念定义",
            "features": "特点",
            "confusing_concepts": "易混淆概念",
            "applicable_scenarios": "适用场景",
            "precautions": "注意事项",
            "common_mistakes": "易错点",
            "extensions": "拓展方向",
            "advanced_solutions": "高级解法",
            "problem": "题目描述",
            "principle": "原理说明",
            "my_notes": "个人笔记",
        }
        label = FIELD_LABELS.get(field_type, field_type)

        system_prompt = f"""你是算法知识整理师。请润色以下算法卡牌的「{label}」内容。
要求：
1. 保持技术准确性
2. 使表述更清晰、结构化
3. 保留原文的核心信息
4. 直接返回润色后的内容，不要额外解释"""

        result = client.chat(
            messages=[{"role": "user", "content": content}],
            system_prompt=system_prompt,
        )

        return success_response(data={"polished_content": result.strip()})
    except Exception as e:
        logger.error("polish_card failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI润色失败: {str(e)}")


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
