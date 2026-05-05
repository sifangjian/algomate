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
from algomate.models.notes import Note
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
        "domain": "新手森林",
        "difficulty": 3,
        "durability": 80,
        "max_durability": 100,
        "is_sealed": False,
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
            max_durability=100,
            review_count=3,
            last_reviewed=datetime.now() - timedelta(days=5),
        )

        before_level = card.review_level
        before_durability = card.durability
        before_review_count = card.review_count

        result = review_service.complete_review(card.id, action="success")

        assert result is not None
        assert result["review_level"] == before_level + 1
        assert result["durability"] == before_durability + 20
        assert result["review_count"] == before_review_count + 1
        assert result["last_reviewed"] is not None
        assert result["next_review_date"] is not None

        session = review_service.db.get_session()
        try:
            updated_card = session.query(Card).filter(Card.id == card.id).first()
            assert updated_card.review_level == before_level + 1
            assert updated_card.durability == before_durability + 20
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
            max_durability=100,
            review_count=10,
            last_reviewed=datetime.now() - timedelta(days=5),
        )

        result = review_service.complete_review(card.id, action="success")

        assert result is not None
        assert result["review_level"] == 6

    def test_complete_review_durability_cap(self, db_session, review_service):
        card = _create_card(
            db_session,
            review_level=1,
            durability=90,
            max_durability=100,
            review_count=1,
            last_reviewed=datetime.now() - timedelta(days=5),
        )

        result = review_service.complete_review(card.id, action="success")

        assert result is not None
        assert result["durability"] <= 100

        session = review_service.db.get_session()
        try:
            updated_card = session.query(Card).filter(Card.id == card.id).first()
            assert updated_card.durability <= updated_card.max_durability
        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
