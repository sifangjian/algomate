"""
应战记录仓库模块

提供应战记录数据的数据库操作，包括记录的创建、查询等功能。
"""

from typing import List, Optional
from datetime import datetime, timedelta
from algomate.models import AnswerRecord
from ..database import Database


class AnswerRecordRepository:
    """应战记录数据仓库

    负责应战记录数据的数据库操作。

    Attributes:
        db: 数据库实例
    """

    def __init__(self, db: Database):
        """初始化应战记录仓库

        Args:
            db: 数据库实例
        """
        self.db = db

    def create(
        self, card_id: int, user_answer: str, is_correct: bool, **kwargs
    ) -> AnswerRecord:
        """创建应战记录

        Args:
            card_id: 卡牌ID
            user_answer: 用户答案
            is_correct: 是否正确
            **kwargs: 其他可选参数（如 boss_id）

        Returns:
            创建的应战记录对象
        """
        session = self.db.get_session()
        try:
            record = AnswerRecord(
                card_id=card_id,
                user_answer=user_answer,
                is_correct=is_correct,
                **kwargs
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def get_by_id(self, record_id: int) -> Optional[AnswerRecord]:
        """根据ID获取应战记录

        Args:
            record_id: 记录ID

        Returns:
            应战记录对象，若不存在则返回 None
        """
        session = self.db.get_session()
        try:
            return session.query(AnswerRecord).filter(AnswerRecord.id == record_id).first()
        finally:
            session.close()

    def get_recent_records(self, days: int = 30) -> List[AnswerRecord]:
        """获取近期的应战记录

        Args:
            days: 天数，默认30天

        Returns:
            应战记录列表
        """
        session = self.db.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            return (
                session.query(AnswerRecord)
                .filter(AnswerRecord.answered_at >= cutoff_date)
                .all()
            )
        finally:
            session.close()

    def get_by_card_id(self, card_id: int) -> List[AnswerRecord]:
        """获取指定卡牌的所有应战记录

        Args:
            card_id: 卡牌ID

        Returns:
            应战记录列表
        """
        session = self.db.get_session()
        try:
            return (
                session.query(AnswerRecord)
                .filter(AnswerRecord.card_id == card_id)
                .order_by(AnswerRecord.answered_at.desc())
                .all()
            )
        finally:
            session.close()

    def get_all(self) -> List[AnswerRecord]:
        """获取所有应战记录

        按应战时间倒序返回。

        Returns:
            应战记录列表
        """
        session = self.db.get_session()
        try:
            return session.query(AnswerRecord).order_by(AnswerRecord.answered_at.desc()).all()
        finally:
            session.close()

    def get_completed_leetcode_urls(self) -> List[str]:
        session = self.db.get_session()
        try:
            urls = session.query(AnswerRecord.leetcode_url).filter(
                AnswerRecord.leetcode_url != "",
                AnswerRecord.is_correct == True
            ).distinct().all()
            return [url[0] for url in urls]
        finally:
            session.close()
