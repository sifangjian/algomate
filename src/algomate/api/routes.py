from fastapi import APIRouter

router = APIRouter()

notes_router = APIRouter()
practice_router = APIRouter()
progress_router = APIRouter()
settings_router = APIRouter()


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
