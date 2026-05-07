import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from algomate.data.database import Base
from algomate.models.dialogue_records import DialogueRecord
from algomate.models.dialogue_messages import DialogueMessageRecord, DialogueMessageCreate, DialogueMessageResponse
from algomate.models.dialogue_notes import DialogueNote, DialogueNoteCreate, DialogueNoteResponse
from algomate.models.npcs import NPC
from algomate.models.cards import Card
from algomate.models.notes import Note


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def npc(session):
    npc = NPC(
        name="测试导师",
        title="算法大师",
        algorithm_type="排序",
    )
    session.add(npc)
    session.commit()
    return npc


@pytest.fixture
def card(session, npc):
    card = Card(
        name="快速排序",
        algorithm_type="Sorting",
        npc_id=npc.id,
        topic="",
    )
    session.add(card)
    session.commit()
    return card


@pytest.fixture
def dialogue(session, npc):
    record = DialogueRecord(
        npc_id=npc.id,
        topic="排序算法",
        status="active",
    )
    session.add(record)
    session.commit()
    return record


class TestDialogueMessageRecord:
    def test_create_message(self, session, dialogue):
        msg = DialogueMessageRecord(
            dialogue_id=dialogue.id,
            role="user",
            content="请讲解快速排序",
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)

        assert msg.id is not None
        assert msg.dialogue_id == dialogue.id
        assert msg.role == "user"
        assert msg.content == "请讲解快速排序"
        assert msg.created_at is not None

    def test_create_assistant_message(self, session, dialogue):
        msg = DialogueMessageRecord(
            dialogue_id=dialogue.id,
            role="assistant",
            content="快速排序是一种分治算法...",
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)

        assert msg.role == "assistant"
        assert msg.content == "快速排序是一种分治算法..."

    def test_create_system_message(self, session, dialogue):
        msg = DialogueMessageRecord(
            dialogue_id=dialogue.id,
            role="system",
            content="对话开始",
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)

        assert msg.role == "system"

    def test_dialogue_relationship(self, session, dialogue):
        msg = DialogueMessageRecord(
            dialogue_id=dialogue.id,
            role="user",
            content="hello",
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)

        assert msg.dialogue is not None
        assert msg.dialogue.id == dialogue.id

    def test_cascade_delete(self, session, npc):
        record = DialogueRecord(npc_id=npc.id)
        session.add(record)
        session.commit()

        msg = DialogueMessageRecord(
            dialogue_id=record.id,
            role="user",
            content="to be deleted",
        )
        session.add(msg)
        session.commit()
        msg_id = msg.id

        session.delete(record)
        session.commit()

        assert session.query(DialogueMessageRecord).filter_by(id=msg_id).first() is None

    def test_pydantic_create_schema(self):
        schema = DialogueMessageCreate(
            dialogue_id=1,
            role="user",
            content="test content",
        )
        assert schema.dialogue_id == 1
        assert schema.role == "user"
        assert schema.content == "test content"

    def test_pydantic_response_schema(self, session, dialogue):
        msg = DialogueMessageRecord(
            dialogue_id=dialogue.id,
            role="user",
            content="test",
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)

        response = DialogueMessageResponse.model_validate(msg)
        assert response.id == msg.id
        assert response.dialogue_id == dialogue.id
        assert response.role == "user"
        assert response.content == "test"


