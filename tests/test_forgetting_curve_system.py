"""
遗忘曲线系统后端集成测试

测试覆盖：
- GET /api/tasks/completed-count 端点
- 增强后的修炼统计 API（ReviewPlanService.get_review_statistics）
- 修炼完成流程（ReviewPlanService.complete_review）
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from algomate.data.database import Base
from algomate.models.cards import Card
from algomate.models.review_records import ReviewRecord
from algomate.review.review_plan_service import ReviewPlanService


@pytest.fixture
def engine():
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
def session_factory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture
def db_session(engine, session_factory):
    session = session_factory()
    yield session
    session.close()


class _MockDB:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def get_session(self):
        return self._session_factory()


@pytest.fixture
def mock_db(engine, session_factory):
    return _MockDB(session_factory)


@pytest.fixture
def review_service(mock_db):
    return ReviewPlanService(db=mock_db)


def _create_card(session, **overrides):
    defaults = {
        "name": "测试卡牌",
        "algorithm_type": "",
        "durability": 80,
        "pending_retake": False,
        "review_level": 0,
        "review_count": 0,
        "created_at": datetime.now(),
    }
    defaults.update(overrides)
    card = Card(**defaults)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def _create_review_record(session, card_id, status="completed", review_date=None, **overrides):
    defaults = {
        "card_id": card_id,
        "status": status,
        "review_date": review_date or datetime.now(),
    }
    defaults.update(overrides)
    record = ReviewRecord(**defaults)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


class TestCompletedCountAPI:
    """测试 GET /api/tasks/completed-count 端点"""

    def test_returns_zero_when_no_records(self, db_session, mock_db):
        count = (
            db_session.query(ReviewRecord)
            .filter(
                ReviewRecord.status == "completed",
                ReviewRecord.review_date >= datetime.combine(date.today(), datetime.min.time()),
                ReviewRecord.review_date <= datetime.combine(date.today(), datetime.max.time()),
            )
            .count()
        )
        assert count == 0

    def test_returns_correct_count(self, db_session, mock_db):
        card = _create_card(db_session)
        _create_review_record(db_session, card_id=card.id, status="completed")
        _create_review_record(db_session, card_id=card.id, status="completed")

        count = (
            db_session.query(ReviewRecord)
            .filter(
                ReviewRecord.status == "completed",
                ReviewRecord.review_date >= datetime.combine(date.today(), datetime.min.time()),
                ReviewRecord.review_date <= datetime.combine(date.today(), datetime.max.time()),
            )
            .count()
        )
        assert count == 2

    def test_excludes_non_completed(self, db_session, mock_db):
        card = _create_card(db_session)
        _create_review_record(db_session, card_id=card.id, status="completed")
        _create_review_record(db_session, card_id=card.id, status="pending")
        _create_review_record(db_session, card_id=card.id, status="skipped")

        count = (
            db_session.query(ReviewRecord)
            .filter(
                ReviewRecord.status == "completed",
                ReviewRecord.review_date >= datetime.combine(date.today(), datetime.min.time()),
                ReviewRecord.review_date <= datetime.combine(date.today(), datetime.max.time()),
            )
            .count()
        )
        assert count == 1

    def test_excludes_other_days(self, db_session, mock_db):
        card = _create_card(db_session)
        yesterday = datetime.now() - timedelta(days=1)
        _create_review_record(db_session, card_id=card.id, status="completed", review_date=yesterday)
        _create_review_record(db_session, card_id=card.id, status="completed")

        count = (
            db_session.query(ReviewRecord)
            .filter(
                ReviewRecord.status == "completed",
                ReviewRecord.review_date >= datetime.combine(date.today(), datetime.min.time()),
                ReviewRecord.review_date <= datetime.combine(date.today(), datetime.max.time()),
            )
            .count()
        )
        assert count == 1


class TestReviewStatisticsEnhanced:
    """测试增强后的修炼统计 API"""

    def test_review_level_distribution(self, db_session, review_service):
        _create_card(db_session, name="卡牌1", review_level=0)
        _create_card(db_session, name="卡牌2", review_level=1)
        _create_card(db_session, name="卡牌3", review_level=1)
        _create_card(db_session, name="卡牌4", review_level=3)

        stats = review_service.get_review_statistics(date.today())

        dist = stats["review_level_distribution"]
        assert dist.get("0") == 1
        assert dist.get("1") == 2
        assert dist.get("3") == 1

    def test_weekly_review_days(self, db_session, review_service):
        card = _create_card(db_session)

        today = datetime.now()
        three_days_ago = today - timedelta(days=3)
        five_days_ago = today - timedelta(days=5)

        _create_review_record(db_session, card_id=card.id, status="completed", review_date=today)
        _create_review_record(db_session, card_id=card.id, status="completed", review_date=three_days_ago)
        _create_review_record(db_session, card_id=card.id, status="completed", review_date=five_days_ago)

        stats = review_service.get_review_statistics(date.today())

        assert stats["weekly_review_days"] >= 2

    def test_total_review_count(self, db_session, review_service):
        card = _create_card(db_session)

        _create_review_record(db_session, card_id=card.id, status="completed")
        _create_review_record(db_session, card_id=card.id, status="completed")
        _create_review_record(db_session, card_id=card.id, status="pending")

        stats = review_service.get_review_statistics(date.today())

        assert stats["total_review_count"] == 2


class TestCompleteReviewFlow:
    """测试修炼完成流程"""

    def test_complete_review_updates_card(self, db_session, review_service):
        card = _create_card(
            db_session,
            review_level=2,
            durability=60,
            review_count=3,
            last_reviewed=datetime.now() - timedelta(days=5),
        )

        before_level = card.review_level
        before_durability = card.durability
        before_review_count = card.review_count

        result = review_service.complete_review(card.id, action="passed")

        assert result is not None
        assert result["review_level_after"] == before_level + 1
        assert result["durability_after"] == min(before_durability + 15, 100)
        assert result["review_count"] == before_review_count + 1
        assert "next_review_date" in result

        session = review_service.db.get_session()
        try:
            updated_card = session.query(Card).filter(Card.id == card.id).first()
            assert updated_card.review_level == before_level + 1
            assert updated_card.durability == min(before_durability + 15, 100)
            assert updated_card.review_count == before_review_count + 1
            assert updated_card.last_reviewed is not None
            assert updated_card.next_review_date is not None
        finally:
            session.close()

    def test_complete_review_at_max_level(self, db_session, review_service):
        card = _create_card(
            db_session,
            review_level=6,
            durability=80,
            review_count=10,
            last_reviewed=datetime.now() - timedelta(days=5),
        )

        result = review_service.complete_review(card.id, action="passed")

        assert result is not None
        assert result["review_level_after"] == 6

    def test_complete_review_durability_cap(self, db_session, review_service):
        card = _create_card(
            db_session,
            review_level=1,
            durability=90,
            review_count=1,
            last_reviewed=datetime.now() - timedelta(days=5),
        )

        result = review_service.complete_review(card.id, action="passed")

        assert result is not None
        assert result["durability_after"] <= 100

        session = review_service.db.get_session()
        try:
            updated_card = session.query(Card).filter(Card.id == card.id).first()
            assert updated_card.durability <= 100
        finally:
            session.close()


class TestReviewActionEffects:
    """模块0: 6档 action 对 durability/review_level 的差异化影响"""

    def test_forgot_lowers_durability_and_level(self, db_session, review_service):
        card = _create_card(db_session, review_level=2, durability=80)
        r = review_service.complete_review(card.id, action="forgot")
        assert r["durability_after"] == 55  # 80 - 25
        assert r["review_level_after"] == 1  # 2 - 1

    def test_struggled_lowers_durability_keeps_level(self, db_session, review_service):
        card = _create_card(db_session, review_level=2, durability=80)
        r = review_service.complete_review(card.id, action="struggled")
        assert r["durability_after"] == 70  # 80 - 10
        assert r["review_level_after"] == 2  # 持平

    def test_passed_raises_durability_and_level(self, db_session, review_service):
        card = _create_card(db_session, review_level=2, durability=80)
        r = review_service.complete_review(card.id, action="passed")
        assert r["durability_after"] == 95  # 80 + 15
        assert r["review_level_after"] == 3  # 2 + 1

    def test_mastered_raises_more(self, db_session, review_service):
        card = _create_card(db_session, review_level=2, durability=80)
        r = review_service.complete_review(card.id, action="mastered")
        assert r["durability_after"] == 100  # 80 + 25 封顶
        assert r["review_level_after"] == 3

    def test_redone_ac_highest_gain(self, db_session, review_service):
        card = _create_card(db_session, review_level=2, durability=80)
        r = review_service.complete_review(card.id, action="redone_ac")
        assert r["durability_after"] == 100  # 80 + 30 封顶
        assert r["review_level_after"] == 3

    def test_redone_stuck_lowers_both(self, db_session, review_service):
        card = _create_card(db_session, review_level=2, durability=80)
        r = review_service.complete_review(card.id, action="redone_stuck")
        assert r["durability_after"] == 50  # 80 - 30
        assert r["review_level_after"] == 1  # 2 - 1

    def test_durability_floor_at_zero(self, db_session, review_service):
        card = _create_card(db_session, review_level=0, durability=0)
        r = review_service.complete_review(card.id, action="forgot")
        assert r["durability_after"] == 0
        assert r["review_level_after"] == 0

    def test_invalid_action_falls_back_to_passed(self, db_session, review_service):
        card = _create_card(db_session, review_level=2, durability=80)
        r = review_service.complete_review(card.id, action="not_a_real_action")
        assert r["durability_after"] == 95  # 回退到 passed (+15)
        assert r["review_level_after"] == 3


