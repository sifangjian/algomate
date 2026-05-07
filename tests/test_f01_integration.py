"""
F01 Card System Integration Tests

Integration tests covering the full Card API lifecycle:
- Card CRUD lifecycle
- Status computation across API boundaries
- Retake workflow
- Update change detection
- Search and filter
- Domain statistics
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.test_f01_card_system import _setup_test_db, _seed_card, _run_async


class TestCardLifecycleIntegration:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_db, self.npc_id = _setup_test_db()
        self._patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=self.test_db,
        )
        self._patcher.start()

    def teardown_method(self):
        self._patcher.stop()

    def test_create_read_update_delete_lifecycle(self):
        # Verify complete CRUD lifecycle: create -> read -> update -> delete
        from algomate.models.cards import create_card, get_card, update_card, delete_card, CardCreate, CardUpdate
        from fastapi import HTTPException

        # Arrange: create a new card
        payload = CardCreate(name="Lifecycle Card", npc_id=self.npc_id)
        created = _run_async(create_card(payload))

        # Assert: creation returns correct data
        assert created.name == "Lifecycle Card"
        assert created.id is not None
        card_id = created.id

        # Act: read the card back
        read_result = _run_async(get_card(card_id))

        # Assert: read matches creation
        assert read_result.name == "Lifecycle Card"
        assert read_result.id == card_id

        # Act: update the card
        update_payload = CardUpdate(name="Updated Lifecycle Card")
        updated = _run_async(update_card(card_id, update_payload))

        # Assert: update applied
        assert updated.name == "Updated Lifecycle Card"

        # Act: delete the card
        _run_async(delete_card(card_id))

        # Assert: card no longer exists
        with pytest.raises(HTTPException) as exc_info:
            _run_async(get_card(card_id))
        assert exc_info.value.status_code == 404

    def test_create_card_with_all_dimensions(self):
        # Verify creating a card with all 10 content dimensions persists them
        from algomate.models.cards import create_card, get_card, CardCreate

        payload = CardCreate(
            name="Full Dimension Card",
            npc_id=self.npc_id,
            core_concept="core concept text",
            code_template="def solve(): pass",
            complexity_analysis="O(n log n)",
            use_cases="sorting, searching",
            common_variants="merge sort variant",
            typical_problems="LC215",
            common_pitfalls="off-by-one",
            comparison="vs quicksort",
            my_notes="remember base case",
        )
        created = _run_async(create_card(payload))

        # Assert: all dimensions persisted
        assert created.coreConcept == "core concept text"
        assert created.codeTemplate == "def solve(): pass"
        assert created.complexityAnalysis == "O(n log n)"
        assert created.useCases == "sorting, searching"
        assert created.commonVariants == "merge sort variant"
        assert created.typicalProblems == "LC215"
        assert created.commonPitfalls == "off-by-one"
        assert created.comparison == "vs quicksort"
        assert created.myNotes == "remember base case"

        # Verify via read
        read_result = _run_async(get_card(created.id))
        assert read_result.coreConcept == "core concept text"
        assert read_result.codeTemplate == "def solve(): pass"

    def test_create_card_default_durability_80(self):
        # Verify new card has default durability of 80
        from algomate.models.cards import create_card, CardCreate

        payload = CardCreate(name="Default Durability Card", npc_id=self.npc_id)
        created = _run_async(create_card(payload))

        assert created.durability == 80
        assert created.status == "normal"

    def test_create_card_durability_zero_is_sealed(self):
        # Verify creating a card with durability=0 sets is_sealed=True
        from algomate.models.cards import create_card, CardCreate

        payload = CardCreate(name="Zero Durability Card", durability=0, npc_id=self.npc_id)
        created = _run_async(create_card(payload))

        assert created.is_sealed is True
        assert created.durability == 0
        assert created.status == "pending_retake"


class TestCardStatusIntegration:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_db, self.npc_id = _setup_test_db()
        self._patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=self.test_db,
        )
        self._patcher.start()

    def teardown_method(self):
        self._patcher.stop()

    def test_normal_card_status(self):
        # Verify durability=80 produces status="normal"
        from algomate.models.cards import get_card

        card_id = _seed_card(self.test_db, self.npc_id, durability=80)
        result = _run_async(get_card(card_id))

        assert result.status == "normal"

    def test_endangered_card_status(self):
        # Verify durability=15 produces status="endangered"
        from algomate.models.cards import get_card

        card_id = _seed_card(self.test_db, self.npc_id, durability=15)
        result = _run_async(get_card(card_id))

        assert result.status == "endangered"

    def test_pending_retake_card_status(self):
        # Verify pending_retake=True produces status="pending_retake"
        from algomate.models.cards import get_card

        card_id = _seed_card(self.test_db, self.npc_id, durability=0, pending_retake=True)
        result = _run_async(get_card(card_id))

        assert result.status == "pending_retake"

    def test_card_list_endangered_count(self):
        # Verify endangered_count and pending_retake_count reflect only matching cards
        from algomate.models.cards import get_cards

        _seed_card(self.test_db, self.npc_id, name="Endangered1", durability=15)
        _seed_card(self.test_db, self.npc_id, name="Endangered2", durability=20)
        _seed_card(self.test_db, self.npc_id, name="Normal1", durability=80)
        _seed_card(self.test_db, self.npc_id, name="Pending1", durability=0, pending_retake=True)

        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword=None, sort=None,
            order="asc", available=None,
        ))

        assert result["endangered_count"] == 2
        assert result["pending_retake_count"] == 1

    def test_filter_by_status_endangered(self):
        # Verify status="endangered" filter returns only endangered cards
        from algomate.models.cards import get_cards

        _seed_card(self.test_db, self.npc_id, name="Endangered", durability=15)
        _seed_card(self.test_db, self.npc_id, name="Normal", durability=80)

        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status="endangered", keyword=None, sort=None,
            order="asc", available=None,
        ))

        assert len(result["cards"]) == 1
        assert result["cards"][0].status == "endangered"
        assert result["cards"][0].name == "Endangered"

    def test_filter_by_status_pending_retake(self):
        # Verify status="pending_retake" filter returns only pending_retake cards
        from algomate.models.cards import get_cards

        _seed_card(self.test_db, self.npc_id, name="Pending", durability=0, pending_retake=True)
        _seed_card(self.test_db, self.npc_id, name="Normal", durability=80)

        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status="pending_retake", keyword=None, sort=None,
            order="asc", available=None,
        ))

        assert len(result["cards"]) == 1
        assert result["cards"][0].status == "pending_retake"
        assert result["cards"][0].name == "Pending"


class TestCardRetakeIntegration:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_db, self.npc_id = _setup_test_db()
        self._patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=self.test_db,
        )
        self._patcher.start()

    def teardown_method(self):
        self._patcher.stop()

    def test_retake_pending_retake_card(self):
        # Verify retaking a pending_retake card resets durability=30 and clears pending_retake
        from algomate.models.cards import retake_card

        card_id = _seed_card(
            self.test_db, self.npc_id,
            durability=0, pending_retake=True,
        )
        result = _run_async(retake_card(card_id))

        assert result.pendingRetake is False
        assert result.durability == 30
        assert result.status == "normal"

    def test_retake_normal_card_fails(self):
        # Verify retaking a normal card raises error 40003
        from algomate.models.cards import retake_card
        from fastapi import HTTPException

        card_id = _seed_card(self.test_db, self.npc_id, durability=80, pending_retake=False)

        with pytest.raises(HTTPException) as exc_info:
            _run_async(retake_card(card_id))

        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        if isinstance(detail, dict):
            assert detail.get("code") == 40003
        else:
            assert "40003" in str(detail)

    def test_retake_nonexistent_card(self):
        # Verify retaking a non-existent card returns 404
        from algomate.models.cards import retake_card
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _run_async(retake_card(99999))

        assert exc_info.value.status_code == 404

    def test_retake_then_update(self):
        # Verify retaking a card then updating its dimensions works correctly
        from algomate.models.cards import retake_card, update_card, get_card, CardUpdate

        card_id = _seed_card(
            self.test_db, self.npc_id,
            durability=0, pending_retake=True,
            core_concept="old concept",
        )

        # Act: retake the card
        retaken = _run_async(retake_card(card_id))
        assert retaken.durability == 30
        assert retaken.pendingRetake is False

        # Act: update dimensions after retake
        update_payload = CardUpdate(core_concept="new concept after retake")
        updated = _run_async(update_card(card_id, update_payload))

        # Assert: update applied after retake
        assert updated.coreConcept == "new concept after retake"
        assert updated.durability == 30
        assert updated.pendingRetake is False

        # Verify persistence via read
        read_result = _run_async(get_card(card_id))
        assert read_result.coreConcept == "new concept after retake"
        assert read_result.durability == 30


class TestCardUpdateIntegration:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_db, self.npc_id = _setup_test_db()
        self._patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=self.test_db,
        )
        self._patcher.start()

    def teardown_method(self):
        self._patcher.stop()

    def test_update_single_dimension(self):
        # Verify updating only core_concept leaves other dimensions unchanged
        from algomate.models.cards import update_card, get_card, CardUpdate

        card_id = _seed_card(
            self.test_db, self.npc_id,
            name="Single Dim Card",
            core_concept="original concept",
            code_template="original template",
        )

        update_payload = CardUpdate(core_concept="updated concept")
        result = _run_async(update_card(card_id, update_payload))

        assert result.coreConcept == "updated concept"
        assert result.codeTemplate == "original template"
        assert result.name == "Single Dim Card"

        # Verify persistence
        read_result = _run_async(get_card(card_id))
        assert read_result.coreConcept == "updated concept"
        assert read_result.codeTemplate == "original template"

    def test_update_no_changes_error(self):
        # Verify updating with same values raises error 40002
        from algomate.models.cards import update_card, CardUpdate
        from fastapi import HTTPException

        card_id = _seed_card(
            self.test_db, self.npc_id,
            name="Same Name", core_concept="same concept",
        )

        payload = CardUpdate(name="Same Name", core_concept="same concept")
        with pytest.raises(HTTPException) as exc_info:
            _run_async(update_card(card_id, payload))

        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        if isinstance(detail, dict):
            assert detail.get("code") == 40002
        else:
            assert "40002" in str(detail)

    def test_update_multiple_fields(self):
        # Verify updating name + multiple dimensions simultaneously
        from algomate.models.cards import update_card, get_card, CardUpdate

        card_id = _seed_card(
            self.test_db, self.npc_id,
            name="Old Name",
            core_concept="old concept",
            code_template="old template",
            complexity_analysis="old analysis",
        )

        update_payload = CardUpdate(
            name="New Name",
            core_concept="new concept",
            complexity_analysis="new analysis",
        )
        result = _run_async(update_card(card_id, update_payload))

        assert result.name == "New Name"
        assert result.coreConcept == "new concept"
        assert result.complexityAnalysis == "new analysis"
        assert result.codeTemplate == "old template"

        # Verify persistence
        read_result = _run_async(get_card(card_id))
        assert read_result.name == "New Name"
        assert read_result.coreConcept == "new concept"

    def test_update_nonexistent_card(self):
        # Verify updating a non-existent card returns 404
        from algomate.models.cards import update_card, CardUpdate
        from fastapi import HTTPException

        payload = CardUpdate(name="Ghost Card")
        with pytest.raises(HTTPException) as exc_info:
            _run_async(update_card(99999, payload))

        assert exc_info.value.status_code == 404


class TestCardSearchIntegration:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_db, self.npc_id = _setup_test_db()
        self._patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=self.test_db,
        )
        self._patcher.start()

    def teardown_method(self):
        self._patcher.stop()

    def test_search_by_name(self):
        # Verify keyword filter matches card name
        from algomate.models.cards import get_cards

        _seed_card(self.test_db, self.npc_id, name="Binary Search Algorithm")
        _seed_card(self.test_db, self.npc_id, name="Quick Sort Algorithm")

        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword="Search", sort=None,
            order="asc", available=None,
        ))

        assert len(result["cards"]) == 1
        assert "Search" in result["cards"][0].name

    def test_search_by_knowledge_content(self):
        # Verify keyword filter matches knowledge_content field
        from algomate.models.cards import get_cards, create_card, CardCreate

        payload1 = CardCreate(
            name="Card A",
            npc_id=self.npc_id,
            knowledge_content="This is about dynamic programming techniques",
        )
        payload2 = CardCreate(
            name="Card B",
            npc_id=self.npc_id,
            knowledge_content="This is about graph traversal",
        )
        _run_async(create_card(payload1))
        _run_async(create_card(payload2))

        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword="dynamic", sort=None,
            order="asc", available=None,
        ))

        assert len(result["cards"]) == 1
        assert result["cards"][0].name == "Card A"

    def test_filter_by_algorithm_type(self):
        # Verify algorithm_type filter returns only matching cards
        from algomate.models.cards import get_cards

        _seed_card(self.test_db, self.npc_id, name="DP Card", algorithm_type="DP")
        _seed_card(self.test_db, self.npc_id, name="Search Card", algorithm_type="Search")
        _seed_card(self.test_db, self.npc_id, name="Sort Card", algorithm_type="Sort")

        result = _run_async(get_cards(
            domain=None, algorithm_type="DP", algorithm_category=None,
            search=None, status=None, keyword=None, sort=None,
            order="asc", available=None,
        ))

        assert len(result["cards"]) == 1
        assert result["cards"][0].algorithmType == "DP"

    def test_filter_by_domain(self):
        # Verify domain filter returns only cards in that domain
        from algomate.models.cards import get_cards

        _seed_card(self.test_db, self.npc_id, name="Forest Card 1", domain="新手森林")
        _seed_card(self.test_db, self.npc_id, name="Forest Card 2", domain="新手森林")

        result = _run_async(get_cards(
            domain="新手森林", algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword=None, sort=None,
            order="asc", available=None,
        ))

        assert len(result["cards"]) == 2

    def test_combined_filters(self):
        # Verify applying multiple filters simultaneously works correctly
        from algomate.models.cards import get_cards

        _seed_card(self.test_db, self.npc_id, name="DP Search", algorithm_type="DP", domain="新手森林")
        _seed_card(self.test_db, self.npc_id, name="DP Sort", algorithm_type="DP", domain="新手森林")
        _seed_card(self.test_db, self.npc_id, name="Search Algo", algorithm_type="Search", domain="新手森林")

        result = _run_async(get_cards(
            domain="新手森林", algorithm_type="DP", algorithm_category=None,
            search=None, status=None, keyword="Search", sort=None,
            order="asc", available=None,
        ))

        assert len(result["cards"]) == 1
        assert result["cards"][0].name == "DP Search"


class TestCardDomainStatsIntegration:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_db, self.npc_id = _setup_test_db()
        self._patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=self.test_db,
        )
        self._patcher.start()

    def teardown_method(self):
        self._patcher.stop()

    def test_domain_stats_empty(self):
        # Verify domain stats returns all zeros when no cards exist
        from algomate.models.cards import get_domain_stats

        result = _run_async(get_domain_stats())

        assert len(result) == 8
        for stat in result:
            assert stat.total_count == 0
            assert stat.mastered_count == 0
            assert stat.sealed_count == 0
            assert stat.avg_durability == 0

    def test_domain_stats_with_cards(self):
        # Verify domain stats correctly counts cards across different domains
        from algomate.models.cards import get_domain_stats

        _seed_card(self.test_db, self.npc_id, name="Card1", domain="新手森林", durability=80)
        _seed_card(self.test_db, self.npc_id, name="Card2", domain="新手森林", durability=90)
        _seed_card(self.test_db, self.npc_id, name="Card3", domain="新手森林", durability=20, is_sealed=True)

        result = _run_async(get_domain_stats())

        novice_stats = next(s for s in result if s.domain == "新手森林")
        assert novice_stats.total_count == 3
        assert novice_stats.mastered_count == 2
        assert novice_stats.sealed_count == 1

        other_stats = [s for s in result if s.domain != "新手森林"]
        for stat in other_stats:
            assert stat.total_count == 0
