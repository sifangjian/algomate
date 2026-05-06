from fastapi import APIRouter

from algomate.api.v1.cards import router as cards_router

router = APIRouter()
router.include_router(cards_router)
