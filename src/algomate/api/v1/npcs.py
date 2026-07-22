import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func

from algomate.models.npcs import NPC

router = APIRouter(prefix="/npcs", tags=["导师"])
logger = logging.getLogger(__name__)

RECOMMENDED_LEARNING_PATH = [
    {"order": 1, "npc_name": "基础数据结构", "algorithm_type": "basic_data_structure", "stage": "基础入门", "goal": "掌握数组、链表、哈希表等基础数据结构"},
    {"order": 2, "npc_name": "搜索与基础", "algorithm_type": "stack_queue_search", "stage": "搜索基础", "goal": "掌握栈队列、二分查找、前缀和"},
    {"order": 3, "npc_name": "搜索进阶", "algorithm_type": "search_traversal", "stage": "搜索进阶", "goal": "掌握滑动窗口、DFS/BFS、拓扑排序"},
    {"order": 4, "npc_name": "树结构", "algorithm_type": "tree", "stage": "树结构", "goal": "掌握二叉树遍历、BST、堆与优先队列"},
    {"order": 5, "npc_name": "图结构", "algorithm_type": "graph", "stage": "图结构", "goal": "掌握图的遍历、最短路径、并查集"},
    {"order": 6, "npc_name": "回溯算法", "algorithm_type": "backtracking", "stage": "回溯算法", "goal": "掌握递归、回溯、剪枝技巧"},
    {"order": 7, "npc_name": "贪心算法", "algorithm_type": "greedy", "stage": "贪心算法", "goal": "掌握贪心选择、区间问题、构造策略"},
    {"order": 8, "npc_name": "动态规划", "algorithm_type": "dynamic_programming", "stage": "动态规划", "goal": "掌握线性DP、背包问题、子序列DP"},
    {"order": 9, "npc_name": "分治与排序", "algorithm_type": "divide_conquer", "stage": "分治与排序", "goal": "掌握分治思想、排序算法、单调栈/队列"},
    {"order": 10, "npc_name": "数学与位运算", "algorithm_type": "math_bit", "stage": "数学与位运算", "goal": "掌握位运算、数学技巧、字符串算法"},
]

VALID_ALGORITHM_TYPES = {step["algorithm_type"] for step in RECOMMENDED_LEARNING_PATH}

