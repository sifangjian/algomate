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


def _ensure_npc_exists(session, realm_name: str, npc_data: dict) -> int:
    """确保 NPC 存在于数据库中，返回 NPC ID"""
    from algomate.models.npcs import NPC

    existing = session.query(NPC).filter(NPC.location == realm_name).first()
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
            "新手森林": {
                "name": "引导者艾琳",
                "domain": "基础数据结构",
                "avatar": "🧙‍♀️",
                "description": "基础数据结构的导师",
                "system_prompt": "你是引导者艾琳，基础数据结构的导师。你采用渐进式传授法：每次回答只聚焦一个核心要点，用1-2句话说清楚核心思想，再配一个形象易懂的例子。回答末尾用【推荐追问】格式给出2-4个追问话题，引导修习者逐步深入。不要一次性输出过多信息，让修习成为互动的渐进过程。",
                "greeting": "欢迎来到新手森林！准备好开始你的算法之旅了吗？",
                "topics": ["数组", "链表", "栈", "队列", "哈希表", "二分查找", "线性查找"]
            },
            "迷雾沼泽": {
                "name": "沼泽向导卡尔",
                "domain": "递归与回溯",
                "avatar": "🐸",
                "description": "递归与回溯的导师",
                "system_prompt": "你是沼泽向导卡尔，递归与回溯的导师。你采用渐进式传授法：每次回答只聚焦一个核心要点，用1-2句话说清楚核心思想，再配一个形象易懂的例子。回答末尾用【推荐追问】格式给出2-4个追问话题，引导修习者逐步深入。不要一次性输出过多信息，让修习成为互动的渐进过程。",
                "greeting": "欢迎来到迷雾沼泽！迷雾虽浓，但我会为你指引方向。想从哪里开始？",
                "topics": ["递归", "回溯", "树遍历", "DFS", "BFS"]
            },
            "智慧圣殿": {
                "name": "智者雅典娜",
                "domain": "动态规划",
                "avatar": "🦉",
                "description": "动态规划的导师",
                "system_prompt": "你是智者雅典娜，动态规划的导师。你采用渐进式传授法：每次回答只聚焦一个核心要点，用1-2句话说清楚核心思想，再配一个形象易懂的例子。回答末尾用【推荐追问】格式给出2-4个追问话题，引导修习者逐步深入。不要一次性输出过多信息，让修习成为互动的渐进过程。",
                "greeting": "欢迎来到智慧圣殿！让我为你照亮智慧之路。",
                "topics": ["动态规划", "贪心算法", "分治策略"]
            },
            "贪婪之塔": {
                "name": "守塔人戈尔",
                "domain": "图论与高级算法",
                "avatar": "🏰",
                "description": "图论与高级算法的导师",
                "system_prompt": "你是守塔人戈尔，图论与高级算法的导师。你采用渐进式传授法：每次回答只聚焦一个核心要点，用1-2句话说清楚核心思想，再配一个形象易懂的例子。回答末尾用【推荐追问】格式给出2-4个追问话题，引导修习者逐步深入。不要一次性输出过多信息，让修习成为互动的渐进过程。",
                "greeting": "欢迎来到贪婪之塔！挑战就在眼前，你准备好了吗？",
                "topics": ["图论", "最短路径", "最小生成树", "网络流"]
            },
            "命运迷宫": {
                "name": "迷宫守护者墨丘利",
                "domain": "高级数据结构",
                "avatar": "🌀",
                "description": "高级数据结构的导师",
                "system_prompt": "你是迷宫守护者墨丘利，高级数据结构的导师。你采用渐进式传授法：每次回答只聚焦一个核心要点，用1-2句话说清楚核心思想，再配一个形象易懂的例子。回答末尾用【推荐追问】格式给出2-4个追问话题，引导修习者逐步深入。不要一次性输出过多信息，让修习成为互动的渐进过程。",
                "greeting": "欢迎来到命运迷宫！每一条路都通向新的发现。",
                "topics": ["堆", "Trie", "并查集", "线段树", "树状数组"]
            },
            "分裂山脉": {
                "name": "山巨人顿",
                "domain": "算法巅峰",
                "avatar": "⛰️",
                "description": "算法巅峰的导师",
                "system_prompt": "你是山巨人顿，算法巅峰的导师。你采用渐进式传授法：每次回答只聚焦一个核心要点，用1-2句话说清楚核心思想，再配一个形象易懂的例子。回答末尾用【推荐追问】格式给出2-4个追问话题，引导修习者逐步深入。不要一次性输出过多信息，让修习成为互动的渐进过程。",
                "greeting": "欢迎来到分裂山脉！前方的挑战将考验你的极限。",
                "topics": ["高级算法", "复杂算法分析", "算法优化"]
            },
            "数学殿堂": {
                "name": "数学家欧几里得",
                "domain": "数学与复杂度",
                "avatar": "📐",
                "description": "数学与复杂度的导师",
                "system_prompt": "你是数学家欧几里得，数学与复杂度的导师。你采用渐进式传授法：每次回答只聚焦一个核心要点，用1-2句话说清楚核心思想，再配一个形象易懂的例子。回答末尾用【推荐追问】格式给出2-4个追问话题，引导修习者逐步深入。不要一次性输出过多信息，让修习成为互动的渐进过程。",
                "greeting": "欢迎来到数学殿堂！让我们一起探索数学的奥秘。",
                "topics": ["数学证明", "时间复杂度", "空间复杂度", "组合数学"]
            },
            "试炼之地": {
                "name": "试炼之主",
                "domain": "终极试炼",
                "avatar": "⚔️",
                "description": "终极试炼的导师",
                "system_prompt": "你是试炼之主，终极试炼的导师。你采用渐进式传授法：每次回答只聚焦一个核心要点，用1-2句话说清楚核心思想，再配一个形象易懂的例子。回答末尾用【推荐追问】格式给出2-4个追问话题，引导修习者逐步深入。不要一次性输出过多信息，让修习成为互动的渐进过程。",
                "greeting": "欢迎来到试炼之地！终极试炼等待着你。",
                "topics": ["综合修炼", "算法面试", "竞赛试炼"]
            },
        }

        for realm_name, npc_data in default_npcs.items():
            _ensure_npc_exists(session, realm_name, npc_data)

    finally:
        session.close()


