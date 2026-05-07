from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import joinedload
from algomate.models.battle_records import BattleRecord
from ..database import Database


class BattleRecordRepository:

    def __init__(self, db: Database):
        self.db = db

    def create(
        self,
        boss_id: int,
        card_id: int,
        question_type: str,
        is_weakness_card: bool,
        is_victory: bool = False,
        durability_change: int = 0,
        question_content: str = None,
        question_options: str = None,
        correct_answer: str = None,
        explanation: str = None,
        leetcode_url: str = None,
    ) -> BattleRecord:
        session = self.db.get_session()
        try:
            record = BattleRecord(
                boss_id=boss_id,
                card_id=card_id,
                question_type=question_type,
                is_weakness_card=is_weakness_card,
                is_victory=is_victory,
                durability_change=durability_change,
                question_content=question_content,
                question_options=question_options,
                correct_answer=correct_answer,
                explanation=explanation,
                leetcode_url=leetcode_url,
                status='in_progress',
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def get_by_id(self, record_id: int) -> Optional[BattleRecord]:
        session = self.db.get_session()
        try:
            return session.query(BattleRecord).filter(BattleRecord.id == record_id).first()
        finally:
            session.close()

    def get_active_by_card(self, card_id: int) -> List[BattleRecord]:
        session = self.db.get_session()
        try:
            return session.query(BattleRecord).filter(
                BattleRecord.card_id == card_id,
                BattleRecord.status == 'in_progress',
            ).all()
        finally:
            session.close()

    def get_recent_by_boss(self, boss_id: int, limit: int = 5) -> List[BattleRecord]:
        session = self.db.get_session()
        try:
            return session.query(BattleRecord).options(
                joinedload(BattleRecord.card)
            ).filter(
                BattleRecord.boss_id == boss_id,
                BattleRecord.status == 'completed',
            ).order_by(BattleRecord.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def update_result(
        self,
        record_id: int,
        is_victory: bool,
        answer: str,
        score: int,
        durability_change: int,
        explanation: str = None,
    ) -> Optional[BattleRecord]:
        session = self.db.get_session()
        try:
            record = session.query(BattleRecord).filter(BattleRecord.id == record_id).first()
            if not record:
                return None
            record.is_victory = is_victory
            record.answer = answer
            record.score = score
            record.durability_change = durability_change
            record.status = 'completed'
            record.completed_at = datetime.now()
            if explanation is not None:
                record.explanation = explanation
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()
