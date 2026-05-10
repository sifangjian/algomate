from fastapi import APIRouter

from algomate.api.v1.cards import router as cards_router
from algomate.api.v1.settings import router as settings_router
from algomate.api.v1.npcs import router as npcs_router
from algomate.api.v1.bosses import router as bosses_router
from algomate.api.v1.reviews import router as reviews_router
from algomate.api.v1.stats import router as stats_router
from algomate.api.v1.realms import router as realms_router
from algomate.api.v1.dialogues import router as dialogues_router
from algomate.api.v1.dashboard import router as dashboard_router
from algomate.api.v1.practice import router as practice_router
from algomate.api.v1.learning import router as learning_router
from algomate.api.v1.tasks import router as tasks_router
from algomate.api.v1.users import router as users_router
from algomate.api.v1.progress import router as progress_router
from algomate.api.v1.algorithm_info import router as algorithm_info_router

router = APIRouter()

router.include_router(cards_router)
router.include_router(settings_router)
router.include_router(npcs_router)
router.include_router(bosses_router)
router.include_router(reviews_router)
router.include_router(stats_router)
router.include_router(realms_router)
router.include_router(dialogues_router)
router.include_router(dashboard_router)
router.include_router(practice_router)
router.include_router(learning_router)
router.include_router(tasks_router)
router.include_router(users_router)
router.include_router(progress_router)
router.include_router(algorithm_info_router)
