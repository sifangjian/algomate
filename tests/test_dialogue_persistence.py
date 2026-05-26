import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from algomate.data.database import Base, Database
from algomate.models.dialogue_records import DialogueRecord
from algomate.models.dialogue_messages import DialogueMessageRecord
from algomate.models.dialogue_notes import DialogueNote
from algomate.models.npcs import NPC
from algomate.models.cards import Card
from algomate.api.v1.dialogues import (
    DialogueState,
    DialogueSession,
    _active_sessions,
)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    _test_db = MagicMock()
    _test_db.engine = engine
    _test_db.get_session = lambda: TestSession()
    _test_db.close = lambda: engine.dispose()

    monkeypatch.setattr(Database, "_instance", _test_db)

    _active_sessions.clear()

    yield

    Database._instance = None
    _active_sessions.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _create_test_npc(session, **overrides):
    defaults = {
        "name": "测试导师",
        "title": "动态规划大师",
        "algorithm_type": "动态规划",
        "specialties": json.dumps(["背包问题"], ensure_ascii=False),
        "avatar": "/avatars/test.png",
        "description": "测试用NPC",
        "topics": json.dumps(["背包问题"], ensure_ascii=False),
        "location": "智慧圣殿",
        "system_prompt": "你是动态规划领域的专家导师。",
        "greeting": "欢迎来到智慧圣殿！",
    }
    defaults.update(overrides)
    npc = NPC(**defaults)
    session.add(npc)
    session.commit()
    session.refresh(npc)
    return npc


def _create_test_dialogue(session, npc_id, **overrides):
    defaults = {
        "npc_id": npc_id,
        "topic": "背包问题",
        "status": "active",
        "last_active_at": datetime.now(),
        "created_at": datetime.now(),
    }
    defaults.update(overrides)
    record = DialogueRecord(**defaults)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def _create_test_message(session, dialogue_id, role, content):
    msg = DialogueMessageRecord(
        dialogue_id=dialogue_id,
        role=role,
        content=content,
        created_at=datetime.now(),
    )
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg


def _create_test_card(session, npc_id, dialogue_id=None, **overrides):
    defaults = {
        "name": "背包问题",
        "algorithm_type": "动态规划",
        "durability": 80,
        "npc_id": npc_id,
        "topic": "背包问题",
    }
    if dialogue_id is not None:
        defaults["dialogue_id"] = dialogue_id
    defaults.update(overrides)
    card = Card(**defaults)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


class TestGetDialogueByCard:
    """GET /dialogues/by-card/{card_id}"""

    def test_returns_dialogue_info_when_card_has_dialogue(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        dialogue = _create_test_dialogue(session, npc.id)
        _create_test_message(session, dialogue.id, "user", "什么是背包问题？")
        _create_test_message(session, dialogue.id, "assistant", "背包问题是一个经典DP问题。")
        card = _create_test_card(session, npc.id, dialogue_id=dialogue.id)

        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get(f"/dialogues/by-card/{card.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dialogue_id"] == dialogue.id
        assert data["npc_id"] == npc.id
        assert data["npc_name"] == "测试导师"
        assert data["message_count"] == 2
        assert data["status"] == "active"
        session.close()

    def test_returns_404_when_card_has_no_dialogue(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        card = _create_test_card(session, npc.id)

        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get(f"/dialogues/by-card/{card.id}")
        assert resp.status_code == 404
        session.close()

    def test_returns_404_when_card_not_found(self):
        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/dialogues/by-card/99999")
        assert resp.status_code == 404


class TestResumeDialogue:
    """POST /dialogues/{dialogue_id}/resume"""

    def test_resumes_ended_dialogue(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        dialogue = _create_test_dialogue(session, npc.id, status="ended")

        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post(f"/dialogues/{dialogue.id}/resume")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dialogue_id"] == dialogue.id
        assert data["status"] == "active"
        assert data["npc_name"] == "测试导师"

        session.refresh(dialogue)
        assert dialogue.status == "active"

        messages = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue.id
        ).all()
        assert len(messages) == 1
        assert "继续" in messages[0].content
        session.close()

    def test_active_dialogue_returns_current_state(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        dialogue = _create_test_dialogue(session, npc.id, status="active")

        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post(f"/dialogues/{dialogue.id}/resume")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "active"

        session.refresh(dialogue)
        assert dialogue.status == "active"
        session.close()

    def test_returns_404_for_nonexistent_dialogue(self):
        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/dialogues/99999/resume")
        assert resp.status_code == 404


class TestClearDialogueMessages:
    """DELETE /dialogues/{dialogue_id}/messages"""

    def test_clears_all_messages(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        dialogue = _create_test_dialogue(session, npc.id)
        _create_test_message(session, dialogue.id, "user", "问题1")
        _create_test_message(session, dialogue.id, "assistant", "回答1")
        _create_test_message(session, dialogue.id, "user", "问题2")

        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.delete(f"/dialogues/{dialogue.id}/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted_count"] == 3

        remaining = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue.id
        ).all()
        assert len(remaining) == 0

        session.refresh(dialogue)
        assert dialogue is not None
        session.close()

    def test_preserves_dialogue_record(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        dialogue = _create_test_dialogue(session, npc.id)

        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.delete(f"/dialogues/{dialogue.id}/messages")
        assert resp.status_code == 200

        saved = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue.id).first()
        assert saved is not None
        assert saved.id == dialogue.id
        session.close()

    def test_returns_404_for_nonexistent_dialogue(self):
        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.delete("/dialogues/99999/messages")
        assert resp.status_code == 404

    def test_clears_empty_dialogue(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        dialogue = _create_test_dialogue(session, npc.id)

        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.delete(f"/dialogues/{dialogue.id}/messages")
        assert resp.status_code == 200
        assert resp.json()["deleted_count"] == 0
        session.close()


class TestDialogueHistoryWithNotes:
    """GET /dialogues/{dialogue_id}/history 包含笔记"""

    def test_history_includes_note(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        dialogue = _create_test_dialogue(session, npc.id)
        _create_test_message(session, dialogue.id, "user", "问题")
        _create_test_message(session, dialogue.id, "assistant", "回答")

        note = DialogueNote(
            dialogue_id=dialogue.id,
            content="这是笔记内容",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(note)
        session.commit()

        from algomate.api.v1.dialogues import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get(f"/dialogues/{dialogue.id}/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["note"] is not None
        assert data["note"]["content"] == "这是笔记内容"
        assert len(data["messages"]) == 2
        session.close()
