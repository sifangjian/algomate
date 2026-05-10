import json
import logging

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/realms", tags=["秘境"])
logger = logging.getLogger(__name__)


def _ensure_npc_exists(session, realm_name: str, npc_data: dict) -> int:
    from algomate.models.npcs import NPC

    existing = session.query(NPC).filter(
        NPC.name == npc_data["name"]
    ).first()
    if existing:
        if not existing.algorithm_type and npc_data.get("algorithm_type"):
            existing.algorithm_type = npc_data["algorithm_type"]
            existing.domain = npc_data["algorithm_type"]
        if not existing.title and npc_data.get("title"):
            existing.title = npc_data["title"]
        if not existing.specialties and npc_data.get("specialties"):
            existing.specialties = json.dumps(npc_data["specialties"], ensure_ascii=False)
        if not existing.description and npc_data.get("description"):
            existing.description = npc_data.get("description", "")
        session.commit()
        return existing.id

    new_npc = NPC(
        name=npc_data["name"],
        title=npc_data.get("title", ""),
        algorithm_type=npc_data.get("algorithm_type", npc_data.get("domain", "")),
        specialties=json.dumps(npc_data.get("specialties", []), ensure_ascii=False),
        domain=npc_data.get("algorithm_type", npc_data.get("domain", "")),
        location=realm_name,
        avatar=npc_data.get("avatar", ""),
        description=npc_data.get("description", ""),
        system_prompt=npc_data.get("system_prompt", f"你是{npc_data['name']}，{npc_data.get('description', '')}"),
        greeting=npc_data.get("greeting", f"欢迎来到{realm_name}！我是{npc_data['name']}。"),
        topics=json.dumps(npc_data.get("topics", []), ensure_ascii=False)
    )
    session.add(new_npc)
    session.commit()
    session.refresh(new_npc)
    return new_npc.id


