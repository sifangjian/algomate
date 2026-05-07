import sys
import types

_overlapped = types.ModuleType("_overlapped")
_overlapped.CreateIoCompletionPort = lambda *a, **kw: 1
_overlapped.GetQueuedCompletionStatus = lambda *a, **kw: (0, 0, 0)
_overlapped.PostQueuedCompletionStatus = lambda *a, **kw: True
_overlapped.OVERLAPPED = type("OVERLAPPED", (), {"__init__": lambda self: None})
_overlapped.NULL = 0
_overlapped.INVALID_HANDLE_VALUE = -1
if "_overlapped" not in sys.modules:
    sys.modules["_overlapped"] = _overlapped

import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from algomate.data.database import Base, Database, _ensure_models_imported


@pytest.fixture(scope="function")
def test_app():
    _ensure_models_imported()
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    class TestDatabase:
        _instance = None

        @classmethod
        def get_instance(cls, config=None):
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

        def __init__(self):
            self.engine = engine
            self.SessionLocal = SessionLocal

        def get_session(self):
            return self.SessionLocal()

        def close(self):
            pass

    original_get_instance = Database.get_instance
    original_instance = Database._instance
    Database.get_instance = TestDatabase.get_instance
    Database._instance = TestDatabase()

    from algomate.config.settings import AppConfig

    original_appconfig_load = AppConfig.load
    original_appconfig_instance = AppConfig._instance

    test_config = AppConfig()
    test_config.LLM_API_KEY = ""
    AppConfig._instance = test_config
    AppConfig.load = classmethod(lambda cls, *a, **kw: test_config)

    from algomate.main import AlgomateApp

    app = AlgomateApp(config=test_config)

    client = TestClient(app.api_app)

    _seed_test_data(engine)

    yield client

    Database.get_instance = original_get_instance
    Database._instance = original_instance
    AppConfig.load = original_appconfig_load
    AppConfig._instance = original_appconfig_instance
    Base.metadata.drop_all(engine)
    engine.dispose()


def _seed_test_data(engine):
    from algomate.models.npcs import NPC
    from algomate.models.bosses import Boss
    from algomate.models.cards import Card

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        npc = NPC(
            name="测试NPC",
            title="测试导师",
            algorithm_type="basic_data_structure",
            specialties='["数组"]',
            domain="基础数据结构",
            location="新手森林",
            avatar="test",
            description="测试用NPC",
            system_prompt="你是测试NPC",
            greeting="你好",
            topics='["数组"]',
        )
        session.add(npc)
        session.commit()
        session.refresh(npc)

        boss = Boss(
            name="测试Boss",
            difficulty="easy",
            weakness_type="basic_data_structure",
            npc_id=npc.id,
            description="测试用Boss",
        )
        session.add(boss)

        boss2 = Boss(
            name="困难Boss",
            difficulty="hard",
            weakness_type="dynamic_programming",
            npc_id=npc.id,
            description="困难难度Boss",
        )
        session.add(boss2)

        weakness_card = Card(
            name="弱点卡牌",
            algorithm_type="basic_data_structure",
            durability=80,
            npc_id=npc.id,
            topic="数组",
            core_concept="数组与双指针",
        )
        session.add(weakness_card)

        other_card = Card(
            name="普通卡牌",
            algorithm_type="tree",
            durability=60,
            npc_id=npc.id,
            topic="树",
            core_concept="二叉树遍历",
        )
        session.add(other_card)

        session.commit()
    finally:
        session.close()
