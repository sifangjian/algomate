"""
F01 Card System Phase 0 测试

测试覆盖：
- F01-T001: Card ORM Model Alignment
- F01-T002: compute_card_status function
- F01-T003: is_in_grace_period tests
- F01-T004: CardRepository extension
- F01-T005: Database migration (manual, no TDD)
"""

import sys
import pytest
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================
# F01-T001: Card ORM Model Alignment Tests
# ============================================================

class TestCardModelAlignment:
    """测试 Card ORM 模型是否对齐 specs"""

    def test_card_has_pending_retake_field(self):
        from algomate.models.cards import Card
        assert hasattr(Card, 'pending_retake'), "Card should have pending_retake field"

    def test_card_pending_retake_default_false(self):
        from algomate.models.cards import Card
        col = Card.__table__.c.pending_retake
        assert col.default.arg is False, "pending_retake default should be False"

    def test_card_pending_retake_not_nullable(self):
        from algomate.models.cards import Card
        col = Card.__table__.c.pending_retake
        assert col.nullable is False, "pending_retake should not be nullable"

    def test_card_durability_default_80(self):
        from algomate.models.cards import Card
        col = Card.__table__.c.durability
        assert col.default.arg == 80, "durability default should be 80"

    def test_card_has_content_dimension_fields(self):
        from algomate.models.cards import Card
        content_dims = [
            'core_concept', 'code_template', 'complexity_analysis',
            'use_cases', 'common_variants', 'typical_problems',
            'common_pitfalls', 'comparison', 'my_notes'
        ]
        for field in content_dims:
            assert hasattr(Card, field), f"Card should have {field} field"

    def test_card_content_dimensions_default_empty_string(self):
        from algomate.models.cards import Card
        content_dims = [
            'core_concept', 'code_template', 'complexity_analysis',
            'use_cases', 'common_variants', 'typical_problems',
            'common_pitfalls', 'comparison', 'my_notes'
        ]
        for field in content_dims:
            col = Card.__table__.c[field]
            assert col.default.arg == "", f"{field} default should be empty string"

    def test_card_has_visual_links_field(self):
        from algomate.models.cards import Card
        assert hasattr(Card, 'visual_links'), "Card should have visual_links field"

    def test_card_visual_links_nullable(self):
        from algomate.models.cards import Card
        col = Card.__table__.c.visual_links
        assert col.nullable is True, "visual_links should be nullable"

    def test_card_has_npc_id_field(self):
        from algomate.models.cards import Card
        assert hasattr(Card, 'npc_id'), "Card should have npc_id field"

    def test_card_npc_id_not_nullable(self):
        from algomate.models.cards import Card
        col = Card.__table__.c.npc_id
        assert col.nullable is False, "npc_id should not be nullable"

    def test_card_npc_id_foreign_key(self):
        from algomate.models.cards import Card
        col = Card.__table__.c.npc_id
        fks = list(col.foreign_keys)
        assert len(fks) > 0, "npc_id should have foreign key"
        fk_ref = str(fks[0].target_fullname)
        assert 'npcs.id' in fk_ref, f"npc_id FK should reference npcs.id, got {fk_ref}"

    def test_card_has_topic_field(self):
        from algomate.models.cards import Card
        assert hasattr(Card, 'topic'), "Card should have topic field"

    def test_card_topic_default_empty_string(self):
        from algomate.models.cards import Card
        col = Card.__table__.c.topic
        assert col.default.arg == "", "topic default should be empty string"

    def test_card_topic_not_nullable(self):
        from algomate.models.cards import Card
        col = Card.__table__.c.topic
        assert col.nullable is False, "topic should not be nullable"

    def test_card_backward_compat_key_points(self):
        from algomate.models.cards import Card
        assert hasattr(Card, 'key_points'), "Card should keep key_points for backward compat"

    def test_card_create_has_new_fields(self):
        from algomate.models.cards import CardCreate
        fields = CardCreate.model_fields
        assert 'name' in fields, "CardCreate should have name"
        assert 'algorithm_type' in fields, "CardCreate should have algorithm_type"
        assert 'npc_id' in fields, "CardCreate should have npc_id"
        assert 'topic' in fields, "CardCreate should have topic"
        assert 'visual_links' in fields, "CardCreate should have visual_links"
        for dim in ['core_concept', 'code_template', 'complexity_analysis',
                     'use_cases', 'common_variants', 'typical_problems',
                     'common_pitfalls', 'comparison', 'my_notes']:
            assert dim in fields, f"CardCreate should have {dim}"

    def test_card_update_has_new_fields(self):
        from algomate.models.cards import CardUpdate
        fields = CardUpdate.model_fields
        for dim in ['core_concept', 'key_points', 'code_template', 'complexity_analysis',
                     'use_cases', 'common_variants', 'typical_problems',
                     'common_pitfalls', 'comparison', 'my_notes', 'visual_links']:
            assert dim in fields, f"CardUpdate should have {dim}"

    def test_card_response_has_new_fields(self):
        from algomate.models.cards import CardResponse
        fields = CardResponse.model_fields
        assert 'pending_retake' in fields, "CardResponse should have pending_retake"
        assert 'npc_id' in fields, "CardResponse should have npc_id"
        assert 'topic' in fields, "CardResponse should have topic"
        assert 'visual_links' in fields, "CardResponse should have visual_links"
        for dim in ['core_concept', 'code_template', 'complexity_analysis',
                     'use_cases', 'common_variants', 'typical_problems',
                     'common_pitfalls', 'comparison', 'my_notes']:
            assert dim in fields, f"CardResponse should have {dim}"