def _init_default_npcs():
    from algomate.data.database import Database
    from algomate.models.npcs import NPC

    db = Database.get_instance()
    session = db.get_session()
    try:
        existing_count = session.query(NPC).count()
        if existing_count > 0:
            return

        default_npcs = {
            "新手森林": [
                {
                    "name": "老夫子",
                    "title": "基础数据结构导师",
                    "algorithm_type": "basic_data_structure",
                    "domain": "基础数据结构",
                    "specialties": ["数组与双指针", "链表", "哈希表"],
                    "avatar": "laofuzi",
                    "description": "基础数据结构的导师，以循循善诱的方式教授数组与双指针、链表、哈希表等核心技巧。",
                    "system_prompt": "你是老夫子，新手森林的导师，专长基础数据结构。你以循循善诱的方式教授数组与双指针、链表、哈希表等核心技巧。你的教学风格是先讲概念，再举例说明，最后让学生思考应用场景。",
                    "greeting": "欢迎来到新手森林！老夫在此等候多时，让我们从基础数据结构开始，循序渐进地踏上算法修习之路吧。",
                    "topics": ["数组与双指针", "链表", "哈希表"]
                },
                {
                    "name": "栈语者",
                    "title": "栈队列与搜索导师",
                    "algorithm_type": "stack_queue_search",
                    "domain": "栈队列与搜索",
                    "specialties": ["栈与队列", "二分查找", "前缀和"],
                    "avatar": "zhanzhe",
                    "description": "栈队列与搜索基础的导师，以严谨的逻辑教授栈与队列、二分查找、前缀和等技巧。",
                    "system_prompt": "你是栈语者，新手森林的导师，专长栈队列与搜索基础。你以严谨的逻辑教授栈与队列、二分查找、前缀和等技巧。你善于用生活比喻解释抽象概念。",
                    "greeting": "欢迎来到新手森林！我是栈语者，让我用严谨的逻辑带你理解栈与队列的奥妙，掌握二分查找与前缀和的精髓。",
                    "topics": ["栈与队列", "二分查找", "前缀和"]
                },
            ],
            "迷雾沼泽": {
                "name": "沼泽向导",
                "title": "搜索与遍历导师",
                "algorithm_type": "search_traversal",
                "domain": "搜索与遍历",
                "specialties": ["滑动窗口", "DFS", "BFS", "拓扑排序"],
                "avatar": "zhaodao",
                "description": "搜索与遍历的导师，以实战导向的方式教授滑动窗口、DFS与BFS、拓扑排序等搜索进阶技巧。",
                "system_prompt": "你是沼泽向导，迷雾沼泽的导师，专长搜索与遍历。你以实战导向的方式教授滑动窗口、DFS与BFS、拓扑排序等搜索进阶技巧。你善于引导学生从暴力解法优化到高效算法。",
                "greeting": "欢迎来到迷雾沼泽！迷雾虽浓，但搜索之道自明。让我带你从暴力到高效，掌握滑动窗口与搜索遍历的进阶技巧。",
                "topics": ["滑动窗口", "DFS", "BFS", "拓扑排序"]
            },
            "古树森林": [
                {
                    "name": "树语者",
                    "title": "树结构导师",
                    "algorithm_type": "tree",
                    "domain": "树结构",
                    "specialties": ["二叉树遍历", "二叉搜索树", "堆与优先队列"],
                    "avatar": "shuzhe",
                    "description": "树结构的导师，以自然比喻教授二叉树遍历、二叉搜索树、堆与优先队列等树相关技巧。",
                    "system_prompt": "你是树语者，古树森林的导师，专长树结构。你以自然比喻教授二叉树遍历、二叉搜索树、堆与优先队列等树相关技巧。你善于用树的生长过程解释递归结构。",
                    "greeting": "欢迎来到古树森林！我是树语者，让我用自然的智慧带你领悟二叉树的递归之美，掌握搜索树与优先队列的精髓。",
                    "topics": ["二叉树遍历", "二叉搜索树", "堆与优先队列"]
                },
                {
                    "name": "图灵使",
                    "title": "图结构导师",
                    "algorithm_type": "graph",
                    "domain": "图结构",
                    "specialties": ["图的遍历", "最短路径", "并查集"],
                    "avatar": "tuling",
                    "description": "图结构的导师，以系统化的方式教授图的遍历、最短路径、并查集等图论技巧。",
                    "system_prompt": "你是图灵使，古树森林的导师，专长图结构。你以系统化的方式教授图的遍历、最短路径、并查集等图论技巧。你善于将复杂问题建模为图论问题。",
                    "greeting": "欢迎来到古树森林！我是图灵使，万物皆可成图，让我教你如何将复杂问题建模为图论模型，系统化地攻克遍历、最短路径与并查集。",
                    "topics": ["图的遍历", "最短路径", "并查集"]
                },
            ],
            "命运迷宫": {
                "name": "迷宫守护者",
                "title": "回溯算法导师",
                "algorithm_type": "backtracking",
                "domain": "回溯算法",
                "specialties": ["递归", "回溯", "剪枝技巧", "组合与排列"],
                "avatar": "migong",
                "description": "回溯算法的导师，以探索迷宫的方式教授递归、回溯、剪枝技巧、组合与排列。",
                "system_prompt": "你是迷宫守护者，命运迷宫的导师，专长回溯算法。你以探索迷宫的方式教授递归、回溯、剪枝技巧、组合与排列。你善于让学生理解'尝试-回退-再尝试'的搜索过程。",
                "greeting": "欢迎来到命运迷宫！每一条路都通向新的发现，让我带你体验'尝试-回退-再尝试'的回溯之美，掌握剪枝与组合排列的精髓。",
                "topics": ["递归", "回溯", "剪枝技巧", "组合与排列"]
            },
            "贪婪之塔": {
                "name": "贪婪之王",
                "title": "贪心算法导师",
                "algorithm_type": "greedy",
                "domain": "贪心算法",
                "specialties": ["贪心选择", "区间问题", "构造策略"],
                "avatar": "tanlan",
                "description": "贪心算法的导师，以果断决策的方式教授贪心选择、区间问题、构造策略。",
                "system_prompt": "你是贪婪之王，贪婪之塔的导师，专长贪心算法。你以果断决策的方式教授贪心选择、区间问题、构造策略。你善于让学生理解'局部最优→全局最优'的条件和反例。",
                "greeting": "欢迎来到贪婪之塔！贪心之道，在于果断抉择。让我教你何时局部最优可推全局最优，以及如何识破贪心的陷阱。",
                "topics": ["贪心选择", "区间问题", "构造策略"]
            },
            "智慧圣殿": {
                "name": "圣殿智者",
                "title": "动态规划导师",
                "algorithm_type": "dynamic_programming",
                "domain": "动态规划",
                "specialties": ["线性DP", "背包问题", "子序列DP"],
                "avatar": "zhizhe",
                "description": "动态规划的导师，以循序渐进的方式教授线性DP、背包问题、子序列DP。",
                "system_prompt": "你是圣殿智者，智慧圣殿的导师，专长动态规划。你以循序渐进的方式教授线性DP、背包问题、子序列DP。你善于引导学生从递归暴力解→记忆化→DP表的过程。",
                "greeting": "欢迎来到智慧圣殿！动态规划是算法的至高智慧，让我带你从递归暴力出发，经历记忆化到DP表的蜕变，领悟线性DP、背包与子序列的奥秘。",
                "topics": ["线性DP", "背包问题", "子序列DP"]
            },
            "分裂山脉": {
                "name": "分裂贤者",
                "title": "分治与排序导师",
                "algorithm_type": "divide_conquer",
                "domain": "分治与排序",
                "specialties": ["分治思想", "排序算法", "单调栈", "单调队列"],
                "avatar": "fenlie",
                "description": "分治与排序的导师，以分解-解决-合并的框架教授分治思想、排序算法、单调栈/队列。",
                "system_prompt": "你是分裂贤者，分裂山脉的导师，专长分治与排序。你以分解-解决-合并的框架教授分治思想、排序算法、单调栈/队列。你善于让学生理解'大问题拆小问题'的核心思想。",
                "greeting": "欢迎来到分裂山脉！分裂之道，在于化大为小。让我教你用'分解-解决-合并'的框架，掌握分治、排序与单调数据结构的精髓。",
                "topics": ["分治思想", "排序算法", "单调栈", "单调队列"]
            },
            "数学殿堂": {
                "name": "数学巫师",
                "title": "数学与位运算导师",
                "algorithm_type": "math_bit",
                "domain": "数学与位运算",
                "specialties": ["位运算", "数学技巧", "字符串算法"],
                "avatar": "shuxue",
                "description": "数学与位运算的导师，以数学之美的方式教授位运算、数学技巧、字符串算法。",
                "system_prompt": "你是数学巫师，数学殿堂的导师，专长数学与位运算。你以数学之美的方式教授位运算、数学技巧、字符串算法。你善于揭示数字和比特背后的规律。",
                "greeting": "欢迎来到数学殿堂！数字与比特蕴含无穷奥秘，让我带你揭示位运算的魔法、数学技巧的优雅与字符串算法的精妙。",
                "topics": ["位运算", "数学技巧", "字符串算法"]
            },
            "试炼之地": [],
        }

        for realm_name, npc_data in default_npcs.items():
            if isinstance(npc_data, list):
                for npc_item in npc_data:
                    _ensure_npc_exists(session, realm_name, npc_item)
            else:
                _ensure_npc_exists(session, realm_name, npc_data)

    finally:
        session.close()


