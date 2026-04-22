from fastapi import APIRouter
from datetime import date, datetime, timedelta

router = APIRouter()

notes_router = APIRouter()
practice_router = APIRouter()
progress_router = APIRouter()
settings_router = APIRouter()
dashboard_router = APIRouter()


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

        chat_client = ChatClient()
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
async def get_today_review():
    from algomate.data.database import Database
    from algomate.data.repositories.review_repo import ReviewRecordRepository
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    review_repo = ReviewRecordRepository(db)
    note_repo = NoteRepository(db)

    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    session = db.get_session()
    try:
        from algomate.data.models import ReviewRecord, Note
        pending_reviews = (
            session.query(ReviewRecord, Note)
            .join(Note, ReviewRecord.note_id == Note.id)
            .filter(ReviewRecord.status == "pending")
            .filter(ReviewRecord.review_date >= today_start, ReviewRecord.review_date <= today_end)
            .all()
        )
        review_list = []
        for record, note in pending_reviews:
            review_list.append({
                "id": record.id,
                "note_id": note.id,
                "title": note.title,
                "algorithm_type": note.algorithm_type,
                "difficulty": note.difficulty,
                "mastery_level": note.mastery_level,
                "review_date": record.review_date.isoformat() if record.review_date else None,
                "status": record.status
            })
        return {"reviews": review_list}
    finally:
        session.close()


@dashboard_router.get("/weak-points")
async def get_weak_points():
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    session = db.get_session()
    try:
        from algomate.data.models import Note
        weak_notes = session.query(Note).filter(Note.mastery_level < 30).order_by(Note.mastery_level).limit(5).all()
        weak_points = []
        for note in weak_notes:
            weak_points.append({
                "id": note.id,
                "title": note.title,
                "algorithm_type": note.algorithm_type,
                "mastery_level": note.mastery_level,
                "review_count": note.review_count
            })
        return {"weak_points": weak_points}
    finally:
        session.close()


@dashboard_router.get("/stats")
async def get_dashboard_stats():
    from algomate.data.database import Database
    from algomate.data.repositories.progress_repo import ProgressRepository

    db = Database.get_instance()
    progress_repo = ProgressRepository(db)

    session = db.get_session()
    try:
        from algomate.data.models import LearningProgress
        learning_days = session.query(LearningProgress).count()
        return {
            "learning_days": learning_days
        }
    finally:
        session.close()


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


router.include_router(notes_router, prefix="/notes")
router.include_router(practice_router, prefix="/practice")
router.include_router(progress_router, prefix="/progress")
router.include_router(settings_router, prefix="/settings")
router.include_router(dashboard_router, prefix="/dashboard")