class TestDialogueNote:
    def test_create_note(self, session, dialogue):
        note = DialogueNote(
            dialogue_id=dialogue.id,
            content="快速排序的核心是分区操作",
        )
        session.add(note)
        session.commit()
        session.refresh(note)

        assert note.id is not None
        assert note.dialogue_id == dialogue.id
        assert note.content == "快速排序的核心是分区操作"
        assert note.created_at is not None
        assert note.updated_at is not None

    def test_default_content(self, session, dialogue):
        note = DialogueNote(dialogue_id=dialogue.id)
        session.add(note)
        session.commit()
        session.refresh(note)

        assert note.content == ""

    def test_dialogue_relationship(self, session, dialogue):
        note = DialogueNote(
            dialogue_id=dialogue.id,
            content="test note",
        )
        session.add(note)
        session.commit()
        session.refresh(note)

        assert note.dialogue is not None
        assert note.dialogue.id == dialogue.id

    def test_cascade_delete(self, session, npc):
        record = DialogueRecord(npc_id=npc.id)
        session.add(record)
        session.commit()

        note = DialogueNote(
            dialogue_id=record.id,
            content="to be deleted",
        )
        session.add(note)
        session.commit()
        note_id = note.id

        session.delete(record)
        session.commit()

        assert session.query(DialogueNote).filter_by(id=note_id).first() is None

    def test_upsert_behavior(self, session, dialogue):
        note = DialogueNote(
            dialogue_id=dialogue.id,
            content="初始笔记",
        )
        session.add(note)
        session.commit()
        session.refresh(note)

        note.content = "更新后的笔记"
        session.commit()
        session.refresh(note)

        assert note.content == "更新后的笔记"

    def test_pydantic_create_schema(self):
        schema = DialogueNoteCreate(
            dialogue_id=1,
            content="test note",
        )
        assert schema.dialogue_id == 1
        assert schema.content == "test note"

    def test_pydantic_create_schema_default(self):
        schema = DialogueNoteCreate(dialogue_id=1)
        assert schema.content == ""

    def test_pydantic_response_schema(self, session, dialogue):
        note = DialogueNote(
            dialogue_id=dialogue.id,
            content="response test",
        )
        session.add(note)
        session.commit()
        session.refresh(note)

        response = DialogueNoteResponse.model_validate(note)
        assert response.id == note.id
        assert response.dialogue_id == dialogue.id
        assert response.content == "response test"


class TestDialogueRecordExtended:
    def test_new_fields_default(self, session, npc):
        record = DialogueRecord(npc_id=npc.id)
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.topic is None
        assert record.status == "active"
        assert record.last_active_at is None
        assert record.card_id is None
        assert record.updated_at is not None

    def test_set_new_fields(self, session, npc, card):
        now = datetime.now()
        record = DialogueRecord(
            npc_id=npc.id,
            topic="动态规划",
            status="completed",
            last_active_at=now,
            card_id=card.id,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.topic == "动态规划"
        assert record.status == "completed"
        assert record.last_active_at is not None
        assert record.card_id == card.id

    def test_messages_relationship(self, session, dialogue):
        msg1 = DialogueMessageRecord(
            dialogue_id=dialogue.id,
            role="user",
            content="问题1",
        )
        msg2 = DialogueMessageRecord(
            dialogue_id=dialogue.id,
            role="assistant",
            content="回答1",
        )
        session.add_all([msg1, msg2])
        session.commit()
        session.refresh(dialogue)

        assert len(dialogue.messages) == 2
        assert dialogue.messages[0].content == "问题1"
        assert dialogue.messages[1].content == "回答1"

    def test_notes_relationship(self, session, dialogue):
        note = DialogueNote(
            dialogue_id=dialogue.id,
            content="笔记1",
        )
        session.add(note)
        session.commit()
        session.refresh(dialogue)

        assert len(dialogue.notes) == 1
        assert dialogue.notes[0].content == "笔记1"

    def test_card_relationship(self, session, npc, card):
        record = DialogueRecord(
            npc_id=npc.id,
            card_id=card.id,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.card is not None
        assert record.card.id == card.id

    def test_card_dialogue_records_back_populates(self, session, npc, card):
        record = DialogueRecord(
            npc_id=npc.id,
            card_id=card.id,
        )
        session.add(record)
        session.commit()
        session.refresh(card)

        assert len(card.dialogue_records) == 1
        assert card.dialogue_records[0].id == record.id

    def test_backward_compatible_fields(self, session, npc):
        record = DialogueRecord(
            npc_id=npc.id,
            dialogue_content='[{"role":"user","content":"hi"}]',
            generated_cards='[1,2]',
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.dialogue_content == '[{"role":"user","content":"hi"}]'
        assert record.generated_cards == '[1,2]'