def _init_default_bosses():
    from algomate.data.database import Database
    from algomate.models.bosses import Boss
    from algomate.models.npcs import NPC

    db = Database.get_instance()
    session = db.get_session()
    try:
        existing_count = session.query(Boss).count()
        if existing_count > 0:
            return

        default_bosses = [
            {"name": "数组守卫", "difficulty": "easy", "weakness_type": "basic_data_structure", "npc_name": "老夫子", "description": "新手森林的守门人，用数组的秩序维护森林的安宁"},
            {"name": "链表巨蟒", "difficulty": "medium", "weakness_type": "basic_data_structure", "npc_name": "老夫子", "description": "潜伏在链表节点间的巨蟒，只有理解指针的人才能击败它"},
            {"name": "栈道守卫", "difficulty": "easy", "weakness_type": "stack_queue_search", "npc_name": "栈语者", "description": "守护栈与队列之道的哨兵，后进先出是它的信条"},
            {"name": "滑窗幻影", "difficulty": "medium", "weakness_type": "search_traversal", "npc_name": "沼泽向导", "description": "迷雾中飘忽不定的幻影，只有滑动窗口才能捕捉它的踪迹"},
            {"name": "树根领主", "difficulty": "medium", "weakness_type": "tree", "npc_name": "树语者", "description": "扎根于古树深处的领主，掌握二叉树的秘密"},
            {"name": "图灵巨兽", "difficulty": "hard", "weakness_type": "graph", "npc_name": "图灵使", "description": "连接所有节点的终极巨兽，只有图论大师才能驯服"},
            {"name": "迷宫回溯者", "difficulty": "hard", "weakness_type": "backtracking", "npc_name": "迷宫守护者", "description": "在命运的岔路口不断回溯的幽灵，剪枝是唯一的出路"},
            {"name": "贪婪巨龙", "difficulty": "medium", "weakness_type": "greedy", "npc_name": "贪婪之王", "description": "永远追求局部最优的巨龙，但全局最优才是制胜之道"},
            {"name": "DP圣殿守卫", "difficulty": "hard", "weakness_type": "dynamic_programming", "npc_name": "圣殿智者", "description": "守护动态规划圣殿的终极守卫，子问题是它的弱点"},
        ]

        for boss_data in default_bosses:
            npc = session.query(NPC).filter(NPC.name == boss_data["npc_name"]).first()
            if not npc:
                continue
            new_boss = Boss(
                name=boss_data["name"],
                difficulty=boss_data["difficulty"],
                weakness_type=boss_data["weakness_type"],
                npc_id=npc.id,
                description=boss_data["description"],
            )
            session.add(new_boss)

        session.commit()
    finally:
        session.close()


