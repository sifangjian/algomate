from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import date, datetime, timedelta
import json

router = APIRouter()

notes_router = APIRouter()
practice_router = APIRouter()
progress_router = APIRouter()
settings_router = APIRouter()
dashboard_router = APIRouter()
learning_router = APIRouter()


def get_review_service():
    from algomate.review.review_plan_service import ReviewPlanService
    return ReviewPlanService()


@notes_router.get("/")
async def get_notes(
    algorithm_type: str = None,
    difficulty: str = None,
    keyword: str = None
):
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    session = db.get_session()
    try:
        from algomate.data.models import Note
        query = session.query(Note)

        if algorithm_type:
            query = query.filter(Note.algorithm_type == algorithm_type)
        if difficulty:
            query = query.filter(Note.difficulty == difficulty)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                Note.algorithm_type.like(pattern) |
                Note.title.like(pattern) |
                Note.content.like(pattern)
            )

        notes = query.order_by(Note.updated_at.desc()).all()
        note_list = []
        for note in notes:
            import json
            tags = []
            try:
                tags = json.loads(note.tags) if note.tags else []
            except:
                tags = []

            note_list.append({
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "summary": note.summary or "",
                "algorithm_type": note.algorithm_type,
                "tags": tags,
                "difficulty": note.difficulty,
                "mastery_level": note.mastery_level,
                "review_count": note.review_count,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None,
                "last_reviewed": note.last_reviewed.isoformat() if note.last_reviewed else None,
                "next_review_date": note.next_review_date.isoformat() if note.next_review_date else None
            })
        return {"notes": note_list}
    finally:
        session.close()


@notes_router.post("/")
async def create_note(note: dict):
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    try:
        new_note = note_repo.create(
            title=note.get("title", ""),
            content=note.get("content", ""),
            algorithm_type=note.get("algorithm_type", "其他"),
            difficulty=note.get("difficulty", "中等"),
            summary=note.get("summary", ""),
            tags=note.get("tags", "[]")
        )
        return {"id": new_note.id, "message": "笔记创建成功"}
    except Exception as e:
        return {"error": str(e)}, 500


@notes_router.get("/{note_id}")
async def get_note(note_id: int):
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    session = db.get_session()
    try:
        from algomate.data.models import Note
        note = session.query(Note).filter(Note.id == note_id).first()
        if not note:
            return {"error": "笔记不存在"}, 404

        import json
        tags = []
        try:
            tags = json.loads(note.tags) if note.tags else []
        except:
            tags = []

        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "summary": note.summary or "",
            "algorithm_type": note.algorithm_type,
            "tags": tags,
            "difficulty": note.difficulty,
            "mastery_level": note.mastery_level,
            "review_count": note.review_count,
            "created_at": note.created_at.isoformat() if note.created_at else None,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None
        }
    finally:
        session.close()


@notes_router.put("/{note_id}")
async def update_note(note_id: int, note_data: dict):
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    session = db.get_session()
    try:
        from algomate.data.models import Note
        note = session.query(Note).filter(Note.id == note_id).first()
        if not note:
            return {"error": "笔记不存在"}, 404

        if "title" in note_data:
            note.title = note_data["title"]
        if "content" in note_data:
            note.content = note_data["content"]
        if "algorithm_type" in note_data:
            note.algorithm_type = note_data["algorithm_type"]
        if "difficulty" in note_data:
            note.difficulty = note_data["difficulty"]
        if "summary" in note_data:
            note.summary = note_data["summary"]
        if "tags" in note_data:
            import json
            note.tags = json.dumps(note_data["tags"]) if isinstance(note_data["tags"], list) else note_data["tags"]

        from datetime import datetime
        note.updated_at = datetime.now()

        session.commit()
        return {"message": "笔记更新成功", "id": note_id}
    finally:
        session.close()


@notes_router.delete("/{note_id}")
async def delete_note(note_id: int):
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    success = note_repo.delete(note_id)
    if success:
        return {"message": "笔记删除成功"}
    return {"error": "笔记不存在"}, 404


@notes_router.post("/{note_id}/analyze")
async def analyze_note(note_id: int):
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository
    from algomate.core.agent.note_analyzer import NoteAnalyzer
    from algomate.core.agent.chat_client import ChatClient

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    session = db.get_session()
    try:
        from algomate.data.models import Note
        note = session.query(Note).filter(Note.id == note_id).first()
        if not note:
            return {"error": "笔记不存在"}, 404

        chat_client = ChatClient(api_key=config.LLM_API_KEY)
        analyzer = NoteAnalyzer(chat_client)

        result = analyzer.analyze_note(note.content)

        note.algorithm_type = result.algorithm_type
        note.difficulty = result.difficulty
        note.summary = result.summary

        import json
        if isinstance(result.tags, list):
            note.tags = json.dumps(result.tags, ensure_ascii=False)
        else:
            note.tags = json.dumps([result.tags], ensure_ascii=False) if result.tags else "[]"

        if not note.summary and result.key_points:
            note.summary = "; ".join(result.key_points[:3])

        from datetime import datetime
        note.updated_at = datetime.now()

        session.commit()

        return {
            "message": "AI分析完成",
            "analysis": {
                "algorithm_type": result.algorithm_type,
                "difficulty": result.difficulty,
                "summary": result.summary,
                "tags": result.tags,
                "key_points": result.key_points
            }
        }
    except Exception as e:
        return {"error": f"AI分析失败: {str(e)}"}, 500
    finally:
        session.close()


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

        import json
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


router.include_router(notes_router, prefix="/notes")
router.include_router(practice_router, prefix="/practice")
router.include_router(progress_router, prefix="/progress")
router.include_router(settings_router, prefix="/settings")
router.include_router(dashboard_router, prefix="/dashboard")
router.include_router(learning_router, prefix="/learning")