# ============================================================
# F01-T002: compute_card_status function Tests
# ============================================================

class TestComputeCardStatus:
    """测试 compute_card_status 函数"""

    def test_pending_retake_when_pending_retake_true(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(0, True) == "pending_retake"

    def test_pending_retake_when_durability_zero(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(0, False) == "pending_retake"

    def test_pending_retake_when_both(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(0, True) == "pending_retake"

    def test_endangered_when_durability_below_30(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(15, False) == "endangered"

    def test_normal_when_durability_85(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(85, False) == "normal"

    def test_boundary_durability_30_is_normal(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(30, False) == "normal"

    def test_boundary_durability_29_is_endangered(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(29, False) == "endangered"

    def test_pending_retake_overrides_normal(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(80, True) == "pending_retake"

    def test_pending_retake_overrides_endangered(self):
        from algomate.core.game.durability import compute_card_status
        assert compute_card_status(10, True) == "pending_retake"


# ============================================================
# F01-T003: is_in_grace_period Tests
# ============================================================

class TestIsInGracePeriod:
    """测试 is_in_grace_period 函数"""

    def test_within_grace_period(self):
        from algomate.core.game.durability import DurabilityManager
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=1)
        assert manager.is_in_grace_period(created_at) is True

    def test_outside_grace_period(self):
        from algomate.core.game.durability import DurabilityManager
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=5)
        assert manager.is_in_grace_period(created_at) is False

    def test_none_created_at(self):
        from algomate.core.game.durability import DurabilityManager
        manager = DurabilityManager()
        assert manager.is_in_grace_period(None) is False

    def test_exact_boundary_3_days(self):
        from algomate.core.game.durability import DurabilityManager
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=3)
        result = manager.is_in_grace_period(created_at)
        assert result is False, "3 days old should be outside grace period (boundary)"

    def test_just_inside_grace_period(self):
        from algomate.core.game.durability import DurabilityManager
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=2, hours=23)
        assert manager.is_in_grace_period(created_at) is True


# ============================================================
# F01-T004: CardRepository extension Tests
# ============================================================

class TestCardRepositoryExtension:
    """测试 CardRepository 扩展方法"""

    @pytest.fixture
    def db_and_repo(self):
        from algomate.data.database import Database, Base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)

        mock_db = MagicMock()
        mock_db.get_session = lambda: SessionLocal()

        from algomate.data.repositories.card_repo import CardRepository
        repo = CardRepository(mock_db)

        from algomate.models.npcs import NPC
        session = mock_db.get_session()
        npc = NPC(
            name="Test NPC",
            domain="新手森林",
            location="新手森林",
            system_prompt="You are a test NPC",
        )
        session.add(npc)
        session.commit()
        npc_id = npc.id
        session.close()

        return mock_db, repo, npc_id

    def _create_card(self, repo, npc_id, name="Test Card", durability=80,
                     pending_retake=False, algorithm_type="", topic=""):
        return repo.create(
            name=name,
            algorithm_type=algorithm_type,
            durability=durability,
            npc_id=npc_id,
            pending_retake=pending_retake,
            topic=topic,
        )

    def test_get_all_with_status_returns_cards_with_status(self, db_and_repo):
        _, repo, npc_id = db_and_repo
        self._create_card(repo, npc_id, name="Normal Card", durability=80)
        result = repo.get_all_with_status()
        assert 'cards' in result
        assert 'endangered_count' in result
        assert 'pending_retake_count' in result
        assert len(result['cards']) >= 1
        card_data = result['cards'][0]
        assert 'status' in card_data

    def test_get_all_with_status_endangered_count(self, db_and_repo):
        _, repo, npc_id = db_and_repo
        self._create_card(repo, npc_id, name="Endangered", durability=15)
        self._create_card(repo, npc_id, name="Normal", durability=80)
        result = repo.get_all_with_status()
        assert result['endangered_count'] >= 1

    def test_get_all_with_status_pending_retake_count(self, db_and_repo):
        _, repo, npc_id = db_and_repo
        self._create_card(repo, npc_id, name="Pending", durability=0, pending_retake=True)
        self._create_card(repo, npc_id, name="Normal", durability=80)
        result = repo.get_all_with_status()
        assert result['pending_retake_count'] >= 1

    def test_get_all_with_status_filter_by_algorithm_type(self, db_and_repo):
        _, repo, npc_id = db_and_repo
        self._create_card(repo, npc_id, name="DP Card", algorithm_type="DP")
        self._create_card(repo, npc_id, name="Search Card", algorithm_type="Search")
        result = repo.get_all_with_status(algorithm_type="DP")
        for card_data in result['cards']:
            assert card_data['card'].algorithm_type == "DP"

    def test_get_all_with_status_filter_by_status(self, db_and_repo):
        _, repo, npc_id = db_and_repo
        self._create_card(repo, npc_id, name="Endangered", durability=15)
        self._create_card(repo, npc_id, name="Normal", durability=80)
        result = repo.get_all_with_status(status="endangered")
        for card_data in result['cards']:
            assert card_data['status'] == "endangered"

    def test_get_all_with_status_filter_by_keyword(self, db_and_repo):
        _, repo, npc_id = db_and_repo
        self._create_card(repo, npc_id, name="Binary Search")
        self._create_card(repo, npc_id, name="Quick Sort")
        result = repo.get_all_with_status(keyword="Search")
        for card_data in result['cards']:
            assert "Search" in card_data['card'].name

    def test_get_all_supports_new_filters(self, db_and_repo):
        _, repo, npc_id = db_and_repo
        self._create_card(repo, npc_id, name="DP Card", algorithm_type="DP")
        self._create_card(repo, npc_id, name="Search Card", algorithm_type="Search")
        cards = repo.get_all(algorithm_type="DP")
        for card in cards:
            assert card.algorithm_type == "DP"


# ============================================================
# Shared API test helpers
# ============================================================

def _setup_test_db():
    from algomate.data.database import Base
    from algomate.models.npcs import NPC
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    class _TestDB:
        def get_session(self):
            return SessionLocal()

    test_db = _TestDB()

    session = test_db.get_session()
    npc = NPC(
        name="Test NPC",
        domain="新手森林",
        location="新手森林",
        system_prompt="You are a test NPC",
    )
    session.add(npc)
    session.commit()
    npc_id = npc.id
    session.close()

    return test_db, npc_id


def _seed_card(test_db, npc_id, **kwargs):
    from algomate.models.cards import Card

    defaults = dict(
        name="Test Card",
        algorithm_type="",
        durability=80,
        npc_id=npc_id,
        pending_retake=False,
        topic="",
    )
    defaults.update(kwargs)
    session = test_db.get_session()
    card = Card(**defaults)
    session.add(card)
    session.commit()
    card_id = card.id
    session.close()
    return card_id


def _run_async(coro):
    import asyncio
    import selectors

    class _DummySelector(selectors.BaseSelector):
        def __init__(self):
            self._map = {}

        def register(self, fileobj, events, data=None):
            key = selectors.SelectorKey(fileobj, 0, events, data)
            self._map[fileobj] = key
            return key

        def unregister(self, fileobj):
            return self._map.pop(fileobj)

        def select(self, timeout=None):
            return []

        def close(self):
            self._map.clear()

        def get_map(self):
            return self._map

    loop = asyncio.SelectorEventLoop(_DummySelector())
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================================
# F01-T006/T007: Card Detail API Tests (Phase 1)
# ============================================================

@pytest.mark.skip(reason="F05 has complete API tests in test_f05_card_workshop.py")
class TestCardDetailAPI:

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

    def test_get_card_detail_returns_ten_dimensions(self):
        from algomate.models.cards import get_card
        card_id = _seed_card(self.test_db, self.npc_id)
        result = _run_async(get_card(card_id))
        dim_fields = [
            "coreConcept", "codeTemplate", "complexityAnalysis",
            "useCases", "commonVariants", "typicalProblems",
            "commonPitfalls", "comparison", "myNotes",
        ]
        for field in dim_fields:
            assert hasattr(result, field) or field in result.model_fields, \
                f"Response should contain {field}"

    def test_get_card_detail_returns_visual_links_when_present(self):
        from algomate.models.cards import get_card
        card_id = _seed_card(
            self.test_db, self.npc_id,
            visual_links="https://example.com/viz",
        )
        result = _run_async(get_card(card_id))
        assert result.visualLinks == "https://example.com/viz"

    def test_get_card_detail_visual_links_null(self):
        from algomate.models.cards import get_card
        card_id = _seed_card(self.test_db, self.npc_id)
        result = _run_async(get_card(card_id))
        assert result.visualLinks is None

    def test_get_card_detail_returns_status(self):
        from algomate.models.cards import get_card
        card_id = _seed_card(self.test_db, self.npc_id, durability=80)
        result = _run_async(get_card(card_id))
        assert result.status == "normal"

    def test_get_card_detail_not_found(self):
        from algomate.models.cards import get_card
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _run_async(get_card(99999))
        assert exc_info.value.status_code == 404


# ============================================================
# F01-T010: Card List API Tests (Phase 2)
# ============================================================

@pytest.mark.skip(reason="F05 has complete API tests in test_f05_card_workshop.py")
class TestCardListAPI:

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

    def test_get_cards_returns_status_field(self):
        from algomate.models.cards import get_cards
        _seed_card(self.test_db, self.npc_id, name="Normal Card", durability=80)
        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword=None, sort=None,
            order="asc", available=None,
        ))
        assert len(result["cards"]) >= 1
        for card in result["cards"]:
            assert card.status is not None

    def test_get_cards_returns_endangered_count(self):
        from algomate.models.cards import get_cards
        _seed_card(self.test_db, self.npc_id, name="Endangered", durability=15)
        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword=None, sort=None,
            order="asc", available=None,
        ))
        assert result["endangered_count"] >= 1

    def test_get_cards_returns_pending_retake_count(self):
        from algomate.models.cards import get_cards
        _seed_card(
            self.test_db, self.npc_id,
            name="Pending", durability=0, pending_retake=True,
        )
        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword=None, sort=None,
            order="asc", available=None,
        ))
        assert result["pending_retake_count"] >= 1

    def test_get_cards_filter_by_status(self):
        from algomate.models.cards import get_cards
        _seed_card(self.test_db, self.npc_id, name="Endangered", durability=15)
        _seed_card(self.test_db, self.npc_id, name="Normal", durability=80)
        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status="endangered", keyword=None, sort=None,
            order="asc", available=None,
        ))
        for card in result["cards"]:
            assert card.status == "endangered"

    def test_get_cards_filter_by_keyword(self):
        from algomate.models.cards import get_cards
        _seed_card(self.test_db, self.npc_id, name="Binary Search")
        _seed_card(self.test_db, self.npc_id, name="Quick Sort")
        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword="Search", sort=None,
            order="asc", available=None,
        ))
        for card in result["cards"]:
            assert "Search" in card.name

    def test_get_cards_filter_by_algorithm_type(self):
        from algomate.models.cards import get_cards
        _seed_card(self.test_db, self.npc_id, name="DP Card", algorithm_type="DP")
        _seed_card(self.test_db, self.npc_id, name="Search Card", algorithm_type="Search")
        result = _run_async(get_cards(
            domain=None, algorithm_type="DP", algorithm_category=None,
            search=None, status=None, keyword=None, sort=None,
            order="asc", available=None,
        ))
        for card in result["cards"]:
            assert card.algorithmType == "DP"