@router.get("")
async def get_realms():
    from algomate.core.game.realm_unlock import Realm, RealmUnlockManager
    from algomate.data.database import Database
    from algomate.models.npcs import NPC
    from algomate.models.cards import Card

    _init_default_npcs()
    _init_default_bosses()

    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.pending_retake == False).all()
        manager = RealmUnlockManager()
        unlocked_realms = manager.get_unlocked_realms(cards)

        realm_config = {
            "新手森林": {
                "icon": "🌲",
                "description": "算法之旅的起点，修习基础数据结构与查找算法",
                "bossInfo": None,
            },
            "迷雾沼泽": {
                "icon": "🌫️",
                "description": "搜索进阶的领域，掌握滑动窗口与搜索遍历技巧",
                "bossInfo": {"id": "boss_slime_king", "name": "迷雾史莱姆王", "difficulty": 2},
            },
            "古树森林": {
                "icon": "🌳",
                "description": "参天古树间隐藏着树与图的奥秘，树语者和图灵使在此等待修习者",
                "color": "#2d5a27",
            },
            "智慧圣殿": {
                "icon": "💡",
                "description": "动态规划的璀璨世界，用智慧照亮黑暗",
                "bossInfo": None,
            },
            "贪婪之塔": {
                "icon": "🏰",
                "description": "贪心算法的试炼场，学会局部最优的果断抉择",
                "bossInfo": {"id": "boss_greed_dragon", "name": "贪婪巨龙", "difficulty": 3},
            },
            "命运迷宫": {
                "icon": "🌀",
                "description": "回溯算法的迷宫，体验尝试与回退的搜索之美",
                "bossInfo": None,
            },
            "分裂山脉": {
                "icon": "⛰️",
                "description": "算法之巅的终极挑战",
                "bossInfo": {"id": "boss_mountain_giant", "name": "分裂山巨", "difficulty": 4},
            },
            "数学殿堂": {
                "icon": "📐",
                "description": "数学证明与复杂度的精妙世界",
                "bossInfo": None,
            },
            "试炼之地": {
                "icon": "⚔️",
                "description": "所有秘境的终极试炼",
                "bossInfo": {"id": "boss_trial_lord", "name": "试炼之主", "difficulty": 5},
            },
        }

        realms_data = []
        for realm in Realm:
            progress = manager.get_realm_progress(realm, cards)
            is_unlocked = realm.value in unlocked_realms
            is_partial = not is_unlocked and progress.current > 0

            if is_unlocked:
                status = "unlocked"
            elif is_partial:
                status = "partial"
            else:
                status = "locked"

            config = realm_config.get(realm.value, {})
            realm_order = list(Realm).index(realm) + 1

            npcs = session.query(NPC).filter(NPC.location == realm.value).all()
            npc_list = [{"id": n.id, "name": n.name, "avatar": n.avatar} for n in npcs] if npcs else []

            realms_data.append({
                "id": realm.value,
                "name": realm.value,
                "icon": config.get("icon", "🗝️"),
                "description": config.get("description", ""),
                "status": status,
                "order": realm_order,
                "progress": int(progress.progress_percentage),
                "npcInfo": npc_list,
                "bossInfo": config.get("bossInfo"),
                "unlockCondition": {
                    "description": f"需要 {progress.required} 张卡牌才能解锁，当前 {progress.current} 张" if status == "partial" else "完成前置秘境解锁" if status == "locked" else "",
                    "required": progress.required,
                    "current": progress.current,
                } if status != "unlocked" else None,
            })
        return realms_data
    finally:
        session.close()


@router.get("/{realm_id}")
async def get_realm_by_id(realm_id: str):
    from algomate.core.game.realm_unlock import Realm, RealmUnlockManager
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.pending_retake == False).all()
        manager = RealmUnlockManager()

        realm = Realm(realm_id)
        progress = manager.get_realm_progress(realm, cards)
        unlocked_realms = manager.get_unlocked_realms(cards)

        return {
            "id": realm.value,
            "name": realm.value,
            "unlocked": realm.value in unlocked_realms,
            "required_cards": progress.required,
            "current_cards": progress.current,
            "progress_percentage": progress.progress_percentage
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"秘境 {realm_id} 不存在")
    finally:
        session.close()


@router.post("/{realm_id}/check-unlock")
async def check_realm_unlock(realm_id: str):
    from algomate.core.game.realm_unlock import Realm, RealmUnlockManager
    from algomate.data.database import Database

    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.pending_retake == False).all()
        manager = RealmUnlockManager()

        realm = Realm(realm_id)
        unlocked = manager.check_realm_unlock(realm, cards)
        progress = manager.get_realm_progress(realm, cards)

        return {
            "realm": realm.value,
            "unlocked": unlocked,
            "required_cards": progress.required,
            "current_cards": progress.current
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"秘境 {realm_id} 不存在")
    finally:
        session.close()
