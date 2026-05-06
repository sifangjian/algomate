"""卡牌数据仓库模块"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy import func
from algomate.models.cards import Card
from algomate.core.game.durability import compute_card_status
from ..database import Database


class CardRepository:

    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, domain: str, **kwargs) -> Card:
        session = self.db.get_session()
        try:
            if kwargs.get("durability") == 0:
                kwargs["is_sealed"] = True
            card = Card(name=name, domain=domain, **kwargs)
            session.add(card)
            session.commit()
            session.refresh(card)
            return card
        finally:
            session.close()

    def get_by_id(self, card_id: int) -> Optional[Card]:
        session = self.db.get_session()
        try:
            return session.query(Card).filter(Card.id == card_id).first()
        finally:
            session.close()

    def get_all(self, domain: Optional[str] = None, algorithm_type: Optional[str] = None,
                is_sealed: Optional[bool] = None) -> List[Card]:
        session = self.db.get_session()
        try:
            query = session.query(Card)
            if domain is not None:
                query = query.filter(Card.domain == domain)
            if algorithm_type is not None:
                query = query.filter(Card.algorithm_type == algorithm_type)
            if is_sealed is not None:
                query = query.filter(Card.is_sealed == is_sealed)
            return query.order_by(Card.created_at.desc()).all()
        finally:
            session.close()

    def get_all_with_status(self, algorithm_type: Optional[str] = None,
                            status: Optional[str] = None,
                            keyword: Optional[str] = None) -> Dict:
        session = self.db.get_session()
        try:
            query = session.query(Card)
            if algorithm_type is not None:
                query = query.filter(Card.algorithm_type == algorithm_type)
            if keyword is not None:
                pattern = f"%{keyword}%"
                query = query.filter(
                    (Card.name.like(pattern)) | (Card.knowledge_content.like(pattern))
                )
            cards = query.order_by(Card.created_at.desc()).all()
            
            result_cards = []
            endangered_count = 0
            pending_retake_count = 0
            for card in cards:
                card_status = compute_card_status(card.durability, card.pending_retake or card.is_sealed)
                if status is not None and card_status != status:
                    continue
                if card_status == "endangered":
                    endangered_count += 1
                elif card_status == "pending_retake":
                    pending_retake_count += 1
                result_cards.append({
                    "card": card,
                    "status": card_status,
                })
            return {
                "cards": result_cards,
                "endangered_count": endangered_count,
                "pending_retake_count": pending_retake_count,
            }
        finally:
            session.close()

    def count_by_status(self) -> Dict[str, int]:
        session = self.db.get_session()
        try:
            cards = session.query(Card).all()
            counts = {"normal": 0, "endangered": 0, "pending_retake": 0}
            for card in cards:
                status = compute_card_status(card.durability, card.pending_retake or card.is_sealed)
                counts[status] = counts.get(status, 0) + 1
            return counts
        finally:
            session.close()

    def update(self, card_id: int, **kwargs) -> Optional[Card]:
        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if card is None:
                return None
            for key, value in kwargs.items():
                if value is not None:
                    setattr(card, key, value)
            if "durability" in kwargs and kwargs["durability"] == 0:
                card.is_sealed = True
            session.commit()
            session.refresh(card)
            return card
        finally:
            session.close()

    def delete(self, card_id: int) -> bool:
        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if card is None:
                return False
            session.delete(card)
            session.commit()
            return True
        finally:
            session.close()

    def get_critical(self, threshold: int = 30) -> List[Card]:
        session = self.db.get_session()
        try:
            return session.query(Card).filter(Card.durability < threshold).order_by(Card.durability.asc()).all()
        finally:
            session.close()

    def seal(self, card_id: int) -> Optional[Card]:
        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if card is None:
                return None
            card.is_sealed = True
            card.durability = 0
            session.commit()
            session.refresh(card)
            return card
        finally:
            session.close()

    def unseal(self, card_id: int, durability: int = 30) -> Optional[Card]:
        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if card is None:
                return None
            card.is_sealed = False
            card.durability = durability
            card.next_review_date = datetime.now() + timedelta(days=2 ** card.review_level)
            session.commit()
            session.refresh(card)
            return card
        finally:
            session.close()

    def count_by_domain(self) -> dict:
        session = self.db.get_session()
        try:
            results = session.query(Card.domain, func.count(Card.id)).group_by(Card.domain).all()
            return {domain: count for domain, count in results}
        finally:
            session.close()

    def get_by_algorithm_type(self, algorithm_type: str) -> List[Card]:
        session = self.db.get_session()
        try:
            return session.query(Card).filter(Card.algorithm_type == algorithm_type).order_by(Card.created_at.desc()).all()
        finally:
            session.close()

    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Card]:
        session = self.db.get_session()
        try:
            pattern = f"%{keyword}%"
            return session.query(Card).filter(
                (Card.name.like(pattern)) | (Card.algorithm_type.like(pattern)) | (Card.knowledge_content.like(pattern))
            ).order_by(Card.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def get_unsealed(self) -> List[Card]:
        session = self.db.get_session()
        try:
            return session.query(Card).filter(Card.is_sealed == False).all()
        finally:
            session.close()

    def count(self) -> int:
        session = self.db.get_session()
        try:
            return session.query(func.count(Card.id)).scalar()
        finally:
            session.close()

    def count_sealed(self) -> int:
        session = self.db.get_session()
        try:
            return session.query(func.count(Card.id)).filter(Card.is_sealed == True).scalar()
        finally:
            session.close()