# ============================================================
# F01-T014/T015: Card Update API Tests (Phase 3)
# ============================================================

@pytest.mark.skip(reason="F05 has complete API tests in test_f05_card_workshop.py")
class TestCardUpdateAPI:

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

    def test_update_card_success(self):
        from algomate.models.cards import update_card, CardUpdate
        card_id = _seed_card(
            self.test_db, self.npc_id,
            name="Old Name", core_concept="old concept",
        )
        payload = CardUpdate(name="New Name", core_concept="new concept")
        result = _run_async(update_card(card_id, payload))
        assert result.name == "New Name"
        assert result.coreConcept == "new concept"

    def test_update_card_no_changes_returns_40002(self):
        from algomate.models.cards import update_card, CardUpdate
        from fastapi import HTTPException
        card_id = _seed_card(self.test_db, self.npc_id, name="Same Name")
        payload = CardUpdate(name="Same Name")
        with pytest.raises(HTTPException) as exc_info:
            _run_async(update_card(card_id, payload))
        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        if isinstance(detail, dict):
            assert detail.get("code") == 40002
        else:
            assert "40002" in str(detail) or "内容未变更" in str(detail)

    def test_update_card_partial_update(self):
        from algomate.models.cards import update_card, CardUpdate
        card_id = _seed_card(
            self.test_db, self.npc_id,
            name="Original", core_concept="keep this",
        )
        payload = CardUpdate(name="Updated")
        result = _run_async(update_card(card_id, payload))
        assert result.name == "Updated"
        assert result.coreConcept == "keep this"

    def test_update_card_not_found(self):
        from algomate.models.cards import update_card, CardUpdate
        from fastapi import HTTPException
        payload = CardUpdate(name="Ghost")
        with pytest.raises(HTTPException) as exc_info:
            _run_async(update_card(99999, payload))
        assert exc_info.value.status_code == 404