DEFAULT_NPCS = [
    {
        "name": "基础数据结构",
        "title": "基础数据结构",
        "algorithm_type": "basic_data_structure",
        "specialties": ["数组与双指针", "链表", "哈希表"],
        "avatar": "📚",
        "description": "掌握数组、链表、哈希表等基础数据结构是算法学习的第一步。这些是构建复杂算法的基石，必须扎实掌握。",
        "topics": ["数组与双指针", "链表", "哈希表"],
        "system_prompt": "你是基础数据结构导师。你以清晰、系统的方式教授数组与双指针、链表、哈希表等核心技巧。你的教学风格是先讲概念，再举例说明，最后让学生思考应用场景。",
        "greeting": "欢迎学习基础数据结构！这是算法学习的基石。让我们从数组、链表和哈希表开始，打好坚实的基础。",
    },
    {
        "name": "搜索与基础",
        "title": "搜索与基础",
        "algorithm_type": "stack_queue_search",
        "specialties": ["栈与队列", "二分查找", "前缀和"],
        "avatar": "🔍",
        "description": "栈与队列是基础数据结构的延伸，二分查找是高效搜索的核心，前缀和是解决区间问题的利器。",
        "topics": ["栈与队列", "二分查找", "前缀和"],
        "system_prompt": "你是搜索与基础导师。你以严谨的逻辑教授栈与队列、二分查找、前缀和等技巧。你善于用生活比喻解释抽象概念。",
        "greeting": "欢迎学习搜索与基础算法！让我用严谨的逻辑带你理解栈与队列的奥妙，掌握二分查找与前缀和的精髓。",
    },
    {
        "name": "搜索进阶",
        "title": "搜索进阶",
        "algorithm_type": "search_traversal",
        "specialties": ["滑动窗口", "DFS", "BFS", "拓扑排序"],
        "avatar": "🌊",
        "description": "滑动窗口、深度优先搜索(DFS)、广度优先搜索(BFS)和拓扑排序是解决复杂搜索问题的核心技巧。",
        "topics": ["滑动窗口", "DFS", "BFS", "拓扑排序"],
        "system_prompt": "你是搜索进阶导师。你以实战导向的方式教授滑动窗口、DFS与BFS、拓扑排序等搜索进阶技巧。你善于引导学生从暴力解法优化到高效算法。",
        "greeting": "欢迎学习搜索进阶算法！让我带你从暴力到高效，掌握滑动窗口与搜索遍历的进阶技巧。",
    },
    {
        "name": "树结构",
        "title": "树结构",
        "algorithm_type": "tree",
        "specialties": ["二叉树遍历", "二叉搜索树", "堆与优先队列"],
        "avatar": "🌳",
        "description": "二叉树是最重要的非线性数据结构之一，掌握二叉树遍历、二叉搜索树和堆是进阶算法的必经之路。",
        "topics": ["二叉树遍历", "二叉搜索树", "堆与优先队列"],
        "system_prompt": "你是树结构导师。你以自然比喻教授二叉树遍历、二叉搜索树、堆与优先队列等树相关技巧。你善于用树的生长过程解释递归结构。",
        "greeting": "欢迎学习树结构！让我用自然的智慧带你领悟二叉树的递归之美，掌握搜索树与优先队列的精髓。",
    },
    {
        "name": "图结构",
        "title": "图结构",
        "algorithm_type": "graph",
        "specialties": ["图的遍历", "最短路径", "并查集"],
        "avatar": "🗺️",
        "description": "图结构是描述复杂关系的强大工具，图的遍历、最短路径和并查集是解决图论问题的核心方法。",
        "topics": ["图的遍历", "最短路径", "并查集"],
        "system_prompt": "你是图结构导师。你以系统化的方式教授图的遍历、最短路径、并查集等图论技巧。你善于将复杂问题建模为图论问题。",
        "greeting": "欢迎学习图结构！万物皆可成图，让我教你如何将复杂问题建模为图论模型，系统化地攻克遍历、最短路径与并查集。",
    },
    {
        "name": "回溯算法",
        "title": "回溯算法",
        "algorithm_type": "backtracking",
        "specialties": ["递归", "回溯", "剪枝技巧", "组合与排列"],
        "avatar": "🔄",
        "description": "回溯算法是解决组合、排列、子集等问题的通用方法，核心在于'尝试-回退-再尝试'的搜索过程。",
        "topics": ["递归", "回溯", "剪枝技巧", "组合与排列"],
        "system_prompt": "你是回溯算法导师。你以探索的方式教授递归、回溯、剪枝技巧、组合与排列。你善于让学生理解'尝试-回退-再尝试'的搜索过程。",
        "greeting": "欢迎学习回溯算法！每一条路都通向新的发现，让我带你体验'尝试-回退-再尝试'的回溯之美，掌握剪枝与组合排列的精髓。",
    },
    {
        "name": "贪心算法",
        "title": "贪心算法",
        "algorithm_type": "greedy",
        "specialties": ["贪心选择", "区间问题", "构造策略"],
        "avatar": "⚖️",
        "description": "贪心算法通过每一步的最优选择来达到全局最优，是解决区间问题、调度问题等的高效方法。",
        "topics": ["贪心选择", "区间问题", "构造策略"],
        "system_prompt": "你是贪心算法导师。你以果断决策的方式教授贪心选择、区间问题、构造策略。你善于让学生理解'局部最优→全局最优'的条件和反例。",
        "greeting": "欢迎学习贪心算法！贪心之道，在于果断抉择。让我教你何时局部最优可推全局最优，以及如何识破贪心的陷阱。",
    },
    {
        "name": "动态规划",
        "title": "动态规划",
        "algorithm_type": "dynamic_programming",
        "specialties": ["线性DP", "背包问题", "子序列DP"],
        "avatar": "💡",
        "description": "动态规划是算法中的'皇冠明珠'，通过将问题分解为子问题并利用记忆化技术避免重复计算。",
        "topics": ["线性DP", "背包问题", "子序列DP"],
        "system_prompt": "你是动态规划导师。你以循序渐进的方式教授线性DP、背包问题、子序列DP。你善于引导学生从递归暴力解→记忆化→DP表的过程。",
        "greeting": "欢迎学习动态规划！这是算法的至高智慧，让我带你从递归暴力出发，经历记忆化到DP表的蜕变，领悟线性DP、背包与子序列的奥秘。",
    },
    {
        "name": "分治与排序",
        "title": "分治与排序",
        "algorithm_type": "divide_conquer",
        "specialties": ["分治思想", "排序算法", "单调栈", "单调队列"],
        "avatar": "🔪",
        "description": "分治思想是'分而治之'的经典策略，排序算法是基础，单调栈和单调队列是处理特定问题的高效工具。",
        "topics": ["分治思想", "排序算法", "单调栈", "单调队列"],
        "system_prompt": "你是分治与排序导师。你以分解-解决-合并的框架教授分治思想、排序算法、单调栈/队列。你善于让学生理解'大问题拆小问题'的核心思想。",
        "greeting": "欢迎学习分治与排序！分裂之道，在于化大为小。让我教你用'分解-解决-合并'的框架，掌握分治、排序与单调数据结构的精髓。",
    },
    {
        "name": "数学与位运算",
        "title": "数学与位运算",
        "algorithm_type": "math_bit",
        "specialties": ["位运算", "数学技巧", "字符串算法"],
        "avatar": "🔢",
        "description": "位运算是处理二进制数据的高效技巧，数学技巧是解决特定问题的关键，字符串算法是处理文本数据的基础。",
        "topics": ["位运算", "数学技巧", "字符串算法"],
        "system_prompt": "你是数学与位运算导师。你以数学之美的方式教授位运算、数学技巧、字符串算法。你善于揭示数字和比特背后的规律。",
        "greeting": "欢迎学习数学与位运算！数字与比特蕴含无穷奥秘，让我带你揭示位运算的魔法、数学技巧的优雅与字符串算法的精妙。",
    },
]


