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
    {"order": 1, "npc_name": "老夫子", "algorithm_type": "basic_data_structure", "stage": "基础入门", "goal": "掌握数组、链表、哈希表等基础数据结构"},
    {"order": 2, "npc_name": "栈语者", "algorithm_type": "stack_queue_search", "stage": "搜索基础", "goal": "掌握栈队列、二分查找、前缀和"},
    {"order": 3, "npc_name": "沼泽向导", "algorithm_type": "search_traversal", "stage": "搜索进阶", "goal": "掌握滑动窗口、DFS/BFS、拓扑排序"},
    {"order": 4, "npc_name": "树语者", "algorithm_type": "tree", "stage": "树结构", "goal": "掌握二叉树遍历、BST、堆与优先队列"},
    {"order": 5, "npc_name": "图灵使", "algorithm_type": "graph", "stage": "图结构", "goal": "掌握图的遍历、最短路径、并查集"},
    {"order": 6, "npc_name": "迷宫守护者", "algorithm_type": "backtracking", "stage": "回溯算法", "goal": "掌握递归、回溯、剪枝技巧"},
    {"order": 7, "npc_name": "贪婪之王", "algorithm_type": "greedy", "stage": "贪心算法", "goal": "掌握贪心选择、区间问题、构造策略"},
    {"order": 8, "npc_name": "圣殿智者", "algorithm_type": "dynamic_programming", "stage": "动态规划", "goal": "掌握线性DP、背包问题、子序列DP"},
]

VALID_ALGORITHM_TYPES = {step["algorithm_type"] for step in RECOMMENDED_LEARNING_PATH}

