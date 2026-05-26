import json
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter(prefix="/dialogues", tags=["对话"])
logger = logging.getLogger(__name__)


class DialogueState(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    TIMED_OUT = "timed_out"


@dataclass
class DialogueSession:
    dialogue_id: Optional[int]
    npc_id: int
    npc_name: str
    npc_domain: str
    npc_system_prompt: str
    topic: str
    status: DialogueState
    messages: List[Dict[str, Any]] = field(default_factory=list)
    note_content: str = ""
    last_active_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


_active_sessions: Dict[int, DialogueSession] = {}


def _get_session(dialogue_id: int):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord
    from algomate.models.npcs import NPC

    if dialogue_id in _active_sessions:
        return _active_sessions[dialogue_id]

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            return None

        npc = session.query(NPC).filter(NPC.id == record.npc_id).first()
        if not npc:
            return None

        messages_records = (
            session.query(DialogueMessageRecord)
            .filter(DialogueMessageRecord.dialogue_id == dialogue_id)
            .order_by(DialogueMessageRecord.created_at.asc())
            .all()
        )

        messages = [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages_records
        ]

        dialogue_session = DialogueSession(
            dialogue_id=record.id,
            npc_id=record.npc_id,
            npc_name=npc.name,
            npc_domain=npc.algorithm_type or npc.domain or "",
            npc_system_prompt=npc.system_prompt or "",
            topic=record.topic or "",
            status=DialogueState(record.status) if record.status else DialogueState.ACTIVE,
            messages=messages,
            last_active_at=record.last_active_at or record.created_at,
            created_at=record.created_at,
        )

        _active_sessions[dialogue_id] = dialogue_session
        return dialogue_session
    finally:
        session.close()


def _build_enhanced_system_prompt(npc_system_prompt: str, npc_domain: str, topics: List[str]) -> str:
    topics_str = "、".join(topics) if topics else npc_domain
    domain_boundary = f"""

## 专长边界规则
- 你只能回答与 {npc_domain} 相关的问题
- 如果用户问的问题明显超出你的专长范围（如数学问题、生活问题、其他算法领域），请礼貌地说明你的专长范围，并引导用户回到你擅长的领域
- 回复格式：'这个问题超出了我的专长范围，我主要擅长{npc_domain}方面的知识。你可以问我关于{topics_str}的问题！'
- 不要尝试回答超出专长的问题，即使你知道答案"""
    return npc_system_prompt + domain_boundary


@router.post("/start")
async def start_dialogue(request: dict):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord
    from algomate.models.npcs import NPC
    from algomate.models.cards import Card

    npc_id = request.get("npc_id")
    topic = request.get("topic", "")

    if not npc_id:
        raise HTTPException(status_code=400, detail={"code": 40001, "message": "npc_id不能为空"})

    db = Database.get_instance()
    session = db.get_session()
    try:
        npc = session.query(NPC).filter(NPC.id == npc_id).first()
        if not npc:
            raise HTTPException(status_code=404, detail={"code": 40402, "message": f"NPC {npc_id} 不存在"})

        now = datetime.now()
        dialogue_record = DialogueRecord(
            npc_id=npc_id,
            topic=topic,
            status="active",
            last_active_at=now,
            created_at=now,
        )
        session.add(dialogue_record)
        session.commit()
        session.refresh(dialogue_record)

        topics = json.loads(npc.topics) if npc.topics else []
        specialties = json.loads(npc.specialties) if npc.specialties else []

        specialties_str = ""
        if specialties:
            specialties_str = f"\n\n🎯 **我的专长**：{'、'.join(specialties[:4])}"

        base_greeting = npc.greeting or f"欢迎来到{npc.location or '这里'}！我是{npc.name}，{npc.title or npc.domain or '导师'}。"
        greeting = base_greeting + specialties_str
        if topic:
            greeting = f"欢迎回来！让我们继续修习「{topic}」吧。" if greeting else f"让我们开始修习「{topic}」吧！"

        greeting_message = DialogueMessageRecord(
            dialogue_id=dialogue_record.id,
            role="assistant",
            content=greeting,
            created_at=now,
        )
        session.add(greeting_message)
        session.commit()

        existing_card = None
        if topic:
            card = session.query(Card).filter(
                Card.npc_id == npc_id,
                Card.topic == topic,
            ).first()
            if card:
                existing_card = {
                    "id": card.id,
                    "name": card.name,
                    "topic": card.topic,
                    "durability": card.durability,
                    "created_at": card.created_at.isoformat() if card.created_at else None,
                }

        dialogue_session = DialogueSession(
            dialogue_id=dialogue_record.id,
            npc_id=npc_id,
            npc_name=npc.name,
            npc_domain=npc.domain or "",
            npc_system_prompt=npc.system_prompt or "",
            topic=topic,
            status=DialogueState.ACTIVE,
            messages=[{"role": "assistant", "content": greeting, "created_at": now.isoformat()}],
            last_active_at=now,
            created_at=now,
        )
        _active_sessions[dialogue_record.id] = dialogue_session

        return {
            "dialogue_id": dialogue_record.id,
            "npc_name": npc.name,
            "npc_avatar": npc.avatar,
            "greeting": greeting,
            "topics": topics,
            "existing_card": existing_card,
            "status": "active",
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("start_dialogue failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail={"code": 50001, "message": str(e)})
    finally:
        session.close()


@router.post("/{dialogue_id}/message")
async def send_message(dialogue_id: int, request: dict):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord
    from algomate.models.npcs import NPC
    from algomate.core.agent.chat_client import ChatClient
    from algomate.config.settings import AppConfig

    content = request.get("content", "")

    if not content:
        raise HTTPException(status_code=400, detail={"code": 40001, "message": "content不能为空"})
    if len(content) > 500:
        raise HTTPException(status_code=400, detail={"code": 40001, "message": "content不能超过500字"})

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": f"对话 {dialogue_id} 不存在"})

        if record.status != "active":
            raise HTTPException(status_code=400, detail={"code": 40003, "message": "对话已结束"})

        now = datetime.now()
        record.last_active_at = now

        user_message = DialogueMessageRecord(
            dialogue_id=dialogue_id,
            role="user",
            content=content,
            created_at=now,
        )
        session.add(user_message)
        session.commit()

        npc = session.query(NPC).filter(NPC.id == record.npc_id).first()
        if not npc:
            raise HTTPException(status_code=404, detail={"code": 40402, "message": f"NPC {record.npc_id} 不存在"})

        topics = json.loads(npc.topics) if npc.topics else []
        enhanced_prompt = _build_enhanced_system_prompt(npc.system_prompt, npc.domain or "", topics)

        messages_records = (
            session.query(DialogueMessageRecord)
            .filter(DialogueMessageRecord.dialogue_id == dialogue_id)
            .order_by(DialogueMessageRecord.created_at.asc())
            .all()
        )

        conversation_history = []
        for m in messages_records:
            conversation_history.append({"role": m.role, "content": m.content})

        max_context_messages = 40
        if len(conversation_history) > max_context_messages:
            conversation_history = conversation_history[-max_context_messages:]

        config = AppConfig.load()
        chat_client = ChatClient(api_key=config.LLM_API_KEY, model=config.LLM_MODEL)

        def generate():
            full_content = ""
            try:
                for chunk in chat_client.stream_chat_with_suggestions(
                    messages=conversation_history,
                    system_prompt=enhanced_prompt,
                ):
                    yield chunk
                    if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
                        try:
                            data_str = chunk.replace("data: ", "").strip()
                            if data_str and data_str != "[DONE]":
                                data = json.loads(data_str)
                                if "content" in data:
                                    full_content += data["content"]
                        except (json.JSONDecodeError, ValueError):
                            pass

                db2 = Database.get_instance()
                session2 = db2.get_session()
                try:
                    npc_response = DialogueMessageRecord(
                        dialogue_id=dialogue_id,
                        role="assistant",
                        content=full_content,
                        created_at=datetime.now(),
                    )
                    session2.add(npc_response)

                    dialogue_rec = session2.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
                    if dialogue_rec:
                        dialogue_rec.last_active_at = datetime.now()

                    session2.commit()
                finally:
                    session2.close()

                if dialogue_id in _active_sessions:
                    _active_sessions[dialogue_id].messages.append(
                        {"role": "user", "content": content, "created_at": now.isoformat()}
                    )
                    _active_sessions[dialogue_id].messages.append(
                        {"role": "assistant", "content": full_content, "created_at": datetime.now().isoformat()}
                    )
                    _active_sessions[dialogue_id].last_active_at = datetime.now()

                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error("send_message stream error for dialogue %s: %s", dialogue_id, e, exc_info=True)
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("send_message failed for dialogue %s: %s", dialogue_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail={"code": 50001, "message": str(e)})
    finally:
        session.close()


@router.post("/{dialogue_id}/note")
async def save_note(dialogue_id: int, request: dict):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_notes import DialogueNote

    content = request.get("content", "")

    if not content:
        raise HTTPException(status_code=400, detail={"code": 40001, "message": "content不能为空"})

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": f"对话 {dialogue_id} 不存在"})

        now = datetime.now()
        existing_note = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).first()

        if existing_note:
            existing_note.content = content
            existing_note.updated_at = now
            session.commit()
            note_id = existing_note.id
            saved_at = existing_note.updated_at.isoformat()
        else:
            new_note = DialogueNote(
                dialogue_id=dialogue_id,
                content=content,
                created_at=now,
                updated_at=now,
            )
            session.add(new_note)
            session.commit()
            session.refresh(new_note)
            note_id = new_note.id
            saved_at = new_note.updated_at.isoformat()

        if dialogue_id in _active_sessions:
            _active_sessions[dialogue_id].note_content = content

        return {
            "saved": True,
            "note_id": note_id,
            "saved_at": saved_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("save_note failed for dialogue %s: %s", dialogue_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{dialogue_id}/end")
async def end_dialogue(dialogue_id: int):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord
    from algomate.models.dialogue_notes import DialogueNote
    from algomate.models.cards import Card

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": f"对话 {dialogue_id} 不存在"})

        if record.status != "active":
            raise HTTPException(status_code=400, detail={"code": 40003, "message": "对话已结束"})

        # 查询本次对话期间创建的卡牌
        dialogue_cards = session.query(Card).filter(
            Card.dialogue_id == dialogue_id
        ).all()

        if not dialogue_cards:
            # 无卡牌 → 放弃本次对话，删除记录
            session.query(DialogueNote).filter(DialogueNote.dialogue_id == dialogue_id).delete()
            session.query(DialogueMessageRecord).filter(DialogueMessageRecord.dialogue_id == dialogue_id).delete()
            session.delete(record)
            session.commit()

            if dialogue_id in _active_sessions:
                del _active_sessions[dialogue_id]

            return {
                "abandoned": True,
                "message": "本次修习未创建卡牌，记录已放弃",
            }

        # 有卡牌 → 保留记录
        record.status = "ended"
        record.card_id = dialogue_cards[0].id
        session.commit()

        if dialogue_id in _active_sessions:
            _active_sessions[dialogue_id].status = DialogueState.ENDED

        from algomate.core.guide.service import GuideService
        from algomate.models.bosses import Boss

        has_available_boss = session.query(Boss).filter(
            Boss.npc_id == record.npc_id
        ).first() is not None

        guide_service = GuideService()
        guides = guide_service.generate_guides(
            scene="after_dialogue",
            card={"id": dialogue_cards[0].id, "name": dialogue_cards[0].name},
            has_available_boss=has_available_boss,
        )

        cards_data = [
            {
                "id": c.id,
                "name": c.name,
                "algorithm_type": c.algorithm_type,
                "durability": c.durability,
                "topic": c.topic,
            }
            for c in dialogue_cards
        ]

        return {
            "cards": cards_data,
            "dialogue_id": dialogue_id,
            "guides": guides.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("end_dialogue failed for dialogue %s: %s", dialogue_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail={"code": 50002, "message": str(e)})
    finally:
        session.close()


@router.get("/by-card/{card_id}")
async def get_dialogue_by_card(card_id: int):
    from algomate.data.database import Database
    from algomate.models.cards import Card
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord
    from algomate.models.npcs import NPC

    db = Database.get_instance()
    session = db.get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail={"code": 40404, "message": "卡牌不存在"})

        if not card.dialogue_id:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": "该卡牌没有关联的对话记录"})

        record = session.query(DialogueRecord).filter(DialogueRecord.id == card.dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": "对话记录不存在"})

        npc = session.query(NPC).filter(NPC.id == record.npc_id).first()
        msg_count = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == record.id
        ).count()

        return {
            "dialogue_id": record.id,
            "npc_id": record.npc_id,
            "npc_name": npc.name if npc else "未知NPC",
            "topic": record.topic,
            "status": record.status,
            "message_count": msg_count,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_dialogue_by_card failed for card %s: %s", card_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{dialogue_id}/resume")
async def resume_dialogue(dialogue_id: int):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord
    from algomate.models.npcs import NPC

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": f"对话 {dialogue_id} 不存在"})

        if record.status == "active":
            npc = session.query(NPC).filter(NPC.id == record.npc_id).first()
            return {
                "dialogue_id": record.id,
                "npc_id": record.npc_id,
                "npc_name": npc.name if npc else "",
                "topic": record.topic,
                "status": "active",
                "message": "对话仍在进行中",
            }

        record.status = "active"
        record.last_active_at = datetime.now()

        resume_msg = DialogueMessageRecord(
            dialogue_id=dialogue_id,
            role="assistant",
            content="欢迎回来！让我们继续修习吧。",
            created_at=datetime.now(),
        )
        session.add(resume_msg)
        session.commit()

        if dialogue_id in _active_sessions:
            _active_sessions[dialogue_id].status = DialogueState.ACTIVE

        npc = session.query(NPC).filter(NPC.id == record.npc_id).first()
        return {
            "dialogue_id": record.id,
            "npc_id": record.npc_id,
            "npc_name": npc.name if npc else "",
            "topic": record.topic,
            "status": "active",
            "greeting": "欢迎回来！让我们继续修习吧。",
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("resume_dialogue failed for dialogue %s: %s", dialogue_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.delete("/{dialogue_id}/messages")
async def clear_dialogue_messages(dialogue_id: int):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": f"对话 {dialogue_id} 不存在"})

        deleted = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue_id
        ).delete()
        session.commit()

        return {"deleted_count": deleted, "message": "对话记录已清空"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("clear_dialogue_messages failed for dialogue %s: %s", dialogue_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/{dialogue_id}/history")
async def get_dialogue_history(dialogue_id: int):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord
    from algomate.models.dialogue_notes import DialogueNote
    from algomate.models.npcs import NPC

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": f"对话 {dialogue_id} 不存在"})

        npc = session.query(NPC).filter(NPC.id == record.npc_id).first()

        messages_records = (
            session.query(DialogueMessageRecord)
            .filter(DialogueMessageRecord.dialogue_id == dialogue_id)
            .order_by(DialogueMessageRecord.created_at.asc())
            .all()
        )

        messages = [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages_records
        ]

        note = session.query(DialogueNote).filter(DialogueNote.dialogue_id == dialogue_id).first()
        note_data = None
        if note:
            note_data = {
                "content": note.content,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None,
            }

        from algomate.models.cards import Card as CardModel
        dialogue_cards = session.query(CardModel).filter(
            CardModel.dialogue_id == dialogue_id
        ).all()
        cards_data = [
            {
                "id": c.id,
                "name": c.name,
                "algorithm_type": c.algorithm_type,
                "durability": c.durability,
                "topic": c.topic,
            }
            for c in dialogue_cards
        ]

        return {
            "dialogue_id": record.id,
            "npc_id": record.npc_id,
            "npc_name": npc.name if npc else "未知NPC",
            "topic": record.topic,
            "status": record.status,
            "messages": messages,
            "note": note_data,
            "card_id": record.card_id,
            "cards": cards_data,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_dialogue_history failed for dialogue %s: %s", dialogue_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{dialogue_id}/heartbeat")
async def heartbeat(dialogue_id: int):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": f"对话 {dialogue_id} 不存在"})

        now = datetime.now()
        record.last_active_at = now
        if record.status == "timed_out":
            record.status = "active"
        session.commit()

        if dialogue_id in _active_sessions:
            _active_sessions[dialogue_id].last_active_at = now
            if _active_sessions[dialogue_id].status == DialogueState.TIMED_OUT:
                _active_sessions[dialogue_id].status = DialogueState.ACTIVE

        return {
            "alive": True,
            "last_active_at": now.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("heartbeat failed for dialogue %s: %s", dialogue_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