def init_default_npcs_v1():
    from algomate.data.database import Database
    from algomate.models.cards import Card
    from algomate.models.dialogue_records import DialogueRecord

    db = Database.get_instance()
    session = db.get_session()
    try:
        existing_npcs = session.query(NPC).order_by(NPC.id.asc()).all()

        if existing_npcs:
            needs_recreate = False
            for npc in existing_npcs:
                if not npc.algorithm_type or not npc.title or not npc.specialties:
                    needs_recreate = True
                    break

            if not needs_recreate:
                return

            new_npcs_list = []
            for npc_data in DEFAULT_NPCS:
                npc = NPC(
                    name=npc_data["name"],
                    title=npc_data["title"],
                    algorithm_type=npc_data["algorithm_type"],
                    specialties=json.dumps(npc_data["specialties"], ensure_ascii=False),
                    avatar=npc_data["avatar"],
                    description=npc_data["description"],
                    topics=json.dumps(npc_data["topics"], ensure_ascii=False),
                    system_prompt=npc_data["system_prompt"],
                    greeting=npc_data["greeting"],
                    domain=npc_data["algorithm_type"],
                    location=npc_data["algorithm_type"],
                )
                session.add(npc)
                new_npcs_list.append(npc)

            session.flush()

            for npc in new_npcs_list:
                session.refresh(npc)

            default_npc_id = new_npcs_list[0].id if new_npcs_list else None

            if default_npc_id:
                all_cards = session.query(Card).all()
                for card in all_cards:
                    card.npc_id = default_npc_id

                all_dialogues = session.query(DialogueRecord).all()
                for dialogue in all_dialogues:
                    dialogue.npc_id = default_npc_id

            session.flush()

            for npc in existing_npcs:
                session.delete(npc)

            session.commit()
            return

        for npc_data in DEFAULT_NPCS:
            npc = NPC(
                name=npc_data["name"],
                title=npc_data["title"],
                algorithm_type=npc_data["algorithm_type"],
                specialties=json.dumps(npc_data["specialties"], ensure_ascii=False),
                avatar=npc_data["avatar"],
                description=npc_data["description"],
                topics=json.dumps(npc_data["topics"], ensure_ascii=False),
                system_prompt=npc_data["system_prompt"],
                greeting=npc_data["greeting"],
                domain=npc_data["algorithm_type"],
                location=npc_data["algorithm_type"],
            )
            session.add(npc)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("init_default_npcs_v1 failed: %s", e, exc_info=True)
        raise e
    finally:
        session.close()


def _parse_json_field(value: str) -> list:
    try:
        result = json.loads(value) if value else []
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


@router.get("")
async def get_npcs(
    algorithm_type: Optional[str] = Query(None, description="按算法类型筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
):
    from algomate.data.database import Database
    from algomate.models.cards import Card

    init_default_npcs_v1()

    db = Database.get_instance()
    session = db.get_session()
    try:
        if algorithm_type and algorithm_type not in VALID_ALGORITHM_TYPES:
            raise HTTPException(status_code=400, detail={"code": 40001, "message": f"非法的算法类型: {algorithm_type}"})

        query = session.query(NPC)

        if algorithm_type:
            query = query.filter(NPC.algorithm_type == algorithm_type)

        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                NPC.name.ilike(pattern)
                | NPC.title.ilike(pattern)
                | NPC.specialties.ilike(pattern)
            )

        npcs = query.order_by(NPC.id.asc()).all()

        result = []
        for npc in npcs:
            card_count = session.query(Card).filter(Card.npc_id == npc.id).count()
            result.append({
                "id": npc.id,
                "name": npc.name,
                "title": npc.title,
                "algorithm_type": npc.algorithm_type,
                "specialties": _parse_json_field(npc.specialties),
                "avatar": npc.avatar,
                "card_count": card_count,
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "npcs": result,
                "learning_path": RECOMMENDED_LEARNING_PATH,
            },
        }
    finally:
        session.close()


