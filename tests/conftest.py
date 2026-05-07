import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from algomate.data.database import Base
from algomate.models.npcs import NPC
from algomate.models.bosses import Boss
from algomate.models.cards import Card
from algomate.models.battle_records import BattleRecord
from algomate.models.notes import Note
from algomate.models.questions import Question
from algomate.models.answer_records import AnswerRecord
from algomate.models.dialogue_records import DialogueRecord
from algomate.models.dialogue_messages import DialogueMessageRecord
from algomate.models.dialogue_notes import DialogueNote
from algomate.models.review_records import ReviewRecord
from algomate.models.learning_progress import LearningProgress
from algomate.models.user_settings import UserSetting


class _InMemoryDatabase:
    def __init__(self, engine):
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=engine)

    def get_session(self):
        return self.SessionLocal()


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_db(db_engine):
    return _InMemoryDatabase(db_engine)


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_npc(db_session):
    npc = NPC(
        name="测试导师",
        title="测试导师",
        algorithm_type="basic_data_structure",
        specialties="[]",
        topics="[]",
    )
    db_session.add(npc)
    db_session.commit()
    db_session.refresh(npc)
    return npc


@pytest.fixture
def sample_boss(db_session, sample_npc):
    boss = Boss(
        name="测试Boss",
        difficulty="easy",
        weakness_type="basic_data_structure",
        npc_id=sample_npc.id,
        description="测试Boss描述",
    )
    db_session.add(boss)
    db_session.commit()
    db_session.refresh(boss)
    return boss


@pytest.fixture
def sample_card(db_session, sample_npc):
    card = Card(
        name="测试卡牌",
        algorithm_type="basic_data_structure",
        npc_id=sample_npc.id,
    )
    db_session.add(card)
    db_session.commit()
    db_session.refresh(card)
    return card
