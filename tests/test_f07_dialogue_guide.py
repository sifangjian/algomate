import pytest
import json
from datetime import datetime
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
from algomate.models.bosses import Boss
from algomate.api.v1.dialogues import _active_sessions
from algomate.core.guide.service import GuideService
from algomate.core.guide.models import GuideData


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
        "domain": "动态规划",
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


def _create_test_boss(session, npc_id, weakness_type="dynamic_programming"):
    boss = Boss(
        name="测试Boss",
        difficulty="medium",
        weakness_type=weakness_type,
        npc_id=npc_id,
        description="测试Boss描述",
    )
    session.add(boss)
    session.commit()
    session.refresh(boss)
    return boss


class TestDialogueEndGuidesFieldFormat:
    """F07-T004: API-006 结束对话响应嵌入 guides 字段（GuideData 格式）"""

    def test_guides_field_has_available_actions_and_message(self):
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card={"id": 1, "name": "测试卡牌"},
        )
        data = guide.model_dump()
        assert "available_actions" in data
        assert "message" in data
        assert isinstance(data["available_actions"], list)
        assert isinstance(data["message"], str)

    def test_guides_with_card_contains_go_boss_and_go_workshop(self):
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card={"id": 1, "name": "数组与双指针"},
        )
        data = guide.model_dump()
        assert len(data["available_actions"]) == 2
        actions = [a["action"] for a in data["available_actions"]]
        assert "go_boss" in actions
        assert "go_workshop" in actions

    def test_guides_go_boss_action_structure(self):
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card={"id": 1, "name": "数组与双指针"},
        )
        go_boss = next(a for a in guide.available_actions if a.action == "go_boss")
        assert go_boss.action == "go_boss"
        assert go_boss.label == "去 Boss 战巩固"
        assert go_boss.target_path == "/boss"
        assert go_boss.params == {"card_id": 1}

    def test_guides_go_workshop_action_structure(self):
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card={"id": 1, "name": "数组与双指针"},
        )
        go_workshop = next(a for a in guide.available_actions if a.action == "go_workshop")
        assert go_workshop.action == "go_workshop"
        assert go_workshop.label == "去卡牌工坊完善"
        assert go_workshop.target_path == "/workshop"
        assert go_workshop.params == {"card_id": 1, "expand": True}

    def test_guides_message_contains_card_name(self):
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card={"id": 1, "name": "数组与双指针"},
        )
        assert "数组与双指针" in guide.message

    def test_guides_without_card_contains_only_go_workshop(self):
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card=None,
        )
        data = guide.model_dump()
        assert len(data["available_actions"]) == 1
        assert data["available_actions"][0]["action"] == "go_workshop"
        assert data["available_actions"][0]["label"] == "去卡牌工坊查看"

    def test_guides_without_card_message_indicates_failure(self):
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card=None,
        )
        assert "失败" in guide.message or "保存" in guide.message

    def test_guides_serialization_matches_api_contract(self):
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card={"id": 42, "name": "二分查找"},
        )
        data = guide.model_dump()
        assert data == {
            "available_actions": [
                {
                    "action": "go_boss",
                    "label": "去 Boss 战巩固",
                    "target_path": "/boss",
                    "params": {"card_id": 42},
                    "available": True,
                },
                {
                    "action": "go_workshop",
                    "label": "去卡牌工坊完善",
                    "target_path": "/workshop",
                    "params": {"card_id": 42, "expand": True},
                    "available": True,
                },
            ],
            "message": "恭喜获得卡牌「二分查找」！",
        }


class TestDialogueEndGuideDataBuild:
    """F07-T004: 验证 end_dialogue 端点应使用 GuideService 生成 guides"""

    def test_end_dialogue_response_should_use_guide_data_format_not_boolean_dict(self):
        """当前 end_dialogue 返回 {"go_boss": True, "go_workshop": True}，
        应改为 GuideData 格式 {available_actions: [...], message: "..."}"""
        card_dict = {"id": 1, "name": "背包问题"}
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card=card_dict,
        )
        result = guide.model_dump()

        assert "available_actions" in result
        assert "message" in result
        assert not isinstance(result.get("go_boss"), bool), "不应使用布尔字典格式"
        assert not isinstance(result.get("go_workshop"), bool), "不应使用布尔字典格式"

    def test_end_dialogue_card_failure_guide_data_format(self):
        """卡牌生成失败时，guides 也应是 GuideData 格式"""
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card=None,
        )
        result = guide.model_dump()

        assert "available_actions" in result
        assert "message" in result
        assert len(result["available_actions"]) == 1
        assert result["available_actions"][0]["action"] == "go_workshop"

    def test_end_dialogue_guide_includes_card_id_in_params(self):
        """引导动作的 params 应包含 card_id"""
        card_dict = {"id": 99, "name": "测试卡牌"}
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card=card_dict,
        )

        go_boss = next(a for a in guide.available_actions if a.action == "go_boss")
        assert go_boss.params["card_id"] == 99

        go_workshop = next(a for a in guide.available_actions if a.action == "go_workshop")
        assert go_workshop.params["card_id"] == 99
        assert go_workshop.params["expand"] is True


class TestDialogueEndGuideAvailability:
    """F07-T005: 对话后引导可用性判断"""

    def test_no_available_boss_filters_out_go_boss(self):
        """无 Boss 可挑战时，go_boss 动作 available=False"""
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card={"id": 1, "name": "测试卡牌"},
            has_available_boss=False,
        )
        go_boss = next(a for a in guide.available_actions if a.action == "go_boss")
        assert go_boss.available is False
        go_workshop = next(a for a in guide.available_actions if a.action == "go_workshop")
        assert go_workshop.available is True

    def test_has_available_boss_includes_go_boss(self):
        """有 Boss 可挑战时，go_boss 动作存在"""
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card={"id": 1, "name": "测试卡牌"},
            has_available_boss=True,
        )
        actions = [a.action for a in guide.available_actions]
        assert "go_boss" in actions
        assert "go_workshop" in actions

    def test_no_card_no_boss_only_workshop(self):
        """无卡牌且无 Boss 时，仅显示 go_workshop"""
        guide = GuideService().generate_guides(
            scene="after_dialogue",
            card=None,
            has_available_boss=False,
        )
        actions = [a.action for a in guide.available_actions]
        assert actions == ["go_workshop"]
        go_workshop = next(a for a in guide.available_actions if a.action == "go_workshop")
        assert go_workshop.available is True

    def test_has_available_boss_check_with_boss_in_db(self):
        """数据库中有 Boss 时，has_available_boss 应为 True"""
        db = Database.get_instance()
        session = db.get_session()
        npc = _create_test_npc(session)
        npc_id = npc.id
        _create_test_boss(session, npc_id)
        session.close()

        boss_count = session.query(Boss).count()
        assert boss_count > 0

    def test_no_available_boss_check_with_empty_db(self):
        """数据库中无 Boss 时，has_available_boss 应为 False"""
        db = Database.get_instance()
        session = db.get_session()
        boss_count = session.query(Boss).count()
        assert boss_count == 0
        session.close()
