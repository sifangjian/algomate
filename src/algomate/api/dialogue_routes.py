from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import json

dialogue_router = APIRouter()


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
    card_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


class CardGenerationResult(BaseModel):
    name: str = Field(description="算法技巧名称")
    algorithm_type: str = Field(description="算法分类")
    core_concept: str = Field(description="核心概念")
    key_points: str = Field(description="要点列表")
    code_template: str = Field(description="代码模板")
    complexity_analysis: str = Field(description="复杂度分析")
    use_cases: str = Field(description="适用场景")
    common_variants: str = Field(description="常见变体")
    typical_problems: str = Field(description="典型题目（JSON数组）")
    common_pitfalls: str = Field(description="常见坑点")
    comparison: str = Field(description="对比辨析")
    my_notes: str = Field(description="用户心得（原文）")
    difficulty: int = Field(ge=1, le=5, description="难度等级")


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
            npc_domain=npc.domain or "",
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


def _build_card_generation_prompt(
    topic: str,
    npc_domain: str,
    dialogue_messages: List[Dict[str, Any]],
    note_content: str,
) -> str:
    messages_formatted = ""
    for msg in dialogue_messages:
        role_label = "用户" if msg["role"] == "user" else "NPC"
        messages_formatted += f"**{role_label}**：{msg['content']}\n\n"

    system_prompt = """你是一个专业的算法知识整理师，擅长从对话记录和用户笔记中提取和结构化算法知识。

你的任务是根据用户与NPC的对话内容和用户笔记，生成一张完整的算法技巧卡牌。

卡牌必须包含以下10个维度，每个维度都要准确、完整、有深度：

1. 核心概念（core_concept）：算法的核心思想和原理，2-3句话概括
2. 要点列表（key_points）：关键步骤和注意事项，每条一行，3-5条
3. 代码模板（code_template）：Python伪代码或通用代码框架，包含关键注释
4. 复杂度分析（complexity_analysis）：时间复杂度和空间复杂度，附带简要推导
5. 适用场景（use_cases）：什么情况下使用该技巧，2-3个典型场景
6. 常见变体（common_variants）：该技巧的衍生版本，2-3个
7. 典型题目（typical_problems）：推荐的LeetCode题目，JSON数组格式，包含title/url/difficulty
8. 常见坑点（common_pitfalls）：易错点和边界条件，2-3条
9. 对比辨析（comparison）：与相似技巧的区别，1-2组对比
10. 我的心得（my_notes）：直接使用用户提供的笔记内容，不做修改

重要规则：
- 如果对话内容不足以填充某个维度，基于该算法领域的通用知识补充
- 典型题目必须是真实存在的LeetCode题目
- 代码模板使用Python语言
- 所有内容必须准确，不要编造不存在的算法特性"""

    user_prompt = f"""请根据以下对话记录和用户笔记，生成算法技巧卡牌。

## 对话话题
{topic}

## NPC专长领域
{npc_domain}

## 对话记录
{messages_formatted}

## 用户笔记
{note_content or '（用户未记录笔记）'}

请严格按照以下JSON格式返回卡牌内容：
{{
    "name": "算法技巧名称",
    "algorithm_type": "算法分类",
    "core_concept": "核心概念...",
    "key_points": "1. 要点一\\n2. 要点二\\n3. 要点三",
    "code_template": "def algorithm():\\n    # 代码模板\\n    pass",
    "complexity_analysis": "时间复杂度: O(...)\\n空间复杂度: O(...)",
    "use_cases": "1. 场景一\\n2. 场景二",
    "common_variants": "1. 变体一\\n2. 变体二",
    "typical_problems": "[{{\\"title\\":\\"题目标题\\",\\"url\\":\\"https://leetcode.cn/problems/xxx/\\",\\"difficulty\\":\\"Easy\\"}}]",
    "common_pitfalls": "1. 坑点一\\n2. 坑点二",
    "comparison": "与XXX的区别：...",
    "my_notes": "用户笔记原文",
    "difficulty": 3
}}"""

    return system_prompt, user_prompt


@dialogue_router.post("/start")
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

        greeting = npc.greeting or f"欢迎来到{npc.location or '这里'}！我是{npc.name}。"
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
        raise HTTPException(status_code=500, detail={"code": 50001, "message": str(e)})
    finally:
        session.close()


@dialogue_router.post("/{dialogue_id}/message")
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
        raise HTTPException(status_code=500, detail={"code": 50001, "message": str(e)})
    finally:
        session.close()


