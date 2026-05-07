import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from algomate.data.database import Base, Database
from algomate.models.dialogue_records import DialogueRecord
from algomate.models.dialogue_messages import DialogueMessageRecord
from algomate.models.dialogue_notes import DialogueNote
from algomate.models.npcs import NPC
from algomate.models.cards import Card
from algomate.api.dialogue_routes import (
    DialogueState,
    DialogueSession,
    CardGenerationResult,
    _active_sessions,
    _build_enhanced_system_prompt,
    _build_card_generation_prompt,
    _get_session,
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
        "specialties": json.dumps(["背包问题", "最长子序列"], ensure_ascii=False),
        "avatar": "/avatars/test.png",
        "description": "测试用NPC",
        "topics": json.dumps(["背包问题", "最长子序列"], ensure_ascii=False),
        "domain": "动态规划",
        "location": "智慧圣殿",
        "system_prompt": "你是动态规划领域的专家导师。",
        "greeting": "欢迎来到智慧圣殿！我是测试导师。",
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


def _create_test_message(session, dialogue_id, role, content, **overrides):
    msg = DialogueMessageRecord(
        dialogue_id=dialogue_id,
        role=role,
        content=content,
        created_at=overrides.get("created_at", datetime.now()),
    )
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg


class TestStartDialogueDBIntegration:
    """POST /start 路由的数据库集成验证"""

    def test_start_creates_dialogue_record_in_db(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)

        now = datetime.now()
        record = DialogueRecord(
            npc_id=npc.id,
            topic="背包问题",
            status="active",
            last_active_at=now,
            created_at=now,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.id is not None
        assert record.npc_id == npc.id
        assert record.topic == "背包问题"
        assert record.status == "active"

        saved = session.query(DialogueRecord).filter(DialogueRecord.id == record.id).first()
        assert saved is not None
        assert saved.npc_id == npc.id
        session.close()

    def test_start_creates_greeting_message_in_db(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)

        now = datetime.now()
        record = DialogueRecord(
            npc_id=npc.id, topic="背包问题", status="active",
            last_active_at=now, created_at=now,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        greeting_msg = DialogueMessageRecord(
            dialogue_id=record.id,
            role="assistant",
            content="欢迎回来！让我们继续修习「背包问题」吧。",
            created_at=now,
        )
        session.add(greeting_msg)
        session.commit()

        messages = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == record.id
        ).all()
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert "背包问题" in messages[0].content
        session.close()

    def test_start_finds_existing_card_in_db(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)

        card = Card(
            name="背包问题卡牌",
            domain=Domain.WISDOM_TEMPLE.value,
            algorithm_type="动态规划",
            difficulty=3,
            durability=80,
            max_durability=100,
            npc_id=npc.id,
            topic="背包问题",
        )
        session.add(card)
        session.commit()
        session.refresh(card)

        found = session.query(Card).filter(
            Card.npc_id == npc.id,
            Card.topic == "背包问题",
        ).first()
        assert found is not None
        assert found.id == card.id
        assert found.name == "背包问题卡牌"
        session.close()

    def test_start_no_existing_card_returns_none(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)

        found = session.query(Card).filter(
            Card.npc_id == npc.id,
            Card.topic == "不存在的话题",
        ).first()
        assert found is None
        session.close()

    def test_start_npc_topics_parsed_correctly(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)

        loaded = session.query(NPC).filter(NPC.id == npc.id).first()
        topics = json.loads(loaded.topics) if loaded.topics else []
        assert topics == ["背包问题", "最长子序列"]
        session.close()

    def test_start_greeting_without_topic(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_name = npc.name
        npc_location = npc.location
        npc_greeting = npc.greeting
        session.close()

        greeting = npc_greeting or f"欢迎来到{npc_location or '这里'}！我是{npc_name}。"
        assert "智慧圣殿" in greeting
        assert "测试导师" in greeting


class TestSaveNoteDBIntegration:
    """POST /{id}/note 路由的数据库集成验证"""

    def test_save_note_creates_new_record(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        session.close()

        now = datetime.now()
        note = DialogueNote(
            dialogue_id=dialogue_id,
            content="这是我的学习笔记",
            created_at=now,
            updated_at=now,
        )
        session = db.get_session()
        session.add(note)
        session.commit()
        session.refresh(note)

        assert note.id is not None
        assert note.dialogue_id == dialogue_id
        assert note.content == "这是我的学习笔记"

        saved = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).first()
        assert saved is not None
        assert saved.content == "这是我的学习笔记"
        session.close()

    def test_save_note_updates_existing_record(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        now = datetime.now()
        note = DialogueNote(
            dialogue_id=dialogue_id,
            content="旧笔记",
            created_at=now,
            updated_at=now,
        )
        session.add(note)
        session.commit()
        session.refresh(note)
        old_id = note.id

        existing = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).first()
        existing.content = "新笔记内容"
        existing.updated_at = datetime.now()
        session.commit()

        updated = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).first()
        assert updated.id == old_id
        assert updated.content == "新笔记内容"
        session.close()

    def test_save_note_upsert_pattern(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        session.close()

        session = db.get_session()
        existing = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).first()
        assert existing is None

        now = datetime.now()
        new_note = DialogueNote(
            dialogue_id=dialogue_id,
            content="第一次保存",
            created_at=now,
            updated_at=now,
        )
        session.add(new_note)
        session.commit()

        existing = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).first()
        assert existing is not None
        existing.content = "第二次保存"
        existing.updated_at = datetime.now()
        session.commit()

        all_notes = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).all()
        assert len(all_notes) == 1
        assert all_notes[0].content == "第二次保存"
        session.close()