# ============================================================
# F01-T016/T017: Card Retake API Tests (Phase 4)
# ============================================================

@pytest.mark.skip(reason="F05 has complete API tests in test_f05_card_workshop.py")
class TestCardRetakeAPI:

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

    def test_retake_card_success(self):
        from algomate.models.cards import retake_card
        card_id = _seed_card(
            self.test_db, self.npc_id,
            durability=0, pending_retake=True,
        )
        result = _run_async(retake_card(card_id))
        assert result.pendingRetake is False
        assert result.durability == 30

    def test_retake_card_not_pending_returns_40003(self):
        from algomate.models.cards import retake_card
        from fastapi import HTTPException
        card_id = _seed_card(
            self.test_db, self.npc_id,
            durability=80, pending_retake=False,
        )
        with pytest.raises(HTTPException) as exc_info:
            _run_async(retake_card(card_id))
        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        if isinstance(detail, dict):
            assert detail.get("code") == 40003
        else:
            assert "40003" in str(detail) or "待重修" in str(detail)

    def test_retake_card_not_found(self):
        from algomate.models.cards import retake_card
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _run_async(retake_card(99999))
        assert exc_info.value.status_code == 404


# ============================================================
# F01-T020: Daily Decay Tests (Phase 4)
# ============================================================

class TestDailyDecay:

    def test_daily_decay_grace_period_skipped(self):
        from algomate.core.game.durability import apply_daily_decay
        card = MagicMock()
        card.durability = 80
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=1)
        result = apply_daily_decay(card)
        assert result["decayed"] is False
        assert result["new_durability"] == 80

    def test_daily_decay_reduces_durability(self):
        from algomate.core.game.durability import apply_daily_decay
        card = MagicMock()
        card.durability = 80
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=5)
        result = apply_daily_decay(card)
        assert result["decayed"] is True
        assert result["new_durability"] < 80

    def test_daily_decay_durability_zero_sets_pending_retake(self):
        from algomate.core.game.durability import apply_daily_decay, compute_card_status
        card = MagicMock()
        card.durability = 2
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=5)
        result = apply_daily_decay(card)
        assert result["decayed"] is True
        if result["new_durability"] == 0:
            assert compute_card_status(result["new_durability"], False) == "pending_retake"

    def test_daily_decay_pending_retake_skipped(self):
        from algomate.core.game.durability import apply_daily_decay
        card = MagicMock()
        card.durability = 0
        card.pending_retake = True
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=5)
        result = apply_daily_decay(card)
        assert result["decayed"] is False
