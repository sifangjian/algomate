import pytest
from algomate.core.guide.service import GuideService, build_dialogue_end_guide, build_boss_result_guide, build_review_complete_guide
from algomate.core.guide.models import GuideData


class TestBuildDialogueEndGuide:
    def test_card_exists_returns_go_boss_and_go_workshop(self):
        card = {"id": 1, "name": "数组与双指针"}
        guide = build_dialogue_end_guide(card=card)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 2
        assert guide.available_actions[0].action == "go_boss"
        assert guide.available_actions[0].label == "去 Boss 战巩固"
        assert guide.available_actions[0].target_path == "/boss"
        assert guide.available_actions[0].params == {"card_id": 1}
        assert guide.available_actions[1].action == "go_workshop"
        assert guide.available_actions[1].label == "去卡牌工坊完善"
        assert guide.available_actions[1].target_path == "/workshop"
        assert guide.available_actions[1].params == {"card_id": 1, "expand": True}
        assert "数组与双指针" in guide.message

    def test_card_none_returns_only_go_workshop(self):
        guide = build_dialogue_end_guide(card=None)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 1
        assert guide.available_actions[0].action == "go_workshop"
        assert guide.available_actions[0].label == "去卡牌工坊查看"
        assert guide.available_actions[0].target_path == "/workshop"
        assert guide.available_actions[0].params is None
        assert "失败" in guide.message or "保存" in guide.message

    def test_card_with_different_id(self):
        card = {"id": 42, "name": "二分查找"}
        guide = build_dialogue_end_guide(card=card)
        assert guide.available_actions[0].params == {"card_id": 42}
        assert guide.available_actions[1].params == {"card_id": 42, "expand": True}
        assert "二分查找" in guide.message


class TestBuildBossResultGuide:
    def test_victory_returns_continue_challenge_and_go_review(self):
        guide = build_boss_result_guide(is_victory=True, card_id=1)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 2
        assert guide.available_actions[0].action == "continue_challenge"
        assert guide.available_actions[0].label == "继续挑战"
        assert guide.available_actions[0].target_path == "/boss"
        assert guide.available_actions[1].action == "go_review"
        assert guide.available_actions[1].label == "去修炼巩固"
        assert guide.available_actions[1].target_path == "/review"
        assert "成功" in guide.message

    def test_defeat_returns_go_review_and_go_dialogue(self):
        guide = build_boss_result_guide(is_victory=False, card_id=1, npc_id=2)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 2
        assert guide.available_actions[0].action == "go_review"
        assert guide.available_actions[0].label == "去修炼巩固"
        assert guide.available_actions[0].target_path == "/review"
        assert guide.available_actions[1].action == "go_dialogue"
        assert guide.available_actions[1].label == "去重新修习"
        assert guide.available_actions[1].target_path == "/"
        assert guide.available_actions[1].params == {"npc_id": 2}
        assert "失败" in guide.message or "巩固" in guide.message

    def test_defeat_without_npc_id_returns_only_go_review(self):
        guide = build_boss_result_guide(is_victory=False, card_id=1, npc_id=None)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 1
        assert guide.available_actions[0].action == "go_review"

    def test_defeat_with_zero_npc_id_returns_only_go_review(self):
        guide = build_boss_result_guide(is_victory=False, card_id=1, npc_id=0)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 1
        assert guide.available_actions[0].action == "go_review"


class TestBuildReviewCompleteGuide:
    def test_has_endangered_cards_returns_continue_review(self):
        guide = build_review_complete_guide(remaining_endangered=3)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 1
        assert guide.available_actions[0].action == "continue_review"
        assert guide.available_actions[0].label == "继续修炼"
        assert guide.available_actions[0].target_path == "/review"
        assert "3" in guide.message

    def test_no_endangered_cards_returns_go_boss(self):
        guide = build_review_complete_guide(remaining_endangered=0)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 1
        assert guide.available_actions[0].action == "go_boss"
        assert guide.available_actions[0].label == "去 Boss 战检验"
        assert guide.available_actions[0].target_path == "/boss"
        assert "Boss" in guide.message or "检验" in guide.message

    def test_one_endangered_card(self):
        guide = build_review_complete_guide(remaining_endangered=1)
        assert guide.available_actions[0].action == "continue_review"
        assert "1" in guide.message


class TestGuideService:
    def test_generate_guides_after_dialogue_with_card(self):
        service = GuideService()
        guide = service.generate_guides(scene="after_dialogue", card={"id": 1, "name": "测试卡牌"})
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 2
        assert guide.available_actions[0].action == "go_boss"

    def test_generate_guides_after_dialogue_without_card(self):
        service = GuideService()
        guide = service.generate_guides(scene="after_dialogue", card=None)
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 1
        assert guide.available_actions[0].action == "go_workshop"

    def test_generate_guides_after_boss_victory(self):
        service = GuideService()
        guide = service.generate_guides(scene="after_boss", is_victory=True, card_id=1)
        assert isinstance(guide, GuideData)
        assert guide.available_actions[0].action == "continue_challenge"

    def test_generate_guides_after_boss_defeat(self):
        service = GuideService()
        guide = service.generate_guides(scene="after_boss", is_victory=False, card_id=1, npc_id=2)
        assert isinstance(guide, GuideData)
        assert guide.available_actions[0].action == "go_review"
        assert guide.available_actions[1].action == "go_dialogue"

    def test_generate_guides_after_review_with_endangered(self):
        service = GuideService()
        guide = service.generate_guides(scene="after_review", remaining_endangered=2)
        assert isinstance(guide, GuideData)
        assert guide.available_actions[0].action == "continue_review"

    def test_generate_guides_after_review_no_endangered(self):
        service = GuideService()
        guide = service.generate_guides(scene="after_review", remaining_endangered=0)
        assert isinstance(guide, GuideData)
        assert guide.available_actions[0].action == "go_boss"

    def test_generate_guides_unknown_scene_returns_empty(self):
        service = GuideService()
        guide = service.generate_guides(scene="unknown_scene")
        assert isinstance(guide, GuideData)
        assert len(guide.available_actions) == 0

    def test_generate_guides_after_dialogue_no_boss_available(self):
        service = GuideService()
        guide = service.generate_guides(
            scene="after_dialogue",
            card={"id": 1, "name": "测试卡牌"},
            has_available_boss=False,
        )
        assert isinstance(guide, GuideData)
        go_boss_action = next((a for a in guide.available_actions if a.action == "go_boss"), None)
        assert go_boss_action is None

    def test_generate_guides_after_boss_all_defeated(self):
        service = GuideService()
        guide = service.generate_guides(
            scene="after_boss",
            is_victory=True,
            card_id=1,
            has_available_boss=False,
        )
        continue_action = next(
            (a for a in guide.available_actions if a.action == "continue_challenge"), None
        )
        assert continue_action is None

    def test_generate_guides_after_review_no_remaining_tasks(self):
        service = GuideService()
        guide = service.generate_guides(
            scene="after_review",
            remaining_endangered=0,
        )
        continue_action = next(
            (a for a in guide.available_actions if a.action == "continue_review"), None
        )
        assert continue_action is None