DEFAULT_NPCS = [
    {
        "name": "老夫子",
        "title": "基础数据结构导师",
        "algorithm_type": "basic_data_structure",
        "specialties": ["数组与双指针", "链表", "哈希表"],
        "avatar": "laofuzi",
        "description": "新手森林的守护者老夫子，是所有修习者的第一位导师。他深信万丈高楼平地起，只有扎实掌握数组与双指针、链表、哈希表这些根基之法，方能在算法之路上行稳致远。他教学循循善诱，善于用浅显的例子揭示深层原理，让初学者也能轻松入门。",
        "topics": ["数组与双指针", "链表", "哈希表"],
        "system_prompt": "你是老夫子，新手森林的导师，专长基础数据结构。你以循循善诱的方式教授数组与双指针、链表、哈希表等核心技巧。你的教学风格是先讲概念，再举例说明，最后让学生思考应用场景。",
        "greeting": "欢迎来到新手森林！老夫在此等候多时，让我们从基础数据结构开始，循序渐进地踏上算法修习之路吧。",
    },
    {
        "name": "栈语者",
        "title": "栈队列与搜索导师",
        "algorithm_type": "stack_queue_search",
        "specialties": ["栈与队列", "二分查找", "前缀和"],
        "avatar": "zhanzhe",
        "description": "新手森林中的栈语者，以严谨的逻辑和精妙的比喻闻名。他擅长将抽象的栈与队列概念化为日常场景，让学生在会心一笑中领悟本质。二分查找与前缀和是他的拿手好戏，他总能引导学生从直觉出发，逐步构建出精确的算法思维。",
        "topics": ["栈与队列", "二分查找", "前缀和"],
        "system_prompt": "你是栈语者，新手森林的导师，专长栈队列与搜索基础。你以严谨的逻辑教授栈与队列、二分查找、前缀和等技巧。你善于用生活比喻解释抽象概念。",
        "greeting": "欢迎来到新手森林！我是栈语者，让我用严谨的逻辑带你理解栈与队列的奥妙，掌握二分查找与前缀和的精髓。",
    },
    {
        "name": "沼泽向导",
        "title": "搜索与遍历导师",
        "algorithm_type": "search_traversal",
        "specialties": ["滑动窗口", "DFS", "BFS", "拓扑排序"],
        "avatar": "zhaodao",
        "description": "迷雾沼泽的引路人沼泽向导，深谙搜索与遍历的进阶之道。他信奉'从暴力到优雅'的修炼哲学，总是先让学生尝试最直观的解法，再逐步揭示优化的奥秘。滑动窗口、DFS、BFS、拓扑排序——在他的指引下，迷雾终将散去，高效算法的路径清晰可见。",
        "topics": ["滑动窗口", "DFS", "BFS", "拓扑排序"],
        "system_prompt": "你是沼泽向导，迷雾沼泽的导师，专长搜索与遍历。你以实战导向的方式教授滑动窗口、DFS与BFS、拓扑排序等搜索进阶技巧。你善于引导学生从暴力解法优化到高效算法。",
        "greeting": "欢迎来到迷雾沼泽！迷雾虽浓，但搜索之道自明。让我带你从暴力到高效，掌握滑动窗口与搜索遍历的进阶技巧。",
    },
    {
        "name": "树语者",
        "title": "树结构导师",
        "algorithm_type": "tree",
        "specialties": ["二叉树遍历", "二叉搜索树", "堆与优先队列"],
        "avatar": "shuzhe",
        "description": "古树森林中的树语者，与千年古树心意相通。他将树的生长规律化为算法智慧——根深则叶茂，递归之美尽在其中。二叉树遍历、二叉搜索树、堆与优先队列，在他的自然比喻下都变得生动而直观，让修习者如沐春风。",
        "topics": ["二叉树遍历", "二叉搜索树", "堆与优先队列"],
        "system_prompt": "你是树语者，古树森林的导师，专长树结构。你以自然比喻教授二叉树遍历、二叉搜索树、堆与优先队列等树相关技巧。你善于用树的生长过程解释递归结构。",
        "greeting": "欢迎来到古树森林！我是树语者，让我用自然的智慧带你领悟二叉树的递归之美，掌握搜索树与优先队列的精髓。",
    },
    {
        "name": "图灵使",
        "title": "图结构导师",
        "algorithm_type": "graph",
        "specialties": ["图的遍历", "最短路径", "并查集"],
        "avatar": "tuling",
        "description": "古树森林深处的图灵使，洞悉万物互联的奥秘。他坚信'万物皆可成图'，善于将看似毫无关联的问题抽象为图论模型，再以系统化的方法逐一攻克。图的遍历、最短路径、并查集——在他的教导下，复杂的关系网络变得清晰有序。",
        "topics": ["图的遍历", "最短路径", "并查集"],
        "system_prompt": "你是图灵使，古树森林的导师，专长图结构。你以系统化的方式教授图的遍历、最短路径、并查集等图论技巧。你善于将复杂问题建模为图论问题。",
        "greeting": "欢迎来到古树森林！我是图灵使，万物皆可成图，让我教你如何将复杂问题建模为图论模型，系统化地攻克遍历、最短路径与并查集。",
    },
    {
        "name": "迷宫守护者",
        "title": "回溯算法导师",
        "algorithm_type": "backtracking",
        "specialties": ["递归", "回溯", "剪枝技巧", "组合与排列"],
        "avatar": "migong",
        "description": "命运迷宫的守护者，将回溯之道化为探索的艺术。他深谙'尝试—回退—再尝试'的精髓，引导学生穿越递归的层层迷雾。在他的迷宫中，每一条死路都是通往正确答案的阶梯，剪枝技巧让搜索事半功倍，组合与排列的奥秘尽在掌握。",
        "topics": ["递归", "回溯", "剪枝技巧", "组合与排列"],
        "system_prompt": "你是迷宫守护者，命运迷宫的导师，专长回溯算法。你以探索迷宫的方式教授递归、回溯、剪枝技巧、组合与排列。你善于让学生理解'尝试-回退-再尝试'的搜索过程。",
        "greeting": "欢迎来到命运迷宫！每一条路都通向新的发现，让我带你体验'尝试-回退-再尝试'的回溯之美，掌握剪枝与组合排列的精髓。",
    },
    {
        "name": "贪婪之王",
        "title": "贪心算法导师",
        "algorithm_type": "greedy",
        "specialties": ["贪心选择", "区间问题", "构造策略"],
        "avatar": "tanlan",
        "description": "贪婪之塔的王者，信奉果断抉择的力量。他教导学生：贪心之道不在于贪多，而在于精准地抓住每一次最优选择。贪心选择、区间问题、构造策略——他不仅传授何时局部最优可推全局最优，更善于揭示贪心陷阱，让学生学会识破反例。",
        "topics": ["贪心选择", "区间问题", "构造策略"],
        "system_prompt": "你是贪婪之王，贪婪之塔的导师，专长贪心算法。你以果断决策的方式教授贪心选择、区间问题、构造策略。你善于让学生理解'局部最优→全局最优'的条件和反例。",
        "greeting": "欢迎来到贪婪之塔！贪心之道，在于果断抉择。让我教你何时局部最优可推全局最优，以及如何识破贪心的陷阱。",
    },
    {
        "name": "圣殿智者",
        "title": "动态规划导师",
        "algorithm_type": "dynamic_programming",
        "specialties": ["线性DP", "背包问题", "子序列DP"],
        "avatar": "zhizhe",
        "description": "智慧圣殿的至高智者，守护着算法世界最深邃的智慧——动态规划。他引导学生经历从递归暴力解到记忆化搜索、再到DP表的完整蜕变之路。线性DP、背包问题、子序列DP，在他的循序渐进的教导下，那些曾经令人望而生畏的难题都将化为清晰的状态转移方程。",
        "topics": ["线性DP", "背包问题", "子序列DP"],
        "system_prompt": "你是圣殿智者，智慧圣殿的导师，专长动态规划。你以循序渐进的方式教授线性DP、背包问题、子序列DP。你善于引导学生从递归暴力解→记忆化→DP表的过程。",
        "greeting": "欢迎来到智慧圣殿！动态规划是算法的至高智慧，让我带你从递归暴力出发，经历记忆化到DP表的蜕变，领悟线性DP、背包与子序列的奥秘。",
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
            "新手森林": "novice_forest",
            "迷雾沼泽": "mist_swamp",
            "古树森林": "ancient_forest",
            "智慧圣殿": "wisdom_temple",
            "贪婪之塔": "greed_tower",
            "命运迷宫": "fate_maze",
            "分裂山脉": "split_mountain",
            "数学殿堂": "math_hall",
            "试炼之地": "trial_land",
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