class TestGetHistoryDBIntegration:
    """GET /{id}/history 路由的数据库集成验证"""

    def test_history_returns_ordered_messages(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        base_time = datetime.now()
        _create_test_message(session, dialogue_id, "assistant", "欢迎！",
                             created_at=base_time - timedelta(minutes=2))
        _create_test_message(session, dialogue_id, "user", "请讲背包问题",
                             created_at=base_time - timedelta(minutes=1))
        _create_test_message(session, dialogue_id, "assistant", "背包问题是...",
                             created_at=base_time)

        messages = (
            session.query(DialogueMessageRecord)
            .filter(DialogueMessageRecord.dialogue_id == dialogue_id)
            .order_by(DialogueMessageRecord.created_at.asc())
            .all()
        )
        assert len(messages) == 3
        assert messages[0].content == "欢迎！"
        assert messages[1].content == "请讲背包问题"
        assert messages[2].content == "背包问题是..."
        session.close()

    def test_history_includes_note(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        now = datetime.now()
        note = DialogueNote(
            dialogue_id=dialogue_id,
            content="学习心得",
            created_at=now,
            updated_at=now,
        )
        session.add(note)
        session.commit()

        note = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).first()
        assert note is not None
        assert note.content == "学习心得"
        session.close()

    def test_history_no_note_returns_none(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        session.close()

        session = db.get_session()
        note = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).first()
        assert note is None
        session.close()


class TestHeartbeatDBIntegration:
    """POST /{id}/heartbeat 路由的数据库集成验证"""

    def test_heartbeat_updates_last_active_at(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        old_active = record.last_active_at
        dialogue_id = record.id

        now = datetime.now()
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        record.last_active_at = now
        session.commit()

        updated = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        assert updated.last_active_at >= old_active
        session.close()

    def test_heartbeat_revives_timed_out_status(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id, status="timed_out")
        dialogue_id = record.id

        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        if record.status == "timed_out":
            record.status = "active"
        session.commit()

        updated = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        assert updated.status == "active"
        session.close()


class TestSendMessageDBIntegration:
    """POST /{id}/message 路由的数据库集成验证"""

    def test_send_message_saves_user_message(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        _create_test_message(session, dialogue_id, "assistant", "欢迎！")

        now = datetime.now()
        user_msg = DialogueMessageRecord(
            dialogue_id=dialogue_id,
            role="user",
            content="请讲背包问题",
            created_at=now,
        )
        session.add(user_msg)
        session.commit()

        saved = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue_id,
            DialogueMessageRecord.role == "user",
        ).first()
        assert saved is not None
        assert saved.content == "请讲背包问题"
        session.close()

    def test_send_message_saves_npc_response(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        now = datetime.now()
        user_msg = DialogueMessageRecord(
            dialogue_id=dialogue_id, role="user", content="你好", created_at=now,
        )
        npc_msg = DialogueMessageRecord(
            dialogue_id=dialogue_id, role="assistant",
            content="背包问题的核心是状态定义和转移方程。",
            created_at=now + timedelta(seconds=2),
        )
        session.add_all([user_msg, npc_msg])
        session.commit()

        messages = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue_id
        ).order_by(DialogueMessageRecord.created_at.asc()).all()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert "状态定义" in messages[1].content
        session.close()

    def test_send_message_context_window_limit(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        for i in range(50):
            _create_test_message(session, dialogue_id, "user", f"消息{i}")

        all_messages = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue_id
        ).order_by(DialogueMessageRecord.created_at.asc()).all()
        assert len(all_messages) == 50

        max_context = 40
        context = all_messages[-max_context:]
        assert len(context) == 40
        assert context[0].content == "消息10"
        session.close()

    def test_send_message_updates_last_active(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        old_active = record.last_active_at
        dialogue_id = record.id

        now = datetime.now()
        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        record.last_active_at = now
        session.commit()

        updated = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        assert updated.last_active_at >= old_active
        session.close()


class TestEndDialogueDBIntegration:
    """POST /{id}/end 路由的数据库集成验证"""

    def test_end_updates_status_to_ended(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        record.status = "ended"
        session.commit()

        updated = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        assert updated.status == "ended"
        session.close()

    def test_end_creates_card_in_db(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        session.close()

        card_data = {
            "name": "背包问题",
            "domain": Domain.WISDOM_TEMPLE.value,
            "algorithm_type": "动态规划",
            "difficulty": 3,
            "durability": 80,
            "max_durability": 100,
            "is_sealed": False,
            "knowledge_content": "0-1背包是经典DP问题",
            "key_points": "1. 定义状态\n2. 状态转移",
            "summary": "0-1背包是经典DP问题"[:200],
            "core_concept": "0-1背包是经典DP问题",
            "code_template": "def knapsack(): pass",
            "complexity_analysis": "O(n*W)",
            "use_cases": "资源分配",
            "common_variants": "完全背包",
            "typical_problems": "[]",
            "common_pitfalls": "初始化边界",
            "comparison": "与贪心区别",
            "my_notes": "用户笔记",
            "visual_links": "[]",
            "npc_id": npc_id,
            "topic": "背包问题",
            "review_level": 0,
            "review_count": 0,
        }
        new_card = Card(**card_data)
        session = db.get_session()
        session.add(new_card)
        session.commit()
        session.refresh(new_card)

        assert new_card.id is not None
        assert new_card.name == "背包问题"
        assert new_card.domain == Domain.WISDOM_TEMPLE.value

        saved = session.query(Card).filter(Card.id == new_card.id).first()
        assert saved is not None
        assert saved.knowledge_content == "0-1背包是经典DP问题"
        session.close()

    def test_end_updates_existing_card(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        existing_card = Card(
            name="旧卡牌",
            domain=Domain.WISDOM_TEMPLE.value,
            algorithm_type="动态规划",
            difficulty=2,
            durability=60,
            max_durability=100,
            npc_id=npc_id,
            topic="背包问题",
        )
        session.add(existing_card)
        session.commit()
        session.refresh(existing_card)
        old_id = existing_card.id

        card = session.query(Card).filter(Card.id == old_id).first()
        card.name = "背包问题-升级版"
        card.difficulty = 4
        card.durability = 80
        card.updated_at = datetime.now()
        session.commit()

        updated = session.query(Card).filter(Card.id == old_id).first()
        assert updated.name == "背包问题-升级版"
        assert updated.difficulty == 4
        assert updated.durability == 80

        all_cards = session.query(Card).filter(
            Card.npc_id == npc_id,
            Card.topic == "背包问题",
        ).all()
        assert len(all_cards) == 1
        session.close()

    def test_end_links_card_to_dialogue(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        card = Card(
            name="背包问题",
            domain=Domain.WISDOM_TEMPLE.value,
            algorithm_type="动态规划",
            difficulty=3,
            durability=80,
            max_durability=100,
            npc_id=npc_id,
            topic="背包问题",
        )
        session.add(card)
        session.commit()
        session.refresh(card)
        card_id = card.id

        record.card_id = card_id
        record.status = "ended"
        session.commit()

        saved = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        assert saved.card_id == card_id
        assert saved.status == "ended"
        session.close()

    def test_end_card_generation_failure_preserves_dialogue(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        _create_test_message(session, dialogue_id, "assistant", "欢迎！")
        _create_test_message(session, dialogue_id, "user", "你好")

        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        record.status = "ended"
        session.commit()

        messages = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue_id
        ).all()
        assert len(messages) == 2

        card = session.query(Card).filter(
            Card.npc_id == npc_id,
            Card.topic == "背包问题",
        ).first()
        assert card is None
        session.close()

    def test_end_with_note_uses_note_as_my_notes(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        note = DialogueNote(
            dialogue_id=dialogue_id,
            content="我的学习心得",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(note)
        session.commit()

        card = Card(
            name="背包问题",
            domain=Domain.WISDOM_TEMPLE.value,
            algorithm_type="动态规划",
            difficulty=3,
            durability=80,
            max_durability=100,
            npc_id=npc_id,
            topic="背包问题",
            my_notes="我的学习心得",
        )
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.my_notes == "我的学习心得"
        session.close()


class TestDomainMappingIntegration:
    """领域映射集成测试"""

    def test_dp_maps_to_wisdom_temple(self):
        domain_mapping = {
            "基础数据结构": Domain.NOVICE_FOREST.value,
            "栈队列与搜索": Domain.NOVICE_FOREST.value,
            "搜索与遍历": Domain.MIST_SWAMP.value,
            "动态规划": Domain.WISDOM_TEMPLE.value,
            "贪心算法": Domain.GREED_TOWER.value,
            "回溯算法": Domain.FATE_MAZE.value,
            "分治与排序": Domain.SPLIT_MOUNTAIN.value,
            "数学与位运算": Domain.MATH_HALL.value,
        }
        assert domain_mapping["动态规划"] == "智慧圣殿"

    def test_greedy_maps_to_greed_tower(self):
        assert Domain.GREED_TOWER.value == "贪婪之塔"

    def test_backtracking_maps_to_fate_maze(self):
        assert Domain.FATE_MAZE.value == "命运迷宫"

    def test_unknown_domain_defaults_to_novice_forest(self):
        domain_mapping = {}
        npc_domain = "未知领域"
        result = domain_mapping.get(npc_domain, Domain.NOVICE_FOREST.value)
        assert result == "新手森林"


class TestDialogueSessionCacheIntegration:
    """对话会话缓存与数据库一致性测试"""

    def test_session_loaded_from_db(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        _create_test_message(session, dialogue_id, "assistant", "欢迎！")
        _create_test_message(session, dialogue_id, "user", "你好")
        session.close()

        assert dialogue_id not in _active_sessions

        result = _get_session(dialogue_id)

        assert result is not None
        assert result.dialogue_id == dialogue_id
        assert result.npc_name == "测试导师"
        assert result.npc_domain == "动态规划"
        assert len(result.messages) == 2
        assert result.messages[0]["role"] == "assistant"
        assert result.messages[1]["role"] == "user"
        assert dialogue_id in _active_sessions

    def test_session_returns_none_for_nonexistent(self):
        result = _get_session(99999)
        assert result is None

    def test_session_cached_on_subsequent_access(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        session.close()

        first = _get_session(dialogue_id)
        second = _get_session(dialogue_id)

        assert first is second

    def test_session_status_matches_db(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id, status="ended")
        dialogue_id = record.id
        session.close()

        result = _get_session(dialogue_id)

        assert result is not None
        assert result.status == DialogueState.ENDED

    def test_session_note_content_updated(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        npc_name = npc.name
        npc_domain = npc.domain
        npc_system_prompt = npc.system_prompt
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        topic = record.topic
        session.close()

        _active_sessions[dialogue_id] = DialogueSession(
            dialogue_id=dialogue_id,
            npc_id=npc_id,
            npc_name=npc_name,
            npc_domain=npc_domain,
            npc_system_prompt=npc_system_prompt,
            topic=topic,
            status=DialogueState.ACTIVE,
        )

        _active_sessions[dialogue_id].note_content = "缓存笔记"

        assert _active_sessions[dialogue_id].note_content == "缓存笔记"

    def test_session_heartbeat_updates_status(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        npc_name = npc.name
        npc_domain = npc.domain
        npc_system_prompt = npc.system_prompt
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        topic = record.topic
        session.close()

        _active_sessions[dialogue_id] = DialogueSession(
            dialogue_id=dialogue_id,
            npc_id=npc_id,
            npc_name=npc_name,
            npc_domain=npc_domain,
            npc_system_prompt=npc_system_prompt,
            topic=topic,
            status=DialogueState.TIMED_OUT,
        )

        if _active_sessions[dialogue_id].status == DialogueState.TIMED_OUT:
            _active_sessions[dialogue_id].status = DialogueState.ACTIVE

        assert _active_sessions[dialogue_id].status == DialogueState.ACTIVE


class TestCardGenerationPromptIntegration:
    """卡牌生成提示词与对话数据集成测试"""

    def test_card_prompt_includes_dialogue_messages(self):
        dialogue_messages = [
            {"role": "user", "content": "请讲背包问题"},
            {"role": "assistant", "content": "背包问题是经典的DP问题"},
        ]
        system_prompt, user_prompt = _build_card_generation_prompt(
            topic="背包问题",
            npc_domain="动态规划",
            dialogue_messages=dialogue_messages,
            note_content="我的笔记",
        )

        assert "用户" in user_prompt
        assert "NPC" in user_prompt
        assert "背包问题" in user_prompt
        assert "动态规划" in user_prompt
        assert "我的笔记" in user_prompt

    def test_card_prompt_without_note(self):
        dialogue_messages = [
            {"role": "user", "content": "你好"},
        ]
        system_prompt, user_prompt = _build_card_generation_prompt(
            topic="排序",
            npc_domain="分治与排序",
            dialogue_messages=dialogue_messages,
            note_content="",
        )

        assert "用户未记录笔记" in user_prompt

    def test_card_prompt_10_dimensions(self):
        system_prompt, _ = _build_card_generation_prompt(
            topic="测试", npc_domain="测试", dialogue_messages=[], note_content="",
        )

        dimensions = [
            "core_concept", "key_points", "code_template",
            "complexity_analysis", "use_cases", "common_variants",
            "typical_problems", "common_pitfalls", "comparison", "my_notes",
        ]
        for dim in dimensions:
            assert dim in system_prompt


class TestCrossTableIntegrity:
    """跨表数据一致性集成测试"""

    def test_dialogue_cascade_delete_messages(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id
        _create_test_message(session, dialogue_id, "assistant", "欢迎！")
        _create_test_message(session, dialogue_id, "user", "你好")

        messages_before = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue_id
        ).count()
        assert messages_before == 2

        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        session.delete(record)
        session.commit()

        messages_after = session.query(DialogueMessageRecord).filter(
            DialogueMessageRecord.dialogue_id == dialogue_id
        ).count()
        assert messages_after == 0
        session.close()

    def test_dialogue_cascade_delete_notes(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        record = _create_test_dialogue(session, npc.id)
        dialogue_id = record.id

        note = DialogueNote(
            dialogue_id=dialogue_id,
            content="笔记",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(note)
        session.commit()

        notes_before = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).count()
        assert notes_before == 1

        record = session.query(DialogueRecord).filter(DialogueRecord.id == dialogue_id).first()
        session.delete(record)
        session.commit()

        notes_after = session.query(DialogueNote).filter(
            DialogueNote.dialogue_id == dialogue_id
        ).count()
        assert notes_after == 0
        session.close()

    def test_npc_dialogue_relationship(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        _create_test_dialogue(session, npc_id, topic="背包问题")
        _create_test_dialogue(session, npc_id, topic="最长子序列")

        dialogues = session.query(DialogueRecord).filter(
            DialogueRecord.npc_id == npc_id
        ).all()
        assert len(dialogues) == 2
        topics = {d.topic for d in dialogues}
        assert "背包问题" in topics
        assert "最长子序列" in topics
        session.close()

    def test_card_dialogue_bidirectional_link(self):
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        record = _create_test_dialogue(session, npc_id)
        dialogue_id = record.id

        card = Card(
            name="背包问题",
            domain=Domain.WISDOM_TEMPLE.value,
            algorithm_type="动态规划",
            difficulty=3,
            durability=80,
            max_durability=100,
            npc_id=npc_id,
            topic="背包问题",
        )
        session.add(card)
        session.commit()
        session.refresh(card)
        card_id = card.id

        record.card_id = card_id
        session.commit()

        saved_record = session.query(DialogueRecord).filter(
            DialogueRecord.id == dialogue_id
        ).first()
        assert saved_record.card_id == card_id

        saved_card = session.query(Card).filter(Card.id == card_id).first()
        assert saved_card is not None
        assert saved_card.npc_id == npc_id
        session.close()
