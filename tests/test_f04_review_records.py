import pytest
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from algomate.models.review_records import ReviewRecord, ReviewRecordCreate, ReviewRecordResponse

TestBase = declarative_base()


class ReviewRecordStub(TestBase):
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, nullable=True)
    card_id = Column(Integer, nullable=True)
    review_date = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    score = Column(Integer, nullable=True)
    review_type = Column(String(20), default="content_review", nullable=False)
    completed_at = Column(DateTime, nullable=True)
    durability_before = Column(Integer, nullable=True)
    durability_after = Column(Integer, nullable=True)
    review_level_before = Column(Integer, nullable=True)
    review_level_after = Column(Integer, nullable=True)


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestBase.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestReviewRecordORM:
    def test_create_record_with_new_fields(self, session):
        now = datetime.now()
        record = ReviewRecordStub(
            card_id=1,
            status="completed",
            score=90,
            review_type="content_review",
            completed_at=now,
            durability_before=80,
            durability_after=100,
            review_level_before=2,
            review_level_after=3,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.id is not None
        assert record.review_type == "content_review"
        assert record.completed_at == now
        assert record.durability_before == 80
        assert record.durability_after == 100
        assert record.review_level_before == 2
        assert record.review_level_after == 3

    def test_review_type_defaults_to_content_review(self, session):
        record = ReviewRecordStub(card_id=1, status="pending")
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.review_type == "content_review"

    def test_new_nullable_fields_default_to_none(self, session):
        record = ReviewRecordStub(card_id=1, status="pending")
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.completed_at is None
        assert record.durability_before is None
        assert record.durability_after is None
        assert record.review_level_before is None
        assert record.review_level_after is None

    def test_retrieve_record_with_new_fields(self, session):
        now = datetime.now()
        record = ReviewRecordStub(
            card_id=1,
            status="completed",
            score=85,
            review_type="boss_battle",
            completed_at=now,
            durability_before=60,
            durability_after=75,
            review_level_before=1,
            review_level_after=2,
        )
        session.add(record)
        session.commit()

        fetched = session.query(ReviewRecordStub).filter(ReviewRecordStub.id == record.id).first()
        assert fetched is not None
        assert fetched.review_type == "boss_battle"
        assert fetched.durability_before == 60
        assert fetched.durability_after == 75
        assert fetched.review_level_before == 1
        assert fetched.review_level_after == 2


class TestReviewRecordModelColumns:
    def test_review_record_has_review_type_column(self):
        col = ReviewRecord.__table__.c.review_type
        assert col is not None
        assert isinstance(col.type, String)
        assert col.default.arg == "content_review"
        assert col.nullable is False

    def test_review_record_has_completed_at_column(self):
        col = ReviewRecord.__table__.c.completed_at
        assert col is not None
        assert isinstance(col.type, DateTime)
        assert col.nullable is True

    def test_review_record_has_durability_before_column(self):
        col = ReviewRecord.__table__.c.durability_before
        assert col is not None
        assert isinstance(col.type, Integer)
        assert col.nullable is True

    def test_review_record_has_durability_after_column(self):
        col = ReviewRecord.__table__.c.durability_after
        assert col is not None
        assert isinstance(col.type, Integer)
        assert col.nullable is True

    def test_review_record_has_review_level_before_column(self):
        col = ReviewRecord.__table__.c.review_level_before
        assert col is not None
        assert isinstance(col.type, Integer)
        assert col.nullable is True

    def test_review_record_has_review_level_after_column(self):
        col = ReviewRecord.__table__.c.review_level_after
        assert col is not None
        assert isinstance(col.type, Integer)
        assert col.nullable is True


class TestReviewRecordCreate:
    def test_create_model_includes_review_type(self):
        data = ReviewRecordCreate(card_id=1, status="pending")
        assert data.review_type == "content_review"

    def test_create_model_custom_review_type(self):
        data = ReviewRecordCreate(card_id=1, status="pending", review_type="boss_battle")
        assert data.review_type == "boss_battle"

    def test_create_model_existing_fields(self):
        data = ReviewRecordCreate(card_id=1, note_id=2, status="completed", score=95)
        assert data.card_id == 1
        assert data.note_id == 2
        assert data.status == "completed"
        assert data.score == 95


class TestReviewRecordResponse:
    def test_response_model_includes_new_fields(self):
        now = datetime.now()
        resp = ReviewRecordResponse(
            id=1,
            card_id=1,
            review_date=now,
            status="completed",
            score=90,
            review_type="boss_battle",
            completed_at=now,
            durability_before=80,
            durability_after=100,
            review_level_before=2,
            review_level_after=3,
        )
        assert resp.review_type == "boss_battle"
        assert resp.completed_at == now
        assert resp.durability_before == 80
        assert resp.durability_after == 100
        assert resp.review_level_before == 2
        assert resp.review_level_after == 3

    def test_response_model_new_fields_default_to_none(self):
        now = datetime.now()
        resp = ReviewRecordResponse(
            id=1,
            card_id=1,
            review_date=now,
            status="pending",
            score=None,
        )
        assert resp.review_type == "content_review"
        assert resp.completed_at is None
        assert resp.durability_before is None
        assert resp.durability_after is None
        assert resp.review_level_before is None
        assert resp.review_level_after is None
