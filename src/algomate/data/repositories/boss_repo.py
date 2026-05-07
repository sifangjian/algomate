from typing import List, Optional
from algomate.models.bosses import Boss
from ..database import Database


class BossRepository:

    def __init__(self, db: Database):
        self.db = db

    def get_all(self) -> List[Boss]:
        session = self.db.get_session()
        try:
            return session.query(Boss).all()
        finally:
            session.close()

    def get_by_id(self, boss_id: int) -> Optional[Boss]:
        session = self.db.get_session()
        try:
            return session.query(Boss).filter(Boss.id == boss_id).first()
        finally:
            session.close()

    def get_by_npc_id(self, npc_id: int) -> List[Boss]:
        session = self.db.get_session()
        try:
            return session.query(Boss).filter(Boss.npc_id == npc_id).all()
        finally:
            session.close()

    def get_by_weakness_type(self, weakness_type: str) -> List[Boss]:
        session = self.db.get_session()
        try:
            return session.query(Boss).filter(Boss.weakness_type == weakness_type).all()
        finally:
            session.close()
