from fastapi import APIRouter
from datetime import date, datetime, timedelta

router = APIRouter()

notes_router = APIRouter()
practice_router = APIRouter()
progress_router = APIRouter()
settings_router = APIRouter()
dashboard_router = APIRouter()


@notes_router.get("/")
async def get_notes():
    return {"notes": []}


@notes_router.post("/")
async def create_note(note: dict):
    return {"id": 1, "message": "笔记创建成功"}


@notes_router.get("/{note_id}")
async def get_note(note_id: int):
    return {"id": note_id, "title": "示例笔记", "content": "笔记内容"}


@notes_router.delete("/{note_id}")
async def delete_note(note_id: int):
    return {"message": "笔记删除成功"}


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
    return {
        "api_key": "",
        "email_host": "",
        "email_port": 587,
        "review_time": "09:00",
        "forgetting_curve_param": 30
    }


@settings_router.post("/")
async def save_settings(settings: dict):
    return {"message": "设置保存成功"}


router.include_router(notes_router, prefix="/notes")
router.include_router(practice_router, prefix="/practice")
router.include_router(progress_router, prefix="/progress")
router.include_router(settings_router, prefix="/settings")
router.include_router(dashboard_router, prefix="/dashboard")
