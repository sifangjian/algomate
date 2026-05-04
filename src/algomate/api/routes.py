from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import date, datetime, timedelta
import json

router = APIRouter()

practice_router = APIRouter()
progress_router = APIRouter()
dashboard_router = APIRouter()
settings_router = APIRouter()
learning_router = APIRouter()
realm_router = APIRouter()
npc_router = APIRouter()
stats_router = APIRouter()
algorithm_info_router = APIRouter()


@algorithm_info_router.get("/algorithm-info")
async def get_algorithm_info():
    from algomate.config.algorithm_types import (
        TOPIC_PREREQUISITES,
        TOPIC_IMPORTANCE,
        ALGORITHM_CATEGORIES,
    )
    return {
        "topic_prerequisites": TOPIC_PREREQUISITES,
        "topic_importance": TOPIC_IMPORTANCE,
        "algorithm_categories": ALGORITHM_CATEGORIES,
    }


def _ensure_npc_exists(session, realm_name: str, npc_data: dict) -> int:
    """确保 NPC 存在于数据库中，返回 NPC ID"""
    from algomate.models.npcs import NPC

    existing = session.query(NPC).filter(
        NPC.location == realm_name,
        NPC.name == npc_data["name"]
    ).first()
    if existing:
        return existing.id

    new_npc = NPC(
        name=npc_data["name"],
        domain=npc_data["domain"],
        location=realm_name,
        avatar=npc_data.get("avatar", "🧙‍♀️"),
        system_prompt=npc_data.get("system_prompt", f"你是{npc_data['name']}，{npc_data.get('description', '')}"),
        greeting=npc_data.get("greeting", f"欢迎来到{realm_name}！我是{npc_data['name']}。"),
        topics=json.dumps(npc_data.get("topics", []), ensure_ascii=False)
    )
    session.add(new_npc)
    session.commit()
    session.refresh(new_npc)
    return new_npc.id


