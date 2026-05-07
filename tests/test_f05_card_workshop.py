import asyncio
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class TestComputeCardStatus:

    def test_pending_retake_when_pending_retake_true(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(80, True) == "pending_retake"

    def test_pending_retake_when_durability_zero(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(0, False) == "pending_retake"

    def test_endangered_when_durability_below_30(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(29, False) == "endangered"
        assert compute_card_status(1, False) == "endangered"

    def test_normal_when_durability_30_or_above(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(30, False) == "normal"
        assert compute_card_status(80, False) == "normal"
        assert compute_card_status(100, False) == "normal"

    def test_pending_retake_takes_priority_over_endangered(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(15, True) == "pending_retake"


class TestGetCardsAPI:

    def test_get_cards_empty(self, client, sample_npc):
        response = client.get("/api/v1/cards")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["cards"] == []
        assert data["data"]["endangered_count"] == 0
        assert data["data"]["pending_retake_count"] == 0

    def test_get_cards_with_one_card(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="二分查找", algorithm_type="Search")
        response = client.get("/api/v1/cards")
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["cards"]) == 1
        assert data["data"]["cards"][0]["name"] == "二分查找"
        assert data["data"]["cards"][0]["status"] == "normal"

    def test_get_cards_filter_by_algorithm_type(self, client, sample_npc, db_session):
        _create_card(db_session, sample_npc.id, name="二分查找", algorithm_type="Search")
        _create_card(db_session, sample_npc.id, name="快速排序", algorithm_type="Sorting")

        response = client.get("/api/v1/cards?algorithm_type=Search")
        data = response.json()
        assert len(data["data"]["cards"]) == 1
        assert data["data"]["cards"][0]["name"] == "二分查找"

    def test_get_cards_filter_by_status_endangered(self, client, sample_npc, db_session):
        _create_card(db_session, sample_npc.id, name="正常卡牌", durability=80)
        _create_card(db_session, sample_npc.id, name="濒危卡牌", durability=20)

        response = client.get("/api/v1/cards?status=endangered")
        data = response.json()
        assert len(data["data"]["cards"]) == 1
        assert data["data"]["cards"][0]["name"] == "濒危卡牌"

    def test_get_cards_filter_by_status_pending_retake(self, client, sample_npc, db_session):
        _create_card(db_session, sample_npc.id, name="正常卡牌", durability=80)
        _create_card(db_session, sample_npc.id, name="待重修卡牌", durability=0, pending_retake=True)

        response = client.get("/api/v1/cards?status=pending_retake")
        data = response.json()
        assert len(data["data"]["cards"]) == 1
        assert data["data"]["cards"][0]["name"] == "待重修卡牌"

    def test_get_cards_keyword_search(self, client, sample_npc, db_session):
        _create_card(db_session, sample_npc.id, name="二分查找", core_concept="二分搜索算法")
        _create_card(db_session, sample_npc.id, name="快速排序", core_concept="分治排序算法")

        response = client.get("/api/v1/cards?keyword=二分")
        data = response.json()
        assert len(data["data"]["cards"]) == 1
        assert data["data"]["cards"][0]["name"] == "二分查找"

    def test_get_cards_keyword_search_key_points(self, client, sample_npc, db_session):
        _create_card(db_session, sample_npc.id, name="二分查找", key_points='["折半查找","有序数组"]')
        _create_card(db_session, sample_npc.id, name="快速排序", key_points='["分治法"]')

        response = client.get("/api/v1/cards?keyword=有序数组")
        data = response.json()
        assert len(data["data"]["cards"]) == 1
        assert data["data"]["cards"][0]["name"] == "二分查找"

    def test_get_cards_endangered_count(self, client, sample_npc, db_session):
        _create_card(db_session, sample_npc.id, name="正常卡牌", durability=80)
        _create_card(db_session, sample_npc.id, name="濒危1", durability=20)
        _create_card(db_session, sample_npc.id, name="濒危2", durability=10)

        response = client.get("/api/v1/cards")
        data = response.json()
        assert data["data"]["endangered_count"] == 2

    def test_get_cards_pending_retake_count(self, client, sample_npc, db_session):
        _create_card(db_session, sample_npc.id, name="正常卡牌", durability=80)
        _create_card(db_session, sample_npc.id, name="待重修1", durability=0, pending_retake=True)
        _create_card(db_session, sample_npc.id, name="待重修2", durability=0, pending_retake=True)

        response = client.get("/api/v1/cards")
        data = response.json()
        assert data["data"]["pending_retake_count"] == 2


class TestGetCardDetailAPI:

    def test_get_card_detail_success(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="二分查找",
                            algorithm_type="Search", core_concept="折半搜索")

        response = client.get(f"/api/v1/cards/{card.id}")
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "二分查找"
        assert data["data"]["algorithm_type"] == "Search"
        assert data["data"]["core_concept"] == "折半搜索"

    def test_get_card_detail_has_all_dimensions(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="测试卡牌")

        response = client.get(f"/api/v1/cards/{card.id}")
        data = response.json()["data"]
        expected_fields = [
            "core_concept", "key_points", "code_template", "complexity_analysis",
            "use_cases", "common_variants", "typical_problems", "common_pitfalls",
            "comparison", "my_notes", "visual_links",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_get_card_detail_404(self, client, sample_npc):
        response = client.get("/api/v1/cards/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == 40404

    def test_get_card_detail_status_field(self, client, sample_npc, db_session):
        card_normal = _create_card(db_session, sample_npc.id, durability=80)
        card_endangered = _create_card(db_session, sample_npc.id, durability=20)
        card_retake = _create_card(db_session, sample_npc.id, durability=0, pending_retake=True)

        r1 = client.get(f"/api/v1/cards/{card_normal.id}")
        assert r1.json()["data"]["status"] == "normal"

        r2 = client.get(f"/api/v1/cards/{card_endangered.id}")
        assert r2.json()["data"]["status"] == "endangered"

        r3 = client.get(f"/api/v1/cards/{card_retake.id}")
        assert r3.json()["data"]["status"] == "pending_retake"


class TestUpdateCardAPI:

    def test_update_card_success(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="测试卡牌", core_concept="旧概念")

        response = client.put(f"/api/v1/cards/{card.id}", json={
            "core_concept": "新概念",
        })
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["updated"] is True

    def test_update_card_verify_persistence(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="测试卡牌", core_concept="旧概念")

        client.put(f"/api/v1/cards/{card.id}", json={"core_concept": "新概念"})

        response = client.get(f"/api/v1/cards/{card.id}")
        assert response.json()["data"]["core_concept"] == "新概念"

    def test_update_card_multiple_fields(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="测试卡牌",
                            core_concept="旧", key_points="旧要点")

        response = client.put(f"/api/v1/cards/{card.id}", json={
            "core_concept": "新概念",
            "key_points": "新要点",
            "my_notes": "个人笔记",
        })
        assert response.json()["code"] == 200

    def test_update_card_non_editable_field_ignored(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="测试卡牌", core_concept="旧概念")

        response = client.put(f"/api/v1/cards/{card.id}", json={
            "name": "新名称",
        })
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["code"] in (40001, 40002)

        verify = client.get(f"/api/v1/cards/{card.id}")
        assert verify.json()["data"]["name"] == "测试卡牌"

    def test_update_card_no_changes(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="测试卡牌", core_concept="概念A")

        response = client.put(f"/api/v1/cards/{card.id}", json={
            "core_concept": "概念A",
        })
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == 40002

    def test_update_card_empty_payload(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="测试卡牌")

        response = client.put(f"/api/v1/cards/{card.id}", json={})
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == 40002

    def test_update_card_not_found(self, client, sample_npc):
        response = client.put("/api/v1/cards/99999", json={"core_concept": "新概念"})
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == 40404

    def test_update_card_visual_links(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="测试卡牌")

        response = client.put(f"/api/v1/cards/{card.id}", json={
            "visual_links": '[{"title":"可视化","url":"https://example.com"}]',
        })
        assert response.json()["code"] == 200


class TestDeleteCardAPI:

    def test_delete_card_success(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="待删除卡牌")

        response = client.delete(f"/api/v1/cards/{card.id}")
        data = response.json()
        assert data["code"] == 200
        assert data["data"] is None

    def test_delete_card_removed_from_list(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="待删除卡牌")

        client.delete(f"/api/v1/cards/{card.id}")

        response = client.get("/api/v1/cards")
        cards = response.json()["data"]["cards"]
        assert all(c["id"] != card.id for c in cards)

    def test_delete_card_not_found(self, client, sample_npc):
        response = client.delete("/api/v1/cards/99999")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == 40404


class TestRetakeCardAPI:

    def test_retake_card_success(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="待重修卡牌",
                            durability=0, pending_retake=True)

        response = client.post(f"/api/v1/cards/{card.id}/retake")
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["durability_after"] == 80
        assert data["data"]["pending_retake"] is False
        assert data["data"]["status"] == "normal"

    def test_retake_card_resets_fields(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="待重修卡牌",
                            durability=0, pending_retake=True,
                            review_level=3, review_count=10)

        client.post(f"/api/v1/cards/{card.id}/retake")

        response = client.get(f"/api/v1/cards/{card.id}")
        card_data = response.json()["data"]
        assert card_data["durability"] == 80
        assert card_data["pending_retake"] is False
        assert card_data["review_level"] == 0
        assert card_data["review_count"] == 0
        assert card_data["last_reviewed"] is None

    def test_retake_card_not_pending_retake(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="正常卡牌",
                            durability=80, pending_retake=False)

        response = client.post(f"/api/v1/cards/{card.id}/retake")
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == 40001

    def test_retake_card_not_found(self, client, sample_npc):
        response = client.post("/api/v1/cards/99999/retake")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == 40404

    def test_retake_card_durability_before_recorded(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="待重修卡牌",
                            durability=0, pending_retake=True)

        response = client.post(f"/api/v1/cards/{card.id}/retake")
        data = response.json()["data"]
        assert data["durability_before"] == 0
        assert data["durability_after"] == 80


class TestDurabilityManagerTerminology:

    def test_update_durability_returns_needs_retake(self):
        from algomate.core.game.durability import DurabilityManager, DurabilityAction
        manager = DurabilityManager()
        new_dur, is_critical, needs_retake = manager.update_durability(
            2, DurabilityAction.REVIEW_FAIL, "normal"
        )
        assert new_dur == 0
        assert is_critical is True
        assert needs_retake is True

    def test_needs_retake_method(self):
        from algomate.core.game.durability import DurabilityManager
        manager = DurabilityManager()
        assert manager.needs_retake(0) is True
        assert manager.needs_retake(1) is False
        assert manager.needs_retake(100) is False

    def test_get_durability_status_uses_needs_retake(self):
        from algomate.core.game.durability import DurabilityManager
        manager = DurabilityManager()
        status = manager.get_durability_status(0)
        assert "needs_retake" in status
        assert status["needs_retake"] is True
        assert status["status"] == "待重修"

    def test_apply_daily_decay_uses_needs_retake(self):
        from algomate.core.game.durability import DurabilityManager, DurabilityAction
        manager = DurabilityManager()
        mock_card = MagicMock()
        mock_card.pending_retake = False
        mock_card.created_at = datetime.now() - timedelta(days=10)
        mock_card.durability = 2

        results = manager.apply_daily_decay_to_cards([mock_card])
        assert len(results) == 1
        assert "needs_retake" in results[0]

    def test_retake_card_convenience_function(self):
        from algomate.core.game.durability import retake_card
        assert retake_card(0) == 80


class TestCardResponseFormat:

    def test_card_response_has_snake_case_fields(self, client, sample_npc, db_session):
        card = _create_card(db_session, sample_npc.id, name="格式测试卡牌",
                            algorithm_type="Search", durability=75)

        response = client.get(f"/api/v1/cards/{card.id}")
        data = response.json()["data"]
        assert "algorithm_type" in data
        assert "pending_retake" in data
        assert "review_level" in data
        assert "review_count" in data
        assert "core_concept" in data
        assert "key_points" in data

    def test_card_list_response_format(self, client, sample_npc, db_session):
        _create_card(db_session, sample_npc.id, name="卡牌A")

        response = client.get("/api/v1/cards")
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data
        assert "cards" in data["data"]
        assert "endangered_count" in data["data"]
        assert "pending_retake_count" in data["data"]


def _create_card(session, npc_id, name="测试卡牌", algorithm_type="Search",
                 durability=80, pending_retake=False, core_concept="",
                 key_points="", review_level=0, review_count=0):
    from algomate.models.cards import Card
    card = Card(
        name=name,
        algorithm_type=algorithm_type,
        npc_id=npc_id,
        durability=durability,
        pending_retake=pending_retake,
        core_concept=core_concept,
        key_points=key_points,
        review_level=review_level,
        review_count=review_count,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card
