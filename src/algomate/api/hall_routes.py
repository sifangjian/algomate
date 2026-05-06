import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func

from algomate.models.npcs import NPC, NPCListItem, NPCDetailResponse

router = APIRouter(prefix="/api/v1", tags=["导师大厅"])

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
        "description": "基础数据结构的导师，以循循善诱的方式教授数组与双指针、链表、哈希表等核心技巧。",
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
        "description": "栈队列与搜索基础的导师，以严谨的逻辑教授栈与队列、二分查找、前缀和等技巧。",
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
        "description": "搜索与遍历的导师，以实战导向的方式教授滑动窗口、DFS与BFS、拓扑排序等搜索进阶技巧。",
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
        "description": "树结构的导师，以自然比喻教授二叉树遍历、二叉搜索树、堆与优先队列等树相关技巧。",
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
        "description": "图结构的导师，以系统化的方式教授图的遍历、最短路径、并查集等图论技巧。",
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
        "description": "回溯算法的导师，以探索迷宫的方式教授递归、回溯、剪枝技巧、组合与排列。",
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
        "description": "贪心算法的导师，以果断决策的方式教授贪心选择、区间问题、构造策略。",
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
        "description": "动态规划的导师，以循序渐进的方式教授线性DP、背包问题、子序列DP。",
        "topics": ["线性DP", "背包问题", "子序列DP"],
        "system_prompt": "你是圣殿智者，智慧圣殿的导师，专长动态规划。你以循序渐进的方式教授线性DP、背包问题、子序列DP。你善于引导学生从递归暴力解→记忆化→DP表的过程。",
        "greeting": "欢迎来到智慧圣殿！动态规划是算法的至高智慧，让我带你从递归暴力出发，经历记忆化到DP表的蜕变，领悟线性DP、背包与子序列的奥秘。",
    },
]


def init_default_npcs_v1():
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        existing_count = session.query(NPC).count()
        if existing_count > 0:
            for npc_data in DEFAULT_NPCS:
                existing = session.query(NPC).filter(NPC.name == npc_data["name"]).first()
                if existing:
                    existing.title = npc_data["title"]
                    existing.algorithm_type = npc_data["algorithm_type"]
                    existing.specialties = json.dumps(npc_data["specialties"], ensure_ascii=False)
                    existing.avatar = npc_data["avatar"]
                    existing.description = npc_data["description"]
                    existing.topics = json.dumps(npc_data["topics"], ensure_ascii=False)
                    existing.domain = npc_data["algorithm_type"]
                    if not existing.system_prompt:
                        existing.system_prompt = npc_data["system_prompt"]
                    if not existing.greeting:
                        existing.greeting = npc_data["greeting"]
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
            )
            session.add(npc)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def _parse_json_field(value: str) -> list:
    try:
        return json.loads(value) if value else []
    except (json.JSONDecodeError, TypeError):
        return []


@router.get("/npcs")
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


@router.get("/npcs/{npc_id}")
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
            },
        }
    finally:
        session.close()


@router.get("/stats")
async def get_stats():
    from algomate.data.database import Database
    from algomate.models.cards import Card

    db = Database.get_instance()
    session = db.get_session()
    try:
        total_cards = session.query(Card).count()
        endangered_cards = session.query(Card).filter(
            Card.durability < 30,
            Card.durability > 0,
        ).count()
        pending_retake_cards = session.query(Card).filter(
            Card.pending_retake == True,
        ).count()

        cards_by_type_rows = session.query(
            Card.algorithm_type, func.count(Card.id)
        ).group_by(Card.algorithm_type).all()
        cards_by_type = {row[0]: row[1] for row in cards_by_type_rows if row[0]}

        return {
            "code": 200,
            "message": "success",
            "data": {
                "total_cards": total_cards,
                "endangered_cards": endangered_cards,
                "pending_retake_cards": pending_retake_cards,
                "cards_by_type": cards_by_type,
                "is_new_user": total_cards == 0,
            },
        }
    finally:
        session.close()
