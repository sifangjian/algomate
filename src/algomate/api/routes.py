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


@dashboard_router.post("/review/start/{note_id}")
async def start_review(note_id: int):
    review_service = get_review_service()
    result = review_service.start_review(note_id)
    if result is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return result


@dashboard_router.post("/review/complete/{note_id}")
async def complete_review(note_id: int, review_data: dict):
    review_service = get_review_service()
    score = review_data.get("score", 0)
    is_correct = review_data.get("is_correct", False)
    difficulty = review_data.get("difficulty", "中等")
    result = review_service.complete_review(note_id, score, is_correct, difficulty)
    if result is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return result


@dashboard_router.post("/review/skip/{note_id}")
async def skip_review(note_id: int, reason: str = ""):
    review_service = get_review_service()
    success = review_service.skip_review(note_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {"message": "已跳过复习", "note_id": note_id}


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


@dashboard_router.get("/review/schedule/{note_id}")
async def get_note_review_schedule(note_id: int):
    review_service = get_review_service()
    schedule = review_service.generate_review_plan_for_note(note_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
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


@learning_router.get("/topics")
async def get_learning_topics():
    """获取可学习的主题列表

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
    """学习模式下的对话（流式）

    Args:
        message: 包含 topic（学习主题）和 question（用户问题）的字典

    Returns:
        流式 AI 回复内容 (text/event-stream)
    """
    from algomate.core.agent.chat_client import ChatClient

    topic = message.get("topic", "")
    question = message.get("question", "")
    conversation_history = message.get("history", [])

    if not question:
        return {"error": "问题不能为空"}

    system_prompt = f"""你是一个专业的算法学习导师，擅长用简洁清晰的方式讲解算法知识。

当前学习主题：{topic}

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
    """为当前学习主题生成小测验

    Args:
        request: 包含 topic（学习主题）的字典

    Returns:
        生成的测验题目
    """
    from algomate.core.agent.question_generator import QuestionGenerator

    topic = request.get("topic", "")

    if not topic:
        return {"error": "主题不能为空"}

    try:
        generator = QuestionGenerator()
        prompt = f"""针对"{topic}"这个算法主题，生成3道高质量的练习题，包括1道选择题、1道简答题和1道代码题。

要求：
- 选择题必须有4个选项（A、B、C、D），只有一个正确答案
- 简答题考查对概念和原理的理解
- 代码题需要编写代码实现

请返回JSON格式，包含一个questions数组：
{{
    "questions": [
        {{
            "question_type": "选择题",
            "content": "题目内容（包含选项A、B、C、D）",
            "answer": "正确答案",
            "explanation": "解析"
        }},
        {{
            "question_type": "简答题",
            "content": "题目内容",
            "answer": "参考答案要点",
            "explanation": "解析"
        }},
        {{
            "question_type": "代码题",
            "content": "题目描述",
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
    """保存学习笔记

    Args:
        note_data: 包含 title, content, algorithm_type, difficulty 的字典

    Returns:
        创建的笔记信息
    """
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    try:
        new_note = note_repo.create(
            title=note_data.get("title", ""),
            content=note_data.get("content", ""),
            algorithm_type=note_data.get("algorithm_type", "其他"),
            difficulty=note_data.get("difficulty", "中等"),
            summary=note_data.get("summary", ""),
            tags=note_data.get("tags", "[]")
        )
        return {"id": new_note.id, "message": "笔记保存成功"}
    except Exception as e:
        return {"error": str(e)}, 500


@learning_router.get("/explain-concept")
async def explain_concept(topic: str, concept: str):
    """获取概念解释

    Args:
        topic: 学习主题
        concept: 概念名称

    Returns:
        概念的详细解释
    """
    from algomate.core.agent.chat_client import ChatClient

    if not concept:
        return {"error": "概念名称不能为空"}

    system_prompt = f"""你是一个专业的算法学习导师，擅长解释算法概念。

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


@tasks_router.get("/tasks/daily")
async def get_daily_tasks():
    """获取今日复习任务"""
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        tasks = scheduler.generate_daily_tasks()
        return {"tasks": [task.to_dict() for task in tasks]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.get("/tasks/upcoming")
async def get_upcoming_tasks(days: int = 7):
    """获取未来N天复习计划"""
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        reviews = scheduler.get_upcoming_reviews(days)
        return {"upcoming": reviews, "days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.post("/tasks/execute")
async def execute_daily_tasks():
    """执行每日复习任务"""
    from algomate.core.scheduler.review_scheduler import ReviewScheduler

    try:
        scheduler = ReviewScheduler()
        count = await scheduler.execute_daily_review()
        return {"executed": count, "message": f"执行了 {count} 个复习任务"}
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
    """结束对话并提交笔记"""
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
router.include_router(boss_router)
router.include_router(tasks_router)
router.include_router(dialogue_router)
router.include_router(user_router)