def _init_default_npcs():
    """初始化默认 NPC 数据"""
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
                    "domain": "基础数据结构",
                    "avatar": "🧓",
                    "description": "基础数据结构的导师",
                    "system_prompt": "你是老夫子，新手森林的导师，专长基础数据结构。你以循循善诱的方式教授数组与双指针、链表、哈希表等核心技巧。你的教学风格是先讲概念，再举例说明，最后让学生思考应用场景。",
                    "greeting": "欢迎来到新手森林！老夫在此等候多时，让我们从基础数据结构开始，循序渐进地踏上算法修习之路吧。",
                    "topics": ["数组与双指针", "链表", "哈希表"]
                },
                {
                    "name": "栈语者",
                    "domain": "栈队列与搜索",
                    "avatar": "📚",
                    "description": "栈队列与搜索基础的导师",
                    "system_prompt": "你是栈语者，新手森林的导师，专长栈队列与搜索基础。你以严谨的逻辑教授栈与队列、二分查找、前缀和等技巧。你善于用生活比喻解释抽象概念。",
                    "greeting": "欢迎来到新手森林！我是栈语者，让我用严谨的逻辑带你理解栈与队列的奥妙，掌握二分查找与前缀和的精髓。",
                    "topics": ["栈与队列", "二分查找", "前缀和"]
                },
            ],
            "迷雾沼泽": {
                "name": "沼泽向导",
                "domain": "搜索与遍历",
                "avatar": "🐸",
                "description": "搜索与遍历的导师",
                "system_prompt": "你是沼泽向导，迷雾沼泽的导师，专长搜索与遍历。你以实战导向的方式教授滑动窗口、DFS与BFS、拓扑排序等搜索进阶技巧。你善于引导学生从暴力解法优化到高效算法。",
                "greeting": "欢迎来到迷雾沼泽！迷雾虽浓，但搜索之道自明。让我带你从暴力到高效，掌握滑动窗口与搜索遍历的进阶技巧。",
                "topics": ["滑动窗口", "DFS", "BFS", "拓扑排序"]
            },
            "古树森林": [
                {
                    "name": "树语者",
                    "domain": "树结构",
                    "avatar": "🌳",
                    "description": "树结构的导师",
                    "system_prompt": "你是树语者，古树森林的导师，专长树结构。你以自然比喻教授二叉树遍历、二叉搜索树、堆与优先队列等树相关技巧。你善于用树的生长过程解释递归结构。",
                    "greeting": "欢迎来到古树森林！我是树语者，让我用自然的智慧带你领悟二叉树的递归之美，掌握搜索树与优先队列的精髓。",
                    "topics": ["二叉树遍历", "二叉搜索树", "堆与优先队列"]
                },
                {
                    "name": "图灵使",
                    "domain": "图结构",
                    "avatar": "🕸️",
                    "description": "图结构的导师",
                    "system_prompt": "你是图灵使，古树森林的导师，专长图结构。你以系统化的方式教授图的遍历、最短路径、并查集等图论技巧。你善于将复杂问题建模为图论问题。",
                    "greeting": "欢迎来到古树森林！我是图灵使，万物皆可成图，让我教你如何将复杂问题建模为图论模型，系统化地攻克遍历、最短路径与并查集。",
                    "topics": ["图的遍历", "最短路径", "并查集"]
                },
            ],
            "命运迷宫": {
                "name": "迷宫守护者",
                "domain": "回溯算法",
                "avatar": "🌀",
                "description": "回溯算法的导师",
                "system_prompt": "你是迷宫守护者，命运迷宫的导师，专长回溯算法。你以探索迷宫的方式教授递归、回溯、剪枝技巧、组合与排列。你善于让学生理解'尝试-回退-再尝试'的搜索过程。",
                "greeting": "欢迎来到命运迷宫！每一条路都通向新的发现，让我带你体验'尝试-回退-再尝试'的回溯之美，掌握剪枝与组合排列的精髓。",
                "topics": ["递归", "回溯", "剪枝技巧", "组合与排列"]
            },
            "贪婪之塔": {
                "name": "贪婪之王",
                "domain": "贪心算法",
                "avatar": "👑",
                "description": "贪心算法的导师",
                "system_prompt": "你是贪婪之王，贪婪之塔的导师，专长贪心算法。你以果断决策的方式教授贪心选择、区间问题、构造策略。你善于让学生理解'局部最优→全局最优'的条件和反例。",
                "greeting": "欢迎来到贪婪之塔！贪心之道，在于果断抉择。让我教你何时局部最优可推全局最优，以及如何识破贪心的陷阱。",
                "topics": ["贪心选择", "区间问题", "构造策略"]
            },
            "智慧圣殿": {
                "name": "圣殿智者",
                "domain": "动态规划",
                "avatar": "🦉",
                "description": "动态规划的导师",
                "system_prompt": "你是圣殿智者，智慧圣殿的导师，专长动态规划。你以循序渐进的方式教授线性DP、背包问题、子序列DP。你善于引导学生从递归暴力解→记忆化→DP表的过程。",
                "greeting": "欢迎来到智慧圣殿！动态规划是算法的至高智慧，让我带你从递归暴力出发，经历记忆化到DP表的蜕变，领悟线性DP、背包与子序列的奥秘。",
                "topics": ["线性DP", "背包问题", "子序列DP"]
            },
            "分裂山脉": {
                "name": "分裂贤者",
                "domain": "分治与排序",
                "avatar": "⛰️",
                "description": "分治与排序的导师",
                "system_prompt": "你是分裂贤者，分裂山脉的导师，专长分治与排序。你以分解-解决-合并的框架教授分治思想、排序算法、单调栈/队列。你善于让学生理解'大问题拆小问题'的核心思想。",
                "greeting": "欢迎来到分裂山脉！分裂之道，在于化大为小。让我教你用'分解-解决-合并'的框架，掌握分治、排序与单调数据结构的精髓。",
                "topics": ["分治思想", "排序算法", "单调栈", "单调队列"]
            },
            "数学殿堂": {
                "name": "数学巫师",
                "domain": "数学与位运算",
                "avatar": "📐",
                "description": "数学与位运算的导师",
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


def get_review_service():
    from algomate.review.review_plan_service import ReviewPlanService
    return ReviewPlanService()


@practice_router.get("/questions")
async def get_questions(question_type: str = None, count: int = 1, algorithm_type: str = None):
    from algomate.core.agent.question_generator import QuestionGenerator

    generator = QuestionGenerator()

    try:
        note_content = algorithm_type or "算法"
        if question_type == "选择题":
            questions = generator.generate_multiple_choice(
                note_content=note_content,
                count=count,
            )
        elif question_type == "简答题":
            questions = generator.generate_short_answer(
                note_content=note_content,
                count=count,
            )
        elif question_type == "LeetCode挑战":
            questions = []
            for _ in range(count):
                q = generator.generate_leetcode_challenge(
                    note_content=note_content,
                    algorithm_type=algorithm_type or "",
                )
                questions.append(q)
        else:
            questions = generator.generate_for_note(
                note_content=note_content,
                count=count,
            )
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@practice_router.post("/submit")
async def submit_answer(request: dict):
    from algomate.core.agent.answer_evaluator import AnswerEvaluator
    from algomate.data.database import Database

    question_id = request.get("question_id")
    user_answer = request.get("user_answer", "")
    question_type = request.get("question_type")

    if not question_id or not user_answer:
        raise HTTPException(status_code=400, detail="question_id 和 user_answer 不能为空")

    db = Database.get_instance()
    evaluator = AnswerEvaluator(db=db)

    try:
        result = evaluator.evaluate_by_question_id(question_id, user_answer)
        return {
            "is_correct": result.get("is_correct", False),
            "feedback": result.get("feedback", ""),
            "improvement": result.get("improvement", ""),
            "score": result.get("score", 0),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@practice_router.get("/weak-points")
async def get_weak_points(days: int = 30, threshold: float = 0.7):
    from algomate.core.agent.weak_point_analyzer import WeakPointAnalyzer
    from algomate.data.database import Database

    db = Database.get_instance()
    analyzer = WeakPointAnalyzer(db=db)

    try:
        result = analyzer.analyze(days=days)
        weak_points = [
            wp for wp in result.get("weak_points", [])
            if wp.get("accuracy", 1.0) < threshold
        ]
        return {
            "weak_points": weak_points,
            "overall_accuracy": result.get("overall_accuracy", 0.0),
            "recommendations": result.get("recommendations", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@progress_router.get("/stats")
async def get_stats():
    return {
        "total_notes": 0,
        "total_practice": 0,
        "accuracy_rate": 0,
        "learning_days": 0
    }


@progress_router.get("/mastery")
async def get_mastery():
    return {"mastery": {}}


@stats_router.get("/overview")
async def get_stats_overview():
    from algomate.data.database import Database
    from algomate.data.repositories.progress_repo import ProgressRepository
    from algomate.models.cards import Card
    from algomate.core.game.realm_unlock import Realm

    db = Database.get_instance()
    session = db.get_session()
    try:
        total_cards = session.query(Card).count()
    finally:
        session.close()

    progress_repo = ProgressRepository(db)
    consecutive_days = progress_repo.get_consecutive_days()

    return {
        "total_cards": total_cards,
        "total_realms": len(Realm),
        "consecutive_days": consecutive_days,
    }


@dashboard_router.get("/today-review")
async def get_today_review(target_date: str = None):
    review_service = get_review_service()
    if target_date:
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()
    review_plan = review_service.get_today_review_plan(target_date)
    return {"reviews": review_plan, "date": target_date.isoformat()}


@dashboard_router.get("/weak-points")
async def get_weak_points_endpoint(threshold: int = 70, limit: int = 10):
    review_service = get_review_service()
    weak_points = review_service.get_weak_points(threshold)
    return {"weak_points": weak_points[:limit], "total": len(weak_points)}


@dashboard_router.post("/review/start/{card_id}")
async def start_review(card_id: int):
    review_service = get_review_service()
    result = review_service.start_review(card_id)
    if result is None:
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return result


@dashboard_router.post("/review/complete/{card_id}")
async def complete_review(card_id: int, review_data: dict):
    review_service = get_review_service()
    action = review_data.get("action", "success")
    result = review_service.complete_review(card_id, action)
    if result is None:
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return result


@dashboard_router.post("/review/skip/{card_id}")
async def skip_review(card_id: int, reason: str = ""):
    review_service = get_review_service()
    success = review_service.skip_review(card_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return {"message": "已跳过修炼", "card_id": card_id}


@dashboard_router.get("/review/statistics")
async def get_review_statistics(target_date: str = None):
    review_service = get_review_service()
    if target_date:
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()
    stats = review_service.get_review_statistics(target_date)
    return stats


@dashboard_router.get("/review/schedule/{card_id}")
async def get_card_review_schedule(card_id: int):
    review_service = get_review_service()
    schedule = review_service.generate_review_plan_for_card(card_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="卡牌不存在")
    return {"schedule": schedule}


@dashboard_router.get("/stats")
async def get_dashboard_stats():
    review_service = get_review_service()
    stats = review_service.get_review_statistics()
    return stats


@dashboard_router.get("/new-user-status")
async def get_new_user_status():
    review_service = get_review_service()
    status = review_service.is_new_user()
    return status


@settings_router.get("/")
async def get_settings():
    from algomate.config.settings import AppConfig
    config = AppConfig.load()
    return {
        "api_key": config.LLM_API_KEY,
        "email_host": config.SMTP_HOST,
        "email_port": config.SMTP_PORT,
        "email_username": config.SMTP_USER,
        "review_time": config.REVIEW_TIME,
        "forgetting_curve_param": config.REVIEW_INTERVALS[-1] if config.REVIEW_INTERVALS else 30
    }


@settings_router.post("/")
async def save_settings(settings: dict):
    from algomate.config.settings import AppConfig
    config = AppConfig.load()
    if "api_key" in settings:
        config.LLM_API_KEY = settings["api_key"]
    if "email_host" in settings:
        config.SMTP_HOST = settings["email_host"]
    if "email_port" in settings:
        config.SMTP_PORT = settings["email_port"]
    if "email_username" in settings:
        config.SMTP_USER = settings["email_username"]
    if "email_password" in settings and settings["email_password"]:
        config.SMTP_PASSWORD = settings["email_password"]
    if "review_time" in settings:
        config.REVIEW_TIME = settings["review_time"]
    if "forgetting_curve_param" in settings:
        param = settings["forgetting_curve_param"]
        config.REVIEW_INTERVALS = [1, 3, 7, 14, 30, param]
    config.save()
    return {"message": "设置保存成功"}


@settings_router.post("/test-api")
async def test_api_key(apiKey: dict):
    """测试API密钥是否有效"""
    from algomate.config.settings import AppConfig
    api_key = apiKey.get("apiKey", "")
    if not api_key:
        return {"success": False, "message": "API密钥不能为空"}

    try:
        import os
        os.environ["OPENAI_API_KEY"] = api_key
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo", max_tokens=10)
        response = llm.invoke("Hello")
        return {"success": True, "message": "API密钥有效"}
    except Exception as e:
        return {"success": False, "message": f"API密钥无效: {str(e)}"}


@settings_router.post("/test-email")
async def test_email_config(emailConfig: dict):
    """测试邮件配置是否正确"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    host = emailConfig.get("host")
    port = emailConfig.get("port", 587)
    username = emailConfig.get("username")
    password = emailConfig.get("password")
    to_email = emailConfig.get("to_email")

    if not all([host, port, username, password, to_email]):
        return {"success": False, "message": "邮件配置不完整"}

    try:
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_email
        msg['Subject'] = "Algomate 邮件测试"
        msg.attach(MIMEText("这是一封来自Algomate的测试邮件", 'plain'))

        server = smtplib.SMTP(host, int(port))
        server.starttls()
        server.login(username, password)
        server.sendmail(username, [to_email], msg.as_string())
        server.quit()
        return {"success": True, "message": "邮件发送成功"}
    except Exception as e:
        return {"success": False, "message": f"邮件发送失败: {str(e)}"}


@learning_router.get("/topics")
async def get_learning_topics():
    """获取可修习的主题列表

    Returns:
        包含算法类型分类的主题列表
    """
    topics = {
        "categories": [
            {
                "id": "sorting",
                "name": "排序算法",
                "icon": "📊",
                "topics": ["冒泡排序", "选择排序", "插入排序", "快速排序", "归并排序", "堆排序"]
            },
            {
                "id": "searching",
                "name": "查找算法",
                "icon": "🔍",
                "topics": ["二分查找", "顺序查找", "哈希查找"]
            },
            {
                "id": "dynamic_programming",
                "name": "动态规划",
                "icon": "🎯",
                "topics": ["基础DP", "背包问题", "最长公共子序列", "最短路径"]
            },
            {
                "id": "graph",
                "name": "图论",
                "icon": "🕸️",
                "topics": ["BFS", "DFS", "最短路径", "最小生成树"]
            },
            {
                "id": "tree",
                "name": "树结构",
                "icon": "🌲",
                "topics": ["二叉树遍历", "二叉搜索树", "平衡树", "线段树"]
            },
            {
                "id": "recursion",
                "name": "递归与回溯",
                "icon": "🔄",
                "topics": ["递归", "回溯", "阶乘与斐波那契", "全排列", "组合", "N皇后"]
            }
        ]
    }
    return topics


@learning_router.post("/chat")
async def learning_chat(message: dict):
    """修习模式下的对话（流式）

    Args:
        message: 包含 topic（修习主题）和 question（用户问题）的字典

    Returns:
        流式 AI 回复内容 (text/event-stream)
    """
    from algomate.core.agent.chat_client import ChatClient

    topic = message.get("topic", "")
    question = message.get("question", "")
    conversation_history = message.get("history", [])

    if not question:
        return {"error": "问题不能为空"}

    system_prompt = f"""你是一个专业的算法修习导师，擅长用简洁清晰的方式讲解算法知识。

当前修习主题：{topic}

请用易于理解的方式解释，并穿插适当的例子和图示说明。
如果用户提问，要耐心解答，可以适当提问引导用户思考。
保持对话生动有趣，避免过于学术化。"""

    def generate():
        from algomate.config.settings import AppConfig
        config = AppConfig.load()
        client = ChatClient(api_key=config.LLM_API_KEY)

        try:
            for chunk in client.stream_chat(
                messages=conversation_history + [{"role": "user", "content": question}],
                system_prompt=system_prompt
            ):
                yield chunk
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
        }
    )


@learning_router.post("/generate-quiz")
async def generate_quiz(request: dict):
    """为当前修习主题生成小试炼

    Args:
        request: 包含 topic（修习主题）的字典

    Returns:
        生成的试炼
    """
    from algomate.core.agent.question_generator import QuestionGenerator

    topic = request.get("topic", "")

    if not topic:
        return {"error": "主题不能为空"}

    try:
        generator = QuestionGenerator()
        prompt = f"""针对"{topic}"这个算法主题，生成3道高质量的试炼，包括1道选择题、1道简答题和1道LeetCode挑战。

要求：
- 选择题必须有4个选项（A、B、C、D），只有一个正确答案
- 简答题考查对概念和原理的理解
- LeetCode挑战需要推荐一道LeetCode题目

请返回JSON格式，包含一个questions数组：
{{
    "questions": [
        {{
            "question_type": "选择题",
            "content": "试炼内容（包含选项A、B、C、D）",
            "answer": "正确答案",
            "explanation": "解析"
        }},
        {{
            "question_type": "简答题",
            "content": "试炼内容",
            "answer": "参考答案要点",
            "explanation": "解析"
        }},
        {{
            "question_type": "LeetCode挑战",
            "content": "试炼描述",
            "answer": "解题思路要点",
            "explanation": "解题思路",
            "leetcode_url": "https://leetcode.cn/problems/xxx/",
            "leetcode_title": "LeetCode题目标题",
            "leetcode_difficulty": "Easy/Medium/Hard"
        }}
    ]
}}"""
        messages = [{"role": "user", "content": prompt}]
        result = generator.chat_client.chat(messages)

        import re
        json_match = re.search(r'\[[\s\S]*\]|\{[\s\S]*\}', result)
        if json_match:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "questions" in parsed:
                return {"questions": parsed["questions"], "topic": topic}
            elif isinstance(parsed, list):
                return {"questions": parsed, "topic": topic}
        return {"questions": [], "topic": topic}
    except Exception as e:
        return {"error": str(e)}


@learning_router.post("/save-note")
async def save_learning_note(note_data: dict):
    """保存修炼心得

    Args:
        note_data: 包含 title, content, algorithm_type, difficulty 的字典

    Returns:
        创建的心得信息
    """
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    try:
        new_note = note_repo.create(
            title=note_data.get("title") or "",
            content=note_data.get("content") or "",
            algorithm_type=note_data.get("algorithm_type") or "其他",
            difficulty=note_data.get("difficulty") or "中等",
            summary=note_data.get("summary") or "",
            tags=note_data.get("tags") or "[]"
        )
        return {"id": new_note.id, "message": "心得保存成功"}
    except Exception as e:
        return {"error": str(e)}, 500


@learning_router.get("/explain-concept")
async def explain_concept(topic: str, concept: str):
    """获取概念解释

    Args:
        topic: 修习主题
        concept: 概念名称

    Returns:
        概念的详细解释
    """
    from algomate.core.agent.chat_client import ChatClient

    if not concept:
        return {"error": "概念名称不能为空"}

    system_prompt = f"""你是一个专业的算法修习导师，擅长解释算法概念。

当前主题：{topic}
需要解释的概念：{concept}

请用简洁清晰的方式解释这个概念，包括：
1. 什么是这个概念
2. 它的核心思想是什么
3. 常见的应用场景
4. 一个简单的代码示例（如果是代码相关的概念）

请使用 Markdown 格式返回，便于前端渲染。"""

    try:
        from algomate.config.settings import AppConfig
        config = AppConfig.load()
        client = ChatClient(api_key=config.LLM_API_KEY)
        response = client.chat(
            messages=[{"role": "user", "content": f"请解释 {concept} 这个概念"}],
            system_prompt=system_prompt
        )
        return {"explanation": response, "concept": concept, "topic": topic}
    except Exception as e:
        return {"error": str(e)}


boss_router = APIRouter()


@boss_router.get("/boss/{boss_id}")
async def get_boss(boss_id: int):
    """获取Boss信息"""
    from algomate.data.database import Database
    from algomate.models.bosses import Boss

    db = Database.get_instance()
    session = db.get_session()
    try:
        boss = session.query(Boss).filter(Boss.id == boss_id).first()
        if not boss:
            raise HTTPException(status_code=404, detail=f"Boss {boss_id} 不存在")

        import json
        return {
            "id": boss.id,
            "name": boss.name,
            "difficulty": boss.difficulty,
            "weakness_domains": json.loads(boss.weakness_domains) if boss.weakness_domains else [],
            "description": boss.description,
            "source": boss.source,
            "drop_rate": boss.drop_rate,
            "question_id": boss.question_id
        }
    finally:
        session.close()


@boss_router.post("/boss/{boss_id}/submit")
async def submit_boss_answer(boss_id: int, request: dict):
    from algomate.core.flow.boss_battle import BossBattleFlow
    from algomate.data.database import Database
    from algomate.models.bosses import Boss
    from algomate.models.questions import Question

    answer = request.get("answer", "")
    leetcode_result = request.get("leetcode_result", "")
    is_solved = request.get("is_solved", False)
    card_id = request.get("card_id") or request.get("cardId")

    if not card_id:
        raise HTTPException(status_code=400, detail="card_id 不能为空")

    try:
        db = Database.get_instance()
        session = db.get_session()
        try:
            boss = session.query(Boss).filter(Boss.id == boss_id).first()
            if not boss:
                raise HTTPException(status_code=404, detail=f"Boss {boss_id} 不存在")

            question = None
            if boss.question_id:
                question = session.query(Question).filter(Question.id == boss.question_id).first()

            if question and question.question_type == "LeetCode挑战":
                user_answer = leetcode_result or ("solved" if is_solved else "give_up")
            else:
                user_answer = answer

            if not user_answer and not is_solved:
                raise HTTPException(status_code=400, detail="answer 或 is_solved 不能同时为空")
        finally:
            session.close()

        flow = BossBattleFlow()
        battle_session = None
        for bid, bs in flow.active_battles.items():
            if bs.boss_id == boss_id:
                battle_session = bs
                battle_id = bid
                break

        if not battle_session:
            battle_session = await flow.start_battle(boss_id, [int(card_id)])
            battle_id = id(battle_session)
            flow.active_battles[battle_id] = battle_session

        result = await flow.submit_answer(battle_id, user_answer, request_data={"is_solved": is_solved})
        return {
            "is_victory": result.is_victory,
            "is_correct": result.is_victory,
            "durability_change": result.durability_change,
            "new_card_dropped": result.new_card_dropped,
            "dropped_card": result.dropped_card,
            "feedback": result.feedback,
            "improvement": result.improvement,
            "reward": {
                "exp": 100 if result.is_victory else 0,
                "durability_change": result.durability_change
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@boss_router.post("/boss/generate")
async def generate_boss(request: dict):
    """为卡牌生成Boss"""
    from algomate.core.flow.boss_battle import BossBattleFlow

    card_id = request.get("card_id")
    difficulty = request.get("difficulty")

    if not card_id:
        raise HTTPException(status_code=400, detail="card_id 不能为空")

    try:
        flow = BossBattleFlow()
        result = await flow.generate_boss_for_card(card_id, difficulty)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@boss_router.post("/boss/generate-for-card")
async def generate_boss_for_card(request: dict):
    from algomate.core.flow.boss_battle import BossBattleFlow

    card_id = request.get("card_id")

    if not card_id:
        raise HTTPException(status_code=400, detail="card_id 不能为空")

    try:
        flow = BossBattleFlow()
        result = await flow.generate_boss_for_card(card_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@boss_router.post("/battle/start")
async def start_battle(request: dict):
    """开始战斗"""
    from algomate.core.flow.boss_battle import BossBattleFlow

    boss_id = request.get("boss_id")
    card_ids = request.get("card_ids", [])

    if not boss_id:
        raise HTTPException(status_code=400, detail="boss_id 不能为空")
    if not card_ids:
        raise HTTPException(status_code=400, detail="card_ids 不能为空")

    try:
        flow = BossBattleFlow()
        result = await flow.start_battle(boss_id, card_ids)
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@boss_router.post("/battle/{battle_id}/submit")
async def submit_battle_answer(battle_id: int, request: dict):
    """提交战斗答案"""
    from algomate.core.flow.boss_battle import BossBattleFlow

    code = request.get("code", "")

    try:
        flow = BossBattleFlow()
        result = await flow.submit_answer(battle_id, code)
        return {
            "is_victory": result.is_victory,
            "durability_change": result.durability_change,
            "new_card_dropped": result.new_card_dropped,
            "dropped_card": result.dropped_card,
            "feedback": result.feedback,
            "improvement": result.improvement
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@boss_router.get("/battle/{battle_id}/result")
async def get_battle_result(battle_id: int):
    """获取战斗结果"""
    from algomate.core.flow.boss_battle import BossBattleFlow

    flow = BossBattleFlow()
    battle_session = flow.active_battles.get(battle_id)

    if not battle_session:
        raise HTTPException(status_code=404, detail=f"战斗 {battle_id} 不存在")

    return battle_session.to_dict()


tasks_router = APIRouter()


@realm_router.get("")
async def get_realms():
    """获取所有秘境列表"""
    from algomate.core.game.realm_unlock import Realm, RealmUnlockManager
    from algomate.data.database import Database
    from algomate.models.cards import Card
    from algomate.models.npcs import NPC

    _init_default_npcs()

    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.is_sealed == False).all()
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


@realm_router.get("/{realm_id}")
async def get_realm_by_id(realm_id: str):
    """根据ID获取秘境详情"""
    from algomate.core.game.realm_unlock import Realm, RealmUnlockManager
    from algomate.data.database import Database
    from algomate.models.cards import Card

    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.is_sealed == False).all()
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


@realm_router.post("/{realm_id}/check-unlock")
async def check_realm_unlock(realm_id: str):
    """检查秘境是否解锁"""
    from algomate.core.game.realm_unlock import Realm, RealmUnlockManager
    from algomate.data.database import Database
    from algomate.models.cards import Card

    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).filter(Card.is_sealed == False).all()
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


@npc_router.get("/{npc_id}")
async def get_npc_by_id(npc_id: int):
    """根据ID获取NPC详情"""
    from algomate.data.database import Database
    from algomate.models.npcs import NPC

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

    db = Database.get_instance()
    session = db.get_session()
    try:
        npc = session.query(NPC).filter(NPC.id == npc_id).first()
        if not npc:
            raise HTTPException(status_code=404, detail=f"NPC {npc_id} 不存在")

        import json
        realm_id = REALM_NAME_TO_ID.get(npc.location, npc.location)
        topics = json.loads(npc.topics) if npc.topics else []
        return {
            "id": npc.id,
            "name": npc.name,
            "domain": npc.domain,
            "realmId": realm_id,
            "location": npc.location,
            "avatar": npc.avatar,
            "greeting": npc.greeting,
            "expertise": topics,
            "topics": topics,
        }
    finally:
        session.close()


@npc_router.post("/{npc_id}/chat")
async def npc_chat(npc_id: int, request: dict):
    """与NPC聊天"""
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
        if "timeout" in error_msg or "timed out" in error_msg:
            raise HTTPException(status_code=504, detail="AI服务响应超时，请稍后重试")
        if "connection" in error_msg or "network" in error_msg:
            raise HTTPException(status_code=503, detail="AI服务连接失败，请稍后重试")
        if "rate limit" in error_msg or "429" in error_msg:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        if "api key" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            raise HTTPException(status_code=500, detail="AI服务认证失败，请检查API配置")
        raise HTTPException(status_code=500, detail=str(e))


@npc_router.post("/{npc_id}/chat/stream")
async def npc_chat_stream(npc_id: int, request: dict):
    """与NPC聊天（SSE流式）"""
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
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.get("/tasks")
async def get_tasks(date: str = None):
    """获取修炼任务

    Args:
        date: 日期字符串，支持 'today' 或 'YYYY-MM-DD' 格式
    """
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        if date == "today" or date is None:
            tasks = scheduler.generate_daily_tasks()
        else:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                tasks = scheduler.generate_daily_tasks(target_date)
            except ValueError:
                tasks = scheduler.generate_daily_tasks()
        return {"tasks": [task.to_dict() for task in tasks]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.get("/tasks/upcoming")
async def get_upcoming_tasks(days: int = 7):
    """获取未来N天修炼计划"""
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        reviews = scheduler.get_upcoming_reviews(days)
        return {"upcoming": reviews, "days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.post("/tasks/execute")
async def execute_daily_tasks():
    """执行每日修炼任务"""
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        count = await scheduler.execute_daily_review()
        return {"executed": count, "message": f"执行了 {count} 个修炼任务"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


dialogue_router = APIRouter()


@dialogue_router.post("/dialogue/start")
async def start_dialogue(request: dict):
    """开始新对话"""
    from algomate.core.flow.npc_dialogue import NPCDialogueFlow

    npc_id = request.get("npc_id")
    topic = request.get("topic")

    if not npc_id:
        raise HTTPException(status_code=400, detail="npc_id 不能为空")

    try:
        flow = NPCDialogueFlow()
        result = await flow.start_dialogue(npc_id, topic)
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dialogue_router.post("/dialogue/{dialogue_id}/continue")
async def continue_dialogue(dialogue_id: int, request: dict):
    """继续对话"""
    from algomate.core.flow.npc_dialogue import NPCDialogueFlow

    message = request.get("message", "")

    if not message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    try:
        flow = NPCDialogueFlow()
        result = await flow.continue_dialogue(dialogue_id, message)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dialogue_router.post("/dialogue/{dialogue_id}/end")
async def end_dialogue(dialogue_id: int, request: dict):
    """结束对话并提交心得"""
    from algomate.core.flow.npc_dialogue import NPCDialogueFlow

    notes = request.get("notes", "")

    try:
        flow = NPCDialogueFlow()
        result = await flow.end_dialogue(dialogue_id, notes)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dialogue_router.get("/dialogue/{dialogue_id}/history")
async def get_dialogue_history(dialogue_id: int):
    """获取对话历史"""
    from algomate.core.flow.npc_dialogue import NPCDialogueFlow

    try:
        flow = NPCDialogueFlow()
        result = flow.get_dialogue_history(dialogue_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


user_router = APIRouter()


@user_router.get("/user")
async def get_user():
    from algomate.data.database import Database
    from algomate.models.user_settings import UserSetting

    db = Database.get_instance()
    session = db.get_session()
    try:
        nickname_setting = session.query(UserSetting).filter(UserSetting.key == "nickname").first()
        level_setting = session.query(UserSetting).filter(UserSetting.key == "level").first()
        experience_setting = session.query(UserSetting).filter(UserSetting.key == "experience").first()

        nickname = nickname_setting.value if nickname_setting else "冒险者"
        level = int(level_setting.value) if level_setting else 1
        experience = int(experience_setting.value) if experience_setting else 0

        nextLevelExp = int(100 * (1.5 ** (level - 1)))

        title_map = {
            1: "新手", 2: "见习生", 3: "探索者", 4: "冒险家", 5: "精英",
            6: "大师", 7: "宗师", 8: "传奇", 9: "神话"
        }
        title = title_map.get(level, "至尊")

        return {
            "id": 1,
            "nickname": nickname,
            "level": level,
            "experience": experience,
            "nextLevelExp": nextLevelExp,
            "title": title
        }
    finally:
        session.close()


@user_router.get("/user/stats")
async def get_user_stats():
    """获取用户统计数据"""
    from algomate.core.scheduler.review_scheduler import ReviewScheduler
    from algomate.data.database import Database
    from algomate.models.cards import Card

    db = Database.get_instance()
    session = db.get_session()
    try:
        total_cards = session.query(Card).count()
        sealed_cards = session.query(Card).filter(Card.is_sealed == True).count()
        critical_cards = session.query(Card).filter(Card.durability < 30).count()

        scheduler = ReviewScheduler()
        stats = scheduler.get_review_statistics()

        return {
            "total_cards": total_cards,
            "sealed_cards": sealed_cards,
            "critical_cards": critical_cards,
            "review_stats": stats
        }
    finally:
        session.close()


router.include_router(stats_router, prefix="/stats")
router.include_router(practice_router, prefix="/practice")
router.include_router(progress_router, prefix="/progress")
router.include_router(settings_router, prefix="/settings")
router.include_router(dashboard_router, prefix="/dashboard")
router.include_router(learning_router, prefix="/learning")
router.include_router(realm_router, prefix="/realms")
router.include_router(npc_router, prefix="/npc")
router.include_router(boss_router)
router.include_router(tasks_router)
router.include_router(dialogue_router)
router.include_router(user_router)
router.include_router(algorithm_info_router)