def get_review_service():
    from algomate.review.review_plan_service import ReviewPlanService
    return ReviewPlanService()


@practice_router.get("/questions")
async def get_questions(question_type: str = None):
    return {"questions": []}


@practice_router.post("/submit")
async def submit_answer(answer: dict):
    return {"result": "correct", "feedback": "回答正确！"}


@practice_router.get("/weak-points")
async def get_weak_points():
    return {"weak_points": []}


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
                "topics": ["阶乘与斐波那契", "全排列", "组合", "N皇后"]
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
        prompt = f"""针对"{topic}"这个算法主题，生成3道高质量的试炼，包括1道选择题、1道简答题和1道代码题。

要求：
- 选择题必须有4个选项（A、B、C、D），只有一个正确答案
- 简答题考查对概念和原理的理解
- 代码题需要编写代码实现

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
            "question_type": "代码题",
            "content": "试炼描述",
            "answer": "参考代码",
            "explanation": "解题思路"
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

    code = request.get("code")
    answer = request.get("answer", "")
    card_id = request.get("card_id") or request.get("cardId")

    if not card_id:
        raise HTTPException(status_code=400, detail="card_id 不能为空")

    if not code and not answer:
        raise HTTPException(status_code=400, detail="code 或 answer 不能同时为空")

    try:
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

        result = await flow.submit_answer(battle_id, answer, code=code)
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


@boss_router.post("/boss/{boss_id}/run-code")
async def run_boss_code(boss_id: int, request: dict):
    from algomate.core.flow.boss_battle import BossBattleFlow
    from algomate.data.database import Database
    from algomate.models.bosses import Boss
    from algomate.models.questions import Question
    import json

    code = request.get("code", "")

    if not code.strip():
        raise HTTPException(status_code=400, detail="code 不能为空")

    try:
        db = Database.get_instance()
        session = db.get_session()
        try:
            boss = session.query(Boss).filter(Boss.id == boss_id).first()
            if not boss:
                raise HTTPException(status_code=404, detail=f"Boss {boss_id} 不存在")

            test_cases = []
            if boss.question_id:
                question = session.query(Question).filter(Question.id == boss.question_id).first()
                if question and question.options:
                    try:
                        parsed = json.loads(question.options)
                        if isinstance(parsed, list):
                            test_cases = parsed
                    except (json.JSONDecodeError, TypeError):
                        pass

            flow = BossBattleFlow()
            result = flow.run_code(code, test_cases)
            return result
        finally:
            session.close()
    except HTTPException:
        raise
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
                "description": "深入递归与回溯的领域，挑战迷雾史莱姆王",
                "bossInfo": {"id": "boss_slime_king", "name": "迷雾史莱姆王", "difficulty": 2},
            },
            "智慧圣殿": {
                "icon": "💡",
                "description": "动态规划的璀璨世界，用智慧照亮黑暗",
                "bossInfo": None,
            },
            "贪婪之塔": {
                "icon": "🏰",
                "description": "图论与高级算法的终极试炼场",
                "bossInfo": {"id": "boss_greed_dragon", "name": "贪婪巨龙", "difficulty": 3},
            },
            "命运迷宫": {
                "icon": "🌀",
                "description": "高级数据结构的圣域，触及算法的极限",
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

            npc = session.query(NPC).filter(NPC.location == realm.value).first()
            npc_id = npc.id if npc else None
            npc_name = npc.name if npc else f"{realm.value}导师"
            npc_avatar = npc.avatar if npc else "🧙‍♀️"

            realms_data.append({
                "id": realm.value,
                "name": realm.value,
                "icon": config.get("icon", "🗝️"),
                "description": config.get("description", ""),
                "status": status,
                "order": realm_order,
                "progress": int(progress.progress_percentage),
                "npcInfo": {"id": npc_id, "name": npc_name, "avatar": npc_avatar},
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
    """获取当前用户信息（单用户系统，返回默认用户）"""
    return {
        "id": 1,
        "username": "default_user",
        "email": "user@example.com",
        "level": 1,
        "experience": 0
    }


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
