import json
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from algomate.config.settings import AppConfig
from algomate.core.agent.chat_client import ChatClient

router = APIRouter(prefix="/quick-ask", tags=["旁问"])
logger = logging.getLogger(__name__)


class QuickAskRequest(BaseModel):
    npc_id: int
    content: str
    npc_name: Optional[str] = ""
    history: Optional[List[dict]] = []


@router.post("")
async def quick_ask(request: QuickAskRequest):
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="content 不能为空")
    if len(request.content) > 500:
        raise HTTPException(status_code=400, detail="content 不能超过 500 字")

    npc_name = request.npc_name or "导师"
    system_prompt = (
        f"你是{npc_name}，一位算法导师。"
        "用户在修习过程中临时问了一个旁问（与主修习对话无关的问题）。"
        "请简洁明了地回答，不需要追问或推荐后续话题。"
        "回答控制在 200 字以内。"
    )

    messages = list(request.history or [])
    messages.append({"role": "user", "content": request.content})

    def generate():
        try:
            config = AppConfig.load()
            client = ChatClient(api_key=config.LLM_API_KEY)
            for chunk in client.stream_chat_with_suggestions(
                messages=messages,
                system_prompt=system_prompt,
            ):
                yield chunk
        except Exception as e:
            logger.error("quick_ask failed: %s", e, exc_info=True)
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
