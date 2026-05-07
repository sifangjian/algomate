from fastapi import APIRouter

from algomate.api.v1.cards import router as cards_router
from algomate.api.v1.settings import router as settings_router

router = APIRouter()
router.include_router(cards_router)
router.include_router(settings_router)
