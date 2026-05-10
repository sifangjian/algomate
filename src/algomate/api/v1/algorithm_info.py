from fastapi import APIRouter

router = APIRouter(prefix="/algorithm-info", tags=["算法信息"])


@router.get("")
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
