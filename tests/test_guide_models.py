import pytest
from algomate.core.guide.models import GuideAction, GuideData


class TestGuideAction:
    def test_create_with_required_fields(self):
        action = GuideAction(action="go_boss", label="去 Boss 战巩固")
        assert action.action == "go_boss"
        assert action.label == "去 Boss 战巩固"
        assert action.target_path is None
        assert action.params is None

    def test_create_with_all_fields(self):
        action = GuideAction(
            action="go_boss",
            label="去 Boss 战巩固",
            target_path="/boss",
            params={"card_id": 1},
        )
        assert action.action == "go_boss"
        assert action.label == "去 Boss 战巩固"
        assert action.target_path == "/boss"
        assert action.params == {"card_id": 1}

    def test_create_with_target_path_and_params(self):
        action = GuideAction(
            action="go_workshop",
            label="去卡牌工坊完善",
            target_path="/workshop",
            params={"card_id": 1, "expand": True},
        )
        assert action.target_path == "/workshop"
        assert action.params == {"card_id": 1, "expand": True}

    def test_action_field_required(self):
        with pytest.raises(Exception):
            GuideAction(label="去 Boss 战巩固")

    def test_label_field_required(self):
        with pytest.raises(Exception):
            GuideAction(action="go_boss")

    def test_serialization(self):
        action = GuideAction(
            action="go_boss",
            label="去 Boss 战巩固",
            target_path="/boss",
            params={"card_id": 1},
        )
        data = action.model_dump()
        assert data == {
            "action": "go_boss",
            "label": "去 Boss 战巩固",
            "target_path": "/boss",
            "params": {"card_id": 1},
        }

    def test_serialization_with_none_optional_fields(self):
        action = GuideAction(action="go_review", label="去修炼巩固")
        data = action.model_dump()
        assert data == {
            "action": "go_review",
            "label": "去修炼巩固",
            "target_path": None,
            "params": None,
        }

    def test_from_dict(self):
        data = {
            "action": "go_boss",
            "label": "去 Boss 战巩固",
            "target_path": "/boss",
            "params": {"card_id": 1},
        }
        action = GuideAction(**data)
        assert action.action == "go_boss"
        assert action.params == {"card_id": 1}


class TestGuideData:
    def test_create_with_required_fields(self):
        actions = [
            GuideAction(action="go_boss", label="去 Boss 战巩固", target_path="/boss"),
        ]
        guide = GuideData(available_actions=actions, message="恭喜获得卡牌！")
        assert len(guide.available_actions) == 1
        assert guide.available_actions[0].action == "go_boss"
        assert guide.message == "恭喜获得卡牌！"

    def test_create_with_multiple_actions(self):
        actions = [
            GuideAction(
                action="go_boss",
                label="去 Boss 战巩固",
                target_path="/boss",
                params={"card_id": 1},
            ),
            GuideAction(
                action="go_workshop",
                label="去卡牌工坊完善",
                target_path="/workshop",
                params={"card_id": 1, "expand": True},
            ),
        ]
        guide = GuideData(available_actions=actions, message="恭喜获得卡牌！")
        assert len(guide.available_actions) == 2
        assert guide.available_actions[0].action == "go_boss"
        assert guide.available_actions[1].action == "go_workshop"

    def test_create_with_empty_actions(self):
        guide = GuideData(available_actions=[], message="暂无引导")
        assert len(guide.available_actions) == 0

    def test_serialization(self):
        actions = [
            GuideAction(
                action="go_boss",
                label="去 Boss 战巩固",
                target_path="/boss",
                params={"card_id": 1},
            ),
        ]
        guide = GuideData(available_actions=actions, message="恭喜获得卡牌！")
        data = guide.model_dump()
        assert data["message"] == "恭喜获得卡牌！"
        assert len(data["available_actions"]) == 1
        assert data["available_actions"][0]["action"] == "go_boss"
        assert data["available_actions"][0]["params"] == {"card_id": 1}

    def test_available_actions_required(self):
        with pytest.raises(Exception):
            GuideData(message="test")

    def test_message_required(self):
        with pytest.raises(Exception):
            GuideData(available_actions=[])