@router.get("/{npc_id}")
async def get_npc_detail(npc_id: int):
    from algomate.data.database import Database
    from algomate.models.cards import Card

    db = Database.get_instance()
    session = db.get_session()
    try:
        npc = session.query(NPC).filter(NPC.id == npc_id).first()
        if not npc:
            raise HTTPException(status_code=404, detail={"code": 40402, "message": "NPC 不存在"})

        topics = _parse_json_field(npc.topics)
        card_count = session.query(Card).filter(Card.npc_id == npc_id).count()

        enhanced_topics = []
        for topic_name in topics:
            has_card = session.query(Card).filter(
                Card.npc_id == npc_id,
                Card.topic == topic_name,
            ).first() is not None
            enhanced_topics.append({
                "name": topic_name,
                "has_card": has_card,
            })

        REALM_NAME_TO_ID = {
            "基础数据结构": "basic_data_structure",
            "搜索与基础": "stack_queue_search",
            "搜索进阶": "search_traversal",
            "树结构": "tree",
            "图结构": "graph",
            "回溯算法": "backtracking",
            "贪心算法": "greedy",
            "动态规划": "dynamic_programming",
            "分治与排序": "divide_conquer",
            "数学与位运算": "math_bit",
        }
        realm_id = REALM_NAME_TO_ID.get(npc.location, npc.location)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "id": npc.id,
                "name": npc.name,
                "title": npc.title,
                "algorithm_type": npc.algorithm_type,
                "specialties": _parse_json_field(npc.specialties),
                "avatar": npc.avatar,
                "description": npc.description,
                "topics": enhanced_topics,
                "card_count": card_count,
                "domain": npc.domain,
                "realmId": realm_id,
                "location": npc.location,
                "greeting": npc.greeting,
                "expertise": topics,
            },
        }
    finally:
        session.close()


@router.post("/{npc_id}/chat")
async def npc_chat(npc_id: int, request: dict):
    from algomate.core.flow.npc_dialogue import NPCDialogueFlow
    import httpx

    message = request.get("message")
    session_id = request.get("sessionId")

    if not message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    try:
        flow = NPCDialogueFlow.get_instance()
        if session_id is None:
            session_result = await flow.start_dialogue(npc_id, None)
            new_session_id = session_result.dialogue_id
            result = await flow.continue_dialogue(new_session_id, message)
            if "suggestions" not in result:
                result["suggestions"] = []
            return result
        else:
            result = await flow.continue_dialogue(int(session_id), message)
            if "suggestions" not in result:
                result["suggestions"] = []
            return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI服务响应超时，请稍后重试")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        raise HTTPException(status_code=502, detail=f"AI服务暂时不可用: {str(e)}")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="AI服务连接失败，请检查网络或稍后重试")
    except Exception as e:
        error_msg = str(e).lower()
        logger.error("npc_chat failed: %s", e, exc_info=True)
        if "timeout" in error_msg or "timed out" in error_msg:
            raise HTTPException(status_code=504, detail="AI服务响应超时，请稍后重试")
        if "connection" in error_msg or "network" in error_msg:
            raise HTTPException(status_code=503, detail="AI服务连接失败，请稍后重试")
        if "rate limit" in error_msg or "429" in error_msg:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        if "api key" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            raise HTTPException(status_code=500, detail="AI服务认证失败，请检查API配置")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{npc_id}/chat/stream")
async def npc_chat_stream(npc_id: int, request: dict):
    from algomate.core.flow.npc_dialogue import NPCDialogueFlow

    message = request.get("message")
    session_id = request.get("sessionId")

    if not message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    try:
        flow = NPCDialogueFlow.get_instance()

        if session_id is None:
            session_result = await flow.start_dialogue(npc_id, None)
            new_session_id = session_result.dialogue_id
        else:
            new_session_id = int(session_id)

        final_session_id = new_session_id
        is_new_session = session_id is None

        def generate():
            try:
                if is_new_session:
                    yield f"data: {json.dumps({'dialogue_id': final_session_id}, ensure_ascii=False)}\n\n"
                for chunk in flow.continue_dialogue_stream(final_session_id, message):
                    yield chunk
            except ValueError as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error("npc_chat_stream stream error for npc %s: %s", npc_id, e, exc_info=True)
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("npc_chat_stream failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
