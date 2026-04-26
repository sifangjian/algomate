"""
数据模型模块

包含所有业务实体的数据模型定义
"""

from algomate.models.user_settings import UserSetting, UserSettingCreate, UserSettingUpdate, UserSettingResponse
from algomate.models.notes import Note, NoteCreate, NoteUpdate, NoteResponse
from algomate.models.cards import Card, CardCreate, CardUpdate, CardResponse, Domain, DomainStats
from algomate.models.npcs import NPC, NPCCreate, NPCUpdate, NPCResponse
from algomate.models.bosses import Boss, BossCreate, BossUpdate, BossResponse, Difficulty, BossSource
from algomate.models.questions import Question, QuestionCreate, QuestionUpdate, QuestionResponse, QuestionType, QuestionDifficulty
from algomate.models.answer_records import AnswerRecord, AnswerRecordCreate, AnswerRecordResponse, AnswerStats
from algomate.models.dialogue_records import DialogueRecord, DialogueRecordCreate, DialogueRecordResponse, DialogueMessage

from algomate.models.user_settings import router as user_settings_router
from algomate.models.notes import router as notes_router
from algomate.models.cards import router as cards_router
from algomate.models.npcs import router as npcs_router
from algomate.models.bosses import router as bosses_router
from algomate.models.questions import router as questions_router
from algomate.models.answer_records import router as answers_router
from algomate.models.dialogue_records import router as dialogues_router

__all__ = [
    "UserSetting",
    "UserSettingCreate",
    "UserSettingUpdate",
    "UserSettingResponse",
    "Note",
    "NoteCreate",
    "NoteUpdate",
    "NoteResponse",
    "Card",
    "CardCreate",
    "CardUpdate",
    "CardResponse",
    "Domain",
    "DomainStats",
    "NPC",
    "NPCCreate",
    "NPCUpdate",
    "NPCResponse",
    "Boss",
    "BossCreate",
    "BossUpdate",
    "BossResponse",
    "Difficulty",
    "BossSource",
    "Question",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "QuestionType",
    "QuestionDifficulty",
    "AnswerRecord",
    "AnswerRecordCreate",
    "AnswerRecordResponse",
    "AnswerStats",
    "DialogueRecord",
    "DialogueRecordCreate",
    "DialogueRecordResponse",
    "DialogueMessage",
    "user_settings_router",
    "notes_router",
    "cards_router",
    "npcs_router",
    "bosses_router",
    "questions_router",
    "answers_router",
    "dialogues_router",
]
