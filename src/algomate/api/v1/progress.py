from fastapi import APIRouter

router = APIRouter(prefix="/progress", tags=["进度"])


@router.get("/stats")
async def get_stats():
    return {
        "total_notes": 0,
        "total_practice": 0,
        "accuracy_rate": 0,
        "learning_days": 0
    }


@router.get("/mastery")
async def get_mastery():
    return {"mastery": {}}