@dialogue_router.post("/{dialogue_id}/note")
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@dialogue_router.post("/{dialogue_id}/end")
async def end_dialogue(dialogue_id: int):
    from algomate.data.database import Database
    from algomate.models.dialogue_records import DialogueRecord
    from algomate.models.dialogue_messages import DialogueMessageRecord
    from algomate.models.dialogue_notes import DialogueNote
    from algomate.models.npcs import NPC
    from algomate.models.cards import Card
    from algomate.core.agent.chat_client import ChatClient
    from algomate.config.settings import AppConfig

    db = Database.get_instance()
    session = db.get_session()
    try:
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if not record:
            raise HTTPException(status_code=404, detail={"code": 40405, "message": f"对话 {dialogue_id} 不存在"})

        if record.status != "active":
            raise HTTPException(status_code=400, detail={"code": 40003, "message": "对话已结束"})

        record.status = "ended"
        session.commit()

        messages_records = (
            session.query(DialogueMessageRecord)
            .filter(DialogueMessageRecord.dialogue_id == dialogue_id)
            .order_by(DialogueMessageRecord.created_at.asc())
            .all()
        )

        note = session.query(DialogueNote).filter(DialogueNote.dialogue_id == dialogue_id).first()
        note_content = note.content if note else ""

        npc = session.query(NPC).filter(NPC.id == record.npc_id).first()

        dialogue_messages = [
            {"role": m.role, "content": m.content}
            for m in messages_records
        ]

        topic = record.topic or npc.domain if npc else ""
        npc_domain = npc.domain if npc else ""

        system_prompt, user_prompt = _build_card_generation_prompt(
            topic=topic,
            npc_domain=npc_domain,
            dialogue_messages=dialogue_messages,
            note_content=note_content,
        )

        config = AppConfig.load()
        chat_client = ChatClient(api_key=config.LLM_API_KEY, model=config.LLM_MODEL)

        card_result = None
        retry_count = 0
        max_retries = 2
        last_error = None

        while retry_count < max_retries:
            try:
                llm = chat_client._get_llm_with_structured_output(CardGenerationResult, temperature=0.5)
                from langchain_core.messages import SystemMessage, HumanMessage
                llm_messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                response = llm.invoke(llm_messages)

                if isinstance(response, CardGenerationResult):
                    card_result = response
                    break
                elif isinstance(response, dict):
                    card_result = CardGenerationResult(**response)
                    break
                else:
                    last_error = "无法解析卡牌生成结果"
                    retry_count += 1
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                import time
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)

        if card_result is None:
            return {
                "card": None,
                "dialogue_preserved": True,
                "dialogue_id": dialogue_id,
                "error": f"卡牌生成失败，对话记录已保存，可稍后重试: {last_error}",
                "retry_available": True,
            }

        existing_card = session.query(Card).filter(
            Card.npc_id == record.npc_id,
            Card.topic == record.topic,
        ).first()

        is_update = existing_card is not None

        algorithm_type_mapping = {
            "基础数据结构": "basic_data_structure",
            "栈队列与搜索": "basic_data_structure",
            "搜索与遍历": "search_traversal",
            "树结构": "tree",
            "图结构": "graph",
            "动态规划": "dynamic_programming",
            "贪心算法": "greedy",
            "回溯算法": "backtracking",
            "分治与排序": "divide_conquer",
            "数学与位运算": "math_bit",
        }
        card_algorithm_type = algorithm_type_mapping.get(npc_domain, "basic_data_structure")

        card_data = {
            "name": card_result.name,
            "algorithm_type": card_result.algorithm_type or card_algorithm_type,
            "durability": 80,
            "pending_retake": False,
            "core_concept": card_result.core_concept,
            "key_points": card_result.key_points,
            "code_template": card_result.code_template,
            "complexity_analysis": card_result.complexity_analysis,
            "use_cases": card_result.use_cases,
            "common_variants": card_result.common_variants,
            "typical_problems": card_result.typical_problems,
            "common_pitfalls": card_result.common_pitfalls,
            "comparison": card_result.comparison,
            "my_notes": note_content or card_result.my_notes,
            "visual_links": "[]",
            "npc_id": record.npc_id,
            "topic": record.topic or "",
            "review_level": 0,
            "review_count": 0,
        }

        if is_update:
            for key, value in card_data.items():
                setattr(existing_card, key, value)
            existing_card.updated_at = datetime.now()
            session.commit()
            session.refresh(existing_card)
            saved_card = existing_card
        else:
            new_card = Card(**card_data)
            session.add(new_card)
            session.commit()
            session.refresh(new_card)
            saved_card = new_card

        record.card_id = saved_card.id
        session.commit()

        if dialogue_id in _active_sessions:
            _active_sessions[dialogue_id].status = DialogueState.ENDED
            _active_sessions[dialogue_id].card_result = card_data

        return {
            "card": {
                "id": saved_card.id,
                "name": saved_card.name,
                "algorithm_type": saved_card.algorithm_type,
                "durability": saved_card.durability,
                "topic": saved_card.topic,
                "core_concept": saved_card.core_concept,
                "key_points": saved_card.key_points,
                "code_template": saved_card.code_template,
                "complexity_analysis": saved_card.complexity_analysis,
                "use_cases": saved_card.use_cases,
                "common_variants": saved_card.common_variants,
                "typical_problems": saved_card.typical_problems,
                "common_pitfalls": saved_card.common_pitfalls,
                "comparison": saved_card.comparison,
                "my_notes": saved_card.my_notes,
                "visual_links": saved_card.visual_links,
            },
            "is_update": is_update,
            "guides": {
                "go_boss": True,
                "go_workshop": True,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail={"code": 50002, "message": str(e)})
    finally:
        session.close()


@dialogue_router.get("/{dialogue_id}/history")
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

        return {
            "dialogue_id": record.id,
            "npc_id": record.npc_id,
            "npc_name": npc.name if npc else "未知NPC",
            "topic": record.topic,
            "status": record.status,
            "messages": messages,
            "note": note_data,
            "card_id": record.card_id,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@dialogue_router.post("/{dialogue_id}/heartbeat")
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
