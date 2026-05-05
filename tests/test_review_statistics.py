import pytest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from algomate.data.database import Base
from algomate.models.cards import Card
from algomate.models.review_records import ReviewRecord
from algomate.review.review_plan_service import ReviewPlanService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_db(db_session):
    mock = MagicMock()
    mock.get_session.return_value = db_session
    return mock


@pytest.fixture
def service(mock_db):
    return ReviewPlanService(db=mock_db)


def _add_card(session, name="test_card", domain="新手森林", review_level=0,
              durability=100, is_sealed=False, next_review_date=None):
    card = Card(
        name=name,
        domain=domain,
        review_level=review_level,
        durability=durability,
        is_sealed=is_sealed,
        next_review_date=next_review_date,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def _add_review_record(session, card_id, review_date, status="completed"):
    record = ReviewRecord(
        card_id=card_id,
        review_date=review_date,
        status=status,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


class TestReviewLevelDistribution:
    def test_review_level_distribution(self, service, db_session):
        _add_card(db_session, name="c0", review_level=0)
        _add_card(db_session, name="c0b", review_level=0)
        _add_card(db_session, name="c1", review_level=1)
        _add_card(db_session, name="c3", review_level=3)

        result = service.get_review_statistics(target_date=date(2026, 5, 5))
        dist = result["review_level_distribution"]

        assert dist["0"] == 2
        assert dist["1"] == 1
        assert dist["3"] == 1
        assert "2" not in dist

    def test_sealed_cards_excluded(self, service, db_session):
        _add_card(db_session, name="active", review_level=2, is_sealed=False)
        _add_card(db_session, name="sealed", review_level=2, is_sealed=True)

        result = service.get_review_statistics(target_date=date(2026, 5, 5))
        dist = result["review_level_distribution"]

        assert dist.get("2", 0) == 1

    def test_empty_distribution(self, service, db_session):
        result = service.get_review_statistics(target_date=date(2026, 5, 5))
        dist = result["review_level_distribution"]

        assert dist == {}


class TestWeeklyReviewDays:
    def test_weekly_review_days(self, service, db_session):
        card = _add_card(db_session, name="c1")

        today = date(2026, 5, 5)
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 3, 10, 0),
            status="completed",
        )
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 5, 14, 0),
            status="completed",
        )

        result = service.get_review_statistics(target_date=today)
        assert result["weekly_review_days"] == 2

    def test_records_outside_week_excluded(self, service, db_session):
        card = _add_card(db_session, name="c1")

        today = date(2026, 5, 5)
        _add_review_record(
            db_session, card.id,
            datetime(2026, 4, 27, 10, 0),
            status="completed",
        )
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 3, 10, 0),
            status="completed",
        )

        result = service.get_review_statistics(target_date=today)
        assert result["weekly_review_days"] == 1

    def test_non_completed_excluded(self, service, db_session):
        card = _add_card(db_session, name="c1")

        today = date(2026, 5, 5)
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 4, 10, 0),
            status="pending",
        )
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 5, 10, 0),
            status="completed",
        )

        result = service.get_review_statistics(target_date=today)
        assert result["weekly_review_days"] == 1

    def test_same_day_multiple_records_count_once(self, service, db_session):
        card = _add_card(db_session, name="c1")

        today = date(2026, 5, 5)
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 5, 9, 0),
            status="completed",
        )
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 5, 15, 0),
            status="completed",
        )

        result = service.get_review_statistics(target_date=today)
        assert result["weekly_review_days"] == 1

    def test_no_records(self, service, db_session):
        result = service.get_review_statistics(target_date=date(2026, 5, 5))
        assert result["weekly_review_days"] == 0


class TestTotalReviewCount:
    def test_total_review_count(self, service, db_session):
        card = _add_card(db_session, name="c1")

        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 1, 10, 0),
            status="completed",
        )
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 3, 10, 0),
            status="completed",
        )
        _add_review_record(
            db_session, card.id,
            datetime(2026, 5, 5, 10, 0),
            status="pending",
        )

        result = service.get_review_statistics(target_date=date(2026, 5, 5))
        assert result["total_review_count"] == 2

    def test_total_review_count_empty(self, service, db_session):
        result = service.get_review_statistics(target_date=date(2026, 5, 5))
        assert result["total_review_count"] == 0

    def test_total_review_count_across_cards(self, service, db_session):
        card1 = _add_card(db_session, name="c1")
        card2 = _add_card(db_session, name="c2")

        _add_review_record(
            db_session, card1.id,
            datetime(2026, 5, 1, 10, 0),
            status="completed",
        )
        _add_review_record(
            db_session, card2.id,
            datetime(2026, 5, 2, 10, 0),
            status="completed",
        )
        _add_review_record(
            db_session, card2.id,
            datetime(2026, 5, 3, 10, 0),
            status="skipped",
        )

        result = service.get_review_statistics(target_date=date(2026, 5, 5))
        assert result["total_review_count"] == 2
